"""Real loopback HTTP, synthetic devices, and a mocked provider transport.

These tests exercise the running Uvicorn/API/auth/adapter stack. They do NOT
prove that any remote model is available or that its output is useful.
conftest.py prevents dotenv loading and owns the temporary storage.
"""
import asyncio
import json
import socket
import threading
import time

import httpx
import pytest
import uvicorn

from test_evidence_contract import request_fixture


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    import main
    from device_store import DeviceStore

    for name in ['CLAUDE_API_KEY', 'GEMINI_API_KEY', 'GROQ_API_KEY',
                 'UPSTAGE_API_KEY', 'OPENROUTER_API_KEY', 'CEREBRAS_API_KEY']:
        monkeypatch.setattr(main, name, '')
    monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'false')
    monkeypatch.setattr(main, 'device_store', DeviceStore(tmp_path / 'devices.db'))
    # Rate-limit/abuse policy is outside this transport and contract test.
    monkeypatch.setattr(main.limiter, 'enabled', False)
    monkeypatch.setattr(main, 'LLM_CASCADE', ['gemini', 'cerebras'])
    calls = []
    responses = {}

    async def respond(request):
        host = request.url.host
        # Inspect public routing metadata and synthetic request bodies only.
        calls.append((host, json.loads(request.content)))
        answer = responses.get(host)
        if answer is None:
            raise AssertionError('No external provider transport is allowed')
        if callable(answer):
            answer = answer(request)
            if asyncio.iscoroutine(answer):
                answer = await answer
        return answer

    provider = httpx.AsyncClient(transport=httpx.MockTransport(respond), trust_env=False)

    async def fake_client():
        return provider

    monkeypatch.setattr(main, 'get_client', fake_client)
    real_connect = socket.socket.connect

    def loopback_only(sock, address):
        # Even a future accidental non-mocked network path must fail locally.
        if not isinstance(address, tuple) or address[0] not in {'127.0.0.1', '::1'}:
            raise AssertionError('Non-loopback socket blocked by runtime test')
        return real_connect(sock, address)

    monkeypatch.setattr(socket.socket, 'connect', loopback_only)
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(main.app, log_level='error', access_log=False))
    worker = threading.Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True)
    worker.start()
    deadline = time.monotonic() + 5
    while not server.started and worker.is_alive() and time.monotonic() < deadline:
        time.sleep(.01)
    try:
        assert server.started, 'Local HTTP server did not start'
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=5,
                          trust_env=False) as http:
            response = http.post('/api/devices/enroll', json={'role': 'self'})
            assert response.status_code == 200
            headers = {'Authorization': 'Bearer ' + response.json()['device_token']}
            yield http, headers, calls, responses
    finally:
        server.should_exit = True
        worker.join(timeout=5)
        listener.close()
        asyncio.run(provider.aclose())
        assert not worker.is_alive(), 'Local HTTP server did not stop'


def gemini_answer(value):
    return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': value}]}}]})


def test_http_auth_keyless_failure_and_revocation(runtime):
    http, headers, calls, _ = runtime
    body = {'input': '합성 시험 질문'}
    assert http.post('/api/agent', json=body).status_code == 401
    health = http.get('/health').json()
    assert health['auth'] == 'device' and not any(health['llm_providers'].values())
    assert health['api_contract'] == 'hibuddy-device-v1'
    assert health['plan_schema_version'] == 1
    assert health['capabilities'] == {
        'device_enrollment': True, 'pairing': True, 'approved_plan_sync': True,
    }
    # Public compatibility checks must not require exposing internal wire schemas.
    assert http.get('/openapi.json').status_code == 404
    assert http.get('/docs').status_code == 404
    response = http.post('/api/agent', headers=headers, json=body)
    assert response.status_code == 503 and 'text' not in response.json()
    assert http.delete('/api/devices/current', headers=headers).status_code == 200
    assert http.post('/api/agent', headers=headers, json=body).status_code == 401
    assert calls == []


def test_http_claude_priority_mock_is_only_text(runtime, monkeypatch):
    import main
    http, headers, calls, responses = runtime
    monkeypatch.setattr(main, 'CLAUDE_API_KEY', 'synthetic-not-a-key')
    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-not-a-key')
    responses['api.anthropic.com'] = httpx.Response(200, json={
        'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': '합성 응답이에요.'}]})
    response = http.post('/api/agent', headers=headers, json={'input': '합성 질문'})
    assert response.status_code == 200 and response.json() == {'text': '합성 응답이에요.'}
    assert [host for host, _ in calls] == ['api.anthropic.com']
    assert calls[0][1]['model'] == main.CLAUDE_MODEL


