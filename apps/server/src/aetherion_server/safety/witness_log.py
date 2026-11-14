"""Direct witness incident logging store for witnessed nonresponse (Q-0167)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from aetherion_server.sqlite_compat import connect_closing
from typing import Any
import uuid

ALLOWED_TELEMETRY_STATES = ("READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED")


def _require_utc_iso(ts: str, field: str) -> str:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{field} must include timezone offset")
    return dt.astimezone(timezone.utc).isoformat()


class WitnessIncidentStore:
    """Persists crew-witnessed nonresponse incidents with explicit source and provenance."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = connect_closing(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS witness_incidents (
                    incident_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    witness_id TEXT NOT NULL,
                    location TEXT NOT NULL,
                    circumstances TEXT NOT NULL,
                    source TEXT NOT NULL,
                    telemetry_state TEXT NOT NULL CHECK(telemetry_state IN ('READY','NO_DATA','STALE','OFFLINE','DENIED','ERROR','UNVERIFIED')),
                    response_status TEXT NOT NULL,
                    observed_at_utc TEXT NOT NULL,
                    recorded_at_utc TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def log_witnessed_nonresponse(
        self,
        *,
        subject_id: str,
        witness_id: str,
        observed_at: str,
        circumstances: str,
        location: str = "UNSPECIFIED",
        telemetry_state: str = "NO_DATA",
    ) -> dict[str, Any]:
        sid = subject_id.strip()
        wid = witness_id.strip()
        circ = circumstances.strip()
        loc = location.strip() or "UNSPECIFIED"
        if not sid or not wid or not circ:
            raise ValueError("subject_id, witness_id, and circumstances must be non-empty")
        if sid == wid:
            raise ValueError("witness_id cannot equal subject_id for a witnessed nonresponse report")
        if telemetry_state not in ALLOWED_TELEMETRY_STATES:
            raise ValueError(f"Unsupported telemetry_state: {telemetry_state}")
        obs_utc = _require_utc_iso(observed_at, "observed_at")
        rec_utc = datetime.now(timezone.utc).isoformat()
        inc_id = f"wit-{uuid.uuid4().hex[:12]}"

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO witness_incidents (
                    incident_id, subject_id, witness_id, location, circumstances,
                    source, telemetry_state, response_status, observed_at_utc, recorded_at_utc
                ) VALUES (?, ?, ?, ?, ?, 'WITNESS_REPORT', ?, 'LOGGED_WITNESS_REPORT', ?, ?)
                """,
                (inc_id, sid, wid, loc, circ, telemetry_state, obs_utc, rec_utc),
            )
            conn.commit()
        return self.get_incident(inc_id)

    def get_incident(self, incident_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM witness_incidents WHERE incident_id = ?", (incident_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown incident_id: {incident_id}")
        return {
            "incident_id": row["incident_id"],
            "subject_id": row["subject_id"],
            "witness_id": row["witness_id"],
            "location": row["location"],
            "circumstances": row["circumstances"],
            "source": row["source"],
            "telemetry_state": row["telemetry_state"],
            "response_status": row["response_status"],
            "observed_at_utc": row["observed_at_utc"],
            "recorded_at_utc": row["recorded_at_utc"],
        }

    def list_incidents(self, *, subject_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT incident_id FROM witness_incidents"
        params: list[Any] = []
        if subject_id is not None:
            sid = subject_id.strip()
            if not sid:
                raise ValueError("subject_id must be non-empty when provided")
            sql += " WHERE subject_id = ?"
            params.append(sid)
        sql += " ORDER BY observed_at_utc DESC, incident_id DESC"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self.get_incident(r["incident_id"]) for r in rows]
