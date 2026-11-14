"""Q-0464 safety checks for Personal Today provenance. Synthetic engineering-only data."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = (Path(__file__).resolve().parents[1]
          / "apps/desktop/src/aetherion_desktop/features/personal/today_dashboard.py")
spec = importlib.util.spec_from_file_location("personal_provenance_q0464", MODULE)
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)

NOW = datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc)


def observation(**updates):
    item = {
        "subject_id": "SYNTHETIC-A",
        "metric": "heart_rate",
        "value": 72.0,
        "unit": "beats/min",
        "scope": "PERSONAL",
        "source_id": "engineering_measurement_example",
        "quality": "READY",
        "verification_state": "VERIFIED",
        "observed_at": "2026-11-14T09:55:00Z",
        "received_at": "2026-11-14T09:55:02Z",
    }
    item.update(updates)
    return item


def snapshot(records, **fields):
    return model.build_personal_today_snapshot(
        {"subject_id": "SYNTHETIC-A", "observations": records, **fields},
        "SYNTHETIC-A", now=NOW,
    )


class PersonalPrivacyTests(unittest.TestCase):
    def test_only_fixture_is_not_a_personal_health_measurement(self):
        result = snapshot([observation(verification_state="TEST_FIXTURE")])
        self.assertEqual(result.state, "NO_DATA")
        self.assertEqual(result.cards, ())
        self.assertFalse(result.intake_required)

    def test_research_records_never_become_personal_vitals(self):
        records = [
            observation(source_id="nasa_osdr:OSD-575"),
            observation(source_id="research:historical_cohort"),
            observation(scope="engineering_test"),
        ]
        result = snapshot(records)
        self.assertEqual((result.state, len(result.cards)), ("NO_DATA", 0))

    def test_real_record_retains_actual_source_and_quality(self):
        result = snapshot([
            observation(source_id="research:archive"),
            observation(verification_state="SELF_REPORTED", source_id="manual_entry"),
        ])
        self.assertEqual(result.state, "UNVERIFIED")
        self.assertEqual(len(result.cards), 1)
        self.assertEqual(result.cards[0].source_id, "manual_entry")
        self.assertEqual(result.cards[0].quality, "UNVERIFIED")

    def test_wrong_subject_is_rejected_before_fixture_filter(self):
        result = snapshot([
            observation(),
            observation(subject_id="SYNTHETIC-OTHER", verification_state="TEST_FIXTURE"),
        ])
        self.assertEqual(result.state, "ERROR")
        self.assertEqual(result.cards, ())

    def test_boolean_or_arbitrary_numeric_text_rejected(self):
        for value in (True, "72", float("nan"), float("inf")):
            with self.subTest(value=value):
                result = snapshot([observation(value=value)])
                self.assertEqual((result.state, result.cards), ("ERROR", ()))

    def test_bad_received_at_fails_closed(self):
        for time in ("2026-11-14T09:54:00Z", "2026-11-14T09:55:01", "not-a-time"):
            with self.subTest(time=time):
                result = snapshot([observation(received_at=time)])
                self.assertEqual((result.state, result.cards), ("ERROR", ()))

    def test_denied_or_offline_mixed_with_values_is_not_displayed(self):
        for quality in ("DENIED", "OFFLINE", "ERROR"):
            with self.subTest(quality=quality):
                result = snapshot([observation(quality=quality)])
                self.assertEqual((result.state, result.cards), ("ERROR", ()))

    def test_pagination_flag_requires_a_boolean(self):
        result = snapshot([observation()], has_more="yes")
        self.assertEqual((result.state, result.cards), ("ERROR", ()))


if __name__ == "__main__":
    unittest.main()
