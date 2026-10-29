"""Real ASGI endpoint + fake provider; no paid/external calls."""
import asyncio
import copy
import json
from datetime import datetime, timedelta, timezone

import pytest

from test_contracts import enroll
from test_evidence_contract import request_fixture

PATH = '/api/physio/dialogue'


def valid_proposal(body):
    feature = body['evidence']['features'][0]
    return {'question_id': 'choose_words', 'expression_ids': ['wait_please'],
            'source_ids': [feature['source_id']], 'facts': [copy.deepcopy(feature)]}


@pytest.fixture
def provider(monkeypatch):
    import main
    calls = []

    async def fake(system, user, **kwargs):
        calls.append((system, json.loads(user), kwargs))
        projected = json.loads(user)
        feature = projected['features'][0]
        return json.dumps({'question_id': 'choose_words',
                           'expression_ids': ['wait_please'],
                           'source_ids': [feature['source_id']], 'facts': [feature]})

    async def forbidden(*args, **kwargs):
        pytest.fail('general cascade must never receive physio evidence')

    monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'true')
    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-test-key')
    monkeypatch.setattr(main, 'gemini_generate', fake)
    monkeypatch.setattr(main, 'llm_generate', forbidden)
    return calls


def test_authentication_and_revocation_precede_provider(client, provider):
    body = request_fixture()
    assert client.post(PATH, json=body).status_code == 401
    headers = enroll(client, 'self')
    assert client.delete('/api/devices/current', headers=headers).status_code == 200
    assert client.post(PATH, headers=headers, json=body).status_code == 401
    assert provider == []


@pytest.mark.parametrize('condition,reason', [
    ('disabled', 'disabled'), ('no_consent', 'consent_required'),
    ('no_key', 'provider_unconfigured'), ('unusable', 'evidence_unusable'),
    ('old', 'evidence_stale'), ('future', 'evidence_stale'),
])
def test_no_call_gates_are_structured(client, provider, monkeypatch, condition, reason):
    import main
    body = request_fixture()
    if condition == 'disabled':
        monkeypatch.delenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', raising=False)
    elif condition == 'no_consent':
        body['consent']['granted'] = False
    elif condition == 'no_key':
        monkeypatch.setattr(main, 'GEMINI_API_KEY', '')
    elif condition == 'unusable':
        body['evidence']['quality'] = {'status': 'insufficient',
                                      'reasons': ['missing_samples'], 'valid_fraction': .5}
    else:
        offset = -48 if condition == 'old' else 2
        for key in ['start', 'end']:
            date = datetime.fromisoformat(body['evidence']['window'][key])
            body['evidence']['window'][key] = (date + timedelta(hours=offset)).isoformat()
        body['evidence']['created_at'] = body['evidence']['window']['end']
    response = client.post(PATH, headers=enroll(client), json=body)
    assert response.status_code == 200
    assert response.json()['status'] == 'unavailable'
    assert response.json()['reason_code'] == reason
    assert response.json()['expression_ids'] == ['wait_please', 'help_please', 'stop_now', 'no_thanks']
    assert provider == []


def test_success_only_projects_allowed_scalars_and_never_identifies_user(client, provider, caplog):
    body = request_fixture()
    response = client.post(PATH, headers=enroll(client, 'self'), json=body)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'proposal' and result['proposal_only'] is True
    assert result['question'] == '지금 어떤 말이 필요한가요?'
    assert result['facts'] == body['evidence']['features']
    assert result['turn_id'] == body['turn_id']
    assert len(provider) == 1
    projection = provider[0][1]
    assert set(projection) == {'data_origin', 'quality', 'features', 'personal_baseline',
                               'predictions', 'limitations'}
    serialized = json.dumps(projection)
    for private in [body['turn_id'], body['evidence']['bundle_id'],
                    body['evidence']['created_at'], 'a' * 64]:
        assert private not in serialized and private not in caplog.text
    assert provider[0][2] == {'json_mode': True, 'max_tokens': 600}


def test_existing_gemini_adapter_is_connected_without_a_real_http_call(client, monkeypatch):
    import httpx
    import main
    captured = []

    class FakeHttpClient:
        async def post(self, url, **kwargs):
            captured.append((url, kwargs))
            projected = json.loads(kwargs['json']['contents'][0]['parts'][0]['text'])
            feature = projected['features'][0]
            answer = {'question_id': 'choose_words', 'expression_ids': ['no_thanks'],
                      'source_ids': [feature['source_id']], 'facts': []}
            return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
                {'text': json.dumps(answer)}]}}]})

    async def get_fake_client():
        return FakeHttpClient()

    async def forbidden(*args, **kwargs):
        pytest.fail('physio adapter must not enter general cascade')

    monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'true')
    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-test-key')
    monkeypatch.setattr(main, 'get_client', get_fake_client)
    monkeypatch.setattr(main, 'llm_generate', forbidden)
    response = client.post(PATH, headers=enroll(client), json=request_fixture())
    assert response.json()['status'] == 'proposal'
    assert len(captured) == 1
    assert captured[0][0].startswith('https://generativelanguage.googleapis.com/')
    assert captured[0][1]['json']['generationConfig']['responseMimeType'] == 'application/json'


