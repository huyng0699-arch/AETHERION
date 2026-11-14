"""Focused server-admin authorization, persistence and backup smoke.

No real network, devices, NASA telemetry or cloud providers are invoked.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class AdminIntegrationTest(unittest.TestCase):
    def test_auth_config_readback_and_backup(self):
        with TemporaryDirectory() as folder:
            database = Path(folder) / "observations.sqlite3"
            ensure_bootstrap_user(database, username="operator_example",
                                  password="operator-strong-pass",
                                  role="operator", allowed_subjects=["*"])
            ensure_bootstrap_user(database, username="admin_example",
                                  password="admin-strong-pass",
                                  role="admin", allowed_subjects=["*"])
            with TestClient(create_app(database)) as client:
                self.assertEqual(client.get("/api/v1/admin/overview").status_code, 401)
                crew = client.post("/api/v1/auth/login", json={
                    "username": "operator_example", "password": "operator-strong-pass"})
                self.assertEqual(crew.status_code, 200)
                crew_headers = {"Authorization": "Bearer " + crew.json()["access_token"]}
                self.assertEqual(client.get("/api/v1/admin/overview",
                                            headers=crew_headers).status_code, 403)
                admin = client.post("/api/v1/auth/login", json={
                    "username": "admin_example", "password": "admin-strong-pass"})
                self.assertEqual(admin.status_code, 200)
                headers = {"Authorization": "Bearer " + admin.json()["access_token"]}
                overview = client.get("/api/v1/admin/overview", headers=headers)
                self.assertEqual(overview.status_code, 200, overview.text)
                self.assertEqual(overview.json()["counts"]["users"], 2)
                users = client.get("/api/v1/admin/users", headers=headers)
                self.assertEqual(users.status_code, 200, users.text)
                self.assertEqual(len(users.json()["users"]), 2)
                self.assertNotIn("password_hash", str(users.json()))
                sources = client.get("/api/v1/admin/sources", headers=headers)
                self.assertEqual(sources.status_code, 200, sources.text)
                self.assertEqual(sources.json()["sources"], [])
                interview_status = client.get("/api/v1/knowledge/interview/ai-status")
                self.assertEqual(interview_status.status_code, 200, interview_status.text)
                self.assertFalse(interview_status.json()["configured"])
                self.assertEqual(interview_status.json()["source"], "server_admin")
                config = {
                    "mode": "off", "local_runtime": "ollama",
                    "local_url": "http://127.0.0.1:11434",
                    "local_model": "", "timeout_seconds": 5,
                    "cloud_data_sharing": False,
                }
                saved = client.put("/api/v1/admin/ai/settings",
                                   json=config, headers=headers)
                self.assertEqual(saved.status_code, 200, saved.text)
                readback = client.get("/api/v1/admin/ai/settings", headers=headers)
                self.assertEqual(readback.json()["settings"], config)
                forbidden = {**config, "local_url": "http://example.com:11434"}
                self.assertEqual(client.put("/api/v1/admin/ai/settings",
                                            json=forbidden, headers=headers).status_code, 422)
                self.assertEqual(client.put("/api/v1/admin/ai/settings",
                                            json={**config, "cloud_data_sharing": True},
                                            headers=headers).status_code, 422)
                backup = client.post("/api/v1/admin/storage/backup", headers=headers)
                self.assertEqual(backup.status_code, 200, backup.text)
                self.assertEqual(backup.json()["integrity"], "ok")
                self.assertTrue((database.parent / "backups" / backup.json()["filename"]).exists())
                events = client.get("/api/v1/admin/events", headers=headers)
                self.assertEqual(events.status_code, 200)
                self.assertGreaterEqual(len(events.json()["events"]), 2)


if __name__ == "__main__":
    unittest.main()
