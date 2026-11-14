"""Verification tests for Q-0109 NASA OSDR dataset selection."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "knowledge" / "nasa" / "osdr_datasets.json"
DOC_PATH = ROOT / "knowledge" / "nasa" / "osdr_datasets.md"

REQUIRED_FIELDS = {
    "osd_id",
    "version",
    "title",
    "url",
    "publisher",
    "license_or_terms",
    "species",
    "mission_or_platform",
    "hazard_domains",
    "assay_types",
    "measurement_units",
    "is_live_telemetry",
    "verification_status",
    "limitations",
}


def test_osdr_catalog_exists_and_is_valid_json() -> None:
    assert CATALOG_PATH.is_file(), f"Missing {CATALOG_PATH}"
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert data["source_repository"]["is_live_telemetry"] is False
    assert isinstance(data["datasets"], list)
    assert len(data["datasets"]) >= 5


def test_osdr_datasets_have_provenance_species_assays_and_units() -> None:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    seen_ids: set[str] = set()
    for ds in data["datasets"]:
        missing = REQUIRED_FIELDS - set(ds.keys())
        assert not missing, f"{ds.get('osd_id')} missing fields: {missing}"
        osd_id = ds["osd_id"]
        assert re.fullmatch(r"OSD-\d+", osd_id), f"Invalid OSD ID: {osd_id}"
        assert osd_id not in seen_ids, f"Duplicate OSD ID: {osd_id}"
        seen_ids.add(osd_id)
        assert ds["url"] == f"https://osdr.nasa.gov/bio/repo/data/studies/{osd_id}"
        assert ds["is_live_telemetry"] is False, "OSDR research is never live telemetry"
        assert len(ds["species"]) >= 1
        assert all(sp.get("scientific_name") for sp in ds["species"])
        assert len(ds["assay_types"]) >= 1
        assert len(ds["measurement_units"]) >= 1
        assert ds["limitations"].strip() != ""


def test_osdr_markdown_references_all_selected_datasets() -> None:
    assert DOC_PATH.is_file(), f"Missing {DOC_PATH}"
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    for ds in data["datasets"]:
        assert ds["osd_id"] in doc_text, f"{ds['osd_id']} missing from osdr_datasets.md"
