"""Q-0423: offline SQLite thumbnails with integrity and rights-aware retrieval.

Extends existing media originals without rewriting their content. No network or
medical imagery is generated here. Thumbnails must be derived from verified
source bytes and supplied by an image decoder, never fabricated.
"""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class OfflineImage:
    media_id: str
    original: bytes
    mime_type: str
    thumbnail: bytes | None
    thumbnail_mime: str | None
    caption: str
    alt_text: str
    attribution: str
    license_identifier: str
    source_url: str


def install(connection: sqlite3.Connection) -> None:
    """Idempotent extension to the v1 media table, retaining originals."""
    names = {r[1] for r in connection.execute("PRAGMA table_info(media)")}
    if not names:
        raise ValueError("Initialize the scientific library schema before thumbnails")
    with connection:
        if "thumbnail_data" not in names:
            connection.execute("ALTER TABLE media ADD COLUMN thumbnail_data BLOB")
        if "thumbnail_mime" not in names:
            connection.execute("ALTER TABLE media ADD COLUMN thumbnail_mime TEXT")
        if "thumbnail_sha256" not in names:
            connection.execute("ALTER TABLE media ADD COLUMN thumbnail_sha256 TEXT")
        if "thumbnail_width" not in names:
            connection.execute("ALTER TABLE media ADD COLUMN thumbnail_width INTEGER")
        if "thumbnail_height" not in names:
            connection.execute("ALTER TABLE media ADD COLUMN thumbnail_height INTEGER")


def set_thumbnail(connection: sqlite3.Connection, media_id: str, *, data: bytes,
                  mime_type: str, width: int, height: int, original_sha256: str) -> None:
    """Attach a pre-rendered thumbnail only to the expected verified original."""
    if mime_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise ValueError("Unsupported thumbnail format")
    if not data or width < 1 or height < 1:
        raise ValueError("Invalid thumbnail data or dimensions")
    row = connection.execute("SELECT data,sha256,usage_review FROM media WHERE media_id=?", (media_id,)).fetchone()
    if row is None:
        raise KeyError(media_id)
    original, declared, review = row
    if review != "APPROVED" or declared != original_sha256 or hashlib.sha256(original).hexdigest() != declared:
        raise ValueError("Original image is unapproved or fails SHA-256 verification")
    digest = hashlib.sha256(data).hexdigest()
    with connection:
        connection.execute("""UPDATE media SET thumbnail_data=?,thumbnail_mime=?,thumbnail_sha256=?,
                           thumbnail_width=?,thumbnail_height=? WHERE media_id=?""",
                           (data,mime_type,digest,width,height,media_id))


def read_offline(connection: sqlite3.Connection, media_id: str) -> OfflineImage:
    """Return only rights-approved, hash-verified image bytes; never an external URL."""
    row = connection.execute("""SELECT data,mime_type,sha256,thumbnail_data,thumbnail_mime,
        thumbnail_sha256,caption,alt_text,attribution,license_identifier,source_url,usage_review
        FROM media WHERE media_id=?""", (media_id,)).fetchone()
    if row is None:
        raise KeyError(media_id)
    original,mime,sha,thumb,thumb_mime,thumb_sha,caption,alt,credit,license_id,url,review = row
    if review != "APPROVED" or not all((caption.strip(),alt.strip(),credit.strip(),license_id.strip(),url.strip())):
        raise ValueError("Image not approved or provenance incomplete")
    if hashlib.sha256(original).hexdigest() != sha:
        raise ValueError("Original SHA-256 mismatch")
    if thumb is not None and (not thumb_sha or hashlib.sha256(thumb).hexdigest() != thumb_sha):
        raise ValueError("Thumbnail SHA-256 mismatch")
    return OfflineImage(media_id,original,mime,thumb,thumb_mime,caption,alt,credit,license_id,url)
