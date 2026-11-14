"""Need Help Now deterministic assistance request store (Q-0166)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any
import uuid

from ..sqlite_compat import connect_sqlite

ALLOWED_TELEMETRY_STATES = ("READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED")


def _require_utc_iso(ts: str, field: str) -> str:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{field} must include timezone offset")
    return dt.astimezone(timezone.utc).isoformat()


class AssistanceRequestStore:
    """Persists Need Help Now requests deterministically, independent of optional AI."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.db_path, row_factory=sqlite3.Row)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assistance_requests (
                    request_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    location TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    source TEXT NOT NULL,
                    telemetry_state TEXT NOT NULL CHECK(telemetry_state IN ('READY','NO_DATA','STALE','OFFLINE','DENIED','ERROR','UNVERIFIED')),
                    ai_enabled INTEGER NOT NULL DEFAULT 0,
                    response_status TEXT NOT NULL,
                    responder_id TEXT,
                    requested_at_utc TEXT NOT NULL,
                    acknowledged_at_utc TEXT
                )
                """
            )
            conn.commit()

    def request_help(
        self,
        *,
        subject_id: str,
        actor_id: str,
        reason: str,
        location: str = "UNSPECIFIED",
        telemetry_state: str = "NO_DATA",
        ai_enabled: bool = False,
        requested_at: str | None = None,
    ) -> dict[str, Any]:
        sid = subject_id.strip()
        aid = actor_id.strip()
        rsn = reason.strip()
        loc = location.strip() or "UNSPECIFIED"
        if not sid or not aid or not rsn:
            raise ValueError("subject_id, actor_id, and reason must be non-empty")
        if telemetry_state not in ALLOWED_TELEMETRY_STATES:
            raise ValueError(f"Unsupported telemetry_state: {telemetry_state}")
        ts = _require_utc_iso(requested_at, "requested_at") if requested_at else datetime.now(timezone.utc).isoformat()
        req_id = f"help-{uuid.uuid4().hex[:12]}"

        # Never fabricate emergency response confirmation; log as pending acknowledgement.
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assistance_requests (
                    request_id, subject_id, actor_id, location, reason, source,
                    telemetry_state, ai_enabled, response_status, responder_id,
                    requested_at_utc, acknowledged_at_utc
                ) VALUES (?, ?, ?, ?, ?, 'USER_ACTION', ?, ?, 'LOGGED_LOCAL_PENDING_ACK', NULL, ?, NULL)
                """,
                (req_id, sid, aid, loc, rsn, telemetry_state, int(ai_enabled), ts),
            )
            conn.commit()
        return self.get_request(req_id)

    def acknowledge_request(
        self,
        request_id: str,
        *,
        responder_id: str,
        acknowledged_at: str | None = None,
    ) -> dict[str, Any]:
        rid = responder_id.strip()
        if not rid:
            raise ValueError("responder_id must be non-empty")
        ts = _require_utc_iso(acknowledged_at, "acknowledged_at") if acknowledged_at else datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE assistance_requests
                SET response_status = 'ACKNOWLEDGED_BY_CREW',
                    responder_id = ?,
                    acknowledged_at_utc = ?
                WHERE request_id = ?
                """,
                (rid, ts, request_id),
            )
            if cur.rowcount == 0:
                raise KeyError(f"Unknown request_id: {request_id}")
            conn.commit()
        return self.get_request(request_id)

    def get_request(self, request_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM assistance_requests WHERE request_id = ?", (request_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown request_id: {request_id}")
        return {
            "request_id": row["request_id"],
            "subject_id": row["subject_id"],
            "actor_id": row["actor_id"],
            "location": row["location"],
            "reason": row["reason"],
            "source": row["source"],
            "telemetry_state": row["telemetry_state"],
            "ai_enabled": bool(row["ai_enabled"]),
            "response_status": row["response_status"],
            "responder_id": row["responder_id"],
            "requested_at_utc": row["requested_at_utc"],
            "acknowledged_at_utc": row["acknowledged_at_utc"],
        }

    def list_requests(self, *, subject_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT request_id FROM assistance_requests"
        params: list[Any] = []
        if subject_id is not None:
            sid = subject_id.strip()
            if not sid:
                raise ValueError("subject_id must be non-empty when provided")
            sql += " WHERE subject_id = ?"
            params.append(sid)
        sql += " ORDER BY requested_at_utc DESC, request_id DESC"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self.get_request(r["request_id"]) for r in rows]
