"""Synthetic regressions for active APIs; no provider calls or user data."""
import asyncio
import logging

import httpx
import pytest
from fastapi import HTTPException

from test_contracts import enroll


@pytest.mark.parametrize('path,method,body', [
    ('/api/schedule/generate', 'post', {'text': 'synthetic'}),
    ('/api/schedule/edit', 'post', {'current_item': {}, 'request': 'synthetic'}),
    ('/api/agent', 'post', {'input': 'synthetic'}),
    ('/api/clothing', 'post', {'temp': 20}),
    ('/api/tts', 'post', {'text': 'synthetic'}),
    ('/api/errors', 'post', {}),
    ('/api/youtube/search?q=synthetic', 'get', None),
    ('/api/image/search?q=synthetic', 'get', None),
    ('/api/recipes', 'get', None),
])
def test_active_apis_require_device_credential(client, path, method, body):
    response = client.request(method, path, **({'json': body} if body is not None else {}))
    assert response.status_code == 401


@pytest.mark.parametrize('field,value', [
    ('profile_name', 'synthetic-name'), ('disability_level', 'mild'),
    ('ingredients', ['synthetic']), ('today_schedule', ['synthetic']),
    ('recent_completions', ['synthetic']), ('emergency_contacts', ['synthetic']),
])
def test_agent_rejects_legacy_personal_context(client, field, value):
    response = client.post('/api/agent', headers=enroll(client),
                           json={'input': 'synthetic', 'context': {field: value}})
    assert response.status_code == 422


def test_agent_uses_catalog_without_invented_diagnostic_or_available_ingredients(client, monkeypatch):
    import main
    captured = {}

    async def fake(system, user, **kwargs):
        captured.update(system=system, user=user)
        return '선택할 수 있어요.'

    monkeypatch.setattr(main, 'CLAUDE_API_KEY', '')
    monkeypatch.setattr(main, 'llm_generate', fake)
    response = client.post('/api/agent', headers=enroll(client), json={
        'input': 'synthetic', 'context': {'available_recipes': ['synthetic-catalog-item']}})
    assert response.status_code == 200
    assert 'synthetic-catalog-item' in captured['system']
    assert 'mild' not in captured['system']
    assert '장애 정도:' not in captured['system']
    assert '재료가 있다는 뜻은 아니다' in captured['system']


@pytest.mark.parametrize('output', ['', '  ', None, {}])
def test_agent_rejects_empty_or_nontext_provider_response(client, monkeypatch, output):
    import main

    async def fake(*args, **kwargs):
        return output

    monkeypatch.setattr(main, 'CLAUDE_API_KEY', '')
    monkeypatch.setattr(main, 'llm_generate', fake)
    response = client.post('/api/agent', headers=enroll(client), json={'input': 'synthetic'})
    assert response.status_code == 502


def test_upstream_error_body_never_reaches_client_or_logs(caplog):
    import main
    marker = 'synthetic private prompt and short-secret'
    with caplog.at_level(logging.WARNING), pytest.raises(HTTPException) as caught:
        main.raise_for_upstream(httpx.Response(400, text=marker), 'SyntheticProvider')
    assert marker not in str(caught.value.detail)
    assert marker not in caplog.text


def test_cascade_does_not_log_exception_content(monkeypatch, caplog):
    import main
    marker = 'synthetic-secret-in-request-url'

    async def fail(*args, **kwargs):
        raise RuntimeError(marker)

    monkeypatch.setattr(main, 'GEMINI_API_KEY', 'synthetic')
    monkeypatch.setattr(main, 'LLM_CASCADE', ['gemini'])
    monkeypatch.setattr(main, 'gemini_generate', fail)
    with caplog.at_level(logging.WARNING), pytest.raises(HTTPException):
        asyncio.run(main.llm_generate('synthetic', 'synthetic'))
    assert marker not in caplog.text


def test_error_collector_bounds_body_before_parsing(client):
    response = client.post('/api/errors', headers=enroll(client), content=b'x' * (65536 + 1))
    assert response.status_code == 413


@pytest.mark.parametrize('field,value', [('name', 'synthetic'), ('disability_level', 'mild')])
def test_clothing_rejects_personal_context(client, field, value):
    response = client.post('/api/clothing', headers=enroll(client),
                           json={'temp': 20, field: value})
    assert response.status_code == 422
