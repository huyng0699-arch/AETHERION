"""Tests for Q-0147 offline licensed document packaging."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.offline_package_verifier import (
    open_offline_document,
    package_licensed_document,
)


def test_packaged_document_opens_disconnected_with_exact_metadata(tmp_path: Path) -> None:
    src = tmp_path / "source_doc.txt"
    src.write_text("NASA Open Science reference extract.", encoding="utf-8")
    bundle_dir = tmp_path / "offline_bundle"

    meta = {
        "doc_id": "DOC-OSDR-575",
        "title": "OSD-575 Study Metadata",
        "publisher": "NASA OSDR",
        "author": "NASA OSDR Contributors",
        "doi": "10.26030/mc5d-p710",
        "date": "2024-06-11",
        "source_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-575",
        "license_or_terms": "CC0-1.0 (open metadata)",
        "relicensed_under_apache_2_0": False,
    }
    package_licensed_document(src, bundle_dir, meta)

    # Remove original source to confirm disconnected bundle independence
    src.unlink()

    opened = open_offline_document(bundle_dir, "DOC-OSDR-575")
    assert opened["status"] == "READY"
    assert opened["offline_verified"] is True
    assert opened["content_bytes"] == b"NASA Open Science reference extract."
    assert opened["metadata"]["license_or_terms"] == "CC0-1.0 (open metadata)"
    assert opened["metadata"]["relicensed_under_apache_2_0"] is False
    assert opened["metadata"]["doi"] == "10.26030/mc5d-p710"


def test_tampered_offline_document_returns_error(tmp_path: Path) -> None:
    src = tmp_path / "doc.txt"
    src.write_text("Original text.", encoding="utf-8")
    bundle_dir = tmp_path / "bundle"
    package_licensed_document(
        src,
        bundle_dir,
        {
            "doc_id": "DOC-1",
            "title": "Test",
            "publisher": "NASA",
            "source_url": "https://www.nasa.gov/",
            "license_or_terms": "U.S. Government work",
            "relicensed_under_apache_2_0": False,
        },
    )
    (bundle_dir / "DOC-1.txt").write_text("Tampered text!", encoding="utf-8")
    opened = open_offline_document(bundle_dir, "DOC-1")
    assert opened["status"] == "ERROR"
    assert opened["content_bytes"] is None
