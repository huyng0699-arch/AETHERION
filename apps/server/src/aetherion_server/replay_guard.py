"""Idempotent event replay and duplicate alert control (Q-0040)."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


@dataclass(frozen=True)
class ReplayOutcome:
    event_uid: str
    stream_name: str
    replayed: bool
    alert_emitted: bool
    row_id: int


class EventReplayGuard:
    """Prevents duplicate rows and duplicate alerts when events are replayed."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream_name TEXT NOT NULL,
                    event_uid TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    alert_emitted INTEGER NOT NULL,
                    processed_at_utc TEXT NOT NULL,
                    UNIQUE(stream_name, event_uid)
                )
                """
            )
            conn.commit()

    def process_event(
        self,
        *,
        stream_name: str,
        event_uid: str,
        payload: dict[str, Any],
        emit_alert: bool,
    ) -> ReplayOutcome:
        stream = stream_name.strip()
        uid = event_uid.strip()
        if not stream or not uid:
            raise ValueError("stream_name and event_uid must be non-empty")

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        now_utc = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id, payload_sha256 FROM processed_events WHERE stream_name = ? AND event_uid = ?",
                (stream, uid),
            ).fetchone()
            if existing is not None:
                if existing["payload_sha256"] != payload_hash:
                    raise ValueError(
                        f"Conflicting replay for ({stream}, {uid}): payload hash mismatch"
                    )
                return ReplayOutcome(
                    event_uid=uid,
                    stream_name=stream,
                    replayed=True,
                    alert_emitted=False,
                    row_id=int(existing["id"]),
                )

            cur = conn.execute(
                """
                INSERT INTO processed_events (
                    stream_name, event_uid, payload_sha256, alert_emitted, processed_at_utc
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (stream, uid, payload_hash, 1 if emit_alert else 0, now_utc),
            )
            conn.commit()
            return ReplayOutcome(
                event_uid=uid,
                stream_name=stream,
                replayed=False,
                alert_emitted=bool(emit_alert),
                row_id=int(cur.lastrowid),
            )

    def count_events(self, *, stream_name: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM processed_events WHERE stream_name = ?",
                (stream_name.strip(),),
            ).fetchone()
        return int(row["cnt"])
