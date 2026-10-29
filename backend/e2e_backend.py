"""Opt-in HTTP contract smoke test against the keyless local_server.py.

Run manually: python -B e2e_backend.py. No module-import network side effects.
All failed assertions produce a nonzero exit. Tokens are never printed.
"""
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx
from contracts import DraftResponse, DraftItem


def main():
    base = os.getenv('HIBUDDY_TEST_BASE_URL', 'http://127.0.0.1:8010')
    if urlparse(base).hostname not in {'localhost', '127.0.0.1', '::1'}:
        raise RuntimeError('Use an explicitly started local test server')
    with httpx.Client(base_url=base, timeout=30) as client:
        health = client.get('/health')
        assert health.status_code == 200 and health.json()['local_draft'], 'Start keyless local_server.py first'
        def enroll(role):
            response = client.post('/api/devices/enroll', json={'role': role})
            assert response.status_code == 200
            return {'Authorization': 'Bearer ' + response.json()['device_token']}
        owner, recipient = enroll('coordinator'), enroll('self')
        response = client.post('/api/schedule/generate', headers=owner, json={'text': '08:00 아침 준비\n12:00 식사 준비'})
        assert response.status_code == 200
        draft = DraftResponse.model_validate(response.json())
        assert len(draft.schedule) == 2
        current = draft.schedule[0].model_dump()
        edited = client.post('/api/schedule/edit', headers=owner, json={'current_item': current, 'request': '시간을 09:00으로 변경'})
        assert edited.status_code == 200
        validated = DraftItem.model_validate(edited.json())
        assert validated.time == '09:00' and validated.task == current['task']
        envelope = {'schema_version': 1, 'plan': {'id': str(uuid.uuid4()), 'version_number': 1,
                    'date': '2026-10-11', 'status': 'published', 'approved_by': 'synthetic-approver',
                    'published_at': datetime.now(timezone.utc).isoformat()},
                    'activities': [{**current, 'id': str(uuid.uuid4())}]}
        assert client.post('/api/schedule/save', headers=owner, json=envelope).status_code == 200
        assert client.get('/api/schedule/load', headers=recipient).status_code == 403
        code = client.post('/api/pairing/code', headers=owner).json()['code']
        accepted = client.post('/api/pairing/accept', headers=recipient, json={'code': code})
        assert accepted.status_code == 200
        received = client.get('/api/schedule/load', headers=recipient)
        assert received.status_code == 200 and received.json()['plan'] == envelope['plan']
        assert client.delete('/api/pairing/' + accepted.json()['link_id'], headers=recipient).status_code == 200
        assert client.get('/api/schedule/load', headers=recipient).status_code == 403
    print('PASS local HTTP draft/edit/published-plan/pair/receive/revoke contracts')


if __name__ == '__main__':
    main()
