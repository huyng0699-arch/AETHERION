"""Verification tests for Q-0137 CliFF documents vs 119 conditions mapping."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_JSON = ROOT / "knowledge" / "medical" / "cliff_document_vs_condition_map.json"
MAP_MD = ROOT / "knowledge" / "medical" / "cliff_document_vs_condition_map.md"
AUDIT_JSON = ROOT / "knowledge" / "medical" / "cliff_119_audit.json"


def test_cliff_doc_vs_condition_map_separates_documents_and_catalog() -> None:
    assert MAP_JSON.is_file(), f"Missing {MAP_JSON}"
    assert MAP_MD.is_file(), f"Missing {MAP_MD}"

    data = json.loads(MAP_JSON.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))

    assert data["source_documents"]["expected_documents"] == 119
    assert data["source_documents"]["verified_local_documents"] == audit["sha256_verified_count"]
    assert data["condition_catalog"]["populated_conditions_count"] == len(data["entries"])
    assert data["mapping_rules"]["one_to_one_assumed"] is False
    assert data["mapping_rules"]["require_verified_source_sha256_for_ready"] is True
    assert data["mapping_rules"]["legacy_astra_count_accepted"] is False

    # Negative/safety check: when 0 local documents are verified, no entry can claim READY.
    if data["source_documents"]["verified_local_documents"] == 0:
        assert data["source_documents"]["verification_state"] == "NO_DATA"
        assert data["condition_catalog"]["verification_state"] == "NO_DATA"
        for entry in data["entries"]:
            assert entry.get("verification_state") != "READY"
