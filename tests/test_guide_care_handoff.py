"""Tests for Q-0161 Guide to care workflow handoff."""

from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "server" / "src"))

from aetherion_server.guide.care_handoff import build_guide_to_care_handoff
from aetherion_server.guide.search import load_guide_entries


def test_guide_handoff_preserves_subject_and_source_to_canonical_episode() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    entries = load_guide_entries(repo_root=repo_root)
    assert entries
    handoff = build_guide_to_care_handoff(
        subject_id="crew-01",
        scope="mission",
        episode_id="EP-2026-001",
        selected_source=entries[0],
        current_stage="GATHER",
    )
    assert handoff["canonical_episode_id"] == "EP-2026-001"
    assert handoff["subject_id"] == "crew-01"
    assert handoff["scope"] == "mission"
    assert handoff["care_flow"] == ["GATHER", "EVALUATE", "ACT", "RECHECK"]
    assert handoff["human_agency_required"] is True
    assert handoff["auto_diagnosed"] is False
    assert handoff["attached_source"]["source_url"] == entries[0]["source_url"]
    assert handoff["attached_source"]["is_live_telemetry"] is False


def test_handoff_rejects_missing_subject_or_live_telemetry_spoof() -> None:
    with pytest.raises(ValueError, match="subject_id"):
        build_guide_to_care_handoff(
            subject_id="",
            scope="personal",
            episode_id="EP-1",
            selected_source={"source_url": "https://www.nasa.gov/"},
        )
    with pytest.raises(ValueError, match="is_live_telemetry"):
        build_guide_to_care_handoff(
            subject_id="crew-01",
            scope="personal",
            episode_id="EP-1",
            selected_source={"source_url": "https://www.nasa.gov/", "is_live_telemetry": True},
        )
