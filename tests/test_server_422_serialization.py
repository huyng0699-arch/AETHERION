from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.main import create_app


class Server422SerializationTests(unittest.TestCase):
    def test_value_error_ctx_serializes_as_typed_422_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_422.sqlite3"
            old_env = {
                k: os.environ.get(k)
                for k in (
                    "AETHERION_BOOTSTRAP_USER",
                    "AETHERION_BOOTSTRAP_PASSWORD",
                    "AETHERION_BOOTSTRAP_ROLE",
                )
            }
            os.environ["AETHERION_BOOTSTRAP_USER"] = "ops_422"
            os.environ["AETHERION_BOOTSTRAP_PASSWORD"] = "ops-422-password"
            os.environ["AETHERION_BOOTSTRAP_ROLE"] = "operator"
            try:
                app = create_app(db_path=db_path)
                with TestClient(app) as client:
                    login_resp = client.post(
                        "/api/v1/auth/login",
                        json={"username": "ops_422", "password": "ops-422-password"},
                    )
                    self.assertEqual(login_resp.status_code, 200)
                    token = login_resp.json()["access_token"]

                    # Triggers Pydantic v2 ValueError in field_validator (ctx={"error": ValueError(...)})
                    bad_obs = client.post(
                        "/api/v1/observations",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "subject_id": "   ",
                            "scope": "crew",
                            "metric": "heart_rate",
                            "value": 72.0,
                            "unit": "beats/min",
                            "source_id": "test_sensor",
                            "observed_at": "2026-11-14T10:00:00",  # missing timezone -> ValueError too
                            "quality": "READY",
                        },
                    )
                    self.assertEqual(bad_obs.status_code, 422, bad_obs.text)
                    body = bad_obs.json()
                    self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
                    self.assertEqual(body["error"]["status"], 422)
                    self.assertIsInstance(body["detail"], list)
                    self.assertGreaterEqual(len(body["detail"]), 1)
                    # Ensure ctx['error'] was serialized to string, not crashing with 500
                    ctx_errors = [
                        item.get("ctx", {}).get("error")
                        for item in body["detail"]
                        if isinstance(item, dict) and "ctx" in item
                    ]
                    self.assertTrue(any(isinstance(err, str) and err for err in ctx_errors))
            finally:
                for k, v in old_env.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
