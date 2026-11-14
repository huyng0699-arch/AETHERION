"""Tests for Q-0144 symptom-to-condition crosswalk."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.symptom_crosswalk import crosswalk_symptoms_to_topics, normalize_symptom_term


def _entries() -> list[dict]:
    return [
        {
            "condition_id": "COND-111111111111",
            "canonical_title": "Spaceflight Associated Neuro-ocular Syndrome",
            "symptoms": ["visual acuity shift", "hyperopic shift"],
            "differential": ["idiopathic intracranial hypertension", "refractive error"],
            "uncertainties": ["Individual susceptibility varies."],
            "verification_state": "READY",
            "review_state": "APPROVED",
        },
        {
            "condition_id": "COND-222222222222",
            "canonical_title": "Unverified Draft",
            "symptoms": ["visual acuity shift"],
            "differential": [],
            "uncertainties": [],
            "verification_state": "UNVERIFIED",
            "review_state": "DRAFT",
        },
    ]


def test_crosswalk_links_aliases_without_automatic_diagnosis() -> None:
    assert normalize_symptom_term("Blurry Vision") == "visual acuity shift"
    res = crosswalk_symptoms_to_topics(["Blurry Vision"], _entries())
    assert res["status"] == "READY"
    assert res["is_diagnosis"] is False
    assert res["auto_diagnosed"] is False
    assert "not an automatic medical diagnosis" in res["clinical_disclaimer"].lower()
    assert len(res["possible_topics"]) == 1
    assert res["possible_topics"][0]["condition_id"] == "COND-111111111111"
    assert res["possible_topics"][0]["is_diagnosis"] is False


def test_crosswalk_returns_no_data_when_no_verified_match() -> None:
    res = crosswalk_symptoms_to_topics(["unknown symptom"], _entries())
    assert res["status"] == "NO_DATA"
    assert res["is_diagnosis"] is False
    assert res["possible_topics"] == []
