"""Tests for Q-0145 condition-to-Atlas mapping."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.condition_atlas_mapping import map_condition_to_atlas


def test_condition_maps_to_atlas_organ_and_preserves_context() -> None:
    condition = {
        "condition_id": "COND-111111111111",
        "canonical_title": "Spaceflight Associated Neuro-ocular Syndrome",
        "body_systems": ["neuro-ocular", "nervous"],
        "verification_state": "READY",
    }
    res = map_condition_to_atlas(condition)
    assert res["status"] == "READY"
    assert res["primary_organ"]["organ_id"] == "eye_optic_nerve"
    assert len(res["organ_targets"]) == 2
    ctx = res["preserved_condition_context"]
    assert ctx["condition_id"] == "COND-111111111111"
    assert ctx["canonical_title"] == "Spaceflight Associated Neuro-ocular Syndrome"
    assert ctx["return_route"] == "/encyclopedia/condition/COND-111111111111"


def test_unmapped_body_system_returns_no_data_with_preserved_context() -> None:
    condition = {
        "condition_id": "COND-999999999999",
        "canonical_title": "Unmapped Condition",
        "body_systems": ["unknown_system"],
        "verification_state": "UNVERIFIED",
    }
    res = map_condition_to_atlas(condition)
    assert res["status"] == "NO_DATA"
    assert res["primary_organ"] is None
    assert res["preserved_condition_context"]["condition_id"] == "COND-999999999999"
