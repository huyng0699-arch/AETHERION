"""Focused tests for Q-0446: typed symptom-to-differential-topic links with evidence, dates, and uncertainty."""

import unittest

from knowledge.medical.symptom_crosswalk import (
    build_reviewed_differential_link,
    crosswalk_symptoms_to_topics,
)


class SymptomDifferentialCrosswalkTests(unittest.TestCase):
    def test_typed_differential_link_preserves_provenance_and_non_equivalence(self):
        entry = build_reviewed_differential_link(
            condition_id="COND-001",
            canonical_title="Orthostatic Intolerance",
            symptoms=["dizziness", "tachycardia"],
            evidence_citations=[
                {"source_id": "NASA-HRP-OI", "url": "https://humanresearchroadmap.nasa.gov/"}
            ],
            author="Dr. Test Reviewer, MD",
            reviewed_at_utc="2026-11-14T09:00:00Z",
            uncertainties=["Non-specific symptom overlap with dehydration and arrhythmia."],
            differential=["Dehydration", "Vasovagal presyncope"],
            is_nasa_cliff_equivalent=False,
        )
        res = crosswalk_symptoms_to_topics(["lightheaded"], [entry])
        self.assertEqual(res["status"], "READY")
        self.assertFalse(res["is_diagnosis"])
        self.assertFalse(res["astra_cliff_equivalence_assumed"])
        topic = res["possible_topics"][0]
        self.assertEqual(topic["evidence_status"], "CITED")
        self.assertEqual(topic["author"], "Dr. Test Reviewer, MD")
        self.assertEqual(topic["reviewed_at_utc"], "2026-11-14T09:00:00Z")
        self.assertTrue(topic["uncertainty_recorded"])
        self.assertFalse(topic["is_nasa_cliff_equivalent"])

    def test_rejects_missing_evidence_or_uncertainty(self):
        with self.assertRaises(ValueError):
            build_reviewed_differential_link(
                condition_id="COND-002",
                canonical_title="Headache",
                symptoms=["headache"],
                evidence_citations=[],
                author="Dr. Reviewer",
                reviewed_at_utc="2026-11-14T09:00:00Z",
                uncertainties=["Uncertain etiology"],
            )


if __name__ == "__main__":
    unittest.main()
