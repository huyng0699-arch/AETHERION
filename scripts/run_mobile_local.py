"""Run the exported mobile web app and authoritative API on one loopback origin."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import secrets
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--verification', action='store_true', help='Use a separate integration-check database')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    runtime = root / '.runtime'
    runtime.mkdir(exist_ok=True)
    access_file = runtime / ('verification-access.json' if args.verification else 'local-access.json')
    db = runtime / ('verification.sqlite3' if args.verification else 'local.sqlite3')
    sys.path.insert(0, str(root / 'apps/server/src'))
    os.environ['AETHERION_DB_PATH'] = str(db)
    os.environ['AETHERION_HOST'] = '127.0.0.1'
    os.environ['AETHERION_PORT'] = str(args.port)
    os.environ['AETHERION_PROFILE'] = 'development'
    os.environ['AETHERION_MOBILE_WEB_DIR'] = str(root / 'apps/mobile/dist')
    from aetherion_server.bootstrap import ensure_bootstrap_user
    from aetherion_server.store import count_users, initialize
    initialize(db)
    if count_users(db) == 0:
        password = secrets.token_urlsafe(24)
        username = 'integration-operator' if args.verification else 'local-operator'
        ensure_bootstrap_user(db, username=username, password=password, role='operator', allowed_subjects=['*'])
        access_file.write_text(json.dumps({'url': f'http://127.0.0.1:{args.port}', 'username': username, 'password': password}, indent=2), encoding='utf-8')
        try:
            access_file.chmod(0o600)
        except OSError:
            pass
        print(f'Local account details: {access_file}', flush=True)
    # No provider is enabled and no health record is created by this launcher.
    from aetherion_server.main import run
    run()


if __name__ == '__main__':
    main()
