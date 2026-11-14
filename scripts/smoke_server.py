"""Real subprocess HTTP server smoke test over loopback 127.0.0.1."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http_json(method: str, url: str, *, payload: dict | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(url, data=data, headers=req_headers, method=method)
    try:
        with urlopen(req, timeout=5) as resp:
            return int(resp.status), json.loads(resp.read().decode("utf-8"))
    except HTTPError as err:
        return int(err.code), json.loads(err.read().decode("utf-8"))


def _wait_ready(base_url: str, proc: subprocess.Popen) -> None:
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Server exited prematurely with code {proc.returncode}")
        try:
            status, body = _http_json("GET", f"{base_url}/ready")
            if status == 200 and body.get("status") == "ready":
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise TimeoutError("Server did not become ready within 15s")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    src_path = str(repo_root / "apps" / "server" / "src")
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "smoke.sqlite3"
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        env["AETHERION_DB_PATH"] = str(db_path)
        env["AETHERION_BOOTSTRAP_USER"] = "smoke_ops"
        env["AETHERION_BOOTSTRAP_PASSWORD"] = "smoke-password-123"
        env["AETHERION_BOOTSTRAP_ROLE"] = "operator"

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "aetherion_server.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",
            ],
            cwd=str(repo_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _wait_ready(base_url, proc)
            unauth_status, _ = _http_json("GET", f"{base_url}/api/v1/observations?subject_id=SMOKE-1&include_non_live=true")
            assert unauth_status == 401, f"Expected 401 unauthenticated, got {unauth_status}"

            login_status, login_body = _http_json(
                "POST",
                f"{base_url}/api/v1/auth/login",
                payload={"username": "smoke_ops", "password": "smoke-password-123"},
            )
            assert login_status == 200, f"Login failed: {login_status} {login_body}"
            headers = {
                "Authorization": f"Bearer {login_body['access_token']}",
                "Idempotency-Key": "smoke-key-1",
            }
            post_status, post_body = _http_json(
                "POST",
                f"{base_url}/api/v1/observations",
                headers=headers,
                payload={
                    "subject_id": "SMOKE-1",
                    "scope": "engineering_test",
                    "metric": "heart_rate",
                    "value": 71.5,
                    "unit": "beats/min",
                    "source_id": "smoke_script",
                    "observed_at": "2026-11-14T04:50:00+00:00",
                    "quality": "READY",
                    "verification_state": "TEST_FIXTURE",
                },
            )
            assert post_status == 201, f"Expected 201, got {post_status} {post_body}"

            replay_status, replay_body = _http_json(
                "POST",
                f"{base_url}/api/v1/observations",
                headers=headers,
                payload={
                    "subject_id": "SMOKE-1",
                    "scope": "engineering_test",
                    "metric": "heart_rate",
                    "value": 71.5,
                    "unit": "beats/min",
                    "source_id": "smoke_script",
                    "observed_at": "2026-11-14T04:50:00+00:00",
                    "quality": "READY",
                    "verification_state": "TEST_FIXTURE",
                },
            )
            assert replay_status == 200 and replay_body["idempotent_replay"] is True

            get_status, get_body = _http_json(
                "GET",
                f"{base_url}/api/v1/observations?subject_id=SMOKE-1",
                headers={"Authorization": f"Bearer {login_body['access_token']}"},
            )
            assert get_status == 200 and len(get_body["observations"]) == 1
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        print(f"OK: smoke_server passed on {base_url} with SQLite {db_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
