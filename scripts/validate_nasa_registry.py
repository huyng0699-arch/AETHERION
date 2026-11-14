#!/usr/bin/env python3
"""Validate knowledge/nasa/source_registry.json against schema rules and actual file SHA-256 digests."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "knowledge" / "nasa" / "source_registry.json"
DEFAULT_SCHEMA = ROOT / "knowledge" / "nasa" / "source_registry_schema.json"

UTC_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
QUEST_RE = re.compile(r"^Q-[0-9]{4}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
VALID_STATES = {
    "VERIFIED_OFFICIAL_SOURCE",
    "VERIFIED_METADATA_FROM_OSDR",
    "VERIFIED_POLICY_FROM_SOURCES",
    "VERIFIED_NOT_IMPORTED",
    "UNVERIFIED",
}


def validate_registry(registry_path: Path, *, root_dir: Path = ROOT, schema_path: Path = DEFAULT_SCHEMA) -> list[str]:
    errors: list[str] = []
    if not schema_path.is_file():
        return [f"Missing schema: {schema_path}"]
    if not registry_path.is_file():
        return [f"Missing registry: {registry_path}"]

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("properties", {}).get("schema_version", {}).get("const") != "1.0.0":
        errors.append("Unexpected schema_version const in schema")

    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0.0":
        errors.append("Registry schema_version must be 1.0.0")
    if not UTC_RE.match(str(data.get("updated_at_utc", ""))):
        errors.append("Registry updated_at_utc must be ISO-8601 UTC ending with Z")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        errors.append("Registry items must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for idx, item in enumerate(items):
        item_id = str(item.get("item_id", f"index-{idx}"))
        if item_id in seen_ids:
            errors.append(f"{item_id}: duplicate item_id")
        seen_ids.add(item_id)

        if not QUEST_RE.match(str(item.get("quest_id", ""))):
            errors.append(f"{item_id}: invalid quest_id")
        if not str(item.get("publisher", "")).strip():
            errors.append(f"{item_id}: missing publisher")
        if not str(item.get("source_uri", "")).startswith("https://"):
            errors.append(f"{item_id}: source_uri must start with https://")
        if not UTC_RE.match(str(item.get("retrieved_at_utc", ""))):
            errors.append(f"{item_id}: invalid retrieved_at_utc")
        if item.get("validation_state") not in VALID_STATES:
            errors.append(f"{item_id}: invalid validation_state {item.get('validation_state')!r}")
        if item.get("is_live_telemetry") is not False:
            errors.append(f"{item_id}: is_live_telemetry must be false")

        expected_sha = str(item.get("sha256", ""))
        if not SHA256_RE.match(expected_sha):
            errors.append(f"{item_id}: invalid sha256 format")
            continue

        rel_path = str(item.get("local_path", ""))
        target = root_dir / rel_path
        if not target.is_file():
            errors.append(f"{item_id}: missing local_path {rel_path}")
            continue

        actual_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            errors.append(f"{item_id}: sha256 mismatch for {rel_path} (expected {expected_sha}, got {actual_sha})")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate AETHERION NASA source registry and file hashes.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv)
    errors = validate_registry(args.registry)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    data = json.loads(args.registry.read_text(encoding="utf-8"))
    print(f"OK: {len(data['items'])} NASA source registry items verified (schema + SHA-256).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
