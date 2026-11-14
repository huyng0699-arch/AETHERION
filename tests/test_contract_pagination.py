"""Tests for Q-0022 historical cursor pagination under concurrent additions."""

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app

ROOT = Path(__file__).resolve().parents[1]


class PaginationContractTests(unittest.TestCase):
    def test_schema_declares_cursor_pagination(self) -> None:
        schema_path = ROOT / "packages" / "contracts" / "pagination.schema.json"
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["required"], ["observations", "has_more", "next_cursor"])
        self.assertTrue(schema["x-cursor-semantics"]["stable_under_concurrent_inserts"])

    def test_cursor_pagination_stable_under_concurrent_insert_and_rejects_bad_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "pagination.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_page",
                password="ops-page-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_page", "password": "ops-page-password-123"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {tok}"}

                for minute, val in ((1, 61.0), (2, 62.0), (3, 63.0), (4, 64.0)):
                    client.post(
                        "/api/v1/observations",
                        headers=headers,
                        json={
                            "subject_id": "CREW-1",
                            "scope": "CREW",
                            "metric": "heart_rate",
                            "value": val,
                            "unit": "beats/min",
                            "source_id": "manual",
                            "observed_at": f"2026-11-14T05:0{minute}:00+00:00",
                        },
                    )

                # Page 1 (desc, limit=2) -> returns 64.0, 63.0
                p1 = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-1", "limit": 2, "order": "desc"},
                    headers=headers,
                )
                self.assertEqual(p1.status_code, 200)
                self.assertEqual([o["value"] for o in p1.json()["observations"]], [64.0, 63.0])
                self.assertTrue(p1.json()["has_more"])
                cursor = p1.json()["next_cursor"]
                self.assertIsNotNone(cursor)

                # Concurrent insert of a newer observation (minute=5, value=65.0)
                client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "scope": "CREW",
                        "metric": "heart_rate",
                        "value": 65.0,
                        "unit": "beats/min",
                        "source_id": "manual",
                        "observed_at": "2026-11-14T05:05:00+00:00",
                    },
                )

                # Page 2 with cursor must return [62.0, 61.0] with ZERO duplicates or skips
                p2 = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-1", "limit": 2, "order": "desc", "cursor": cursor},
                    headers=headers,
                )
                self.assertEqual(p2.status_code, 200)
                self.assertEqual([o["value"] for o in p2.json()["observations"]], [62.0, 61.0])
                self.assertFalse(p2.json()["has_more"])
                self.assertIsNone(p2.json()["next_cursor"])

                # Negative: malformed cursor rejected with 422
                bad = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-1", "cursor": "not-valid-base64!"},
                    headers=headers,
                )
                self.assertEqual(bad.status_code, 422)


if __name__ == "__main__":
    unittest.main()
