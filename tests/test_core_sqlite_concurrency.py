"""Tests for Q-0044 concurrent SQLite transactions, busy-timeout, rollback, and cross-subject isolation."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import unittest

from aetherion_server import store


class SqliteConcurrencyTests(unittest.TestCase):
    def test_concurrent_writes_preserve_cross_subject_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "concurrent.sqlite3"
            store.initialize(db)

            def write_for_subject(subject_id: str, count: int) -> None:
                for idx in range(count):
                    store.ingest_observation(
                        db,
                        {
                            "subject_id": subject_id,
                            "scope": "CREW",
                            "metric": "heart_rate",
                            "value": 65.0 + idx,
                            "unit": "beats/min",
                            "source_id": "manual_log",
                            "observed_at": f"2026-11-14T05:19:{idx:02d}+00:00",
                        },
                    )

            with ThreadPoolExecutor(max_workers=2) as pool:
                f1 = pool.submit(write_for_subject, "CREW-A", 10)
                f2 = pool.submit(write_for_subject, "CREW-B", 10)
                f1.result()
                f2.result()

            obs_a = store.query_observations(db, subject_id="CREW-A", include_non_live=True)
            obs_b = store.query_observations(db, subject_id="CREW-B", include_non_live=True)
            self.assertEqual(len(obs_a), 10)
            self.assertEqual(len(obs_b), 10)
            self.assertTrue(all(row["subject_id"] == "CREW-A" for row in obs_a))
            self.assertTrue(all(row["subject_id"] == "CREW-B" for row in obs_b))

    def test_transaction_rollback_and_short_busy_timeout_lock_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "rollback_lock.sqlite3"
            store.initialize(db)

            # 1) Atomic rollback on mid-transaction exception
            conn = sqlite3.connect(db)
            try:
                conn.execute("BEGIN")
                conn.execute(
                    """
                    INSERT INTO observations (
                        subject_id, scope, metric, value, unit, source_id, source, observed_at, received_at
                    ) VALUES ('CREW-ROLLBACK', 'CREW', 'heart_rate', 70.0, 'beats/min', 'manual_log', 'manual_log', '2026-11-14T05:19:00+00:00', '2026-11-14T05:19:00+00:00')
                    """
                )
                conn.rollback()
            finally:
                conn.close()

            self.assertEqual(
                len(store.query_observations(db, subject_id="CREW-ROLLBACK", include_non_live=True)),
                0,
            )

            # 2) Active EXCLUSIVE lock causes a 10ms busy_timeout connection to fail with OperationalError
            holder = sqlite3.connect(db)
            contender = sqlite3.connect(db, timeout=0.01)
            try:
                holder.execute("BEGIN EXCLUSIVE")
                with self.assertRaises(sqlite3.OperationalError):
                    contender.execute("BEGIN IMMEDIATE")
                holder.rollback()
            finally:
                contender.close()
                holder.close()


if __name__ == "__main__":
    unittest.main()
