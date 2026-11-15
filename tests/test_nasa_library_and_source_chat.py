"""Regression checks for NASA's 119 condition names and archive separation."""
from pathlib import Path
import sys

from fastapi import HTTPException
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "server" / "src"))
from aetherion_server import knowledge_catalog
from aetherion_server.assistant_chat import _source_context


def test_nasa_roster_preserves_real_ids_and_sources():
    result = knowledge_catalog.conditions()
    assert result["total"] == result["matched"] == len(result["items"]) == 119
    assert len({item["condition_id"] for item in result["items"]}) == 119
    assert all(item["source_page"] > 100 for item in result["items"])
    assert all("#page=" in item["source_url"] for item in result["items"])
    by_id = {item["condition_id"]: item for item in result["items"]}
    assert by_id["ICL119"]["title"] == "Venous Thromboembolism"
    assert by_id["ICL119"]["article_id"] == "CLIFF-017"
    assert by_id["ICL36A"]["article_id"] == "CLIFF-098"
    assert by_id["ICL36B"]["article_id"] == "CLIFF-097"
    for removed in ("ICL27", "ICL36", "ICL69", "ICL79", "ICL120", "ICL121"):
        assert removed not in by_id
    assert knowledge_catalog.conditions("thromboembolism")["items"][0]["condition_id"] == "ICL119"


def test_document_archive_counts_do_not_duplicate_vte():
    state = knowledge_catalog.status()
    assert state["json_articles"] == state["full_text_records"] == 118
    assert state["metadata_only_records"] == 0
    assert state["missing_slots"] == ["CLIFF-119"]
    assert knowledge_catalog.article("CLIFF-119") is None
    assert knowledge_catalog.article("CLIFF-017")["sections"]


def test_source_chat_attaches_provenance_and_rejects_unavailable_record():
    context, sources = _source_context("CLIFF-017")
    assert "ATTACHED RECORD EXCERPT:" in context
    assert sources[0]["independent_pdf_verification"] is False
    with pytest.raises(HTTPException) as error:
        _source_context("CLIFF-119")
    assert error.value.status_code == 404