def test_http_cascade_mock_fallback_preserves_adapter_model(runtime, monkeypatch):
    import main
    http, headers, calls, responses = runtime
    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-not-a-key')
    monkeypatch.setattr(main, 'CEREBRAS_API_KEY', 'synthetic-not-a-key')
    responses['generativelanguage.googleapis.com'] = httpx.Response(503)
    responses['api.cerebras.ai'] = httpx.Response(200, json={
        'choices': [{'finish_reason': 'stop', 'message': {'content': '다른 합성 응답이에요.'}}]})
    response = http.post('/api/agent', headers=headers, json={'input': '합성 질문'})
    assert response.status_code == 200 and response.json()['text'] == '다른 합성 응답이에요.'
    assert [host for host, _ in calls] == ['generativelanguage.googleapis.com', 'api.cerebras.ai']
    assert calls[1][1]['model'] == main.CEREBRAS_MODEL


def test_http_empty_chat_response_is_not_success(runtime, monkeypatch):
    import main
    http, headers, calls, responses = runtime
    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-not-a-key')
    responses['generativelanguage.googleapis.com'] = gemini_answer('   ')
    response = http.post('/api/agent', headers=headers, json={'input': '합성 질문'})
    assert response.status_code == 503 and 'text' not in response.json()
    assert len(calls) == 1


@pytest.mark.parametrize('case,reason', [('disabled', 'disabled'),
                                      ('no_consent', 'consent_required'),
                                      ('no_key', 'provider_unconfigured')])
def test_http_physio_no_call_gates(runtime, monkeypatch, case, reason):
    import main
    http, headers, calls, _ = runtime
    body = request_fixture()
    if case != 'disabled':
        monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'true')
    if case != 'no_key':
        monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-not-a-key')
    if case == 'no_consent':
        body['consent']['granted'] = False
    response = http.post('/api/physio/dialogue', headers=headers, json=body)
    result = response.json()
    assert response.status_code == 200 and result['status'] == 'unavailable'
    assert result['reason_code'] == reason and result['proposal_only'] is True
    assert result['facts'] == [] and len(result['expression_ids']) == 4
    assert calls == []


@pytest.mark.parametrize('invalid', [False, True], ids=['mock-proposal', 'unsupported-emotion'])
def test_http_physio_mock_only_bounded_proposal(runtime, monkeypatch, invalid):
    import main
    http, headers, calls, responses = runtime
    monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'true')
    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-not-a-key')
    body = request_fixture()
    proposal = {'question_id': 'you_are_anxious' if invalid else 'choose_words',
                'expression_ids': ['no_thanks'],
                'source_ids': [body['evidence']['features'][0]['source_id']], 'facts': []}
    responses['generativelanguage.googleapis.com'] = gemini_answer(json.dumps(proposal))
    response = http.post('/api/physio/dialogue', headers=headers, json=body)
    result = response.json()
    assert response.status_code == 200 and result['proposal_only'] is True
    assert result['status'] == ('unavailable' if invalid else 'proposal')
    assert result['reason_code'] == ('invalid_provider_response' if invalid else 'none')
    assert result['question'] == '지금 어떤 말이 필요한가요?'
    assert len(calls) == 1
    projected = json.loads(calls[0][1]['contents'][0]['parts'][0]['text'])
    assert set(projected) == {'data_origin', 'quality', 'features',
                              'personal_baseline', 'predictions', 'limitations'}


@pytest.mark.parametrize('failure,reason', [('error', 'provider_error'),
                                          ('timeout', 'provider_timeout')])
def test_http_physio_never_cascades_on_failure(runtime, monkeypatch, failure, reason):
    import main
    from services import grounded_dialogue_service
    http, headers, calls, responses = runtime
    monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'true')
    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-not-a-key')
    monkeypatch.setattr(main, 'CEREBRAS_API_KEY', 'synthetic-not-a-key')
    if failure == 'timeout':
        async def delayed(_):
            await asyncio.sleep(.2)
            return gemini_answer('{}')
        responses['generativelanguage.googleapis.com'] = delayed
        monkeypatch.setattr(grounded_dialogue_service, 'PROVIDER_TIMEOUT_SECONDS', .01)
    else:
        responses['generativelanguage.googleapis.com'] = httpx.Response(503)
    response = http.post('/api/physio/dialogue', headers=headers, json=request_fixture())
    assert response.status_code == 200 and response.json()['status'] == 'unavailable'
    assert response.json()['reason_code'] == reason
    assert [host for host, _ in calls] == ['generativelanguage.googleapis.com']


def test_http_physio_auth_and_sensitive_extra_fields_reject_before_adapter(runtime, monkeypatch):
    import main
    http, headers, calls, _ = runtime
    monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'true')
    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic-not-a-key')
    body = request_fixture()
    assert http.post('/api/physio/dialogue', json=body).status_code == 401
    body['evidence']['raw_ppg'] = [1, 2]
    response = http.post('/api/physio/dialogue', headers=headers, json=body)
    assert response.status_code == 422 and response.json()['reason_code'] == 'invalid_request'
    assert calls == []
