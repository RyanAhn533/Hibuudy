"""All backend tests use temporary test-owned storage and no provider keys."""
import atexit
import os
import tempfile

_storage = tempfile.TemporaryDirectory(prefix='hibuddy-backend-tests-')
atexit.register(_storage.cleanup)
os.environ.update(HIBUDDY_SKIP_DOTENV='true', HIBUDDY_DATA_DIR=_storage.name,
                  HIBUDDY_LOCAL_DRAFT='false', USE_V3_ORCHESTRATOR='false')
for _name in list(os.environ):
    if _name.endswith('_API_KEY') or _name in {'APP_AUTH_TOKEN', 'GOOGLE_CSE_ID'}:
        os.environ[_name] = ''

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    import main
    from device_store import DeviceStore
    from fastapi.testclient import TestClient
    monkeypatch.setattr(main, 'device_store', DeviceStore(tmp_path / 'device-test.db'))
    monkeypatch.setattr(main.limiter, 'enabled', False)
    return TestClient(main.app)
