"""Tests for Q-0038 self-reported health observation model."""

from pathlib import Path
from contextlib import closing
import sqlite3
import tempfile
import unittest

from aetherion_server.self_report import SelfReportStore


class SelfReportTests(unittest.TestCase):
    def test_self_report_persists_separately_from_sensor_observations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "self_reports.sqlite3"
            store = SelfReportStore(db)
            created = store.record_self_report(
                subject_id="CREW-1",
                symptom="headache",
                severity_scale=4,
                notes="Mild headache after EVA prep",
                reported_at="2026-11-14T05:15:00+00:00",
            )
            self.assertEqual(created["source_kind"], "SELF_REPORT")
            self.assertEqual(created["scope"], "CREW")

            items = store.list_self_reports(subject_id="CREW-1")
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["symptom"], "headache")

            with closing(sqlite3.connect(db)) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
            self.assertIn("self_reports", tables)
            self.assertNotIn("observations", tables)

    def test_invalid_scope_severity_or_naive_timestamp_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "self_reports_bad.sqlite3"
            store = SelfReportStore(db)
            with self.assertRaises(ValueError):
                store.record_self_report(
                    subject_id="CREW-1",
                    symptom="headache",
                    severity_scale=11,
                    notes="out of range",
                    reported_at="2026-11-14T05:15:00+00:00",
                )
            with self.assertRaises(ValueError):
                store.record_self_report(
                    subject_id="CREW-1",
                    symptom="cabin_co2",
                    severity_scale=3,
                    notes="wrong metric",
                    reported_at="2026-11-14T05:15:00+00:00",
                )
            with self.assertRaises(ValueError):
                store.record_self_report(
                    subject_id="CREW-1",
                    symptom="fatigue",
                    severity_scale=3,
                    notes="naive time",
                    reported_at="2026-11-14T05:15:00",
                )


if __name__ == "__main__":
    unittest.main()
