"""Tests for Q-0141 encyclopedia keyword search."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.encyclopedia_search import search_encyclopedia


def _corpus() -> list[dict]:
    return [
        {
            "condition_id": "COND-111111111111",
            "canonical_title": "Spaceflight Associated Neuro-ocular Syndrome",
            "synonyms": ["SANS", "VIIP"],
            "body_systems": ["neuro-ocular", "nervous"],
            "symptoms": ["visual acuity shift", "optic disc edema"],
            "overview": "Neuro-ocular changes observed during long-duration microgravity.",
            "verification_state": "READY",
            "review_state": "APPROVED",
        },
        {
            "condition_id": "COND-222222222222",
            "canonical_title": "Post-flight Orthostatic Intolerance",
            "synonyms": ["orthostatic hypotension", "OI"],
            "body_systems": ["cardiovascular"],
            "symptoms": ["dizziness", "tachycardia"],
            "overview": "Cardiovascular deconditioning on return to gravity.",
            "verification_state": "READY",
            "review_state": "APPROVED",
        },
        {
            "condition_id": "COND-333333333333",
            "canonical_title": "Unverified Draft Entry",
            "synonyms": ["SANS"],
            "body_systems": ["neuro-ocular"],
            "symptoms": ["headache"],
            "overview": "Draft not yet verified.",
            "verification_state": "UNVERIFIED",
            "review_state": "DRAFT",
        },
    ]


def test_search_matches_title_and_synonyms_and_excludes_unverified() -> None:
    res = search_encyclopedia(_corpus(), query="SANS")
    assert res["status"] == "READY"
    assert res["total_matches"] == 1
    assert res["results"][0]["condition_id"] == "COND-111111111111"


def test_search_filters_by_body_system() -> None:
    res = search_encyclopedia(_corpus(), query="", body_system="cardiovascular")
    assert res["status"] == "READY"
    assert res["total_matches"] == 1
    assert res["results"][0]["condition_id"] == "COND-222222222222"


def test_empty_corpus_returns_no_data_honestly() -> None:
    res = search_encyclopedia([], query="SANS")
    assert res["status"] == "NO_DATA"
    assert res["total_matches"] == 0
    assert res["results"] == []
