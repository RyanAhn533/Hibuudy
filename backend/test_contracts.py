import copy
import json
import pytest


def enroll(client, role='coordinator'):
    response = client.post('/api/devices/enroll', json={'role': role})
    assert response.status_code == 200
    return {'Authorization': 'Bearer ' + response.json()['device_token']}


def plan():
    return {'schema_version': 1, 'plan': {'id': '00000000-0000-4000-8000-000000000001', 'version_number': 1,
            'status': 'published', 'approved_by': 'synthetic-approver',
            'published_at': '2026-10-11T12:00:00', 'date': '2026-10-11'},
            'activities': [{'id': 'synthetic-activity-1', 'time': '08:00', 'type': 'GENERAL',
                            'task': 'synthetic', 'guide_script': ['synthetic step']}]}


def connect(client, owner, recipient):
    code = client.post('/api/pairing/code', headers=owner).json()['code']
    response = client.post('/api/pairing/accept', json={'code': code}, headers=recipient)
    assert response.status_code == 200
    return response.json()['link_id']


def test_fail_closed_without_global_configuration(client, monkeypatch):
    import main
    monkeypatch.setattr(main, 'APP_AUTH_TOKEN', '')
    assert client.post('/api/schedule/save', json=plan()).status_code == 401
    monkeypatch.setattr(main, 'APP_AUTH_TOKEN', 'old-shared-token')
    assert client.post('/api/schedule/save', json=plan(), headers={'Authorization': 'Bearer old-shared-token'}).status_code == 401


def test_pair_accept_receives_exact_published_plan_and_revocation_blocks_new_reads(client):
    owner, recipient, stranger = enroll(client), enroll(client, 'self'), enroll(client, 'self')
    assert client.post('/api/schedule/save', json=plan(), headers=owner).status_code == 200
    assert client.get('/api/schedule/load', headers=recipient).status_code == 403
    link = connect(client, owner, recipient)
    received = client.get('/api/schedule/load', headers=recipient)
    assert received.status_code == 200
    assert received.json()['plan'] == plan()['plan']
    assert received.json()['activities'][0]['id'] == 'synthetic-activity-1'
    assert client.get('/api/schedule/load?user_id=synthetic-owner', headers=stranger).status_code == 422
    assert client.get('/api/schedule/load', headers=stranger).status_code == 403
    assert client.delete('/api/pairing/' + link, headers=stranger).status_code == 404
    assert client.delete('/api/pairing/' + link, headers=owner).status_code == 200
    assert client.get('/api/schedule/load', headers=recipient).status_code == 403


def test_recipient_cannot_publish_or_create_pair_codes(client):
    recipient = enroll(client, 'self')
    assert client.post('/api/schedule/save', json=plan(), headers=recipient).status_code == 403
    assert client.post('/api/pairing/code', headers=recipient).status_code == 403


def test_pair_code_is_single_use_and_expires(client):
    import main
    owner, first, second = enroll(client), enroll(client, 'self'), enroll(client, 'self')
    code = client.post('/api/pairing/code', headers=owner).json()['code']
    assert client.post('/api/pairing/accept', json={'code': code}, headers=first).status_code == 200
    assert client.post('/api/pairing/accept', json={'code': code}, headers=second).status_code == 404
    code = client.post('/api/pairing/code', headers=owner).json()['code']
    with main.device_store.conn() as db:
        db.execute('UPDATE pairing_offers SET expires=0')
    assert client.post('/api/pairing/accept', json={'code': code}, headers=second).status_code == 404


def test_published_identity_is_immutable_and_new_version_is_delivered(client):
    owner, recipient = enroll(client), enroll(client, 'self')
    connect(client, owner, recipient)
    assert client.post('/api/schedule/save', json=plan(), headers=owner).status_code == 200
    assert client.post('/api/schedule/save', json=plan(), headers=owner).status_code == 200
    changed = plan(); changed['activities'][0]['task'] = 'changed'
    assert client.post('/api/schedule/save', json=changed, headers=owner).status_code == 409
    changed['plan'].update(id='00000000-0000-4000-8000-000000000002', version_number=2)
    assert client.post('/api/schedule/save', json=changed, headers=owner).status_code == 200
    assert client.get('/api/schedule/load', headers=recipient).json()['plan']['id'] == '00000000-0000-4000-8000-000000000002'


