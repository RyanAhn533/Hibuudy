"""Manual local-server smoke test; offline regression tests use pytest instead.

Start local_server.py with a test-only data directory, then run this script.
This replaces the obsolete shared-token/provider-key smoke checks.
"""
from e2e_backend import main

if __name__ == '__main__':
    main()
