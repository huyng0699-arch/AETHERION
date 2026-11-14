"""Idempotent, provenance-verified NASA CliFF SQLite importer (Q-0421)."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from knowledge.nasa.cliff_119_2023 import library_schema

ALLOWED_IMAGE_MIMES = frozenset({"image/png", "image/jpeg", "image/webp", "image/svg+xml"})


class ImportValidationError(ValueError):
    """Raised when an article record or media asset fails provenance, MIME, or hash checks."""


def _is_sha256(val: str | None) -> bool:
    return bool(val and re.match(r"^[a-f0-9]{64}$", val))


def _load_media_bytes(item: dict[str, Any], assets_root: Path | None) -> bytes:
    if "data_bytes" in item and item["data_bytes"] is not None:
        raw = bytes(item["data_bytes"])
    elif "file_path" in item and item["file_path"]:
        path = Path(item["file_path"])
        if not path.is_absolute() and assets_root is not None:
            path = assets_root / path
        if not path.is_file():
            raise ImportValidationError(f"Media file not found: {path}")
        raw = path.read_bytes()
    else:
        raise ImportValidationError(f"Media {item.get('media_id')} missing data_bytes or file_path")
    if not raw:
        raise ImportValidationError(f"Media {item.get('media_id')} is 0 bytes")
    return raw


def ingest_article_record(
    db_path: str | Path,
    record: dict[str, Any],
    *,
    assets_root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate provenance/MIME/hashes and idempotently ingest one article record into SQLite."""
    article_id = str(record.get("article_id", "")).strip()
    slot = record.get("slot")
    display_title = str(record.get("display_title", "")).strip()
    category = str(record.get("category", "")).strip()
    source = record.get("source") or {}

    if not article_id or not display_title or not category:
        raise ImportValidationError("article_id, display_title, and category are required")
    if not isinstance(slot, int) or slot < 1 or slot > 119:
        raise ImportValidationError(f"slot must be integer 1..119, got {slot!r}")

    source_id = str(source.get("source_id", "")).strip()
    publisher = str(source.get("publisher", "")).strip()
    source_title = str(source.get("title", "")).strip()
    source_url = str(source.get("source_url", "")).strip()
    license_id = str(source.get("license_identifier", "")).strip()
    attribution = str(source.get("attribution", "")).strip()
    content_sha256 = source.get("content_sha256")

    if not all([source_id, publisher, source_title, source_url, license_id, attribution]):
        raise ImportValidationError(f"Article {article_id} missing required source provenance fields")
    if not (source_url.startswith("https://") or source_url.startswith("http://")):
        raise ImportValidationError(f"Invalid source_url for {article_id}: {source_url!r}")
    if content_sha256 is not None and not _is_sha256(str(content_sha256)):
        raise ImportValidationError(f"Invalid source content_sha256 for {article_id}")

    root_path = Path(assets_root) if assets_root is not None else None
    prepared_media: list[tuple[dict[str, Any], bytes, str]] = []
    for idx, media in enumerate(record.get("media", [])):
        mime = str(media.get("mime_type", "")).strip()
        if mime not in ALLOWED_IMAGE_MIMES:
            raise ImportValidationError(f"Unsupported media mime_type {mime!r} for {article_id}")
        raw_bytes = _load_media_bytes(media, root_path)
        actual_sha = hashlib.sha256(raw_bytes).hexdigest()
        declared_sha = str(media.get("sha256", "")).strip()
        if not _is_sha256(declared_sha) or declared_sha != actual_sha:
            raise ImportValidationError(
                f"SHA-256 mismatch for media {media.get('media_id')}: expected {declared_sha!r}, got {actual_sha}"
            )
        for req_field in ("media_id", "media_kind", "creator", "license_identifier", "source_url", "attribution", "caption", "alt_text"):
            if not str(media.get(req_field, "")).strip():
                raise ImportValidationError(f"Media item {idx} missing {req_field}")
        prepared_media.append((media, raw_bytes, actual_sha))

    now_utc = datetime.now(timezone.utc).isoformat()
    conn = library_schema.connect(db_path)
    try:
        library_schema.initialize(conn)
        conn.execute("BEGIN")
        conn.execute(
            """
            INSERT INTO sources (
                source_id, publisher, title, source_url, final_url, retrieved_at_utc,
                content_sha256, original_mime, original_bytes, license_identifier, attribution, verification_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                publisher=excluded.publisher,
                title=excluded.title,
                source_url=excluded.source_url,
                final_url=excluded.final_url,
                retrieved_at_utc=excluded.retrieved_at_utc,
                content_sha256=excluded.content_sha256,
                original_mime=excluded.original_mime,
                original_bytes=excluded.original_bytes,
                license_identifier=excluded.license_identifier,
                attribution=excluded.attribution,
                verification_state=excluded.verification_state
            """,
            (
                source_id,
                publisher,
                source_title,
                source_url,
                source.get("final_url"),
                source.get("retrieved_at_utc", now_utc),
                content_sha256,
                source.get("original_mime"),
                source.get("original_bytes"),
                license_id,
                attribution,
                source.get("verification_state", "VERIFIED"),
            ),
        )
        conn.execute(
            """
            INSERT INTO articles (
                article_id, slot, display_title, category, source_id, article_version,
                completeness_state, source_notes, created_utc, updated_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(article_id) DO UPDATE SET
                slot=excluded.slot,
                display_title=excluded.display_title,
                category=excluded.category,
                source_id=excluded.source_id,
                article_version=excluded.article_version,
                completeness_state=excluded.completeness_state,
                source_notes=excluded.source_notes,
                updated_utc=excluded.updated_utc
            """,
            (
                article_id,
                slot,
                display_title,
                category,
                source_id,
                record.get("article_version"),
                record.get("completeness_state", "COMPLETE"),
                record.get("source_notes", ""),
                now_utc,
                now_utc,
            ),
        )

        # Idempotent replacement of child rows for this article
        conn.execute("DELETE FROM article_sections WHERE article_id = ?", (article_id,))
        for idx, sec in enumerate(record.get("sections", [])):
            conn.execute(
                """
                INSERT INTO article_sections (
                    section_id, article_id, ordinal, heading, text_content, page_start, page_end, source_anchor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sec.get("section_id") or f"{article_id}-sec-{idx}",
                    article_id,
                    idx,
                    str(sec["heading"]),
                    str(sec["text_content"]),
                    sec.get("page_start"),
                    sec.get("page_end"),
                    sec.get("source_anchor"),
                ),
            )

        conn.execute("DELETE FROM article_tables WHERE article_id = ?", (article_id,))
        for idx, tbl in enumerate(record.get("tables", [])):
            conn.execute(
                """
                INSERT INTO article_tables (
                    table_id, article_id, ordinal, title, rows_json, page_number, source_anchor
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tbl.get("table_id") or f"{article_id}-tbl-{idx}",
                    article_id,
                    idx,
                    str(tbl["title"]),
                    json.dumps(tbl["rows"]),
                    tbl.get("page_number"),
                    tbl.get("source_anchor"),
                ),
            )

        conn.execute("DELETE FROM media WHERE article_id = ?", (article_id,))
        for idx, (media, raw_bytes, actual_sha) in enumerate(prepared_media):
            conn.execute(
                """
                INSERT INTO media (
                    media_id, article_id, ordinal, media_kind, data, mime_type,
                    width, height, sha256, creator, license_identifier, source_url,
                    attribution, caption, alt_text, page_number, figure_reference, usage_review
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    media["media_id"],
                    article_id,
                    idx,
                    media["media_kind"],
                    raw_bytes,
                    media["mime_type"],
                    media.get("width"),
                    media.get("height"),
                    actual_sha,
                    media["creator"],
                    media["license_identifier"],
                    media["source_url"],
                    media["attribution"],
                    media["caption"],
                    media["alt_text"],
                    media.get("page_number"),
                    media.get("figure_reference"),
                    media.get("usage_review", "APPROVED"),
                ),
            )

        conn.execute("DELETE FROM source_references WHERE article_id = ?", (article_id,))
        for idx, ref in enumerate(record.get("references", [])):
            conn.execute(
                """
                INSERT INTO source_references (
                    reference_id, article_id, source_id, ordinal, label, citation_url, doi, page_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ref.get("reference_id") or f"{article_id}-ref-{idx}",
                    article_id,
                    source_id,
                    idx,
                    str(ref["label"]),
                    str(ref["citation_url"]),
                    ref.get("doi"),
                    ref.get("page_number"),
                ),
            )

        conn.execute(
            """
            INSERT INTO ingestion_audit (article_id, action, timestamp_utc, source_sha256, message)
            VALUES (?, 'INGEST_ARTICLE', ?, ?, ?)
            """,
            (article_id, now_utc, content_sha256, f"Ingested slot {slot} ({len(prepared_media)} media)"),
        )
        conn.commit()
        audit_summary = library_schema.audit(conn, verify_media=True)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "article_id": article_id,
        "slot": slot,
        "media_count": len(prepared_media),
        "audit": audit_summary,
    }


def ingest_directory(
    db_path: str | Path,
    records_dir: str | Path,
    *,
    assets_root: str | Path | None = None,
) -> dict[str, Any]:
    """Incrementally ingest all JSON article records in records_dir."""
    directory = Path(records_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Records directory not found: {directory}")

    ingested: list[str] = []
    for json_path in sorted(directory.glob("*.json")):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        res = ingest_article_record(db_path, payload, assets_root=assets_root)
        ingested.append(res["article_id"])

    conn = library_schema.connect(db_path)
    try:
        summary = library_schema.audit(conn, verify_media=True)
    finally:
        conn.close()
    return {"ingested_articles": ingested, "audit": summary}
