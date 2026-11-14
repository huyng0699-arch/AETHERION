"""Focused regression test for Q-0251: clock time zones, late packets, duplicates, STALE classification, and session expiry."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

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


class ClockTimezoneStaleRegressionTests(unittest.TestCase):
    def test_timezone_offsets_late_packets_duplicates_stale_and_expiry(self) -> None:
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "clock_stale_reg.sqlite3"
            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(db_path)
            env["AETHERION_BOOTSTRAP_USER"] = "admin_clock"
            env["AETHERION_BOOTSTRAP_PASSWORD"] = "TestPass1234!"
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

                st, login_body = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/auth/login",
                    {"username": "admin_clock", "password": "TestPass1234!"},
                )
                self.assertEqual(st, 200)
                token = login_body["access_token"]

                # 1. Naive timestamp without timezone offset must fail closed (422)
                st, _ = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-01",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 70.0,
                        "unit": "bpm",
                        "source_id": "wearable_1",
                        "observed_at": "2026-11-14T10:00:00",
                        "quality": "READY",
                        "verification_state": "DEVICE_UNVERIFIED",
                        "idempotency_key": "q0251-naive",
                    },
                    token=token,
                )
                self.assertEqual(st, 422)

                # 2. Out-of-order late packet with different timezone offsets
                # Newer instant first: 10:00:00-05:00 == 15:00:00Z
                st1, _ = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-01",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 80.0,
                        "unit": "bpm",
                        "source_id": "wearable_1",
                        "observed_at": "2026-11-14T10:00:00-05:00",
                        "quality": "READY",
                        "verification_state": "DEVICE_UNVERIFIED",
                        "idempotency_key": "q0251-newer",
                    },
                    token=token,
                )
                self.assertEqual(st1, 201)

                # Late packet arriving second: 16:00:00+07:00 == 09:00:00Z (earlier)
                st2, _ = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-01",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 65.0,
                        "unit": "bpm",
                        "source_id": "wearable_1",
                        "observed_at": "2026-11-14T16:00:00+07:00",
                        "quality": "READY",
                        "verification_state": "DEVICE_UNVERIFIED",
                        "idempotency_key": "q0251-late",
                    },
                    token=token,
                )
                self.assertEqual(st2, 201)

                # 3. Duplicate update with same idempotency_key -> 200 idempotent_replay
                st_dup, dup_body = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-01",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 65.0,
                        "unit": "bpm",
                        "source_id": "wearable_1",
                        "observed_at": "2026-11-14T16:00:00+07:00",
                        "quality": "READY",
                        "verification_state": "DEVICE_UNVERIFIED",
                        "idempotency_key": "q0251-late",
                    },
                    token=token,
                )
                self.assertEqual(st_dup, 200)
                self.assertEqual(dup_body["status"], "idempotent_replay")

                # 4. STALE observation classified separately from live READY observations
                st_stale, _ = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-01",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "bpm",
                        "source_id": "wearable_1",
                        "observed_at": "2026-11-14T15:30:00Z",
                        "quality": "STALE",
                        "verification_state": "DEVICE_UNVERIFIED",
                        "idempotency_key": "q0251-stale",
                    },
                    token=token,
                )
                self.assertEqual(st_stale, 201)

                st_nodata, _ = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-01",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 0.0,
                        "unit": "bpm",
                        "source_id": "wearable_1",
                        "observed_at": "2026-11-14T15:45:00Z",
                        "quality": "NO_DATA",
                        "verification_state": "TEST_FIXTURE",
                        "idempotency_key": "q0251-nodata",
                    },
                    token=token,
                )
                self.assertEqual(st_nodata, 201)

                _, live_page = _http_json(
                    opener,
                    "GET",
                    f"{base_url}/api/v1/observations?subject_id=CREW-01&order=asc&include_non_live=false",
                    token=token,
                )
                self.assertEqual([item["value"] for item in live_page["observations"]], [65.0, 80.0, 72.0])
                self.assertEqual([item["quality"] for item in live_page["observations"]], ["READY", "READY", "STALE"])

                _, all_page = _http_json(
                    opener,
                    "GET",
                    f"{base_url}/api/v1/observations?subject_id=CREW-01&order=asc&include_non_live=true",
                    token=token,
                )
                self.assertEqual([item["quality"] for item in all_page["observations"]], ["READY", "READY", "STALE", "NO_DATA"])

                # 5. Session expiry fails closed (401)
                conn = sqlite3.connect(db_path)
                conn.execute("UPDATE sessions SET expires_at = '2020-01-01T00:00:00+00:00'")
                conn.commit()
                conn.close()

                st_exp, _ = _http_json(
                    opener,
                    "GET",
                    f"{base_url}/api/v1/observations?subject_id=CREW-01",
                    token=token,
                )
                self.assertEqual(st_exp, 401)
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
