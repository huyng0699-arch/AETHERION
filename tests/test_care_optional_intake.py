"""Q-0094: isolated engineering tests; no genuine patient observations."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / "apps/server/src/aetherion_server/care/symptom_intake.py"
spec = importlib.util.spec_from_file_location("aetherion_optional_intake_test", MODULE)
intake = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = intake
spec.loader.exec_module(intake)

def report(**changes):
    params = {
        "subject_id": "ENGINEERING-ONLY",
        "actor_id": "TEST-USER",
        "answer": "YES",
        "note": "SYNTHETIC TEST, not medical data",
        "impact": "UNKNOWN",
        "explicit_consent": True,
        "reported_at": datetime(2026, 11, 14, 8, 0, tzinfo=timezone.utc),
    }
    params.update(changes)
    return intake.prepare_optional_checkin(**params)


class OptionalIntakeTests(unittest.TestCase):
    def test_skip_returns_none_without_requiring_identity_or_consent(self):
        # No phantom 'healthy' observation or hidden storage on skip.
        self.assertIsNone(intake.prepare_optional_checkin(
            subject_id=None, actor_id=None, answer="SKIP",
            note="confidential and deliberately ignored", explicit_consent=False
        ))

    def test_yes_is_explicitly_self_reported_and_unsaved(self):
        data = report()
        self.assertEqual(data["kind"], "USER_REPORTED_CONCERN")
        self.assertEqual(data["quality"], "UNVERIFIED")
        self.assertEqual(data["verification_state"], "SELF_REPORTED")
        self.assertEqual(data["persistence_state"], "NOT_SAVED")
        self.assertIsNone(data["clinical_assessment"])
        self.assertEqual(data["reported_at"], "2026-11-14T08:00:00+00:00")

    def test_no_is_never_clinically_certified_healthy(self):
        data = report(answer="NO", note="")
        self.assertEqual(data["kind"], "VOLUNTARY_USER_CHECKIN")
        self.assertIsNone(data["clinical_assessment"])
        self.assertEqual(data["quality"], "UNVERIFIED")

    def test_requires_explicit_consent(self):
        with self.assertRaises(ValueError):
            report(explicit_consent=False)

    def test_rejects_invalid_report_and_impact(self):
        for changes in ({"answer": "DIAGNOSED"}, {"impact": "EMERGENCY_DIAGNOSIS"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                report(**changes)

    def test_rejects_identifiers_and_control_characters(self):
        for changes in (
            {"subject_id": ""}, {"actor_id": "\n"}, {"note": "\x00poison"},
            {"note": "x" * 2001}, {"subject_id": "a" * 81},
        ):
            with self.subTest(changes=list(changes)), self.assertRaises(ValueError):
                report(**changes)

    def test_rejects_naive_report_time(self):
        with self.assertRaises(ValueError):
            report(reported_at=datetime(2026, 11, 14, 8, 0))

    def test_keeps_separation_of_missing_and_unknown(self):
        self.assertIsNone(report(answer="SKIP"))
        self.assertEqual(report(answer="UNKNOWN")["answer"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
