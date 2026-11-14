"""Isolation tests for Q-0034: test fixtures and NASA research never appear as live crew readings."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class CoreIsolationTests(unittest.TestCase):
    def test_test_fixtures_and_imported_research_excluded_from_default_live_queries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "isolation.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_iso",
                password="ops-iso-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_iso", "password": "ops-iso-password-123"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                # 1) Authentic self-reported crew reading
                r1 = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "scope": "CREW",
                        "metric": "heart_rate",
                        "value": 64.0,
                        "unit": "beats/min",
                        "source_id": "crew_manual_log",
                        "observed_at": "2026-11-14T04:50:00+00:00",
                        "quality": "READY",
                        "verification_state": "SELF_REPORTED",
                    },
                )
                self.assertEqual(r1.status_code, 201)

                # 2) Engineering test fixture
                r2 = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "scope": "engineering_test",
                        "metric": "heart_rate",
                        "value": 99.0,
                        "unit": "beats/min",
                        "source_id": "pytest_fixture",
                        "observed_at": "2026-11-14T04:51:00+00:00",
                        "quality": "READY",
                        "verification_state": "TEST_FIXTURE",
                    },
                )
                self.assertEqual(r2.status_code, 201)

                # 3) Imported NASA OSDR research record
                r3 = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "scope": "CREW",
                        "metric": "heart_rate",
                        "value": 112.0,
                        "unit": "beats/min",
                        "source_id": "nasa_osdr:OSD-575",
                        "observed_at": "2026-11-14T04:52:00+00:00",
                        "quality": "READY",
                        "verification_state": "UNVERIFIED",
                    },
                )
                self.assertEqual(r3.status_code, 201)

                # Default live query must return ONLY the authentic crew reading
                live = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-1"},
                    headers=headers,
                )
                self.assertEqual(live.status_code, 200)
                live_obs = live.json()["observations"]
                self.assertEqual(len(live_obs), 1)
                self.assertEqual(live_obs[0]["source_id"], "crew_manual_log")
                self.assertEqual(live_obs[0]["value"], 64.0)

                # Explicit opt-in returns all three
                all_obs = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-1", "include_non_live": "true"},
                    headers=headers,
                )
                self.assertEqual(all_obs.status_code, 200)
                self.assertEqual(len(all_obs.json()["observations"]), 3)


if __name__ == "__main__":
    unittest.main()
