"""Tests for Q-0162 Guide to Body Atlas link."""

from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "server" / "src"))

from aetherion_server.guide.atlas_link import build_guide_to_atlas_link


def test_atlas_link_preserves_user_and_science_topic() -> None:
    link = build_guide_to_atlas_link(
        user_id="crew-01",
        scope="mission",
        science_topic_id="space_radiation",
        science_topic_title="Space Radiation & Endothelium",
        organ_id="heart_vasculature",
        return_route="/guide/hazards/space_radiation",
    )
    assert link["target_route"] == "/atlas/organ/heart_vasculature"
    assert link["organ_id"] == "heart_vasculature"
    ctx = link["preserved_context"]
    assert ctx["user_id"] == "crew-01"
    assert ctx["scope"] == "mission"
    assert ctx["science_topic_id"] == "space_radiation"
    assert ctx["science_topic_title"] == "Space Radiation & Endothelium"
    assert ctx["return_route"] == "/guide/hazards/space_radiation"
    assert link["is_live_telemetry"] is False


def test_atlas_link_rejects_missing_user_or_topic() -> None:
    with pytest.raises(ValueError, match="user_id"):
        build_guide_to_atlas_link(
            user_id="",
            scope="personal",
            science_topic_id="topic-1",
            science_topic_title="Title",
            organ_id="eye_optic_nerve",
        )
    with pytest.raises(ValueError, match="science_topic_id"):
        build_guide_to_atlas_link(
            user_id="crew-01",
            scope="personal",
            science_topic_id="",
            science_topic_title="Title",
            organ_id="eye_optic_nerve",
        )