@pytest.mark.parametrize('mutation', ['date', 'item', 'images', 'duplicate', 'approver', 'uuid', 'timestamp', 'menu', 'menu_image', 'video'])
def test_transfer_rejects_invalid_or_private_data(client, mutation):
    owner = enroll(client)
    invalid = plan()
    if mutation == 'date': invalid['plan']['date'] = '2026-99-99'
    if mutation == 'item': invalid['activities'] = [17]
    if mutation == 'images': invalid['activities'][0]['guide_images'] = ['/private/photo.jpg']
    if mutation == 'duplicate': invalid['activities'].append(copy.deepcopy(invalid['activities'][0]))
    if mutation == 'approver': invalid['plan']['approved_by'] = ' '
    if mutation == 'uuid': invalid['plan']['id'] = 'not-a-real-global-uuid'
    if mutation == 'timestamp': invalid['plan']['published_at'] = '2026-10-11'
    if mutation == 'menu': invalid['activities'][0]['menus'] = [{'name': 'synthetic', 'private_note': 'must not transfer'}]
    if mutation == 'menu_image': invalid['activities'][0]['menus'] = [{'name': 'synthetic', 'image': '/private/image.jpg'}]
    if mutation == 'video': invalid['activities'][0]['video_url'] = '/private/video.mp4'
    assert client.post('/api/schedule/save', json=invalid, headers=owner).status_code == 422


@pytest.mark.parametrize('output', ['{}', '[]', '{"schedule":[]}', '{"schedule":[{"time":"99:99","type":"GENERAL","task":"x","guide_script":["x"]}]}'])
def test_generation_rejects_invalid_provider_contract(client, monkeypatch, output):
    import main
    async def fake(*args, **kwargs): return output
    monkeypatch.setattr(main, 'llm_generate', fake)
    assert client.post('/api/schedule/generate', json={'text': 'synthetic'}, headers=enroll(client)).status_code == 502


def test_edit_rejects_missing_fields_and_changed_task_with_old_guide(client, monkeypatch):
    import main
    current = plan()['activities'][0]
    headers = enroll(client)
    async def empty(*args, **kwargs): return '{}'
    monkeypatch.setattr(main, 'llm_generate', empty)
    body = {'current_item': current, 'request': 'synthetic change'}
    assert client.post('/api/schedule/edit', json=body, headers=headers).status_code == 502
    async def stale(*args, **kwargs): return json.dumps({**current, 'task': 'different activity'})
    monkeypatch.setattr(main, 'llm_generate', stale)
    assert client.post('/api/schedule/edit', json=body, headers=headers).status_code == 502
    async def valid(*args, **kwargs): return json.dumps({**current, 'task': 'different activity', 'guide_script': ['new step']})
    monkeypatch.setattr(main, 'llm_generate', valid)
    assert client.post('/api/schedule/edit', json=body, headers=headers).status_code == 200


def test_credentials_and_plans_survive_store_restart_and_device_revoke(client, monkeypatch):
    import main
    from device_store import DeviceStore
    owner = enroll(client)
    assert client.post('/api/schedule/save', json=plan(), headers=owner).status_code == 200
    monkeypatch.setattr(main, 'device_store', DeviceStore(main.device_store.path))
    assert client.get('/api/schedule/load', headers=owner).json()['plan']['id'] == plan()['plan']['id']
    assert client.delete('/api/devices/current', headers=owner).status_code == 200
    assert client.get('/api/schedule/load', headers=owner).status_code == 401


def test_step_free_approved_activity_transfers_without_inventing_steps(client):
    owner, recipient = enroll(client), enroll(client, 'self')
    connect(client, owner, recipient)
    published = plan()
    published['activities'][0]['guide_script'] = []
    assert client.post('/api/schedule/save', json=published, headers=owner).status_code == 200
    received = client.get('/api/schedule/load', headers=recipient)
    assert received.status_code == 200
    assert received.json()['activities'][0]['guide_script'] == []
