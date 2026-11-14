"""Contract and live API tests for Q-0019 data provenance classification."""

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app

ROOT = Path(__file__).resolve().parents[1]


class ProvenanceClassificationTests(unittest.TestCase):
    def test_schema_separates_provenance_classes_and_safety_flags(self) -> None:
        schema_path = ROOT / "packages" / "contracts" / "provenance_classification.schema.json"
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["properties"]["provenance_class"]["enum"],
            ["measured", "self_reported", "derived", "unverified", "absent"],
        )
        self.assertIn("NO_DATA", schema["properties"]["quality"]["enum"])
        self.assertIn("UNVERIFIED", schema["properties"]["verification_state"]["enum"])
        self.assertFalse(schema["x-aetherion-semantics"]["no_data_is_healthy"])
        self.assertFalse(schema["x-aetherion-semantics"]["missing_heartbeat_means_unconscious"])

    def test_api_rejects_invented_clinical_verification_and_preserves_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "provenance.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_prov",
                password="ops-prov-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_prov", "password": "ops-prov-password-123"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                # Invented/unallowed clinical verification state must be rejected
                forged = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "some_watch",
                        "observed_at": "2026-11-14T04:50:00+00:00",
                        "verification_state": "CLINICALLY_CERTIFIED",
                    },
                )
                self.assertEqual(forged.status_code, 422)

                # Missing source_id/source must be rejected
                no_source = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "observed_at": "2026-11-14T04:50:00+00:00",
                    },
                )
                self.assertEqual(no_source.status_code, 422)

                # Valid self-reported + NO_DATA quality preserved distinctly
                valid = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "fatigue_score",
                        "value": 3.0,
                        "unit": "scale_1_10",
                        "source_id": "crew_self_report",
                        "observed_at": "2026-11-14T04:50:00+00:00",
                        "quality": "READY",
                        "verification_state": "SELF_REPORTED",
                    },
                )
                self.assertEqual(valid.status_code, 201)
                obs = valid.json()["observation"]
                self.assertEqual(obs["quality"], "READY")
                self.assertEqual(obs["verification_state"], "SELF_REPORTED")
                self.assertEqual(obs["source_id"], "crew_self_report")


if __name__ == "__main__":
    unittest.main()
