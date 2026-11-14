"""Tests for Q-0140 normalized medical condition schema."""

import copy
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.condition_schema import (
    load_condition_schema,
    normalize_condition_record,
    validate_normalized_condition,
)

SAMPLE_SHA = "a" * 64


def _sample_record() -> dict:
    return normalize_condition_record(
        canonical_title="Spaceflight Associated Neuro-ocular Syndrome (SANS) Reference",
        overview="Reference summary of neuro-ocular structural changes observed in long-duration spaceflight.",
        symptoms=["visual acuity shift", "hyperopic shift"],
        differential=["idiopathic intracranial hypertension", "refractive error"],
        uncertainties=["Exact individual susceptibility thresholds remain under active NASA HRP investigation."],
        evidence=[
            {
                "source_id": "nasa-hrp-sans-ref",
                "source_url": "https://humanresearchroadmap.nasa.gov/",
                "source_publisher": "NASA HRP",
                "source_sha256": SAMPLE_SHA,
                "evidence_grade": "NASA_HRP_SUMMARY",
                "is_live_telemetry": False,
            }
        ],
        source_publisher="NASA HRP",
        source_url="https://humanresearchroadmap.nasa.gov/",
        source_sha256=SAMPLE_SHA,
        review_state="APPROVED",
        verification_state="READY",
    )


def test_schema_json_and_normalized_record_validate() -> None:
    schema = load_condition_schema()
    for required_key in ("overview", "symptoms", "differential", "uncertainties", "evidence", "review_state"):
        assert required_key in schema["required"]

    rec = _sample_record()
    assert rec["condition_id"].startswith("COND-")
    validate_normalized_condition(rec)


def test_validator_rejects_missing_uncertainties_or_unverified_approval() -> None:
    rec = _sample_record()

    missing_uncertainties = copy.deepcopy(rec)
    missing_uncertainties["uncertainties"] = []
    with pytest.raises(ValueError, match="uncertainties"):
        validate_normalized_condition(missing_uncertainties)

    unverified_approved = copy.deepcopy(rec)
    unverified_approved["verification_state"] = "UNVERIFIED"
    with pytest.raises(ValueError, match="READY"):
        validate_normalized_condition(unverified_approved)

    live_claim = copy.deepcopy(rec)
    live_claim["evidence"][0]["is_live_telemetry"] = True
    with pytest.raises(ValueError, match="is_live_telemetry"):
        validate_normalized_condition(live_claim)
