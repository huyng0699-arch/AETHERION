"""Tests for Q-0043 local test-data reset utility."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.dev_reset import reset_development_test_data
from aetherion_server.main import create_app


class DevResetTests(unittest.TestCase):
    def test_deletes_only_engineering_test_fixtures_preserving_crew_and_cabin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "reset.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_reset",
                password="ops-reset-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_reset", "password": "ops-reset-password-123"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {tok}"}

                # 1. Live CREW observation
                r1 = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "scope": "CREW",
                        "metric": "heart_rate",
                        "value": 70.0,
                        "unit": "beats/min",
                        "source_id": "manual_log",
                        "observed_at": "2026-11-14T05:18:00+00:00",
                    },
                )
                self.assertEqual(r1.status_code, 201)

                # 2. Live CABIN observation
                r2 = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CABIN-1",
                        "scope": "CABIN",
                        "metric": "cabin_co2",
                        "value": 0.4,
                        "unit": "kPa",
                        "source_id": "manual_log",
                        "observed_at": "2026-11-14T05:18:00+00:00",
                    },
                )
                self.assertEqual(r2.status_code, 201)

                # 3. Explicitly marked engineering_test TEST_FIXTURE
                r3 = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "DEV-BENCH-1",
                        "scope": "engineering_test",
                        "metric": "heart_rate",
                        "value": 88.0,
                        "unit": "beats/min",
                        "source_id": "test_fixture",
                        "observed_at": "2026-11-14T05:18:00+00:00",
                    },
                )
                self.assertEqual(r3.status_code, 201)

                # Negative test: unconfirmed reset is rejected
                with self.assertRaises(ValueError):
                    reset_development_test_data(db, confirm=False)

                deleted = reset_development_test_data(db, confirm=True)
                self.assertEqual(deleted, 1)

                crew_rows = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-1"},
                    headers=headers,
                ).json()["observations"]
                self.assertEqual(len(crew_rows), 1)

                cabin_rows = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CABIN-1"},
                    headers=headers,
                ).json()["observations"]
                self.assertEqual(len(cabin_rows), 1)

                dev_rows = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "DEV-BENCH-1", "include_non_live": True},
                    headers=headers,
                ).json()["observations"]
                self.assertEqual(len(dev_rows), 0)


if __name__ == "__main__":
    unittest.main()
