"""Run synthetic contract checks against an owned, keyless loopback server.

Starts and stops its own processes and temporary database. No remote URL,
provider call, participant data, credentials file, or existing server is used.
Prints a JSON summary without device tokens. Run: python -B smoke_contract.py
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import uuid

import httpx
from contracts import PlanEnvelope


@contextmanager
def local_server(data_dir, log_path):
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    # local_server.py repeats this isolation before importing the application.
    for name in list(env):
        if name.endswith('_API_KEY') or name in {'APP_AUTH_TOKEN', 'GOOGLE_CSE_ID'}:
            env.pop(name, None)
    env['HIBUDDY_SKIP_DOTENV'] = 'true'
    with log_path.open('w', encoding='utf-8') as log:
        process = subprocess.Popen(
            [sys.executable, '-B', str(Path(__file__).with_name('local_server.py')),
             '--port', str(port), '--data-dir', str(data_dir)],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            env=env, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        try:
            with httpx.Client(base_url=f'http://127.0.0.1:{port}',
                              timeout=5, trust_env=False) as client:
                deadline = time.monotonic() + 30
                while True:
                    if process.poll() is not None:
                        raise RuntimeError('Owned local server exited before readiness')
                    try:
                        response = client.get('/health')
                        if response.status_code == 200:
                            break
                    except httpx.RequestError:
                        pass
                    if time.monotonic() >= deadline:
                        raise RuntimeError('Owned local server did not become ready')
                    time.sleep(.1)
                yield client
        finally:
            # Only the exact process started above is stopped; never kill by name/port.
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def expect(response, status, step):
    if response.status_code != status:
        raise AssertionError(f'{step}: expected HTTP {status}, got {response.status_code}')
    return response


def enroll(client, role):
    response = expect(client.post('/api/devices/enroll', json={'role': role}),
                      200, 'enroll ' + role)
    return {'Authorization': 'Bearer ' + response.json()['device_token']}


def run():
    checks = []
    with tempfile.TemporaryDirectory(prefix='hibuddy-contract-smoke-') as temporary:
        root = Path(temporary)
        data_dir = root / 'data'
        with local_server(data_dir, root / 'first.log') as client:
            health = client.get('/health').json()
            assert health['api_contract'] == 'hibuddy-device-v1', 'contract identity'
            assert health['auth'] == 'device' and health['plan_schema_version'] == 1, 'auth contract'
            assert health['local_draft'] and not any(health['llm_providers'].values()), 'keyless local server'
            expect(client.get('/openapi.json'), 404, 'private wire schema')
            expect(client.post('/api/agent', json={'input': 'synthetic'}),
                   401, 'unauthenticated request')
            checks.append('contract_identity_and_fail_closed_auth')

            owner, recipient, stranger = (enroll(client, role)
                                          for role in ('coordinator', 'self', 'self'))
            draft = expect(client.post('/api/schedule/generate', headers=owner,
                json={'text': '08:00 합성 활동 준비'}), 200, 'local draft').json()
            activity = draft['schedule'][0]
            envelope = {
                'schema_version': 1,
                'plan': {'id': str(uuid.uuid4()), 'version_number': 1,
                         'date': '2026-10-14', 'status': 'published',
                         'approved_by': 'synthetic-smoke-test',
                         'published_at': datetime.now(timezone.utc).isoformat()},
                'activities': [{**activity, 'id': str(uuid.uuid4())}],
            }
            envelope = PlanEnvelope.model_validate(envelope).model_dump(mode='json')
            expect(client.post('/api/schedule/save', headers=owner, json=envelope),
                   200, 'publish')
            expect(client.get('/api/schedule/load', headers=recipient),
                   403, 'unpaired recipient')
            code = expect(client.post('/api/pairing/code', headers=owner),
                          200, 'pair offer').json()['code']
            link = expect(client.post('/api/pairing/accept', headers=recipient,
                          json={'code': code}), 200, 'pair accept').json()['link_id']
            expect(client.post('/api/pairing/accept', headers=stranger,
                               json={'code': code}), 404, 'single-use pairing code')
            received = expect(client.get('/api/schedule/load', headers=recipient),
                              200, 'receive').json()
            assert received['plan']['id'] == envelope['plan']['id'], 'published identity'
            assert received['activities'] == envelope['activities'], 'published activities'
            expect(client.get('/api/schedule/load', headers=stranger),
                   403, 'unrelated recipient')
            expect(client.post('/api/schedule/save', headers=recipient, json=envelope),
                   403, 'recipient cannot publish')
            checks.append('publish_pair_exact_receive_and_permissions')

            changed = json.loads(json.dumps(envelope))
            changed['activities'][0]['task'] = 'different synthetic task'
            expect(client.post('/api/schedule/save', headers=owner, json=changed),
                   409, 'immutable published version')
            expect(client.post('/api/schedule/save', headers=owner, json=envelope),
                   200, 'idempotent identical retry')
            checks.append('immutable_version_and_idempotent_retry')

        # A new OS process opens the same DB: this tests more than reopening a class.
        with local_server(data_dir, root / 'restart.log') as client:
            received = expect(client.get('/api/schedule/load', headers=recipient),
                              200, 'receive after process restart').json()
            assert received['plan']['id'] == envelope['plan']['id'], 'restart identity'
            checks.append('credentials_pairing_and_plan_survive_process_restart')
            expect(client.delete('/api/pairing/' + link, headers=recipient),
                   200, 'revoke link')
            expect(client.get('/api/schedule/load', headers=recipient),
                   403, 'revoked link blocked')
            for headers in (owner, recipient, stranger):
                expect(client.delete('/api/devices/current', headers=headers),
                       200, 'revoke synthetic device')
                expect(client.get('/api/pairing/status', headers=headers),
                       401, 'revoked credential blocked')
            checks.append('link_and_device_revocation')
    return {'status': 'passed', 'checks': checks, 'remote_requests': 0,
            'live_model_calls': 0, 'storage': 'temporary_test_owned'}


if __name__ == '__main__':
    try:
        print(json.dumps(run(), ensure_ascii=False))
    except Exception as error:
        # Do not dump response bodies, headers, environment values or tokens.
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__,
                          'failed_check': str(error) if isinstance(error, AssertionError) else None,
                          'message': 'Local contract smoke failed; no deployment performed.'}))
        raise SystemExit(1)
