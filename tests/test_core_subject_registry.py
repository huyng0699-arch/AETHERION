"""Tests for Q-0037 fail-closed subject registry and identity lookup."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app
from aetherion_server.subject_registry import SubjectRegistry, UnknownSubjectError


class SubjectRegistryTests(unittest.TestCase):
    def test_unknown_subject_never_selects_existing_profile(self) -> None:
        registry = SubjectRegistry()
        registry.register(subject_id="CREW-1", scope="CREW", display_name="Commander One")
        self.assertEqual(registry.get_exact("CREW-1").display_name, "Commander One")

        with self.assertRaises(UnknownSubjectError):
            registry.get_exact("CREW-2")
        with self.assertRaises(UnknownSubjectError):
            registry.get_exact("crew-1")
        with self.assertRaises(UnknownSubjectError):
            registry.get_exact("")

    def test_live_api_unknown_subject_returns_404_when_other_profiles_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "subj_reg.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_reg",
                password="ops-reg-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_reg", "password": "ops-reg-password-123"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {tok}"}

                created = client.post(
                    "/api/v1/subjects",
                    headers=headers,
                    json={"subject_id": "CREW-1", "scope": "CREW", "display_name": "Crew One"},
                )
                self.assertEqual(created.status_code, 201)

                missing = client.get("/api/v1/subjects/CREW-UNKNOWN", headers=headers)
                self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
