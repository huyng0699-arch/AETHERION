"""Tests for Q-0146 condition to Care documentation link."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.care_documentation_link import get_care_workflow_documentation
from knowledge.medical.condition_schema import normalize_condition_record

SHA = "c" * 64


def test_only_approved_ready_material_appears_in_care_workflow() -> None:
    approved = normalize_condition_record(
        canonical_title="SANS Reference",
        overview="Reviewed educational overview.",
        symptoms=["visual acuity shift"],
        differential=["refractive error"],
        uncertainties=["Individual thresholds vary."],
        evidence=[
            {
                "source_id": "nasa-hrp-sans",
                "source_url": "https://humanresearchroadmap.nasa.gov/",
                "source_publisher": "NASA HRP",
                "source_sha256": SHA,
                "is_live_telemetry": False,
            }
        ],
        source_publisher="NASA HRP",
        source_url="https://humanresearchroadmap.nasa.gov/",
        source_sha256=SHA,
        review_state="APPROVED",
        verification_state="READY",
    )
    draft = normalize_condition_record(
        canonical_title="Draft Condition",
        overview="Unreviewed draft.",
        symptoms=["headache"],
        differential=["dehydration"],
        uncertainties=["Not reviewed."],
        evidence=[],
        source_publisher="NASA HRP",
        source_url="https://humanresearchroadmap.nasa.gov/",
        source_sha256=SHA,
        review_state="DRAFT",
        verification_state="READY",
    )

    ok_res = get_care_workflow_documentation(approved["condition_id"], [approved, draft])
    assert ok_res["status"] == "READY"
    assert ok_res["workflow_role"] == "EDUCATIONAL_REFERENCE_ONLY"
    assert ok_res["replaces_clinician_judgment"] is False

    blocked_res = get_care_workflow_documentation(draft["condition_id"], [approved, draft])
    assert blocked_res["status"] == "NO_DATA"
    assert blocked_res["documentation"] is None
