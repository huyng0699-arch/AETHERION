"""Tests for Q-0050 summary API data availability (NO_DATA, READY, STALE)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class ServerAvailabilityTests(unittest.TestCase):
    def test_computes_no_data_ready_and_stale_without_clinical_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "availability.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_avail",
                password="ops-avail-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_avail", "password": "ops-avail-password-123"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {tok}"}

                # 1) NO_DATA when no observations exist
                empty = client.get("/api/v1/subjects/CREW-EMPTY/summary", headers=headers)
                self.assertEqual(empty.status_code, 200)
                self.assertEqual(empty.json()["availability_status"], "NO_DATA")
                self.assertEqual(
                    empty.json()["clinical_interpretation"],
                    "NONE_DETERMINISTIC_AVAILABILITY_ONLY",
                )

                # 2) STALE when latest observation is 3 hours old and stale_after_seconds=3600
                old_ts = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
                client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-STALE",
                        "scope": "CREW",
                        "metric": "heart_rate",
                        "value": 70.0,
                        "unit": "beats/min",
                        "source_id": "manual_log",
                        "observed_at": old_ts,
                    },
                )
                stale = client.get(
                    "/api/v1/subjects/CREW-STALE/summary",
                    params={"stale_after_seconds": 3600},
                    headers=headers,
                )
                self.assertEqual(stale.status_code, 200)
                self.assertEqual(stale.json()["availability_status"], "STALE")
                self.assertGreater(stale.json()["age_seconds"], 3600)

                # 3) READY when latest observation is fresh (10 seconds old)
                fresh_ts = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
                client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-READY",
                        "scope": "CREW",
                        "metric": "spo2",
                        "value": 98.0,
                        "unit": "%",
                        "source_id": "manual_log",
                        "observed_at": fresh_ts,
                    },
                )
                ready = client.get(
                    "/api/v1/subjects/CREW-READY/summary",
                    params={"stale_after_seconds": 3600},
                    headers=headers,
                )
                self.assertEqual(ready.status_code, 200)
                self.assertEqual(ready.json()["availability_status"], "READY")
                self.assertEqual(ready.json()["metrics_present"], ["spo2"])

                # Negative: invalid stale_after_seconds <= 0 rejected with 422
                bad_param = client.get(
                    "/api/v1/subjects/CREW-READY/summary",
                    params={"stale_after_seconds": 0},
                    headers=headers,
                )
                self.assertEqual(bad_param.status_code, 422)


if __name__ == "__main__":
    unittest.main()
