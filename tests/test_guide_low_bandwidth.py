"""Tests for Q-0160 keyboard and low-bandwidth Guide reading."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "server" / "src"))

from aetherion_server.guide.low_bandwidth_reader import build_low_bandwidth_article_payload
from aetherion_server.guide.search import load_guide_entries


def test_real_guide_entries_load_in_low_bandwidth_keyboard_mode() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    entries = load_guide_entries(repo_root=repo_root)
    assert len(entries) > 0
    payload = build_low_bandwidth_article_payload(entries[0], max_bytes=2048, include_images=False)
    assert payload["low_bandwidth_mode"] is True
    assert payload["payload_bytes"] <= 2048
    assert payload["source_url"].startswith("https://")
    assert payload["is_live_telemetry"] is False
    assert payload["keyboard_navigation"]["shortcuts"]["focus_search"] == "/"
    assert "source_citation" in payload["keyboard_navigation"]["tab_order"]


def test_long_article_truncates_summary_without_dropping_provenance() -> None:
    long_entry = {
        "entry_id": "TEST-LONG",
        "title": "Long Spaceflight Article",
        "summary": "A" * 3000,
        "publisher": "NASA",
        "source_url": "https://www.nasa.gov/hrp/",
        "verification_status": "READY",
        "is_live_telemetry": False,
        "media": [{"alt_text": "Optic disc diagram", "bytes": b"1234"}],
    }
    payload = build_low_bandwidth_article_payload(long_entry, max_bytes=1024, include_images=False)
    assert payload["truncated"] is True
    assert payload["images_omitted"] is True
    assert payload["payload_bytes"] <= 1024
    assert payload["source_url"] == "https://www.nasa.gov/hrp/"
