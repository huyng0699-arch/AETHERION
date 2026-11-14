"""Versioned, offline-only SQLite schema for original-source CliFF medical reference.

This creates tables and constraints; it does NOT manufacture disease records.
The database is a separate read-only scientific library, not the server's
patient observation database.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DEFAULT_LIBRARY_NAME = "AETHERION_NASA_CLIFF_119.sqlite"

SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS library_info (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    publisher TEXT NOT NULL,
    title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    final_url TEXT,
    retrieved_at_utc TEXT,
    content_sha256 TEXT CHECK (content_sha256 IS NULL OR length(content_sha256) = 64),
    original_mime TEXT,
    original_bytes INTEGER CHECK(original_bytes IS NULL OR original_bytes > 0),
    license_identifier TEXT NOT NULL,
    attribution TEXT NOT NULL,
    verification_state TEXT NOT NULL DEFAULT 'UNVERIFIED'
       CHECK (verification_state IN ('UNVERIFIED','VERIFIED','RESTRICTED','MISSING','ERROR')),
    CHECK (length(trim(source_url)) > 0)
);
CREATE TABLE IF NOT EXISTS articles (
    article_id TEXT PRIMARY KEY,
    slot INTEGER NOT NULL UNIQUE CHECK(slot BETWEEN 1 AND 119),
    display_title TEXT NOT NULL,
    category TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    article_version TEXT,
    completeness_state TEXT NOT NULL DEFAULT 'UNVERIFIED'
       CHECK(completeness_state IN ('UNVERIFIED','PARTIAL','COMPLETE','RESTRICTED')),
    source_notes TEXT NOT NULL DEFAULT '',
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS article_sections (
    section_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    heading TEXT NOT NULL,
    text_content TEXT NOT NULL,
    page_start INTEGER CHECK(page_start IS NULL OR page_start >= 1),
    page_end INTEGER CHECK(page_end IS NULL OR page_end >= page_start),
    source_anchor TEXT,
    UNIQUE(article_id,ordinal)
);
CREATE TABLE IF NOT EXISTS article_tables (
    table_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    title TEXT NOT NULL,
    rows_json TEXT NOT NULL CHECK(json_valid(rows_json)),
    page_number INTEGER CHECK(page_number IS NULL OR page_number >= 1),
    source_anchor TEXT,
    UNIQUE(article_id,ordinal)
);
CREATE TABLE IF NOT EXISTS media (
    media_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    media_kind TEXT NOT NULL CHECK(media_kind IN ('NASA_FIGURE','CLINICAL','ANATOMY','RADIOLOGY','HISTOLOGY','DIAGRAM','OTHER')),
    data BLOB NOT NULL CHECK(length(data) > 0),
    mime_type TEXT NOT NULL CHECK(mime_type IN ('image/png','image/jpeg','image/webp','image/svg+xml')),
    width INTEGER CHECK(width IS NULL OR width > 0),
    height INTEGER CHECK(height IS NULL OR height > 0),
    sha256 TEXT NOT NULL CHECK(length(sha256)=64),
    creator TEXT NOT NULL,
    license_identifier TEXT NOT NULL,
    source_url TEXT NOT NULL,
    attribution TEXT NOT NULL,
    caption TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    page_number INTEGER CHECK(page_number IS NULL OR page_number >= 1),
    figure_reference TEXT,
    usage_review TEXT NOT NULL DEFAULT 'PENDING'
       CHECK(usage_review IN ('PENDING','APPROVED','RESTRICTED','REJECTED')),
    UNIQUE(article_id,ordinal)
);
CREATE TABLE IF NOT EXISTS source_references (
    reference_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    source_id TEXT REFERENCES sources(source_id) ON DELETE RESTRICT,
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    label TEXT NOT NULL,
    citation_url TEXT NOT NULL,
    doi TEXT,
    page_number INTEGER CHECK(page_number IS NULL OR page_number >= 1),
    UNIQUE(article_id,ordinal)
);
CREATE TABLE IF NOT EXISTS ingestion_audit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT REFERENCES articles(article_id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    source_sha256 TEXT,
    message TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_sections_article ON article_sections(article_id,ordinal);
CREATE INDEX IF NOT EXISTS idx_media_article ON media(article_id,ordinal);
CREATE INDEX IF NOT EXISTS idx_references_article ON source_references(article_id,ordinal);
"""

