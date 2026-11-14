"""Tests for Q-0165 Guide offline end-to-end acceptance."""

from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "server" / "src"))

from aetherion_server.guide.offline_acceptance import run_offline_guide_flow


def test_offline_guide_search_and_citations_work_with_cloud_ai_disabled() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    res = run_offline_guide_flow(
        query="radiation",
        user_id="crew-01",
        scope="mission",
        repo_root=repo_root,
        cloud_ai_enabled=False,
    )
    assert res["status"] == "READY"
    assert res["cloud_ai_used"] is False
    assert res["offline_verified"] is True
    assert res["matched_count"] >= 1
    assert all(c["source_url"].startswith("https://") for c in res["citations"])
    assert all(c["is_live_telemetry"] is False for c in res["citations"])
    assert res["hazard_route"]["status"] == "ROUTED"
    assert res["reader_payload"]["low_bandwidth_mode"] is True
    assert res["care_handoff"]["canonical_episode_id"] == "EP-OFFLINE-001"
    assert res["atlas_link"]["organ_id"] == "heart_vasculature"


def test_offline_guide_unmatched_query_returns_no_data_without_hallucination() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    res = run_offline_guide_flow(
        query="nonexistent_xyz_topic",
        user_id="crew-01",
        scope="personal",
        repo_root=repo_root,
        cloud_ai_enabled=False,
    )
    assert res["status"] == "NO_DATA"
    assert res["citations"] == []
    assert res["cloud_ai_used"] is False

    with pytest.raises(ValueError, match="cloud_ai_enabled=False"):
        run_offline_guide_flow(
            query="radiation",
            user_id="crew-01",
            scope="mission",
            repo_root=repo_root,
            cloud_ai_enabled=True,
        )
