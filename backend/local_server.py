"""Explicit keyless local test server. Never loads project .env credentials."""
import argparse
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8010)
parser.add_argument('--data-dir', type=Path, required=True)
args = parser.parse_args()
for name in list(os.environ):
    if name.endswith('_API_KEY') or name in {'APP_AUTH_TOKEN', 'GOOGLE_CSE_ID'}:
        os.environ[name] = ''
os.environ.update(HIBUDDY_SKIP_DOTENV='true', HIBUDDY_LOCAL_DRAFT='true',
                  HIBUDDY_DATA_DIR=str(args.data_dir.resolve()), ENVIRONMENT='development',
                  HIBUDDY_PHYSIO_EXTERNAL_ENABLED='false', USE_V3_ORCHESTRATOR='false')
import uvicorn
uvicorn.run('main:app', host='127.0.0.1', port=args.port, access_log=False)
