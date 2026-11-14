"""Focused regression test for Q-0252: cross-crew subject isolation and fail-closed revocation."""

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

from aetherion_server.store import initialize, upsert_user

REPO_ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _http_json(opener, method: str, url: str, payload: dict | None = None, token: str | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=5.0) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


class SubjectIsolationPermissionsRegressionTests(unittest.TestCase):
    def test_cross_crew_isolation_and_fail_closed_revocation(self) -> None:
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "subject_iso_reg.sqlite3"
            initialize(db_path)
            upsert_user(db_path, username="crew_a", password="CrewAPass1234!", role="crew", allowed_subjects=["CREW-A"])
            upsert_user(db_path, username="crew_b", password="CrewBPass1234!", role="crew", allowed_subjects=["CREW-B"])

            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(db_path)
            env["AETHERION_BOOTSTRAP_USER"] = "admin_iso"
            env["AETHERION_BOOTSTRAP_PASSWORD"] = "AdminPass1234!"
            env["AETHERION_BOOTSTRAP_ROLE"] = "admin"

            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "aetherion_server.main:app", "--host", "127.0.0.1", "--port", str(port)],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                deadline = time.monotonic() + 10.0
                while time.monotonic() < deadline:
                    try:
                        st, _ = _http_json(opener, "GET", f"{base_url}/health")
                        if st == 200:
                            break
                    except Exception:
                        time.sleep(0.15)
                else:
                    raise RuntimeError("Server did not start")

                _, login_a = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/auth/login",
                    {"username": "crew_a", "password": "CrewAPass1234!"},
                )
                token_a = login_a["access_token"]

                # 1. crew_a can write and read CREW-A
                st_post_a, _ = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-A",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 66.0,
                        "unit": "bpm",
                        "source_id": "wearable_a",
                        "observed_at": "2026-11-14T10:00:00+00:00",
                        "quality": "READY",
                        "verification_state": "DEVICE_UNVERIFIED",
                        "idempotency_key": "q0252-a1",
                    },
                    token=token_a,
                )
                self.assertEqual(st_post_a, 201)

                st_get_a, body_a = _http_json(
                    opener,
                    "GET",
                    f"{base_url}/api/v1/observations?subject_id=CREW-A",
                    token=token_a,
                )
                self.assertEqual(st_get_a, 200)
                self.assertEqual(len(body_a["observations"]), 1)

                # 2. crew_a is denied (403) reading or writing CREW-B
                st_get_b, _ = _http_json(
                    opener,
                    "GET",
                    f"{base_url}/api/v1/observations?subject_id=CREW-B",
                    token=token_a,
                )
                self.assertEqual(st_get_b, 403)

                st_post_b, _ = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-B",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 99.0,
                        "unit": "bpm",
                        "source_id": "wearable_a",
                        "observed_at": "2026-11-14T10:00:00+00:00",
                        "quality": "READY",
                        "verification_state": "DEVICE_UNVERIFIED",
                        "idempotency_key": "q0252-b-forbid",
                    },
                    token=token_a,
                )
                self.assertEqual(st_post_b, 403)

                # 3. Revoke crew_a token via logout -> fails closed (401)
                st_logout, _ = _http_json(opener, "POST", f"{base_url}/api/v1/auth/logout", token=token_a)
                self.assertEqual(st_logout, 200)

                st_after_logout, _ = _http_json(
                    opener,
                    "GET",
                    f"{base_url}/api/v1/observations?subject_id=CREW-A",
                    token=token_a,
                )
                self.assertEqual(st_after_logout, 401)
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()


if __name__ == "__main__":
    unittest.main()
