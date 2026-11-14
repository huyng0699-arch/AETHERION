"""Real cross-process HTTP API health & observation persistence E2E test (Q-0242)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.bootstrap import ensure_bootstrap_user


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


_NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _http_json(method: str, url: str, *, payload: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _NO_PROXY_OPENER.open(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _start_server(db_path: Path, port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SERVER_SRC)
    env["AETHERION_DB_PATH"] = str(db_path)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import uvicorn; "
                "from aetherion_server.main import create_app; "
                f"uvicorn.run(create_app(db_path=r'{db_path}'), host='127.0.0.1', port={port}, log_level='error')"
            ),
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        try:
            code, body = _http_json("GET", f"http://127.0.0.1:{port}/health")
            if code == 200 and body.get("status") == "ok":
                return proc
        except Exception:
            time.sleep(0.15)
    proc.terminate()
    proc.wait(timeout=5)
    raise RuntimeError("Server failed to become healthy within 10s")


class TestApiHealthObservationE2E(unittest.TestCase):
    def test_start_post_get_restart_verify_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "e2e_api.sqlite3"
            ensure_bootstrap_user(
                db_path,
                username="qa_ops",
                password="qa-ops-password-123",
                role="operator",
                allowed_subjects=["*"],
            )

            port1 = _free_port()
            proc1 = _start_server(db_path, port1)
            try:
                base1 = f"http://127.0.0.1:{port1}"
                code, health = _http_json("GET", f"{base1}/health")
                self.assertEqual(code, 200)
                self.assertEqual(health["status"], "ok")

                # Negative: unauthenticated observations access must be 401
                unauth_code, _ = _http_json("GET", f"{base1}/api/v1/observations?subject_id=ENG-TEST-01")
                self.assertEqual(unauth_code, 401)

                code, login = _http_json(
                    "POST",
                    f"{base1}/api/v1/auth/login",
                    payload={"username": "qa_ops", "password": "qa-ops-password-123"},
                )
                self.assertEqual(code, 200)
                token = login["access_token"]

                code, subj = _http_json(
                    "POST",
                    f"{base1}/api/v1/subjects",
                    payload={
                        "subject_id": "ENG-TEST-01",
                        "display_name": "Bench Pressure Fixture",
                        "scope": "engineering_test",
                        "role_label": "test_fixture",
                    },
                    token=token,
                )
                self.assertIn(code, (200, 201))

                code, created = _http_json(
                    "POST",
                    f"{base1}/api/v1/observations",
                    payload={
                        "subject_id": "ENG-TEST-01",
                        "scope": "engineering_test",
                        "metric": "cabin_pressure",
                        "value": 101.3,
                        "unit": "kPa",
                        "source_id": "bench_sensor_01",
                        "observed_at": "2026-11-14T10:00:00+00:00",
                        "quality": "UNVERIFIED",
                        "verification_state": "TEST_FIXTURE",
                        "idempotency_key": "q0242-e2e-001",
                    },
                    token=token,
                )
                self.assertIn(code, (200, 201))

                # Without include_non_live=true, TEST_FIXTURE must not appear as live telemetry
                code, live_only = _http_json("GET", f"{base1}/api/v1/observations?subject_id=ENG-TEST-01", token=token)
                self.assertEqual(code, 200)
                self.assertEqual(len(live_only["observations"]), 0)

                code, fetched1 = _http_json(
                    "GET",
                    f"{base1}/api/v1/observations?subject_id=ENG-TEST-01&include_non_live=true",
                    token=token,
                )
                self.assertEqual(code, 200)
                items1 = fetched1["observations"]
                self.assertEqual(len(items1), 1)
                self.assertAlmostEqual(items1[0]["value"], 101.3)
            finally:
                proc1.terminate()
                proc1.wait(timeout=5)

            # Restart server on a new port with the same SQLite database
            port2 = _free_port()
            proc2 = _start_server(db_path, port2)
            try:
                base2 = f"http://127.0.0.1:{port2}"
                code, login2 = _http_json(
                    "POST",
                    f"{base2}/api/v1/auth/login",
                    payload={"username": "qa_ops", "password": "qa-ops-password-123"},
                )
                self.assertEqual(code, 200)
                token2 = login2["access_token"]

                code, fetched2 = _http_json(
                    "GET",
                    f"{base2}/api/v1/observations?subject_id=ENG-TEST-01&include_non_live=true",
                    token=token2,
                )
                self.assertEqual(code, 200)
                items2 = fetched2["observations"]
                self.assertEqual(len(items2), 1)
                self.assertAlmostEqual(items2[0]["value"], 101.3)
                self.assertEqual(items2[0]["verification_state"], "TEST_FIXTURE")
            finally:
                proc2.terminate()
                proc2.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
