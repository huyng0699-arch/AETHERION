"""Contract and live API tests for Q-0020 CREW/CABIN/VEHICLE scope separation."""

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app

ROOT = Path(__file__).resolve().parents[1]


class ScopeContractTests(unittest.TestCase):
    def test_schema_declares_crew_cabin_vehicle_and_disallowed_mixes(self) -> None:
        schema_path = ROOT / "packages" / "contracts" / "scope_contract.schema.json"
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for scope in ("CREW", "CABIN", "VEHICLE"):
            self.assertIn(scope, schema["properties"]["scope"]["enum"])
        self.assertIn("cabin_co2", schema["x-scope-metric-rules"]["environment_metrics_disallowed_on_person"])
        self.assertIn("heart_rate", schema["x-scope-metric-rules"]["person_metrics_disallowed_on_environment"])

    def test_api_rejects_cabin_co2_on_person_and_accepts_on_cabin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "scope.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_scope",
                password="ops-scope-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_scope", "password": "ops-scope-password-123"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                # Negative: cabin_co2 assigned to CREW/person must be rejected with 422
                bad_person = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "scope": "CREW",
                        "metric": "cabin_co2",
                        "value": 1200.0,
                        "unit": "ppm",
                        "source_id": "env_sensor_1",
                        "observed_at": "2026-11-14T04:55:00+00:00",
                    },
                )
                self.assertEqual(bad_person.status_code, 422)

                # Negative: heart_rate assigned to CABIN must be rejected with 422
                bad_env = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CABIN-NODE-1",
                        "scope": "CABIN",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "wearable_1",
                        "observed_at": "2026-11-14T04:55:00+00:00",
                    },
                )
                self.assertEqual(bad_env.status_code, 422)

                # Positive: cabin_co2 assigned to CABIN succeeds
                good_cabin = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CABIN-NODE-1",
                        "scope": "CABIN",
                        "metric": "cabin_co2",
                        "value": 1200.0,
                        "unit": "ppm",
                        "source_id": "env_sensor_1",
                        "observed_at": "2026-11-14T04:55:00+00:00",
                    },
                )
                self.assertEqual(good_cabin.status_code, 201)
                self.assertEqual(good_cabin.json()["observation"]["scope"], "CABIN")


if __name__ == "__main__":
    unittest.main()
