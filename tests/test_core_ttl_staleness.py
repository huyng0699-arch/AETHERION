"""Tests for Q-0041 no-data and stale TTL logic."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.availability import compute_availability
from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class TtlStalenessTests(unittest.TestCase):
    def test_no_data_is_never_zero_and_invalid_ttl_rejected(self) -> None:
        empty = compute_availability([], stale_after_seconds=600)
        self.assertEqual(empty["availability_status"], "NO_DATA")
        self.assertIsNone(empty["age_seconds"])
        self.assertIsNone(empty["latest_observed_at"])
        self.assertEqual(empty["metrics_present"], [])

        with self.assertRaises(ValueError):
            compute_availability([], stale_after_seconds=0)

    def test_stale_values_remain_visible_with_age(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "ttl.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_ttl",
                password="ops-ttl-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_ttl", "password": "ops-ttl-password-123"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {tok}"}

                old_ts = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
                post = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-TTL",
                        "scope": "CREW",
                        "metric": "heart_rate",
                        "value": 64.0,
                        "unit": "beats/min",
                        "source_id": "manual_log",
                        "observed_at": old_ts,
                    },
                )
                self.assertEqual(post.status_code, 201)

                summary = client.get(
                    "/api/v1/subjects/CREW-TTL/summary",
                    params={"stale_after_seconds": 60},
                    headers=headers,
                ).json()
                self.assertEqual(summary["availability_status"], "STALE")
                self.assertGreater(summary["age_seconds"], 60.0)
                self.assertEqual(summary["metrics_present"], ["heart_rate"])

                obs = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-TTL"},
                    headers=headers,
                ).json()["observations"]
                self.assertEqual(len(obs), 1)
                self.assertEqual(obs[0]["value"], 64.0)


if __name__ == "__main__":
    unittest.main()
