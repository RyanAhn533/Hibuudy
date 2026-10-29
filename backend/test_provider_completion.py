"""Incomplete, filtered or malformed provider output is never text success."""
import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException

from test_contracts import enroll
from test_evidence_contract import request_fixture


def response(provider, finish, text='합성 응답이에요.'):
    if provider == 'gemini':
        return httpx.Response(200, json={'candidates': [{
            'finishReason':finish, 'content':{'parts':[{'text':text}]}}]})
    if provider == 'claude':
        return httpx.Response(200, json={'stop_reason':finish,
            'content':[{'type':'text','text':text}]})
    return httpx.Response(200, json={'choices':[{
        'finish_reason':finish,'message':{'content':text}}]})


@pytest.mark.parametrize('provider,finish', [
    ('cerebras','length'),('cerebras','content_filter'),('cerebras','tool_calls'),
    ('cerebras',None),('gemini','MAX_TOKENS'),('gemini','SAFETY'),
    ('gemini',None),('claude','max_tokens'),('claude','tool_use'),
    ('claude','pause_turn'),('claude',None),
])
def test_nonempty_incomplete_output_rejected(provider, finish):
    import main
    with pytest.raises(HTTPException) as caught:
        main.completed_provider_text(response(provider, finish), provider)
    assert caught.value.status_code == 502


@pytest.mark.parametrize('provider,finish', [('cerebras','stop'),('gemini','STOP'),('claude','end_turn')])
def test_normally_finished_text_can_pass(provider, finish):
    import main
    assert main.completed_provider_text(response(provider, finish), provider) == '합성 응답이에요.'


@pytest.mark.parametrize('provider,finish', [('cerebras','stop'),('gemini','STOP'),('claude','end_turn')])
@pytest.mark.parametrize('text', ['', '  ', None, {}, 123])
def test_finished_but_empty_or_nontext_output_rejected(provider, finish, text):
    import main
    with pytest.raises(HTTPException) as caught:
        main.completed_provider_text(response(provider, finish, text), provider)
    assert caught.value.status_code == 502


@pytest.mark.parametrize('payload', [{}, [], None, {'choices':None}, {'choices':[None]}])
def test_malformed_body_is_fixed_error_not_uncaught_or_echoed(payload):
    import main
    with pytest.raises(HTTPException) as caught:
        main.completed_provider_text(httpx.Response(200,json=payload), 'cerebras')
    assert caught.value.status_code == 502
    assert '완성된 텍스트' in caught.value.detail


@pytest.mark.parametrize('provider', ['gemini','claude'])
def test_thinking_block_not_used_as_answer_and_final_spacing_preserved(provider):
    import main
    if provider == 'gemini':
        body={'candidates':[{'finishReason':'STOP','content':{'parts':[
            {'thought':True,'text':'private intermediate thought'},
            {'text':'잠깐 '},{'text':'기다려 주세요.'}]}}]}
    else:
        body={'stop_reason':'end_turn','content':[
            {'type':'thinking','thinking':'private intermediate thought'},
            {'type':'text','text':'잠깐 '},{'type':'text','text':'기다려 주세요.'}]}
    assert main.completed_provider_text(httpx.Response(200,json=body),provider) == '잠깐 기다려 주세요.'


@pytest.mark.parametrize('provider,finish', [('cerebras','length'),('gemini','MAX_TOKENS'),('claude','max_tokens')])
def test_agent_does_not_publish_incomplete_text(client, monkeypatch, provider, finish):
    import main
    calls=[]
    for name in ['CLAUDE_API_KEY','GEMINI_API_KEY','CEREBRAS_API_KEY']:
        monkeypatch.setattr(main,name,'')
    monkeypatch.setattr(main,provider.upper()+'_API_KEY','synthetic-key')
    monkeypatch.setattr(main,'LLM_CASCADE', [] if provider=='claude' else [provider])
    class FakeClient:
        async def post(self,*args,**kwargs):
            calls.append(1)
            return response(provider,finish)
    async def fake_client():return FakeClient()
    monkeypatch.setattr(main,'get_client',fake_client)
    result=client.post('/api/agent',headers=enroll(client),json={'input':'합성 질문'})
    assert result.status_code == 503 and 'text' not in result.json()
    assert len(calls) == 1


def test_truncated_but_valid_physio_json_is_unavailable_without_general_fallback(client,monkeypatch):
    import main
    body=request_fixture()
    answer={'question_id':'choose_words','expression_ids':['no_thanks'],
            'source_ids':[body['evidence']['features'][0]['source_id']],'facts':[]}
    class FakeClient:
        async def post(self,*args,**kwargs):
            return response('gemini','MAX_TOKENS',json.dumps(answer))
    async def fake_client():return FakeClient()
    async def forbidden(*args,**kwargs):pytest.fail('physio must not cascade')
    monkeypatch.setenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED','true')
    monkeypatch.setattr(main,'GEMINI_API_KEY','synthetic-key')
    monkeypatch.setattr(main,'get_client',fake_client)
    monkeypatch.setattr(main,'llm_generate',forbidden)
    result=client.post('/api/physio/dialogue',headers=enroll(client),json=body)
    assert result.status_code == 200 and result.json()['status']=='unavailable'
    assert result.json()['reason_code']=='provider_error'
    assert result.json()['facts']==[]
