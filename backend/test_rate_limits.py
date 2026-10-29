"""Same-IP synthetic devices with the real auth dependency and enabled limiter.

Provider calls are mocked; onboarding fixtures use only a test-owned DB.
Public enrollment limits are exercised separately without fixture shortcuts.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import uuid

from fastapi.testclient import TestClient
import pytest
from starlette.requests import Request


@pytest.fixture
def limited_client(tmp_path, monkeypatch):
    import main
    from device_store import DeviceStore

    monkeypatch.setattr(main, 'device_store', DeviceStore(tmp_path / 'devices.db'))
    monkeypatch.setattr(main.limiter, 'enabled', True)
    monkeypatch.setattr(main, 'CLAUDE_API_KEY', '')
    main.limiter.reset()
    calls = []

    async def mock_provider(*args, **kwargs):
        calls.append('synthetic')
        return '합성 시험 응답이에요.'

    monkeypatch.setattr(main, 'llm_generate', mock_provider)
    try:
        with TestClient(main.app) as client:
            yield client, calls
    finally:
        main.limiter.reset()


def headers(credential):
    return {'Authorization': 'Bearer ' + credential['device_token']}


def published_plan():
    return {
        'schema_version': 1,
        'plan': {'id': str(uuid.uuid4()), 'version_number': 1,
                 'date': '2026-10-14', 'status': 'published',
                 'approved_by': 'synthetic-rate-test',
                 'published_at': datetime.now(timezone.utc).isoformat()},
        'activities': [{'id': str(uuid.uuid4()), 'time': '08:00', 'type': 'GENERAL',
                        'task': '합성 준비', 'guide_script': ['필요한 것을 준비해요.']}],
    }


def test_same_ip_twenty_verified_devices_chat_and_receive(limited_client, monkeypatch):
    import main
    client, calls = limited_client
    # Test-owned storage fixtures avoid changing or waiting out public onboarding policy.
    devices = [main.device_store.enroll('coordinator') for _ in range(20)]

    def no_ip_fallback(_request):
        raise AssertionError('Verified dependency must run before limiter key selection')

    monkeypatch.setattr(main, 'get_remote_address', no_ip_fallback)

    def use_device(credential):
        auth = headers(credential)
        plan = published_plan()
        assert client.post('/api/schedule/save', headers=auth, json=plan).status_code == 200
        for _ in range(2):
            response = client.post('/api/agent', headers=auth, json={'input': '합성 질문'})
            assert response.status_code == 200
            response = client.get('/api/schedule/load', headers=auth)
            assert response.status_code == 200
            assert response.json()['plan']['id'] == plan['plan']['id']

    with ThreadPoolExecutor(max_workers=20) as pool:
        list(pool.map(use_device, devices))
    assert len(calls) == 40


def test_same_device_limit_remains_and_other_device_is_unaffected(limited_client):
    import main
    client, calls = limited_client
    one, two = [headers(main.device_store.enroll('coordinator')) for _ in range(2)]
    for _ in range(20):
        assert client.post('/api/agent', headers=one, json={'input': '합성 질문'}).status_code == 200
    assert client.post('/api/agent', headers=one, json={'input': '합성 질문'}).status_code == 429
    assert client.post('/api/agent', headers=two, json={'input': '합성 질문'}).status_code == 200
    assert len(calls) == 21
    plan = published_plan()
    assert client.post('/api/schedule/save', headers=one, json=plan).status_code == 200
    for _ in range(30):
        assert client.get('/api/schedule/load', headers=one).status_code == 200
    assert client.get('/api/schedule/load', headers=one).status_code == 429
    assert client.post('/api/schedule/save', headers=two, json=published_plan()).status_code == 200
    assert client.get('/api/schedule/load', headers=two).status_code == 200


def test_unauthenticated_enrollment_cannot_split_ip_limit_by_headers(limited_client):
    client, _ = limited_client
    for index in range(10):
        response = client.post('/api/devices/enroll', json={'role': 'self'}, headers={
            'Authorization': f'Bearer fake-{index}', 'X-Device-ID': f'fake-{index}',
            'X-Forwarded-For': f'192.0.2.{index}',
        })
        assert response.status_code == 200
    assert client.post('/api/devices/enroll', json={'role': 'self'}, headers={
        'Authorization': 'Bearer another-fake', 'X-Device-ID': 'another-fake',
        'X-Forwarded-For': '192.0.2.99',
    }).status_code == 429


def test_invalid_and_revoked_credentials_never_reach_provider_or_get_identity(limited_client):
    import main
    client, calls = limited_client
    for index in range(25):
        assert client.post('/api/agent', headers={'Authorization': f'Bearer fake-{index}'},
                           json={'input': '합성 질문'}).status_code == 401
    credential = main.device_store.enroll('self')
    auth = headers(credential)
    assert client.delete('/api/devices/current', headers=auth).status_code == 200
    assert client.post('/api/agent', headers=auth, json={'input': '합성 질문'}).status_code == 401
    assert calls == []
    request = Request({'type': 'http', 'client': ('192.0.2.1', 1234),
                       'headers': [(b'authorization', b'Bearer fake'), (b'x-device-id', b'fake')]})
    with pytest.raises(main.HTTPException):
        main.verify_token(request)
    assert not hasattr(request.state, 'verified_device_id')
    assert main.rate_limit_key(request) == 'ip:192.0.2.1'
