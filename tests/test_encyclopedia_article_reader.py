"""Tests for Q-0142 source-aware article reader."""

from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.article_reader import render_article_view
from knowledge.medical.scientific_rights_inventory import load_rights_inventory


def test_reader_exposes_author_doi_url_date_and_respects_unimported_gate() -> None:
    inv = load_rights_inventory()
    cliff_rights = next(s for s in inv["sources"] if s["source_id"] == "nasa-imm-cliff-119-2023")

    article = {
        "article_id": "ART-001",
        "title": "NASA IMM Clinical Finding Reference",
        "author": "NASA Integrated Medical Model Team",
        "doi": "10.26030/example-placeholder",
        "source_url": "https://www.nasa.gov/integrated-medical-model-documentation/",
        "date": "2023-01-01",
        "verification_status": "NO_DATA",
        "abstract": "Should not be shown when abstract_rights is UNVERIFIED",
        "full_text": "Should not be shown when NOT_IMPORTED",
    }
    view = render_article_view(article, cliff_rights)
    assert view["author"] == "NASA Integrated Medical Model Team"
    assert view["doi"] == "10.26030/example-placeholder"
    assert view["source_url"].startswith("https://")
    assert view["date"] == "2023-01-01"
    assert view["verification_status"] == "NO_DATA"
    assert view["is_live_telemetry"] is False
    assert view["abstract"] is None
    assert view["full_text"] is None
    assert view["figures_allowed"] is False


def test_reader_allows_abstract_for_verified_metadata_and_rejects_missing_provenance() -> None:
    inv = load_rights_inventory()
    osdr_rights = next(s for s in inv["sources"] if s["source_id"] == "nasa-osdr-open-metadata")

    article = {
        "article_id": "OSD-575",
        "title": "Inspiration4 Spaceflight Study Metadata",
        "author": "NASA OSDR Contributors",
        "doi": "10.26030/mc5d-p710",
        "source_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-575",
        "date": "2024-06-11",
        "verification_status": "READY",
        "abstract": "Open study metadata summary.",
        "full_text": "Should stay link-out only",
    }
    view = render_article_view(article, osdr_rights)
    assert view["abstract"] == "Open study metadata summary."
    assert view["full_text"] is None

    bad_article = dict(article)
    bad_article["author"] = ""
    with pytest.raises(ValueError, match="author"):
        render_article_view(bad_article, osdr_rights)
