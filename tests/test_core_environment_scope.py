"""Tests for Q-0039 cabin environmental data scopes."""

from pathlib import Path
import sqlite3
import tempfile
import unittest

from aetherion_server.environment_store import EnvironmentStore
from aetherion_server.sqlite_compat import connect_sqlite


class EnvironmentScopeTests(unittest.TestCase):
    def test_cabin_metrics_stored_separately_from_personal_health(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "env.sqlite3"
            store = EnvironmentStore(db)
            rec = store.record_environment_metric(
                subject_id="CABIN-HAB-1",
                scope="CABIN",
                metric="cabin_co2",
                value=0.45,
                unit="kPa",
                source_id="eclss_sensor",
                observed_at="2026-11-14T05:15:00+00:00",
            )
            self.assertEqual(rec["scope"], "CABIN")
            self.assertEqual(rec["metric"], "cabin_co2")
            self.assertEqual(len(store.list_environment_metrics(subject_id="CABIN-HAB-1")), 1)

            with connect_sqlite(db) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
            self.assertIn("environment_observations", tables)
            self.assertNotIn("observations", tables)

    def test_personal_health_metric_or_crew_scope_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "env_bad.sqlite3"
            store = EnvironmentStore(db)
            with self.assertRaises(ValueError):
                store.record_environment_metric(
                    subject_id="CREW-1",
                    scope="CREW",
                    metric="cabin_co2",
                    value=0.45,
                    unit="kPa",
                    source_id="eclss_sensor",
                    observed_at="2026-11-14T05:15:00+00:00",
                )
            with self.assertRaises(ValueError):
                store.record_environment_metric(
                    subject_id="CABIN-HAB-1",
                    scope="CABIN",
                    metric="heart_rate",
                    value=72.0,
                    unit="beats/min",
                    source_id="wearable_1",
                    observed_at="2026-11-14T05:15:00+00:00",
                )


if __name__ == "__main__":
    unittest.main()
