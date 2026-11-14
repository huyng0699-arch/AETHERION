"""Focused API test for Q-0174: offline assistance fallback without Earth delivery claim."""

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


class SafetyOfflineFallbackTests(unittest.TestCase):
    def test_offline_fallback_bilingual_never_claims_earth_delivery(self) -> None:
        old_env = {
            k: os.environ.get(k)
            for k in ("AETHERION_BOOTSTRAP_USER", "AETHERION_BOOTSTRAP_PASSWORD", "AETHERION_BOOTSTRAP_ROLE")
        }
        os.environ["AETHERION_BOOTSTRAP_USER"] = "crew_fb"
        os.environ["AETHERION_BOOTSTRAP_PASSWORD"] = "fallback-pass-123"
        os.environ["AETHERION_BOOTSTRAP_ROLE"] = "operator"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                app = create_app(db_path=Path(tmpdir) / "offline_fb.sqlite3")
                with TestClient(app) as client:
                    token = client.post(
                        "/api/v1/auth/login",
                        json={"username": "crew_fb", "password": "fallback-pass-123"},
                    ).json()["access_token"]
                    hdr = {"Authorization": f"Bearer {token}"}

                    for loc in ("vi", "en"):
                        resp = client.get(f"/api/v1/safety/offline-fallback?locale={loc}", headers=hdr)
                        self.assertEqual(resp.status_code, 200, resp.text)
                        data = resp.json()
                        self.assertEqual(data["locale"], loc)
                        self.assertEqual(data["relay_status"], "OFFLINE_ONBOARD_ONLY")
                        self.assertFalse(data["earth_delivery_claimed"])
                        self.assertTrue(data["requires_local_crew_followup"])
                        self.assertGreaterEqual(len(data["local_followup_steps"]), 3)
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
