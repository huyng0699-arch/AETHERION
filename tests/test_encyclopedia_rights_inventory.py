"""Tests for Q-0139 scientific rights inventory for encyclopedia articles."""

import copy
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.scientific_rights_inventory import (
    can_display_in_encyclopedia,
    load_rights_inventory,
    validate_article_rights_record,
)


def test_inventory_loads_and_validates_all_records() -> None:
    data = load_rights_inventory()
    sources = data["sources"]
    assert len(sources) >= 4
    ids = {s["source_id"] for s in sources}
    assert "nasa-imm-cliff-119-2023" in ids
    assert "nasa-osdr-open-metadata" in ids
    for src in sources:
        assert src["relicensed_under_apache_2_0"] is False


def test_unimported_cliff_blocks_full_text_and_figures() -> None:
    data = load_rights_inventory()
    cliff = next(s for s in data["sources"] if s["source_id"] == "nasa-imm-cliff-119-2023")
    assert cliff["import_status"] == "NOT_IMPORTED"
    assert cliff["imported_file_count"] == 0
    assert can_display_in_encyclopedia(cliff, surface="abstract") is False
    assert can_display_in_encyclopedia(cliff, surface="full_text") is False
    assert can_display_in_encyclopedia(cliff, surface="figure") is False


def test_validator_rejects_relicensed_or_unimported_display_claims() -> None:
    data = load_rights_inventory()
    cliff = copy.deepcopy(next(s for s in data["sources"] if s["source_id"] == "nasa-imm-cliff-119-2023"))

    bad_relicense = copy.deepcopy(cliff)
    bad_relicense["relicensed_under_apache_2_0"] = True
    with pytest.raises(ValueError, match="Apache-2.0"):
        validate_article_rights_record(bad_relicense)

    bad_display = copy.deepcopy(cliff)
    bad_display["full_text_display_allowed"] = True
    with pytest.raises(ValueError, match="full-text"):
        validate_article_rights_record(bad_display)

    bad_dim = copy.deepcopy(cliff)
    bad_dim["figure_rights"] = "FREE_FOR_ALL"
    with pytest.raises(ValueError, match="figure_rights"):
        validate_article_rights_record(bad_dim)
