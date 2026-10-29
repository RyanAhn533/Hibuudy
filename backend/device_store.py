"""Opaque device credentials, expiring pairing offers, and approved plans.

Only token hashes are stored. All schedule ownership comes from the credential
and accepted device links; callers cannot choose a schedule owner via user_id.
"""
import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from fastapi import HTTPException


class DeviceStore:
    def __init__(self, path):
        self.path = str(path)
        with self.conn() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS devices (
              id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL,
              role TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS pairing_offers (
              code_hash TEXT PRIMARY KEY, owner_id TEXT NOT NULL,
              expires REAL NOT NULL, consumed INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS device_links (
              id TEXT PRIMARY KEY, owner_id TEXT NOT NULL,
              recipient_id TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS approved_plans (
              owner_id TEXT NOT NULL, plan_id TEXT NOT NULL, date TEXT NOT NULL,
              version INTEGER NOT NULL, envelope TEXT NOT NULL,
              PRIMARY KEY(owner_id, plan_id));
            CREATE INDEX IF NOT EXISTS plans_latest ON approved_plans(owner_id, date, version);
            ''')

    @contextmanager
    def conn(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode()).hexdigest()

    def enroll(self, role):
        device_id, token = secrets.token_urlsafe(24), secrets.token_urlsafe(48)
        with self.conn() as db:
            db.execute('INSERT INTO devices(id, token_hash, role) VALUES(?,?,?)', (device_id, self.digest(token), role))
        return {'device_id': device_id, 'device_token': token, 'role': role}

    def authenticate(self, token):
        if not token or len(token) > 512:
            raise HTTPException(401, '기기 인증이 필요해요.')
        with self.conn() as db:
            row = db.execute('SELECT id, role FROM devices WHERE token_hash=? AND revoked=0', (self.digest(token),)).fetchone()
        if not row:
            raise HTTPException(401, '기기 인증을 다시 해 주세요.')
        return dict(row)

    @staticmethod
    def coordinator(device):
        if device['role'] != 'coordinator':
            raise HTTPException(403, '담당자 기기에서만 할 수 있어요.')

    def offer(self, device):
        self.coordinator(device)
        code = f'{secrets.randbelow(1000000):06d}'
        expires = time.time() + 600
        with self.conn() as db:
            db.execute('DELETE FROM pairing_offers WHERE owner_id=? OR expires<?', (device['id'], time.time()))
            # A collision is extremely unlikely; retry instead of replacing another offer.
            while db.execute('SELECT 1 FROM pairing_offers WHERE code_hash=?', (self.digest(code),)).fetchone():
                code = f'{secrets.randbelow(1000000):06d}'
            db.execute('INSERT INTO pairing_offers(code_hash,owner_id,expires) VALUES(?,?,?)', (self.digest(code),device['id'],expires))
        return {'code': code, 'expires_at': expires}

    def accept(self, device, code):
        if device['role'] != 'self':
            raise HTTPException(403, '당사자 기기에서 연결 코드를 입력해 주세요.')
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            offer = db.execute('SELECT * FROM pairing_offers WHERE code_hash=? AND consumed=0 AND expires>?', (self.digest(code),time.time())).fetchone()
            if not offer:
                raise HTTPException(404, '연결 코드가 맞지 않거나 시간이 지났어요.')
            current = db.execute('SELECT id FROM device_links WHERE recipient_id=? AND revoked=0', (device['id'],)).fetchone()
            if current:
                raise HTTPException(409, '기존 연결을 먼저 해제해 주세요.')
            link_id = secrets.token_urlsafe(24)
            db.execute('INSERT INTO device_links(id,owner_id,recipient_id) VALUES(?,?,?)', (link_id,offer['owner_id'],device['id']))
            db.execute('UPDATE pairing_offers SET consumed=1 WHERE code_hash=?', (self.digest(code),))
        return {'link_id': link_id, 'connected': True}

    def links(self, device):
        with self.conn() as db:
            rows = db.execute('SELECT id,owner_id,recipient_id FROM device_links WHERE revoked=0 AND (owner_id=? OR recipient_id=?)', (device['id'],device['id'])).fetchall()
        return [{'link_id': r['id'], 'direction': 'sending' if r['owner_id'] == device['id'] else 'receiving'} for r in rows]

    def revoke(self, device, link_id):
        with self.conn() as db:
            result = db.execute('UPDATE device_links SET revoked=1 WHERE id=? AND (owner_id=? OR recipient_id=?)', (link_id,device['id'],device['id']))
            if not result.rowcount:
                raise HTTPException(404, '연결을 찾을 수 없어요.')

    def revoke_device(self, device):
        with self.conn() as db:
            db.execute('UPDATE devices SET revoked=1 WHERE id=?', (device['id'],))
            db.execute('UPDATE device_links SET revoked=1 WHERE owner_id=? OR recipient_id=?', (device['id'],device['id']))
            db.execute('DELETE FROM pairing_offers WHERE owner_id=?', (device['id'],))

    def save(self, device, envelope):
        self.coordinator(device)
        plan = envelope['plan']
        encoded = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT envelope FROM approved_plans WHERE owner_id=? AND plan_id=?', (device['id'],plan['id'])).fetchone()
            if existing:
                if existing['envelope'] != encoded:
                    raise HTTPException(409, '게시한 판은 바꿀 수 없어요. 새 판을 게시해 주세요.')
                return
            latest = db.execute('SELECT MAX(version) AS v FROM approved_plans WHERE owner_id=? AND date=?', (device['id'],plan['date'])).fetchone()['v']
            if latest is not None and plan['version_number'] <= latest:
                raise HTTPException(409, '더 최신 판이 있어요. 확인하고 다시 게시해 주세요.')
            db.execute('INSERT INTO approved_plans(owner_id,plan_id,date,version,envelope) VALUES(?,?,?,?,?)', (device['id'],plan['id'],plan['date'],plan['version_number'],encoded))

    def load(self, device, date=''):
        with self.conn() as db:
            owner_id = device['id']
            if device['role'] == 'self':
                link = db.execute('SELECT owner_id FROM device_links WHERE recipient_id=? AND revoked=0', (device['id'],)).fetchone()
                if not link:
                    raise HTTPException(403, '연결된 담당자 기기가 없어요.')
                owner_id = link['owner_id']
            sql = 'SELECT envelope FROM approved_plans WHERE owner_id=?'
            params = [owner_id]
            if date:
                sql += ' AND date=?'
                params.append(date)
            row = db.execute(sql + ' ORDER BY date DESC, version DESC LIMIT 1', params).fetchone()
        if not row:
            raise HTTPException(404, '게시된 안내가 아직 없어요.')
        return json.loads(row['envelope'])
