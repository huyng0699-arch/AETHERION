"""Tests for Q-0150 full encyclopedia claim and asset audit."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.encyclopedia_audit import audit_encyclopedia_package


def test_live_encyclopedia_package_has_zero_violations() -> None:
    report = audit_encyclopedia_package()
    assert report["audit_passed"] is True
    assert report["violation_count"] == 0
    assert report["violations"] == []
    assert report["cliff_119_imported_pdfs"] == 0
    assert report["rights_sources_audited"] >= 4

    saved = json.loads(
        (Path(__file__).resolve().parents[1] / "knowledge/medical/encyclopedia_audit_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert saved["audit_passed"] == report["audit_passed"]
    assert saved["violation_count"] == report["violation_count"]


def test_audit_catches_uncited_medical_assertion_or_spoofed_nasa_label() -> None:
    bad_records = [
        {"condition_id": "COND-000000000001", "evidence": []},
        {"condition_id": "COND-000000000002", "evidence": [{"source_id": "x"}], "origin_type": "AUTHOR_GENERATED", "label_as_nasa": True},
    ]
    report = audit_encyclopedia_package(condition_records=bad_records)
    assert report["audit_passed"] is False
    assert report["violation_count"] == 2
