"""Focused SQLite/provenance smoke for the deliberately fictional patient demo.

No real patient records or production database is accessed.
"""
from datetime import date
import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

MODULE = (
    Path(__file__).resolve().parents[1] / "apps" / "desktop" / "src" /
    "aetherion_desktop" / "features" / "demo" / "synthetic_patients.py"
)
spec = importlib.util.spec_from_file_location("synthetic_patients_smoke", MODULE)
demo = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = demo
spec.loader.exec_module(demo)


class SyntheticPatientDemoTests(unittest.TestCase):
    def test_complete_isolated_longitudinal_fixture_and_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "demo.sqlite3"
            info = demo.build_demo_database(db, today=date(2026, 11, 14))
            self.assertTrue(info["is_synthetic"])
            self.assertEqual(info["days"], 540)
            self.assertEqual(info["subjects"], 5)
            self.assertEqual(info["metrics"], 12)
            self.assertGreater(info["observations"], 30000)
            self.assertEqual(len(demo.subjects(db)), 5)
            self.assertEqual(info["from"], "2025-05-24")
            self.assertEqual(info["to"], "2026-11-14")
            items = demo.series("DEMO-P001", "heart_rate", path=db)
            self.assertGreater(len(items), 500)
            self.assertTrue(all(x["source_id"] == demo.SOURCE_ID for x in items))
            day = demo.day_values("DEMO-P002", info["to"], db)
            self.assertGreater(len(day), 8)
            self.assertTrue(all(x["quality"] == "UNVERIFIED" for x in day))
            with sqlite3.connect(db) as conn:
                states = conn.execute(
                    "SELECT DISTINCT scope, verification_state, quality, synthetic "
                    "FROM demo_observations"
                ).fetchall()
                self.assertEqual(states, [("engineering_test", "TEST_FIXTURE", "UNVERIFIED", 1)])
            # Reopening does not duplicate seeded data.
            again = demo.build_demo_database(db, today=date(2026, 11, 14))
            self.assertEqual(info["observations"], again["observations"])
            self.assertEqual(info["observations"], demo.demo_stats(db)["observations"])

    def test_fail_closed_if_file_is_not_a_demo_database(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "private.sqlite3"
            with sqlite3.connect(db) as conn:
                conn.execute("CREATE TABLE patients (id INTEGER)")
            with self.assertRaises(ValueError):
                demo.build_demo_database(db)
            with sqlite3.connect(db) as conn:
                self.assertIsNotNone(conn.execute(
                    "SELECT name FROM sqlite_master WHERE name='patients'"
                ).fetchone())

    def test_reject_unknown_metrics(self):
        with self.assertRaises(ValueError):
            demo.series("DEMO-P001", "made_up_metric")


if __name__ == "__main__":
    unittest.main()
