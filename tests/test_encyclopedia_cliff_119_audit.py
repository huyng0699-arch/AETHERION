"""Verification tests for Q-0136 encyclopedia CliFF 119 file and hash audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_JSON = ROOT / "knowledge" / "medical" / "cliff_119_audit.json"
AUDIT_MD = ROOT / "knowledge" / "medical" / "cliff_119_audit.md"
CLIFF_ORIGINAL_DIR = ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "original"
CLIFF_MANIFEST = ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "manifest.json"


def test_encyclopedia_cliff_119_audit_matches_filesystem() -> None:
    assert AUDIT_JSON.is_file(), f"Missing {AUDIT_JSON}"
    assert AUDIT_MD.is_file(), f"Missing {AUDIT_MD}"

    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    actual_files = (
        [p for p in CLIFF_ORIGINAL_DIR.iterdir() if p.is_file()]
        if CLIFF_ORIGINAL_DIR.is_dir()
        else []
    )
    verified_hashes = 0
    if CLIFF_MANIFEST.is_file():
        manifest = json.loads(CLIFF_MANIFEST.read_text(encoding="utf-8"))
        for item in manifest.get("items", []):
            fpath = ROOT / item.get("local_path", "")
            if fpath.is_file():
                digest = hashlib.sha256(fpath.read_bytes()).hexdigest()
                if digest == item.get("sha256"):
                    verified_hashes += 1

    assert data["expected_condition_count"] == 119
    assert data["fetched_original_files_count"] == len(actual_files)
    assert data["sha256_verified_count"] == verified_hashes
    expected_pct = round((verified_hashes / 119) * 100, 2)
    assert data["completeness_percent"] == expected_pct

    if verified_hashes < 119:
        assert data["verification_state"] in {"NO_DATA", "UNVERIFIED"}
        assert len(data["observed_gaps"]) >= 1
