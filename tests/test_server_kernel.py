"""End-to-end headless FastAPI + SQLite kernel tests for AETHERION server."""

from pathlib import Path
import tempfile
import time
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class ServerKernelTests(unittest.TestCase):
    def test_health_ready_and_unauthenticated_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "kernel.sqlite3"
            app = create_app(db_path=db)
            with TestClient(app) as client:
                health = client.get("/health")
                self.assertEqual(health.status_code, 200)
                self.assertEqual(health.json()["status"], "ok")

                ready = client.get("/ready")
                self.assertEqual(ready.status_code, 200)
                self.assertEqual(ready.json()["database"], "ok")

                unauth_get = client.get("/api/v1/observations", params={"subject_id": "CREW-1"})
                self.assertEqual(unauth_get.status_code, 401)

                unauth_post = client.post(
                    "/api/v1/observations",
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 70.0,
                        "unit": "beats/min",
                        "source_id": "manual_entry",
                        "observed_at": "2026-11-14T04:00:00+00:00",
                    },
                )
                self.assertEqual(unauth_post.status_code, 401)

    def test_auth_subject_isolation_validation_idempotency_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "kernel_restart.sqlite3"
            ensure_bootstrap_user(
                db,
                username="alice",
                password="alice-secret-password",
                role="crew",
                allowed_subjects=["CREW-ALICE"],
            )
            ensure_bootstrap_user(
                db,
                username="flight_ops",
                password="ops-secret-password",
                role="operator",
                allowed_subjects=["*"],
            )

            app1 = create_app(db_path=db)
            with TestClient(app1) as client1:
                bad_login = client1.post(
                    "/api/v1/auth/login",
                    json={"username": "alice", "password": "wrong-password"},
                )
                self.assertEqual(bad_login.status_code, 401)

                login = client1.post(
                    "/api/v1/auth/login",
                    json={"username": "alice", "password": "alice-secret-password"},
                )
                self.assertEqual(login.status_code, 200)
                token = login.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                me = client1.get("/api/v1/auth/me", headers=headers)
                self.assertEqual(me.status_code, 200)
                self.assertEqual(me.json()["username"], "alice")

                # Cross-subject access denied
                forbidden = client1.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-BOB"},
                    headers=headers,
                )
                self.assertEqual(forbidden.status_code, 403)

                # Negative validation: naive timestamp, non-finite value, invalid scope
                naive_ts = client1.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-ALICE",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "manual_entry",
                        "observed_at": "2026-11-14T04:00:00",
                    },
                )
                self.assertEqual(naive_ts.status_code, 422)

                nan_val = client1.post(
                    "/api/v1/observations",
                    headers=headers,
                    content=(
                        '{"subject_id":"CREW-ALICE","metric":"heart_rate","value":NaN,'
                        '"unit":"beats/min","source_id":"manual_entry",'
                        '"observed_at":"2026-11-14T04:00:00+00:00"}'
                    ),
                )
                self.assertEqual(nan_val.status_code, 422)

                bad_scope = client1.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-ALICE",
                        "scope": "invalid_scope",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "manual_entry",
                        "observed_at": "2026-11-14T04:00:00+00:00",
                    },
                )
                self.assertEqual(bad_scope.status_code, 422)

                # Valid ingest + idempotent replay
                obs_payload = {
                    "subject_id": "CREW-ALICE",
                    "scope": "personal",
                    "metric": "heart_rate",
                    "value": 68.0,
                    "unit": "beats/min",
                    "source_id": "manual_entry",
                    "observed_at": "2026-11-14T04:00:00+00:00",
                    "quality": "READY",
                    "verification_state": "SELF_REPORTED",
                }
                first = client1.post(
                    "/api/v1/observations",
                    headers={**headers, "Idempotency-Key": "idem-alice-1"},
                    json=obs_payload,
                )
                self.assertEqual(first.status_code, 201)
                self.assertFalse(first.json()["idempotent_replay"])

                replay = client1.post(
                    "/api/v1/observations",
                    headers={**headers, "Idempotency-Key": "idem-alice-1"},
                    json=obs_payload,
                )
                self.assertEqual(replay.status_code, 200)
                self.assertTrue(replay.json()["idempotent_replay"])
                self.assertEqual(first.json()["id"], replay.json()["id"])

                # Logout revokes session
                logout = client1.post("/api/v1/auth/logout", headers=headers)
                self.assertEqual(logout.status_code, 200)
                after_logout = client1.get("/api/v1/auth/me", headers=headers)
                self.assertEqual(after_logout.status_code, 401)

            # Simulate full server restart with a brand-new FastAPI app instance on same SQLite DB
            app2 = create_app(db_path=db)
            with TestClient(app2) as client2:
                ops_login = client2.post(
                    "/api/v1/auth/login",
                    json={"username": "flight_ops", "password": "ops-secret-password"},
                )
                self.assertEqual(ops_login.status_code, 200)
                ops_headers = {"Authorization": f"Bearer {ops_login.json()['access_token']}"}
                read_back = client2.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-ALICE"},
                    headers=ops_headers,
                )
                self.assertEqual(read_back.status_code, 200)
                items = read_back.json()["observations"]
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0]["value"], 68.0)
                self.assertEqual(items[0]["scope"], "personal")
                self.assertEqual(items[0]["source_id"], "manual_entry")
                self.assertEqual(items[0]["verification_state"], "SELF_REPORTED")

    def test_session_expiry_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "expiry.sqlite3"
            ensure_bootstrap_user(
                db,
                username="short_lived",
                password="valid-password-123",
                role="crew",
                allowed_subjects=["CREW-SHORT"],
            )
            app = create_app(db_path=db, session_ttl_seconds=1)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "short_lived", "password": "valid-password-123"},
                )
                self.assertEqual(login.status_code, 200)
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
                time.sleep(1.15)
                expired = client.get("/api/v1/auth/me", headers=headers)
                self.assertEqual(expired.status_code, 401)

    def test_ready_fails_503_on_partial_tables_and_post_blocks_verified_elevation(self):
        import sqlite3

        with tempfile.TemporaryDirectory() as directory:
            broken_db = Path(directory) / "partial.sqlite3"
            with sqlite3.connect(broken_db) as conn:
                conn.execute(
                    """
                    CREATE TABLE subjects (
                        subject_id TEXT PRIMARY KEY,
                        display_name TEXT NOT NULL
                    )
                    """
                )
            app_broken = create_app(db_path=broken_db)
            with TestClient(app_broken) as client_broken:
                ready = client_broken.get("/ready")
                self.assertEqual(ready.status_code, 503)

            good_db = Path(directory) / "good.sqlite3"
            ensure_bootstrap_user(
                good_db,
                username="crew_guard",
                password="guard-password-123",
                role="crew",
                allowed_subjects=["CREW-G"],
            )
            app_good = create_app(db_path=good_db)
            with TestClient(app_good) as client_good:
                login = client_good.post(
                    "/api/v1/auth/login",
                    json={"username": "crew_guard", "password": "guard-password-123"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
                elevated = client_good.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-G",
                        "metric": "heart_rate",
                        "value": 70.0,
                        "unit": "beats/min",
                        "source_id": "verified_spoof",
                        "observed_at": "2026-11-14T04:00:00+00:00",
                        "verification_state": "VERIFIED",
                    },
                )
                self.assertEqual(elevated.status_code, 422)


if __name__ == "__main__":
    unittest.main()
