#!/usr/bin/env python3
"""Build the OFFLINE CliFF reader database from existing, attributed records.

This is a packaging step, not a NASA download, PDF verification or medical
approval. Never inserts placeholders for missing originals. Individual invalid
records are rejected and listed in the manifest; a partially populated
database is explicitly labelled PARTIAL.

Example:
    python scripts/build_offline_medical_library.py --db build/science/AETHERION_NASA_CLIFF_119.sqlite --report build/science/medical-manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge.nasa.cliff_119_2023 import importer, library_schema  # noqa: E402

RECORDS = ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "records"
EXPECTED = frozenset(f"CLIFF-{i:03}" for i in range(1, 120))


def build(db_path: Path, manifest_path: Path) -> dict:
    if not RECORDS.is_dir():
        raise FileNotFoundError("Original source record directory is missing")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(db_path.name + ".building")
    if tmp.exists():
        tmp.unlink()
    succeeded: list[str] = []
    rejected: dict[str, str] = {}
    record_hashes: dict[str, str] = {}
    try:
        library_schema.create_file(tmp)
        files = sorted(RECORDS.glob("CLIFF-???.json"))
        for path in files:
            key = path.stem
            try:
                raw = path.read_bytes()
                payload = json.loads(raw.decode("utf-8"))
                if (not isinstance(payload, dict) or payload.get("article_id") != key
                        or key not in EXPECTED):
                    raise ValueError("Article ID does not match an expected original slot")
                importer.ingest_article_record(
                    tmp, payload, assets_root=ROOT, verify_audit=False
                )
                succeeded.append(key)
                record_hashes[key] = hashlib.sha256(raw).hexdigest()
            except (OSError, UnicodeError, ValueError, KeyError, TypeError,
                    IndexError, RuntimeError, sqlite3.Error) as exc:
                # Never repair or fabricate missing source text, image bytes,
                # hashes, citations or rights to satisfy the package count.
                rejected[key] = f"{type(exc).__name__}: {str(exc)[:220]}"

        connection = library_schema.connect(tmp, read_only=True)
        try:
            audit = library_schema.audit(connection, verify_media=True)
        finally:
            # sqlite3 connection context managers do NOT close the handle.
            # Windows refuses an atomic rename while the DB is open.
            connection.close()
        if (audit["integrity"] != "ok" or audit["foreign_key_errors"] != 0
                or audit["media_hash_mismatches"]
                or audit["articles"] != len(succeeded)):
            raise RuntimeError("Scientific library integrity audit failed")
        if not succeeded:
            raise RuntimeError("No source-backed CliFF article was accepted")

        db_sha = hashlib.sha256(tmp.read_bytes()).hexdigest()
        absent = sorted(EXPECTED - set(succeeded))
        is_complete = bool(audit["library_complete"] and not rejected and not absent)
        result = {
            "library_kind": "NASA_CLIFF_119_MEDICAL_REFERENCE",
            "import_status": "COMPLETE" if is_complete else "PARTIAL",
            "expected_articles": 119,
            "imported_articles": len(succeeded),
            "missing_or_rejected_slots": absent,
            "rejected_records": rejected,
            "record_sha256": record_hashes,
            "sqlite_sha256": db_sha,
            "sqlite_filename": db_path.name,
            "audit": audit,
            "source_form": "EXISTING_STRUCTURED_JSON_NOT_ORIGINAL_PDF_ARCHIVE",
            "original_pdf_archive_verified": False,
            "independent_clinical_review": False,
            "note": (
                "Source metadata and source-language text are preserved as imported. "
                "The importer cannot independently certify original NASA PDF bytes, "
                "medical suitability, figure licensing, or clinical accuracy."
            ),
        }
        # Persist the accepted DB atomically; readers are read-only.
        tmp.replace(db_path)
        manifest_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result
    finally:
        if tmp.exists():
            tmp.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build(args.db, args.report)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"BLOCKED: Cannot build scientific SQLite: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": result["import_status"],
        "imported": result["imported_articles"],
        "expected": result["expected_articles"],
        "missing_or_rejected": result["missing_or_rejected_slots"],
        "db_sha256": result["sqlite_sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