@pytest.mark.parametrize('mutation', ['emotion', 'number', 'unit', 'unknown_source',
                                      'uncited_fact', 'duplicate', 'extra_text',
                                      'missing', 'empty', 'nonjson', 'huge'])
def test_bad_provider_answer_is_never_success(client, provider, monkeypatch, mutation):
    import main
    body = request_fixture()
    answer = valid_proposal(body)
    if mutation == 'emotion':
        answer['question_id'] = 'you_are_stressed'
    elif mutation == 'number':
        answer['facts'][0]['value'] = 99
    elif mutation == 'unit':
        answer['facts'][0]['unit'] = 'arbitrary_unit'
    elif mutation == 'unknown_source':
        answer['source_ids'] = ['00000000-0000-4000-8000-000000000099']
    elif mutation == 'uncited_fact':
        new_feature = copy.deepcopy(body['evidence']['features'][0])
        new_feature.update(id='signal_mean', source='signal_summary', unit='arbitrary_unit',
                           source_id='00000000-0000-4000-8000-000000000098')
        body['evidence']['features'].append(new_feature)
        answer['source_ids'] = [new_feature['source_id']]
    elif mutation == 'duplicate':
        answer['expression_ids'] *= 2
    elif mutation == 'extra_text':
        answer['explanation'] = 'You feel anxious and need support.'
    elif mutation == 'missing':
        answer.pop('question_id')
    raw = json.dumps(answer)
    if mutation == 'empty': raw = ''
    if mutation == 'nonjson': raw = 'model unavailable'
    if mutation == 'huge': raw = 'x' * 16385

    async def fake(*args, **kwargs):
        return raw

    monkeypatch.setattr(main, 'gemini_generate', fake)
    response = client.post(PATH, headers=enroll(client), json=body)
    assert response.json()['status'] == 'unavailable'
    assert response.json()['reason_code'] == 'invalid_provider_response'
    assert response.json()['facts'] == []


@pytest.mark.parametrize('failure,reason', [('timeout', 'provider_timeout'),
                                          ('error', 'provider_error'),
                                          ('revoke', 'consent_changed')])
def test_provider_failure_or_flag_change_preserves_fallback(client, provider, monkeypatch,
                                                           caplog, failure, reason):
    import main
    from services import grounded_dialogue_service
    body = request_fixture()

    async def fake(*args, **kwargs):
        if failure == 'timeout':
            await asyncio.sleep(.2)
        if failure == 'error':
            raise RuntimeError('private-evidence-and-key-must-not-escape')
        monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'false')
        return json.dumps(valid_proposal(body))

    monkeypatch.setattr(grounded_dialogue_service, 'PROVIDER_TIMEOUT_SECONDS', .01)
    monkeypatch.setattr(main, 'gemini_generate', fake)
    response = client.post(PATH, headers=enroll(client), json=body)
    assert response.json()['reason_code'] == reason
    assert 'private-evidence-and-key' not in response.text + caplog.text


@pytest.mark.parametrize('change', ['user_id', 'raw', 'purpose', 'provider', 'granted'])
def test_sensitive_or_wrong_purpose_request_never_calls_provider(client, provider, change):
    body = request_fixture()
    path = PATH
    if change == 'user_id': path += '?user_id=someone-else'
    elif change == 'raw': body['evidence']['raw_ppg'] = [1, 2, 3]
    elif change == 'purpose': body['consent']['purpose'] = 'general_chat'
    elif change == 'provider': body['consent']['provider'] = 'groq'
    elif change == 'granted': body['consent']['granted'] = 'true'
    response = client.post(path, headers=enroll(client), json=body)
    assert response.status_code == 422
    assert response.json()['reason_code'] == 'invalid_request'
    assert provider == []


@pytest.mark.parametrize('raw,status', [(b'{broken', 422), (b'x' * 32769, 413)],
                         ids=['malformed-json', 'oversize-body'])
def test_malformed_and_oversize_input_is_bounded(client, provider, raw, status):
    response = client.post(PATH, headers=enroll(client), content=raw)
    assert response.status_code == status
    assert response.json()['status'] == 'unavailable'
    assert provider == []
