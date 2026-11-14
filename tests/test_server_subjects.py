"""Tests for Q-0049 subject profile read endpoint (exact match or explicit 404)."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class ServerSubjectsTests(unittest.TestCase):
    def test_fetch_exact_subject_or_explicit_404(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "subjects.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_subj",
                password="ops-subj-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            ensure_bootstrap_user(
                db,
                username="crew_alice",
                password="crew-alice-password-123",
                role="crew",
                allowed_subjects=["CREW-ALICE"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                ops_tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_subj", "password": "ops-subj-password-123"},
                ).json()["access_token"]
                ops_h = {"Authorization": f"Bearer {ops_tok}"}

                # Non-existent subject -> explicit 404 (no fallback)
                missing = client.get("/api/v1/subjects/CREW-UNKNOWN", headers=ops_h)
                self.assertEqual(missing.status_code, 404)

                # Register exact subject
                created = client.post(
                    "/api/v1/subjects",
                    headers=ops_h,
                    json={
                        "subject_id": "CREW-ALICE",
                        "display_name": "Alice Commander",
                        "scope": "CREW",
                        "role_label": "commander",
                    },
                )
                self.assertEqual(created.status_code, 201)

                # Fetch exact subject
                fetched = client.get("/api/v1/subjects/CREW-ALICE", headers=ops_h)
                self.assertEqual(fetched.status_code, 200)
                self.assertEqual(fetched.json()["subject"]["subject_id"], "CREW-ALICE")
                self.assertEqual(fetched.json()["subject"]["display_name"], "Alice Commander")

                # Crew user unauthorized for CREW-BOB -> 403
                crew_tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "crew_alice", "password": "crew-alice-password-123"},
                ).json()["access_token"]
                denied = client.get(
                    "/api/v1/subjects/CREW-BOB",
                    headers={"Authorization": f"Bearer {crew_tok}"},
                )
                self.assertEqual(denied.status_code, 403)


if __name__ == "__main__":
    unittest.main()
