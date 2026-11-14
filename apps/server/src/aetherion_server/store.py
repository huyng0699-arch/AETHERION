"""Canonical SQLite observation provenance, user identity, and session store."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from .sqlite_compat import connect_sqlite

from .security import (
    VALID_ROLES,
    compute_expiry_iso,
    generate_session_token,
    hash_password,
    hash_token,
    is_expired,
    utc_now_iso,
)

DEFAULT_SCOPE = "crew"
DEFAULT_QUALITY = "UNVERIFIED"
DEFAULT_VERIFICATION_STATE = "UNVERIFIED"


def _connect(path: str | Path):
    return connect_sqlite(path, row_factory=sqlite3.Row, foreign_keys=True)


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def initialize(path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with _connect(target) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id TEXT NOT NULL,
                scope TEXT NOT NULL DEFAULT 'crew',
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                source_id TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                received_at TEXT NOT NULL DEFAULT '',
                quality TEXT NOT NULL DEFAULT 'UNVERIFIED',
                verification_state TEXT NOT NULL DEFAULT 'UNVERIFIED',
                idempotency_key TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Idempotent migration for starter-schema databases.
        existing_cols = _table_columns(conn, "observations")
        migrations = [
            ("scope", "TEXT NOT NULL DEFAULT 'crew'"),
            ("source_id", "TEXT NOT NULL DEFAULT ''"),
            ("received_at", "TEXT NOT NULL DEFAULT ''"),
            ("quality", "TEXT NOT NULL DEFAULT 'UNVERIFIED'"),
            ("verification_state", "TEXT NOT NULL DEFAULT 'UNVERIFIED'"),
            ("idempotency_key", "TEXT"),
            ("created_by", "TEXT"),
        ]
        for col_name, col_def in migrations:
            if col_name not in existing_cols:
                conn.execute(f"ALTER TABLE observations ADD COLUMN {col_name} {col_def}")

        conn.execute(
            """
            UPDATE observations
            SET source_id = source
            WHERE (source_id IS NULL OR source_id = '') AND source IS NOT NULL
            """
        )
        conn.execute(
            """
            UPDATE observations
            SET received_at = created_at
            WHERE (received_at IS NULL OR received_at = '') AND created_at IS NOT NULL
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_obs_subject_time "
            "ON observations(subject_id, observed_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_obs_subject_scope_metric "
            "ON observations(subject_id, scope, metric, observed_at)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_obs_idempotency "
            "ON observations(subject_id, idempotency_key) "
            "WHERE idempotency_key IS NOT NULL"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                allowed_subjects_json TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                scope TEXT NOT NULL DEFAULT 'CREW',
                role_label TEXT NOT NULL DEFAULT 'crew_member',
                created_at TEXT NOT NULL
            )
            """
        )


def check_readiness(path: str | Path) -> dict[str, str]:
    initialize(path)
    with _connect(path) as conn:
        row = conn.execute("SELECT 1 AS ok").fetchone()
        if not row or int(row["ok"]) != 1:
            raise RuntimeError("SQLite readiness check failed")
    return {"database": "ok", "path": str(path)}


def _row_to_observation(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["observation_uid"] = f"obs-{data['id']}"
    if not data.get("source_id"):
        data["source_id"] = data.get("source", "")
    if not data.get("source"):
        data["source"] = data.get("source_id", "")
    if not data.get("received_at"):
        data["received_at"] = data.get("created_at", "")
    return data


def ingest_observation(
    path: str | Path,
    item: dict[str, Any],
    *,
    created_by: str | None = None,
) -> tuple[int, bool, dict[str, Any]]:
    """Insert an observation or return an existing row on idempotent replay.

    Returns (observation_id, created_new, stored_record).
    """
    initialize(path)
    subject_id = str(item["subject_id"])
    scope = str(item.get("scope") or DEFAULT_SCOPE)
    metric = str(item["metric"])
    value = float(item["value"])
    unit = str(item["unit"])
    source_id = str(item.get("source_id") or item.get("source") or "")
    source = str(item.get("source") or source_id)
    observed_at = str(item["observed_at"])
    received_at = str(item.get("received_at") or utc_now_iso())
    quality = str(item.get("quality") or DEFAULT_QUALITY)
    verification_state = str(item.get("verification_state") or DEFAULT_VERIFICATION_STATE)
    idempotency_key = item.get("idempotency_key")
    if idempotency_key is not None:
        idempotency_key = str(idempotency_key).strip() or None

    with _connect(path) as conn:
        if idempotency_key is not None:
            existing = conn.execute(
                """
                SELECT id, subject_id, scope, metric, value, unit, source_id, source,
                       observed_at, received_at, quality, verification_state,
                       idempotency_key, created_by, created_at
                FROM observations
                WHERE subject_id = ? AND idempotency_key = ?
                """,
                (subject_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                record = _row_to_observation(existing)
                return int(record["id"]), False, record

        cursor = conn.execute(
            """
            INSERT INTO observations
            (subject_id, scope, metric, value, unit, source_id, source,
             observed_at, received_at, quality, verification_state,
             idempotency_key, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                subject_id,
                scope,
                metric,
                value,
                unit,
                source_id,
                source,
                observed_at,
                received_at,
                quality,
                verification_state,
                idempotency_key,
                created_by,
            ),
        )
        obs_id = int(cursor.lastrowid)
        row = conn.execute(
            """
            SELECT id, subject_id, scope, metric, value, unit, source_id, source,
                   observed_at, received_at, quality, verification_state,
                   idempotency_key, created_by, created_at
            FROM observations WHERE id = ?
            """,
            (obs_id,),
        ).fetchone()
        assert row is not None
        return obs_id, True, _row_to_observation(row)


