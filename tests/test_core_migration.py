"""Verification tests for Q-0032 SQLite schema migration from starter."""

from pathlib import Path
import sqlite3
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app
from aetherion_server.store import initialize, list_observations


class CoreMigrationTests(unittest.TestCase):
    def test_starter_database_migrates_without_losing_observations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "starter.sqlite3"
            with sqlite3.connect(db) as conn:
                conn.execute(
                    """
                    CREATE TABLE observations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject_id TEXT NOT NULL,
                        metric TEXT NOT NULL,
                        value REAL NOT NULL,
                        unit TEXT NOT NULL,
                        source TEXT NOT NULL,
                        observed_at TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO observations (subject_id, metric, value, unit, source, observed_at)
                    VALUES
                        ('CREW-01', 'heart_rate', 71.0, 'beats/min', 'starter_manual', '2026-11-14T01:00:00+00:00'),
                        ('CREW-01', 'spo2', 98.5, '%', 'starter_manual', '2026-11-14T01:05:00+00:00'),
                        ('CREW-02', 'body_mass', 67.2, 'kg', 'starter_scale', '2026-11-14T01:10:00+00:00')
                    """
                )

            # Run migration twice to prove idempotency
            initialize(db)
            initialize(db)

            crew1 = list_observations(db, "CREW-01")
            crew2 = list_observations(db, "CREW-02")
            self.assertEqual(len(crew1), 2)
            self.assertEqual(len(crew2), 1)
            self.assertEqual({row["metric"] for row in crew1}, {"heart_rate", "spo2"})
            self.assertEqual(crew2[0]["source_id"], "starter_scale")
            self.assertEqual(crew2[0]["scope"], "crew")
            self.assertTrue(crew2[0]["received_at"])

            # Verify migrated records are readable via authenticated FastAPI server
            ensure_bootstrap_user(
                db,
                username="ops_migrated",
                password="ops-migrated-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_migrated", "password": "ops-migrated-password-123"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
                resp = client.get("/api/v1/observations", params={"subject_id": "CREW-01"}, headers=headers)
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(len(resp.json()["observations"]), 2)


if __name__ == "__main__":
    unittest.main()
