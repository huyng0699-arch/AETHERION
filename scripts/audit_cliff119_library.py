#!/usr/bin/env python3
"""Fail-closed audit of an offline NASA CliFF 119 SQLite reference library.

Release evidence needs real NASA source bytes, not a completed placeholder index.
No network requests, medical content generation, or older repositories are used.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit

EXPECTED = 119
SHA256 = re.compile(r"^[0-9a-f]{64}$")
BLOCKED_LICENSES = {"", "UNKNOWN", "UNVERIFIED", "FAIR_USE_ONLY", "NO_REDISTRIBUTION", "ALL_RIGHTS_RESERVED", "TEST_ONLY"}
MAGIC = {
    "image/png": lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": lambda b: b.startswith(b"\xff\xd8\xff"),
    "image/webp": lambda b: len(b) > 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP",
    "image/svg+xml": lambda b: b"<svg" in b[:2048].lower(),
}


def nasa_url(url: str) -> bool:
    try:
        parts = urlsplit(str(url))
        host = (parts.hostname or "").lower()
        return parts.scheme == "https" and (host == "nasa.gov" or host.endswith(".nasa.gov") or host == "nasa.sharepoint.com")
    except ValueError:
        return False


def _sha256(value: object) -> bool:
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def audit_library(
    db_path: str | Path,
    catalog_path: str | Path,
    manifest_path: str | Path,
    *,
    min_approved_images: int = 3,
    require_original_bytes: bool = True,
) -> dict:
    """Return machine-auditable reasons for refusing a false 119/119 release."""
    if min_approved_images < 0:
        raise ValueError("min_approved_images cannot be negative")
    issues: list[dict] = []
    counts = {"articles": 0, "verified_originals": 0, "approved_images": 0, "verified_images": 0}

    def issue(code: str, detail: str, slot: int | None = None):
        item = {"code": code, "detail": detail}
        if slot is not None:
            item["slot"] = slot
        issues.append(item)

    catalog_path = Path(catalog_path)
    manifest_path = Path(manifest_path)
    db_path = Path(db_path)
    if not catalog_path.is_file():
        issue("CATALOG_MISSING", str(catalog_path))
        catalog = {}
    else:
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            issue("CATALOG_INVALID", str(exc))
            catalog = {}
    entries = catalog.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    slot_to_entry = {e.get("slot"): e for e in entries if isinstance(e, dict) and isinstance(e.get("slot"), int)}
    if len(entries) != EXPECTED or len(slot_to_entry) != EXPECTED:
        issue("CATALOG_COUNT", f"Expected {EXPECTED} distinct slots, found {len(entries)} entries and {len(slot_to_entry)} distinct slots")
    for slot in range(1, EXPECTED + 1):
        entry = slot_to_entry.get(slot)
        if not entry or not str(entry.get("source_title") or "").strip():
            issue("UNRESOLVED_INDEX_SLOT", "No independently verified NASA condition title", slot)
        elif not str(entry.get("original_document_url") or "").strip():
            issue("DIRECT_URL_UNVERIFIED", "Direct original document URL not verified", slot)
        elif not nasa_url(entry["original_document_url"]):
            issue("INVALID_NASA_URL", "The source index URL is not a trusted NASA HTTPS host", slot)
        elif entry.get("url_verification") != "VERIFIED":
            issue("DIRECT_URL_UNVERIFIED", "NASA original URL has no independently recorded verification", slot)

    if not manifest_path.is_file():
        issue("MANIFEST_MISSING", str(manifest_path))
        manifest = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            issue("MANIFEST_INVALID", str(exc))
            manifest = {}
    if manifest and (manifest.get("complete") is not True or manifest.get("downloaded_pdf_count") != EXPECTED):
        issue("MANIFEST_NOT_COMPLETE", "Manifest does not confirm exactly 119 successfully downloaded original PDFs")
    manifest_items = manifest.get("files", [])
    if not isinstance(manifest_items, list):
        manifest_items = []
    originals_by_sha: dict[str, list[dict]] = {}
    for item in manifest_items:
        if isinstance(item, dict) and item.get("status") == "downloaded" and _sha256(item.get("sha256")):
            originals_by_sha.setdefault(item["sha256"], []).append(item)

    if not db_path.is_file():
        issue("DATABASE_MISSING", str(db_path))
    else:
        try:
            conn = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            try:
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    issue("SQLITE_INTEGRITY", str(integrity))
                if conn.execute("PRAGMA foreign_key_check").fetchall():
                    issue("FOREIGN_KEY_FAILURE", "Foreign key check failed")
                required = {"articles", "sources", "article_sections", "article_tables", "media", "source_references"}
                existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                missing = required - existing
                if missing:
                    issue("SCHEMA_INCOMPLETE", ", ".join(sorted(missing)))
                else:
                    articles = conn.execute("SELECT a.*, s.publisher, s.title AS source_title, s.source_url, s.final_url, s.content_sha256, s.original_bytes, s.license_identifier, s.attribution, s.verification_state, s.retrieved_at_utc FROM articles a JOIN sources s ON a.source_id=s.source_id ORDER BY a.slot").fetchall()
                    counts["articles"] = len(articles)
                    if len(articles) != EXPECTED:
                        issue("ARTICLE_COUNT", f"Expected {EXPECTED} articles, found {len(articles)}")
                    byslot = {a["slot"]: a for a in articles}
                    if len(byslot) != len(articles):
                        issue("DUPLICATE_ARTICLE_SLOT", "Duplicate article slots")
                    source_keys: list[str] = []
                    source_urls: list[str] = []
                    source_hashes: list[str] = []
                    for slot in range(1, EXPECTED + 1):
                        a = byslot.get(slot)
                        if a is None:
                            issue("ARTICLE_MISSING", "No SQLite article for NASA slot", slot)
                            continue
                        spec = slot_to_entry.get(slot)
                        source_keys.append(a["source_id"])
                        source_urls.append(a["source_url"])
                        if _sha256(a["content_sha256"]):
                            source_hashes.append(a["content_sha256"])
                        if spec and spec.get("article_id") != a["article_id"]:
                            issue("ARTICLE_ID_MISMATCH", f"Catalog {spec.get('article_id')!r}; SQLite {a['article_id']!r}", slot)
                        if spec and spec.get("source_title") and spec["source_title"].strip().casefold() != a["display_title"].strip().casefold():
                            issue("ARTICLE_TITLE_MISMATCH", "SQLite title differs from NASA catalog title", slot)
                        if spec and spec.get("original_document_url") and spec["original_document_url"] != a["source_url"]:
                            issue("SOURCE_URL_MISMATCH", "SQLite source link differs from verified NASA index", slot)
                        if a["completeness_state"] != "COMPLETE":
                            issue("ARTICLE_INCOMPLETE", f"State: {a['completeness_state']}", slot)
                        if a["publisher"].strip().upper() != "NASA" or not nasa_url(a["source_url"]):
                            issue("SOURCE_NOT_NASA", str(a["source_url"]), slot)
                        if a["verification_state"] != "VERIFIED" or not _sha256(a["content_sha256"]):
                            issue("SOURCE_UNVERIFIED", "NASA document SHA-256 or verification state missing", slot)
                        if a["license_identifier"].strip().upper() in BLOCKED_LICENSES or not a["attribution"].strip():
                            issue("SOURCE_RIGHTS_UNVERIFIED", "Missing allowed rights or source attribution", slot)
                        if not isinstance(a["original_bytes"], int) or a["original_bytes"] <= 0:
                            issue("SOURCE_BYTES_MISSING", "Original byte count missing", slot)
                        try:
                            timestamp = datetime.fromisoformat(a["retrieved_at_utc"] or "")
                            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                                raise ValueError("timestamp lacks timezone")
                        except ValueError:
                            issue("RETRIEVAL_TIME_INVALID", "Source retrieval timestamp must be timezone-aware", slot)
                        if _sha256(a["content_sha256"]):
                            matching = [m for m in originals_by_sha.get(a["content_sha256"], []) if m.get("source_url") == a["source_url"]]
                            if not matching:
                                issue("ORIGINAL_MANIFEST_MISSING", "Original source hash and direct URL not in manifest", slot)
                            else:
                                item = matching[0]
                                if require_original_bytes:
                                    relative = Path(str(item.get("path") or ""))
                                    root = manifest_path.parent.resolve()
                                    sourcefile = (root / relative).resolve()
                                    if relative.is_absolute() or not sourcefile.is_relative_to(root) or not sourcefile.is_file():
                                        issue("ORIGINAL_FILE_MISSING", "Original document absent or path outside archive", slot)
                                    else:
                                        data = sourcefile.read_bytes()
                                        if not data.startswith(b"%PDF-") or sourcefile.suffix.lower() != ".pdf":
                                            issue("ORIGINAL_NOT_PDF", "Original must be an actual PDF, not merely a renamed file", slot)
                                        if hashlib.sha256(data).hexdigest() != a["content_sha256"] or len(data) != a["original_bytes"]:
                                            issue("ORIGINAL_HASH_MISMATCH", "Original bytes differ from source SHA-256/size", slot)
                                        else:
                                            counts["verified_originals"] += 1
                        sections = conn.execute("SELECT text_content, source_anchor, page_start FROM article_sections WHERE article_id=?", (a["article_id"],)).fetchall()
                        if not sections or any(not s["text_content"].strip() or (not s["source_anchor"] and s["page_start"] is None) for s in sections):
                            issue("SECTION_EVIDENCE_MISSING", "No substantive text or page/anchor mapping", slot)
                        references = conn.execute("SELECT citation_url, label FROM source_references WHERE article_id=?", (a["article_id"],)).fetchall()
                        if not references or any(not r["label"].strip() or not str(r["citation_url"]).startswith("https://") for r in references):
                            issue("CITATIONS_MISSING", "Missing linked source citations", slot)
                        media = conn.execute("SELECT * FROM media WHERE article_id=?", (a["article_id"],)).fetchall()
                        usable = 0
                        hashes = Counter()
                        for m in media:
                            content = m["data"]
                            digest = hashlib.sha256(content).hexdigest()
                            hashes[digest] += 1
                            if digest != m["sha256"] or m["mime_type"] not in MAGIC or not MAGIC[m["mime_type"]](content):
                                issue("IMAGE_CORRUPT", m["media_id"], slot)
                                continue
                            if (m["license_identifier"].strip().upper() in BLOCKED_LICENSES or not m["creator"].strip() or not m["attribution"].strip() or not str(m["source_url"]).startswith("https://") or not m["alt_text"].strip() or not m["caption"].strip() or m["usage_review"] != "APPROVED"):
                                issue("IMAGE_RIGHTS_OR_REVIEW", m["media_id"], slot)
                                continue
                            usable += 1
                            counts["verified_images"] += 1
                        if any(n > 1 for n in hashes.values()):
                            issue("IMAGE_DUPLICATION", "Identical images repeated within article", slot)
                        counts["approved_images"] += usable
                        if usable < min_approved_images:
                            issue("IMAGE_COVERAGE", f"{usable}/{min_approved_images} approved, integrity-checked images", slot)
                    for key, keys in (("DUPLICATE_SOURCE_ID", source_keys), ("DUPLICATE_SOURCE_URL", source_urls), ("DUPLICATE_SOURCE_HASH", source_hashes)):
                        if len(keys) != len(set(keys)):
                            issue(key, "Two distinct CliFF articles have the same original document identity")
            finally:
                conn.close()
        except sqlite3.DatabaseError as exc:
            issue("SQLITE_ERROR", str(exc))

    passed = not issues and counts["verified_originals"] == EXPECTED and counts["articles"] == EXPECTED
    return {"collection": "NASA IMM CliFF 119 (2023)", "expected": EXPECTED, "counts": counts, "passed": passed, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("knowledge/nasa/cliff_119_2023/AETHERION_NASA_CLIFF_119.sqlite"))
    parser.add_argument("--catalog", type=Path, default=Path("knowledge/nasa/cliff_119_2023/quest_source_index.json"))
    parser.add_argument("--manifest", type=Path, default=Path("knowledge/nasa/cliff_119_2023/manifest.json"))
    parser.add_argument("--min-images", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_library(args.db, args.catalog, args.manifest, min_approved_images=args.min_images)
    result = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    print(result)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
