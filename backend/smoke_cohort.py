"""Twenty synthetic devices against an owned keyless loopback server.

No load claim for real participants, providers, phones or deployment. Uses the
unchanged public enrollment throttle; one delayed retry follows a 429 response.
Run: python -B smoke_cohort.py [--output <local evidence JSON>]
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import time
import uuid

from contracts import PlanEnvelope
from smoke_contract import expect, local_server


def auth(credential):
    return {'Authorization': 'Bearer ' + credential['device_token']}


def counts(responses):
    return dict(sorted(Counter(str(item.status_code) for item in responses).items()))


def run():
    result = {'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'scope': '20 synthetic devices, 10 pairs, one loopback IP; not real-user load validation',
              'remote_requests': 0, 'live_model_calls': 0}
    with tempfile.TemporaryDirectory(prefix='hibuddy-cohort-smoke-') as temporary:
        root = Path(temporary)
        with local_server(root / 'data', root / 'server.log') as client:
            health = client.get('/health').json()
            assert health['local_draft'] and not any(health['llm_providers'].values()), 'keyless server'
            assert health['api_contract'] == 'hibuddy-device-v1', 'contract identity'
            roles = ['coordinator', 'self'] * 10

            def enroll(role):
                return client.post('/api/devices/enroll', json={'role': role})

            with ThreadPoolExecutor(max_workers=20) as pool:
                first = list(pool.map(enroll, roles))
            result['enrollment_first_burst_statuses'] = counts(first)
            assert result['enrollment_first_burst_statuses'] == {'200': 10, '429': 10}, 'public enrollment throttle'
            credentials = [response.json() if response.status_code == 200 else None for response in first]
            waiting = [index for index, value in enumerate(credentials) if value is None]
            print(json.dumps({'phase': 'enrollment_limited_as_expected', 'retry_after_seconds': 61}), flush=True)
            time.sleep(31)
            print(json.dumps({'phase': 'enrollment_cooldown', 'remaining_seconds': 30}), flush=True)
            time.sleep(30)
            with ThreadPoolExecutor(max_workers=10) as pool:
                retry = list(pool.map(enroll, [roles[index] for index in waiting]))
            result['enrollment_retry_statuses'] = counts(retry)
            for index, response in zip(waiting, retry):
                credentials[index] = expect(response, 200, 'enrollment retry').json()
            owners = [item for item in credentials if item['role'] == 'coordinator']
            recipients = [item for item in credentials if item['role'] == 'self']

            def publish_and_pair(pair):
                owner, recipient = pair
                owner_auth, recipient_auth = auth(owner), auth(recipient)
                draft = expect(client.post('/api/schedule/generate', headers=owner_auth,
                    json={'text': '08:00 합성 준비'}), 200, 'keyless draft').json()['schedule'][0]
                envelope = PlanEnvelope.model_validate({
                    'schema_version': 1,
                    'plan': {'id': str(uuid.uuid4()), 'version_number': 1, 'date': '2026-10-14',
                             'status': 'published', 'approved_by': 'synthetic-cohort',
                             'published_at': datetime.now(timezone.utc).isoformat()},
                    'activities': [{**draft, 'id': str(uuid.uuid4())}],
                }).model_dump(mode='json')
                expect(client.post('/api/schedule/save', headers=owner_auth, json=envelope), 200, 'publish')
                code = expect(client.post('/api/pairing/code', headers=owner_auth), 200, 'offer').json()['code']
                expect(client.post('/api/pairing/accept', headers=recipient_auth, json={'code': code}), 200, 'accept')
                return envelope

            phase_start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=10) as pool:
                plans = list(pool.map(publish_and_pair, zip(owners, recipients)))
            result['pairs_published_and_connected'] = len(plans)
            result['pairing_publish_elapsed_ms'] = round((time.perf_counter() - phase_start) * 1000)

            def receive(item):
                credential, envelope = item
                for _ in range(2):
                    received = expect(client.get('/api/schedule/load', headers=auth(credential)), 200, 'receive').json()
                    assert received == envelope, 'exact approved envelope'

            phase_start = time.perf_counter()
            all_devices = list(zip(owners, plans)) + list(zip(recipients, plans))
            with ThreadPoolExecutor(max_workers=20) as pool:
                list(pool.map(receive, all_devices))
            result['schedule_loads_200'] = 40
            result['concurrent_load_elapsed_ms'] = round((time.perf_counter() - phase_start) * 1000)
            # Cross-owner query/recipient publication cannot exploit the rate-key change.
            denied = client.get('/api/schedule/load', headers=auth(recipients[0]),
                                params={'user_id': owners[1]['device_id']})
            expect(denied, 422, 'caller-selected owner rejected')
            expect(client.post('/api/schedule/save', headers=auth(recipients[0]), json=plans[0]),
                   403, 'recipient cannot publish')
            for credential in credentials:
                expect(client.delete('/api/devices/current', headers=auth(credential)), 200, 'revoke test device')
            result['devices_revoked'] = len(credentials)
    return {**result, 'status': 'passed', 'storage': 'temporary_test_owned_and_removed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        summary = run()
    except Exception as error:
        summary = {'status': 'failed', 'error_type': type(error).__name__,
                   'failed_check': str(error) if isinstance(error, AssertionError) else None,
                   'remote_requests': 0, 'live_model_calls': 0}
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + '\n', encoding='utf-8')
    print(text)
    raise SystemExit(0 if summary['status'] == 'passed' else 1)