def connect(path: str | Path, *, read_only: bool = False) -> sqlite3.Connection:
    """Open the scientific library (never the health observation store)."""
    if read_only:
        db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    else:
        db = sqlite3.connect(str(path))
    db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = sqlite3.Row
    return db

def initialize(connection: sqlite3.Connection) -> None:
    """Apply safe forward-only v0 -> v1 migration. Existing content is not erased."""
    current = connection.execute("PRAGMA user_version").fetchone()[0]
    if current > SCHEMA_VERSION:
        raise RuntimeError(f"Unsupported future SQLite library version: {current}")
    if current == SCHEMA_VERSION:
        check_required_tables(connection)
        return
    if current != 0:
        raise RuntimeError(f"Unknown migration path: {current} -> {SCHEMA_VERSION}")
    with connection:
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            "INSERT OR REPLACE INTO library_info(key,value) VALUES ('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        connection.execute(
            "INSERT OR REPLACE INTO library_info(key,value) VALUES ('library_kind','NASA_CLIFF_119_MEDICAL_REFERENCE')"
        )
        # FTS5 is optional; some embedded SQLite builds do not include it.
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS article_search USING fts5(article_id UNINDEXED, display_title, content)"
            )
            connection.execute(
                "INSERT OR REPLACE INTO library_info(key,value) VALUES ('fts5','available')"
            )
        except sqlite3.OperationalError as exc:
            if "no such module" not in str(exc).lower():
                raise
            connection.execute(
                "INSERT OR REPLACE INTO library_info(key,value) VALUES ('fts5','unavailable')"
            )
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

def check_required_tables(connection: sqlite3.Connection) -> None:
    required = {
        "library_info", "sources", "articles", "article_sections", "article_tables",
        "media", "source_references", "ingestion_audit"
    }
    found = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = required - found
    if missing:
        raise RuntimeError(f"Malformed scientific library: missing tables {sorted(missing)}")

def audit(connection: sqlite3.Connection, *, verify_media: bool = True) -> dict[str, Any]:
    """Real content statistics; empty database is explicitly INCOMPLETE."""
    check_required_tables(connection)
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    fk = connection.execute("PRAGMA foreign_key_check").fetchall()
    media = connection.execute("SELECT media_id,data,sha256,usage_review FROM media").fetchall()
    bad_hash = [row["media_id"] for row in media
                if verify_media and hashlib.sha256(row["data"]).hexdigest() != row["sha256"]]
    articles = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    complete = connection.execute(
        "SELECT COUNT(*) FROM articles WHERE completeness_state='COMPLETE'"
    ).fetchone()[0]
    approved_images = sum(row["usage_review"] == "APPROVED" for row in media)
    return {
        "schema_version": connection.execute("PRAGMA user_version").fetchone()[0],
        "integrity": integrity,
        "foreign_key_errors": len(fk),
        "articles": articles,
        "complete_articles": complete,
        "media_assets": len(media),
        "approved_images": approved_images,
        "media_hash_mismatches": bad_hash,
        "library_complete": integrity == "ok" and not fk and not bad_hash and complete == 119,
    }

def create_file(path: str | Path) -> dict[str, Any]:
    """Create an actual empty database. Empty means 0/119, never verified."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with connect(dest) as db:
        initialize(db)
        return audit(db)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("db", type=Path, help="Output SQLite library file")
    args = parser.parse_args()
    print(json.dumps(create_file(args.db), indent=2))
