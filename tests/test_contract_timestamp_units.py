"""Contract and live API tests for Q-0018 timestamps and measurement units."""

from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app

ROOT = Path(__file__).resolve().parents[1]


class TimestampUnitsContractTests(unittest.TestCase):
    def test_schema_requires_offset_aware_times_and_declared_unit(self) -> None:
        schema_path = ROOT / "packages" / "contracts" / "timestamp_units.schema.json"
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["required"], ["observed_at", "received_at", "unit"])
        self.assertIn("(Z|[+-][0-9]{2}:[0-9]{2})$", schema["properties"]["observed_at"]["pattern"])
        self.assertIn("heart_rate", schema["x-canonical-units"])

    def test_api_rejects_naive_time_and_blank_unit_and_persists_received_at(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "ts_units.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_ts",
                password="ops-ts-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_ts", "password": "ops-ts-password-123"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                # Naive timestamp rejected
                naive = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "manual_entry",
                        "observed_at": "2026-11-14T04:50:00",
                    },
                )
                self.assertEqual(naive.status_code, 422)

                # Blank unit rejected
                blank_unit = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "   ",
                        "source_id": "manual_entry",
                        "observed_at": "2026-11-14T04:50:00+00:00",
                    },
                )
                self.assertEqual(blank_unit.status_code, 422)

                # Valid offset-aware request returns both observed_at and server received_at
                valid = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "manual_entry",
                        "observed_at": "2026-11-14T04:50:00+07:00",
                    },
                )
                self.assertEqual(valid.status_code, 201)
                obs = valid.json()["observation"]
                self.assertEqual(obs["unit"], "beats/min")
                self.assertIsNotNone(datetime.fromisoformat(obs["observed_at"]).tzinfo)
                self.assertIsNotNone(datetime.fromisoformat(obs["received_at"]).tzinfo)


if __name__ == "__main__":
    unittest.main()
