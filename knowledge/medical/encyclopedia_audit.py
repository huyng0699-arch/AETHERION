"""Final encyclopedia package audit for uncited medical assertions and restricted assets (Q-0150)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knowledge.medical.scientific_rights_inventory import (
    can_display_in_encyclopedia,
    load_rights_inventory,
)


def audit_encyclopedia_package(
    *,
    medical_dir: Path | None = None,
    condition_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Audit encyclopedia artifacts and condition records for uncited claims or restricted assets."""
    root = medical_dir or Path(__file__).resolve().parent
    rights = load_rights_inventory(root / "scientific_rights_inventory.json")
    identifiers = json.loads((root / "condition_identifiers.json").read_text(encoding="utf-8"))
    cliff_audit = json.loads((root / "cliff_119_audit.json").read_text(encoding="utf-8"))

    violations: list[str] = []

    for src in rights["sources"]:
        if src.get("relicensed_under_apache_2_0") is not False:
            violations.append(f"Source {src['source_id']} claims Apache-2.0 relicensing")
        if src["import_status"] in {"NOT_IMPORTED", "NO_DATA", "UNVERIFIED"}:
            if can_display_in_encyclopedia(src, surface="full_text") or can_display_in_encyclopedia(src, surface="figure"):
                violations.append(f"Unimported source {src['source_id']} allows restricted display")

    records = condition_records if condition_records is not None else identifiers.get("records", [])
    for rec in records:
        if not rec.get("evidence"):
            violations.append(f"Uncited condition record: {rec.get('condition_id', '<unknown>')}")
        if rec.get("origin_type") in {"AUTHOR_GENERATED", "AI_ASSISTED"} and rec.get("label_as_nasa") is True:
            violations.append(f"Author-generated record spoofed as NASA: {rec.get('condition_id', '<unknown>')}")

    return {
        "schema_version": "1.0.0",
        "audit_passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
        "cliff_119_imported_pdfs": cliff_audit.get("local_pdf_count", 0),
        "cliff_119_expected_pdfs": cliff_audit.get("expected_count", 119),
        "accepted_condition_records": len(records),
        "rights_sources_audited": len(rights["sources"]),
    }
