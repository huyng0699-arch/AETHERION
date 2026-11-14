"""Benchmark and index-plan tests for Q-0045 time-series query performance."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import closing
import sqlite3
import tempfile
import time
import unittest

from aetherion_server import store


class TimeSeriesPerformanceTests(unittest.TestCase):
    def test_indexed_timeseries_query_against_reproducible_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "perf.sqlite3"
            store.initialize(db)

            base = datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc)
            rows = []
            for subj_idx in range(4):
                subject_id = f"CREW-{subj_idx + 1}"
                for i in range(500):
                    ts = (base + timedelta(seconds=i * 10)).isoformat()
                    rows.append(
                        (
                            subject_id,
                            "CREW",
                            "heart_rate",
                            65.0 + (i % 30),
                            "beats/min",
                            "manual_log",
                            "manual_log",
                            ts,
                            ts,
                        )
                    )

            with closing(sqlite3.connect(db)) as conn:
                conn.executemany(
                    """
                    INSERT INTO observations (
                        subject_id, scope, metric, value, unit, source_id, source, observed_at, received_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                plan_rows = conn.execute(
                    """
                    EXPLAIN QUERY PLAN
                    SELECT * FROM observations
                    WHERE subject_id = 'CREW-2' AND scope = 'CREW' AND metric = 'heart_rate'
                    ORDER BY observed_at ASC
                    """
                ).fetchall()
                plan_text = " ".join(str(r[3]) for r in plan_rows)
                self.assertIn("USING INDEX idx_obs_subject_scope_metric", plan_text)

            t0 = time.perf_counter()
            series = store.query_observations(
                db,
                subject_id="CREW-2",
                scope="CREW",
                metric="heart_rate",
                include_non_live=True,
                limit=500,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            self.assertEqual(len(series), 500)
            self.assertLess(elapsed_ms, 200.0, f"Indexed query too slow: {elapsed_ms:.2f}ms")
            self.assertEqual(
                store.query_observations(db, subject_id="CREW-UNKNOWN", include_non_live=True),
                [],
            )


if __name__ == "__main__":
    unittest.main()
