"""Contract and live API conformance fixture tests for Q-0029."""

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = ROOT / "packages" / "contracts" / "conformance_fixtures.json"


class CrossClientConformanceTests(unittest.TestCase):
    def test_conformance_fixtures_declare_all_clients(self) -> None:
        data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(data["target_clients"]), {"desktop-qt", "mobile", "watch", "cli"})
        self.assertGreaterEqual(len(data["fixtures"]), 3)

    def test_all_conformance_fixtures_match_live_server(self) -> None:
        data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "conformance.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_conf",
                password="ops-conf-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_conf", "password": "ops-conf-password-123"},
                ).json()["access_token"]
                base_headers = {"Authorization": f"Bearer {tok}"}

                for fx in data["fixtures"]:
                    headers = dict(base_headers)
                    headers.update(fx.get("headers", {}))
                    if fx["method"] == "POST":
                        resp = client.post(fx["path"], headers=headers, json=fx["request_body"])
                    else:
                        resp = client.get(fx["path"], headers=headers)
                    self.assertEqual(resp.status_code, fx["expected_status"], fx["name"])
                    body = resp.json()
                    for key in fx.get("expected_response_keys", []):
                        self.assertIn(key, body, f"{fx['name']} missing {key}")
                    for k, v in fx.get("expected_body_subset", {}).items():
                        self.assertEqual(body.get(k), v, f"{fx['name']} mismatch on {k}")


if __name__ == "__main__":
    unittest.main()
