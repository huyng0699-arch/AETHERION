"""Tests actual SQLite behavior; no synthetic data is shown in the app UI."""

from pathlib import Path
import sqlite3
import tempfile
import unittest

from aetherion_server.security import verify_password
from aetherion_server.store import (
    add_observation,
    check_readiness,
    create_session,
    get_active_session,
    get_user_by_username,
    ingest_observation,
    list_observations,
    query_observations,
    revoke_session,
    upsert_user,
)


class StoreTests(unittest.TestCase):
    def test_persist_and_filter_by_subject(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "observations.sqlite3"
            item = {
                "subject_id": "ENGINEERING-A",
                "metric": "heart_rate",
                "value": 72.0,
                "unit": "beats/min",
                "source": "manual_software_test",
                "observed_at": "2026-11-14T09:00:00+07:00",
            }
            observation_id = add_observation(db, item)
            self.assertGreater(observation_id, 0)
            matching = list_observations(db, "ENGINEERING-A")
            other = list_observations(db, "ENGINEERING-B")
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]["value"], 72.0)
            self.assertEqual(matching[0]["source"], "manual_software_test")
            self.assertEqual(matching[0]["source_id"], "manual_software_test")
            self.assertEqual(matching[0]["scope"], "crew")
            self.assertEqual(matching[0]["verification_state"], "UNVERIFIED")
            self.assertEqual(other, [])
            self.assertTrue(db.exists())

    def test_idempotent_replay_and_scope_metric_filtering(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "observations.sqlite3"
            payload = {
                "subject_id": "CREW-01",
                "scope": "personal",
                "metric": "body_mass",
                "value": 68.4,
                "unit": "kg",
                "source_id": "manual_scale_entry",
                "observed_at": "2026-11-14T04:00:00+00:00",
                "quality": "READY",
                "verification_state": "SELF_REPORTED",
                "idempotency_key": "req-001",
            }
            first_id, created_first, rec_first = ingest_observation(db, payload, created_by="crew1")
            second_id, created_second, rec_second = ingest_observation(db, payload, created_by="crew1")
            self.assertTrue(created_first)
            self.assertFalse(created_second)
            self.assertEqual(first_id, second_id)
            self.assertEqual(rec_first["id"], rec_second["id"])
            rows = query_observations(db, "CREW-01", scope="personal", metric="body_mass")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["created_by"], "crew1")
            self.assertEqual(rows[0]["verification_state"], "SELF_REPORTED")

    def test_legacy_starter_schema_migrates_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "legacy.sqlite3"
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
                    VALUES ('LEGACY-1', 'spo2', 98.0, '%', 'legacy_source', '2026-11-14T01:00:00+00:00')
                    """
                )
            readiness = check_readiness(db)
            self.assertEqual(readiness["database"], "ok")
            rows = list_observations(db, "LEGACY-1")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_id"], "legacy_source")
            self.assertTrue(rows[0]["received_at"])

    def test_user_and_session_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "auth.sqlite3"
            user = upsert_user(
                db,
                username="crew_alice",
                password="correct-horse-battery",
                role="crew",
                allowed_subjects=["CREW-ALICE"],
            )
            fetched = get_user_by_username(db, "crew_alice")
            self.assertIsNotNone(fetched)
            assert fetched is not None
            self.assertTrue(verify_password("correct-horse-battery", fetched["password_hash"]))
            self.assertFalse(verify_password("wrong-password", fetched["password_hash"]))

            session_info = create_session(db, user_id=user["id"], ttl_seconds=60)
            active = get_active_session(db, session_info["access_token"])
            self.assertIsNotNone(active)
            assert active is not None
            self.assertEqual(active["username"], "crew_alice")

            self.assertTrue(revoke_session(db, session_info["access_token"]))
            self.assertIsNone(get_active_session(db, session_info["access_token"]))


if __name__ == "__main__":
    unittest.main()