def add_observation(path: str | Path, item: dict[str, Any]) -> int:
    """Backward-compatible starter API returning only the inserted integer ID."""
    obs_id, _, _ = ingest_observation(path, item)
    return obs_id


def _parse_utc(iso_str: str) -> datetime:
    from datetime import datetime, timezone

    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def query_observations(
    path: str | Path,
    subject_id: str,
    *,
    scope: str | None = None,
    metric: str | None = None,
    include_non_live: bool = False,
    order: str = "desc",
    since: str | None = None,
    until: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if order not in {"asc", "desc"}:
        raise ValueError("order must be 'asc' or 'desc'")
    initialize(path)
    clauses = ["subject_id = ?"]
    params: list[Any] = [subject_id]
    if scope is not None:
        clauses.append("scope = ?")
        params.append(scope)
    if metric is not None:
        clauses.append("metric = ?")
        params.append(metric)
    if not include_non_live and scope != "engineering_test":
        clauses.append("scope != 'engineering_test'")
        clauses.append("verification_state != 'TEST_FIXTURE'")
        clauses.append("LOWER(source_id) NOT LIKE 'nasa_osdr:%'")
        clauses.append("LOWER(source_id) NOT LIKE 'research:%'")
    where_sql = " AND ".join(clauses)
    with _connect(path) as conn:
        rows = conn.execute(
            f"""
            SELECT id, subject_id, scope, metric, value, unit, source_id, source,
                   observed_at, received_at, quality, verification_state,
                   idempotency_key, created_by, created_at
            FROM observations
            WHERE {where_sql}
            """,
            params,
        ).fetchall()
    items = [_row_to_observation(row) for row in rows]
    if since is not None:
        since_dt = _parse_utc(since)
        items = [item for item in items if _parse_utc(item["observed_at"]) >= since_dt]
    if until is not None:
        until_dt = _parse_utc(until)
        items = [item for item in items if _parse_utc(item["observed_at"]) <= until_dt]
    items.sort(
        key=lambda item: (_parse_utc(item["observed_at"]), int(item["id"])),
        reverse=(order == "desc"),
    )
    return items[:limit]


def encode_cursor(observed_at: str, obs_id: int) -> str:
    import base64

    payload = json.dumps({"t": _parse_utc(observed_at).isoformat(), "id": int(obs_id)}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> tuple[Any, int]:
    import base64

    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict) or "t" not in data or "id" not in data:
            raise ValueError("Missing cursor keys")
        return _parse_utc(str(data["t"])), int(data["id"])
    except Exception as exc:
        raise ValueError(f"Invalid pagination cursor: {exc}") from exc


def query_observations_page(
    path: str | Path,
    subject_id: str,
    *,
    scope: str | None = None,
    metric: str | None = None,
    include_non_live: bool = False,
    order: str = "desc",
    since: str | None = None,
    until: str | None = None,
    cursor: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    all_items = query_observations(
        path,
        subject_id,
        scope=scope,
        metric=metric,
        include_non_live=include_non_live,
        order=order,
        since=since,
        until=until,
        limit=100_000,
    )
    if cursor is not None:
        cursor_key = decode_cursor(cursor)
        if order == "desc":
            all_items = [
                item for item in all_items
                if (_parse_utc(item["observed_at"]), int(item["id"])) < cursor_key
            ]
        else:
            all_items = [
                item for item in all_items
                if (_parse_utc(item["observed_at"]), int(item["id"])) > cursor_key
            ]
    has_more = len(all_items) > limit
    page = all_items[:limit]
    next_cursor = (
        encode_cursor(page[-1]["observed_at"], int(page[-1]["id"]))
        if has_more and page
        else None
    )
    return {
        "observations": page,
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


def list_observations(path: str | Path, subject_id: str, limit: int = 100) -> list[dict[str, Any]]:
    return query_observations(path, subject_id, limit=limit)


def count_users(path: str | Path) -> int:
    initialize(path)
    with _connect(path) as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
    return int(row["cnt"]) if row else 0


def upsert_user(
    path: str | Path,
    *,
    username: str,
    password: str,
    role: str = "crew",
    allowed_subjects: list[str] | None = None,
    active: bool = True,
) -> dict[str, Any]:
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")
    clean_username = username.strip()
    if not clean_username:
        raise ValueError("Username cannot be empty")
    subjects = allowed_subjects if allowed_subjects is not None else [clean_username]
    pw_hash = hash_password(password)
    now_iso = utc_now_iso()
    subjects_json = json.dumps(subjects)

    initialize(path)
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, allowed_subjects_json, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = excluded.password_hash,
                role = excluded.role,
                allowed_subjects_json = excluded.allowed_subjects_json,
                active = excluded.active
            """,
            (clean_username, pw_hash, role, subjects_json, 1 if active else 0, now_iso),
        )
        row = conn.execute(
            "SELECT id, username, role, allowed_subjects_json, active, created_at "
            "FROM users WHERE username = ?",
            (clean_username,),
        ).fetchone()
    assert row is not None
    return {
        "id": int(row["id"]),
        "username": str(row["username"]),
        "role": str(row["role"]),
        "allowed_subjects": json.loads(str(row["allowed_subjects_json"])),
        "active": bool(row["active"]),
        "created_at": str(row["created_at"]),
    }


def get_user_by_username(path: str | Path, username: str) -> dict[str, Any] | None:
    initialize(path)
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, allowed_subjects_json, active, created_at "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": int(row["id"]),
        "username": str(row["username"]),
        "password_hash": str(row["password_hash"]),
        "role": str(row["role"]),
        "allowed_subjects": json.loads(str(row["allowed_subjects_json"])),
        "active": bool(row["active"]),
        "created_at": str(row["created_at"]),
    }


def create_session(
    path: str | Path,
    *,
    user_id: int,
    ttl_seconds: int | None = None,
) -> dict[str, str]:
    initialize(path)
    raw_token = generate_session_token()
    token_digest = hash_token(raw_token)
    now_iso = utc_now_iso()
    expires_iso = compute_expiry_iso(ttl_seconds)
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO sessions (token_hash, user_id, created_at, expires_at, revoked_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (token_digest, user_id, now_iso, expires_iso),
        )
    return {
        "access_token": raw_token,
        "token_type": "bearer",
        "expires_at": expires_iso,
    }


def get_active_session(path: str | Path, raw_token: str) -> dict[str, Any] | None:
    if not raw_token:
        return None
    initialize(path)
    token_digest = hash_token(raw_token)
    with _connect(path) as conn:
        row = conn.execute(
            """
            SELECT s.token_hash, s.user_id, s.created_at, s.expires_at, s.revoked_at,
                   u.username, u.role, u.allowed_subjects_json, u.active
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ?
            """,
            (token_digest,),
        ).fetchone()
    if row is None:
        return None
    if row["revoked_at"] is not None or not bool(row["active"]):
        return None
    if is_expired(str(row["expires_at"])):
        return None
    return {
        "user_id": int(row["user_id"]),
        "username": str(row["username"]),
        "role": str(row["role"]),
        "allowed_subjects": json.loads(str(row["allowed_subjects_json"])),
        "expires_at": str(row["expires_at"]),
    }


def revoke_session(path: str | Path, raw_token: str) -> bool:
    if not raw_token:
        return False
    initialize(path)
    token_digest = hash_token(raw_token)
    now_iso = utc_now_iso()
    with _connect(path) as conn:
        cursor = conn.execute(
            "UPDATE sessions SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
            (now_iso, token_digest),
        )
    return cursor.rowcount > 0


def upsert_subject(
    path: str | Path,
    *,
    subject_id: str,
    display_name: str,
    scope: str = "CREW",
    role_label: str = "crew_member",
) -> dict[str, Any]:
    initialize(path)
    clean_id = subject_id.strip()
    if not clean_id:
        raise ValueError("subject_id cannot be blank")
    now_iso = utc_now_iso()
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO subjects (subject_id, display_name, scope, role_label, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(subject_id) DO UPDATE SET
                display_name = excluded.display_name,
                scope = excluded.scope,
                role_label = excluded.role_label
            """,
            (clean_id, display_name.strip(), scope, role_label.strip(), now_iso),
        )
        row = conn.execute(
            "SELECT subject_id, display_name, scope, role_label, created_at FROM subjects WHERE subject_id = ?",
            (clean_id,),
        ).fetchone()
    assert row is not None
    return dict(row)


def get_subject(path: str | Path, subject_id: str) -> dict[str, Any] | None:
    initialize(path)
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT subject_id, display_name, scope, role_label, created_at FROM subjects WHERE subject_id = ?",
            (subject_id.strip(),),
        ).fetchone()
    return dict(row) if row is not None else None
