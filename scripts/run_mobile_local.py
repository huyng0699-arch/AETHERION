"""Run the exported mobile web app and authoritative API on one loopback origin."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import sys
from urllib.request import urlopen


def build_fingerprint(root: Path) -> str:
    """Identify the server source and the exported client served together."""
    digest = hashlib.sha256()
    folders = (root / 'apps/server/src/aetherion_server', root / 'packages/medical_library')
    files = [path for folder in folders for path in folder.rglob('*.py')]
    files.append(root / 'apps/mobile/dist/index.html')
    for path in sorted(files):
        digest.update(path.relative_to(root).as_posix().encode('utf8'))
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=None)
    parser.add_argument('--verification', action='store_true', help='Use a separate integration-check database')
    args = parser.parse_args()
    if args.port is None:
        args.port = 8769 if args.verification else 8765
    root = Path(__file__).resolve().parents[1]
    runtime = root / '.runtime'
    access_file = runtime / ('verification-access.json' if args.verification else 'local-access.json')
    other_access_file = runtime / ('local-access.json' if args.verification else 'verification-access.json')
    requested_url = f'http://127.0.0.1:{args.port}'
    fingerprint = build_fingerprint(root)
    scope = 'verification' if args.verification else 'local'
    try:
        with socket.create_connection(('127.0.0.1', args.port), timeout=1):
            occupied = True
    except ConnectionRefusedError:
        occupied = False
    except OSError:
        # Some Windows firewall profiles time out instead of refusing a vacant
        # loopback port. An exclusive bind probe safely distinguishes that case.
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                    probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                probe.bind(('127.0.0.1', args.port))
            occupied = False
        except OSError as exc:
            raise SystemExit('Cannot determine local server availability; no second server was started') from exc
    if occupied:
        try:
            # Refuse to mistake the other database's listener for this one.
            if other_access_file.is_file():
                other = json.loads(other_access_file.read_text(encoding='utf-8'))
                if other.get('url') == requested_url:
                    raise ValueError('Other runtime scope uses this port')
            if not access_file.is_file() or json.loads(access_file.read_text(encoding='utf-8')).get('url') != requested_url:
                raise ValueError('No matching local runtime account')
            with urlopen(f'http://127.0.0.1:{args.port}/health', timeout=2) as response:
                health = json.load(response)
            with urlopen(f'http://127.0.0.1:{args.port}/', timeout=2) as response:
                html = response.read().decode('utf8')
            if (health.get('service') != 'aetherion-server'
                    or health.get('runtime_fingerprint') != fingerprint
                    or health.get('runtime_scope') != scope
                    or html.strip() != (root / 'apps/mobile/dist/index.html').read_text(encoding='utf8').strip()):
                raise ValueError('Different server or client export')
        except Exception as exc:
            raise SystemExit('Port is occupied by another or older runtime. Update that runtime before starting this client/server build; no duplicate listener was created.') from exc
        print(f'AETHERION already running: http://127.0.0.1:{args.port}', flush=True)
        return
    runtime.mkdir(exist_ok=True)
    db = runtime / ('verification.sqlite3' if args.verification else 'local.sqlite3')
    sys.path.insert(0, str(root / 'apps/server/src'))
    os.environ['AETHERION_DB_PATH'] = str(db)
    os.environ['AETHERION_HOST'] = '127.0.0.1'
    os.environ['AETHERION_PORT'] = str(args.port)
    os.environ['AETHERION_PROFILE'] = 'development'
    os.environ['AETHERION_MOBILE_WEB_DIR'] = str(root / 'apps/mobile/dist')
    os.environ['AETHERION_RUNTIME_FINGERPRINT'] = fingerprint
    os.environ['AETHERION_RUNTIME_SCOPE'] = scope
    from aetherion_server.bootstrap import ensure_bootstrap_user
    from aetherion_server.store import count_users, initialize
    initialize(db)
    if count_users(db) == 0:
        password = secrets.token_urlsafe(24)
        username = 'integration-operator' if args.verification else 'local-owner'
        ensure_bootstrap_user(db, username=username, password=password, role='operator' if args.verification else 'admin', allowed_subjects=['*'])
        access_file.write_text(json.dumps({'url': f'http://127.0.0.1:{args.port}', 'username': username, 'password': password}, indent=2), encoding='utf-8')
        try:
            access_file.chmod(0o600)
        except OSError:
            pass
        print(f'Local account details: {access_file}', flush=True)
    elif access_file.is_file():
        # Keep this launcher-owned account file on the selected port without
        # rotating an existing user's password or copying credentials to logs.
        access = json.loads(access_file.read_text(encoding='utf-8'))
        selected_url = f'http://127.0.0.1:{args.port}'
        if access.get('url') != selected_url:
            access['url'] = selected_url
            access_file.write_text(json.dumps(access, indent=2), encoding='utf-8')
    # No provider is enabled and no health record is created by this launcher.
    from aetherion_server.main import run
    run()


if __name__ == '__main__':
    main()
