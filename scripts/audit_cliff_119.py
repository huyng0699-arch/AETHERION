#!/usr/bin/env python3
"""Verify actual NASA CliFF 119 original files against manifest without fabricating completeness."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_COUNT = 119
SOURCE_URL = "https://www.nasa.gov/integrated-medical-model-documentation/"
DEFAULT_BASE = Path(__file__).resolve().parents[1] / "knowledge" / "nasa" / "cliff_119_2023"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def audit_cliff_directory(base_dir: Path, *, checked_at_utc: str | None = None) -> dict[str, object]:
    original_dir = base_dir / "original"
    manifest_path = base_dir / "manifest.json"

    original_dir_exists = original_dir.is_dir()
    manifest_exists = manifest_path.is_file()

    pdf_files = sorted(original_dir.glob("*.pdf")) if original_dir_exists else []
    valid_pdf_files: list[Path] = []
    invalid_pdf_files: list[str] = []

    for pdf in pdf_files:
        if _is_pdf(pdf):
            valid_pdf_files.append(pdf)
        else:
            invalid_pdf_files.append(pdf.name)

    manifest_entries_count = 0
    manifest_mismatches: list[str] = []
    if manifest_exists:
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = manifest_data.get("documents", []) if isinstance(manifest_data, dict) else []
            manifest_entries_count = len(entries)
            for entry in entries:
                rel_name = entry.get("filename")
                expected_sha = entry.get("sha256")
                if not rel_name:
                    manifest_mismatches.append("<missing filename>")
                    continue
                target = original_dir / rel_name
                if not target.is_file():
                    manifest_mismatches.append(f"missing:{rel_name}")
                elif not _is_pdf(target):
                    manifest_mismatches.append(f"not_pdf:{rel_name}")
                elif expected_sha and _sha256_file(target) != expected_sha:
                    manifest_mismatches.append(f"sha256_mismatch:{rel_name}")
        except (json.JSONDecodeError, OSError) as exc:
            manifest_mismatches.append(f"manifest_error:{exc}")

    verified_count = len(valid_pdf_files)
    if verified_count == 0 and not manifest_exists:
        verification_status = "NOT_IMPORTED"
    elif (
        verified_count == EXPECTED_COUNT
        and manifest_exists
        and manifest_entries_count == EXPECTED_COUNT
        and not invalid_pdf_files
        and not manifest_mismatches
    ):
        verification_status = "VERIFIED_119_COMPLETE"
    else:
        verification_status = "PARTIAL_OR_UNVERIFIED"

    return {
        "schema_version": "1.0.0",
        "source_url": SOURCE_URL,
        "checked_at_utc": checked_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expected_count": EXPECTED_COUNT,
        "original_dir_exists": original_dir_exists,
        "manifest_exists": manifest_exists,
        "manifest_entries_count": manifest_entries_count,
        "total_pdf_candidates": len(pdf_files),
        "verified_pdf_count": verified_count,
        "invalid_pdf_files": invalid_pdf_files,
        "manifest_mismatches": manifest_mismatches,
        "is_119_complete": verification_status == "VERIFIED_119_COMPLETE",
        "verification_status": verification_status,
        "not_live_crew_telemetry": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit NASA CliFF 119 original files vs manifest.")
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--out", type=Path, default=None, help="Optional JSON output path")
    args = parser.parse_args(argv)

    report = audit_cliff_directory(args.base_dir)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out is not None:
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
