"""Normalized medical condition schema and validator (Q-0140)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knowledge.medical.condition_identifiers import make_condition_id, validate_condition_record

VALID_REVIEW_STATES = {"DRAFT", "UNDER_REVIEW", "APPROVED", "NEEDS_REVISION", "UNVERIFIED"}
REQUIRED_FIELDS = (
    "schema_version",
    "condition_id",
    "canonical_title",
    "overview",
    "symptoms",
    "differential",
    "uncertainties",
    "evidence",
    "review_state",
    "verification_state",
)


def load_condition_schema(path: Path | None = None) -> dict[str, Any]:
    """Load the canonical condition JSON schema."""
    target = path or Path(__file__).with_name("condition_schema.json")
    return json.loads(target.read_text(encoding="utf-8"))


def validate_normalized_condition(record: dict[str, Any]) -> None:
    """Validate that a condition record captures overview, symptoms, differential, uncertainties, evidence, and review state."""
    for field in REQUIRED_FIELDS:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")

    if record["schema_version"] != "1.0.0":
        raise ValueError(f"Unsupported schema_version: {record['schema_version']!r}")

    for text_field in ("canonical_title", "overview"):
        val = record[text_field]
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"Field '{text_field}' must be a non-empty string")

    for list_field in ("symptoms", "differential", "uncertainties"):
        items = record[list_field]
        if not isinstance(items, list) or not items or not all(isinstance(x, str) and x.strip() for x in items):
            raise ValueError(f"Field '{list_field}' must be a non-empty list of non-empty strings")

    evidence = record["evidence"]
    if not isinstance(evidence, list):
        raise ValueError("Field 'evidence' must be a list")
    for item in evidence:
        if not isinstance(item, dict):
            raise ValueError("Each evidence entry must be a dict")
        if item.get("is_live_telemetry") is not False:
            raise ValueError("Reference condition evidence must have is_live_telemetry=False")
        if not str(item.get("source_url", "")).startswith("https://"):
            raise ValueError("Evidence source_url must use https://")

    review_state = record["review_state"]
    if review_state not in VALID_REVIEW_STATES:
        raise ValueError(f"Invalid review_state: {review_state!r}")

    validate_condition_record(record)

    if review_state == "APPROVED":
        if record["verification_state"] != "READY":
            raise ValueError("Cannot mark review_state='APPROVED' when verification_state != 'READY'")
        if not evidence:
            raise ValueError("Cannot mark review_state='APPROVED' without at least one verified evidence item")


def normalize_condition_record(
    *,
    canonical_title: str,
    overview: str,
    symptoms: list[str],
    differential: list[str],
    uncertainties: list[str],
    evidence: list[dict[str, Any]],
    source_publisher: str,
    source_url: str,
    source_sha256: str,
    review_state: str = "DRAFT",
    verification_state: str = "READY",
) -> dict[str, Any]:
    """Construct and validate a normalized condition record bound to source provenance."""
    condition_id = make_condition_id(
        source_publisher=source_publisher,
        source_url=source_url,
        canonical_title=canonical_title,
        source_sha256=source_sha256,
    )
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "condition_id": condition_id,
        "canonical_title": canonical_title.strip(),
        "overview": overview.strip(),
        "symptoms": [s.strip() for s in symptoms],
        "differential": [d.strip() for d in differential],
        "uncertainties": [u.strip() for u in uncertainties],
        "evidence": evidence,
        "review_state": review_state,
        "verification_state": verification_state,
        "source_publisher": source_publisher,
        "source_url": source_url,
        "source_sha256": source_sha256,
    }
    validate_normalized_condition(record)
    return record
