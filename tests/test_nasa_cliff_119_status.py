"""Verification tests for Q-0108 CliFF 119 original-file status audit."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIFF_DIR = ROOT / "knowledge" / "nasa" / "cliff_119_2023"
AUDIT_JSON = CLIFF_DIR / "audit_status.json"
AUDIT_MD = CLIFF_DIR / "audit_status.md"


def test_cliff_119_audit_matches_actual_disk_state() -> None:
    assert AUDIT_JSON.is_file(), f"Missing {AUDIT_JSON}"
    assert AUDIT_MD.is_file(), f"Missing {AUDIT_MD}"

    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    original_dir = CLIFF_DIR / "original"
    manifest_path = CLIFF_DIR / "manifest.json"

    actual_originals = (
        [p for p in original_dir.iterdir() if p.is_file()]
        if original_dir.is_dir()
        else []
    )

    assert audit["expected_count"] == 119
    assert audit["original_dir_exists"] is original_dir.is_dir()
    assert audit["manifest_exists"] is manifest_path.is_file()
    assert audit["verified_original_files_count"] == len(actual_originals)
    assert audit["completeness_ratio"] == f"{len(actual_originals)}/119"

    records_dir = CLIFF_DIR / "records"
    actual_records = (
        sorted(p.stem for p in records_dir.glob("CLIFF-*.json"))
        if records_dir.is_dir()
        else []
    )
    assert audit["structured_json_records_count"] == len(actual_records)
    assert audit["structured_json_completeness"] == f"{len(actual_records)}/119"

    if len(actual_originals) < 119 or not manifest_path.is_file():
        assert audit["verification_state"] in {
            "NO_DATA",
            "UNVERIFIED",
            "PARTIAL_STRUCTURED_JSON_NO_PDF_ARCHIVE",
        }
        assert "0 / 119" in AUDIT_MD.read_text(encoding="utf-8") or "0/119" in AUDIT_MD.read_text(encoding="utf-8")
