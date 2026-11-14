"""Verification tests for Q-0138 verifiable condition identifiers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "knowledge" / "medical"))

from condition_identifiers import make_condition_id, validate_condition_record  # noqa: E402

REGISTRY_JSON = ROOT / "knowledge" / "medical" / "condition_identifiers.json"


def test_condition_id_is_deterministic_and_verifiable() -> None:
    sha = "a" * 64
    cid1 = make_condition_id(
        source_publisher="NASA",
        source_url="https://www.nasa.gov/integrated-medical-model-documentation/",
        canonical_title="Spaceflight Associated Neuro-ocular Syndrome (SANS)",
        source_sha256=sha,
    )
    cid2 = make_condition_id(
        source_publisher="NASA",
        source_url="https://www.nasa.gov/integrated-medical-model-documentation/",
        canonical_title="Spaceflight  Associated  Neuro-ocular Syndrome (SANS)",
        source_sha256=sha,
    )
    assert cid1 == cid2
    assert cid1.startswith("COND-")
    assert len(cid1) == 17

    validate_condition_record({
        "condition_id": cid1,
        "canonical_title": "Spaceflight Associated Neuro-ocular Syndrome (SANS)",
        "source_publisher": "NASA",
        "source_url": "https://www.nasa.gov/integrated-medical-model-documentation/",
        "source_sha256": sha,
        "verification_state": "READY",
    })


def test_condition_id_rejects_unverified_or_tampered_records() -> None:
    with pytest.raises(ValueError):
        validate_condition_record({
            "condition_id": "COND-000000000000",
            "canonical_title": "Fake Condition",
            "source_publisher": "NASA",
            "source_url": "https://www.nasa.gov/example",
            "source_sha256": "not-a-sha256",
            "verification_state": "READY",
        })


def test_condition_registry_json_reflects_zero_accepted_until_sources_exist() -> None:
    data = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    assert data["accepted_conditions_count"] == len(data["accepted_conditions"])
    if data["accepted_conditions_count"] == 0:
        assert data["verification_state"] == "NO_DATA"
