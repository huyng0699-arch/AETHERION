"""Q-0095 source-quality tests only. No patient data or diagnostic thresholds."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / "apps/server/src/aetherion_server/care/provenance_evaluation.py"
spec = importlib.util.spec_from_file_location("aetherion_quality_eval_test", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=timezone.utc)


def sample(**changes):
    record = {
        "observation_uid": "obs-test-1",
        "subject_id": "ENGINEERING-1",
        "metric": "heart_rate",
        "value": 70,
        "unit": "beats/min",
        "scope": "CREW",
        "quality": "READY",
        "verification_state": "SELF_REPORTED",
        "source_id": "manual_test",
        "observed_at": "2026-11-14T08:55:00Z",
        "received_at": "2026-11-14T08:55:01Z",
    }
    record.update(changes)
    return record


class ProvenanceEvaluationTests(unittest.TestCase):
    def assess(self, rows):
        return mod.evaluate_provenance("ENGINEERING-1", rows, now=NOW)

    def test_empty_source_is_no_data_not_health(self):
        s = self.assess([])
        self.assertEqual(s.state, "NO_DATA")
        self.assertEqual(s.clinical_status, "NOT_ASSESSED")

    def test_self_report_is_unverified_despite_ready_quality(self):
        s = self.assess([sample()])
        self.assertEqual(s.state, "UNVERIFIED")
        self.assertTrue(s.requires_human_review)

    def test_verified_provenance_is_not_diagnosis(self):
        s = self.assess([sample(verification_state="VERIFIED")])
        self.assertEqual(s.state, "PROVENANCE_PRESENT")
        self.assertEqual(s.clinical_status, "NOT_ASSESSED")

    def test_stale_and_future_measurements_distinguished(self):
        self.assertEqual(self.assess([sample(observed_at="2026-11-12T09:00:00Z")]).state, "STALE")
        self.assertEqual(self.assess([sample(observed_at="2026-11-16T09:00:00Z")]).state, "UNVERIFIED")

    def test_wrong_subject_never_exposes_any_finding(self):
        s = self.assess([sample(), sample(subject_id="OTHER-1")])
        self.assertEqual((s.state, s.findings, s.reviewed_observations), ("DENIED", (), 0))

    def test_missing_provenance_and_nonfinite_values_error(self):
        for changes in (
            {"source_id": ""},
            {"value": float("nan")},
            {"observed_at": "2026-11-14T08:55:00"},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(self.assess([sample(**changes)]).state, "ERROR")

    def test_duplicate_record_id_rejected(self):
        self.assertEqual(self.assess([sample(), sample()]).state, "ERROR")

    def test_explicit_offline_status_kept_separate_from_medical_health(self):
        s = self.assess([sample(quality="OFFLINE")])
        self.assertEqual(s.state, "OFFLINE")
        self.assertEqual(s.clinical_status, "NOT_ASSESSED")


if __name__ == "__main__":
    unittest.main()
