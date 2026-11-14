"""Contract and live API tests for Q-0023 idempotent command keys."""

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app

ROOT = Path(__file__).resolve().parents[1]


class IdempotencyContractTests(unittest.TestCase):
    def test_schema_declares_idempotent_replay_contract(self) -> None:
        schema_path = ROOT / "packages" / "contracts" / "idempotency.schema.json"
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["x-idempotency-semantics"]["header"], "Idempotency-Key")
        self.assertEqual(schema["x-idempotency-semantics"]["initial_http_status"], 201)
        self.assertEqual(schema["x-idempotency-semantics"]["replay_http_status"], 200)

    def test_retried_post_does_not_create_duplicate_observation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "idem.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_idem",
                password="ops-idem-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_idem", "password": "ops-idem-password-123"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {tok}", "Idempotency-Key": "cmd-retry-001"}
                payload = {
                    "subject_id": "CREW-1",
                    "scope": "CREW",
                    "metric": "heart_rate",
                    "value": 66.0,
                    "unit": "beats/min",
                    "source_id": "manual_log",
                    "observed_at": "2026-11-14T05:06:00+00:00",
                }
                first = client.post("/api/v1/observations", headers=headers, json=payload)
                self.assertEqual(first.status_code, 201)
                self.assertFalse(first.json()["idempotent_replay"])

                retry = client.post("/api/v1/observations", headers=headers, json=payload)
                self.assertEqual(retry.status_code, 200)
                self.assertTrue(retry.json()["idempotent_replay"])
                self.assertEqual(first.json()["id"], retry.json()["id"])

                rows = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-1"},
                    headers={"Authorization": f"Bearer {tok}"},
                ).json()["observations"]
                self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
