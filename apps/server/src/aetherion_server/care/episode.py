"""Stateful GATHER -> EVALUATE -> ACT -> RECHECK care episode domain model (Q-0091)."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from aetherion_server.sqlite_compat import connect_closing
from typing import Any
import uuid

CARE_PHASES = ("GATHER", "EVALUATE", "ACT", "RECHECK", "CLOSED")
ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "GATHER": ("EVALUATE",),
    "EVALUATE": ("ACT",),
    "ACT": ("RECHECK",),
    "RECHECK": ("GATHER", "EVALUATE", "CLOSED"),
    "CLOSED": (),
}
ALLOWED_DATA_STATES = ("READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED")


class CareEpisodeTransitionError(ValueError):
    """Raised when a care episode transition violates GATHER->EVALUATE->ACT->RECHECK ordering."""


def _require_utc_iso(ts: str, field: str) -> str:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{field} must include timezone offset")
    return dt.astimezone(timezone.utc).isoformat()


class CareEpisodeStore:
    """SQLite-backed stateful care episode store enforcing GATHER->EVALUATE->ACT->RECHECK."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = connect_closing(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS care_episodes (
                    episode_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    chief_concern TEXT NOT NULL,
                    current_phase TEXT NOT NULL CHECK(current_phase IN ('GATHER','EVALUATE','ACT','RECHECK','CLOSED')),
                    ai_assisted INTEGER NOT NULL DEFAULT 0,
                    human_confirmed INTEGER NOT NULL DEFAULT 1,
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS care_episode_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    episode_id TEXT NOT NULL REFERENCES care_episodes(episode_id) ON DELETE CASCADE,
                    phase TEXT NOT NULL CHECK(phase IN ('GATHER','EVALUATE','ACT','RECHECK','CLOSED')),
                    actor_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    data_state TEXT NOT NULL CHECK(data_state IN ('READY','NO_DATA','STALE','OFFLINE','DENIED','ERROR','UNVERIFIED')),
                    summary TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    human_confirmed INTEGER NOT NULL DEFAULT 1,
                    recorded_at_utc TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def start_episode(
        self,
        *,
        subject_id: str,
        actor_id: str,
        chief_concern: str,
        source: str,
        unit: str = "episode",
        data_state: str = "READY",
        recorded_at: str | None = None,
        payload: dict[str, Any] | None = None,
        ai_assisted: bool = False,
        human_confirmed: bool = True,
    ) -> dict[str, Any]:
        sid = subject_id.strip()
        aid = actor_id.strip()
        concern = chief_concern.strip()
        src = source.strip()
        if not sid or not aid or not concern or not src:
            raise ValueError("subject_id, actor_id, chief_concern, and source must be non-empty")
        if data_state not in ALLOWED_DATA_STATES:
            raise ValueError(f"Unsupported data_state: {data_state}")
        ts = _require_utc_iso(recorded_at, "recorded_at") if recorded_at else datetime.now(timezone.utc).isoformat()
        episode_id = f"ep-{uuid.uuid4().hex[:12]}"

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO care_episodes (
                    episode_id, subject_id, actor_id, chief_concern, current_phase,
                    ai_assisted, human_confirmed, created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, 'GATHER', ?, ?, ?, ?)
                """,
                (episode_id, sid, aid, concern, int(ai_assisted), int(human_confirmed), ts, ts),
            )
            conn.execute(
                """
                INSERT INTO care_episode_events (
                    episode_id, phase, actor_id, source, unit, data_state,
                    summary, payload_json, human_confirmed, recorded_at_utc
                ) VALUES (?, 'GATHER', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode_id,
                    aid,
                    src,
                    unit.strip() or "episode",
                    data_state,
                    f"Initial GATHER: {concern}",
                    json.dumps(payload or {}, sort_keys=True),
                    int(human_confirmed),
                    ts,
                ),
            )
            conn.commit()
        return self.get_episode(episode_id)

    def advance_phase(
        self,
        episode_id: str,
        *,
        next_phase: str,
        actor_id: str,
        source: str,
        summary: str,
        unit: str = "assessment",
        data_state: str = "READY",
        recorded_at: str | None = None,
        payload: dict[str, Any] | None = None,
        human_confirmed: bool = True,
    ) -> dict[str, Any]:
        if next_phase not in CARE_PHASES:
            raise CareEpisodeTransitionError(f"Unknown care phase: {next_phase}")
        if data_state not in ALLOWED_DATA_STATES:
            raise ValueError(f"Unsupported data_state: {data_state}")
        aid = actor_id.strip()
        src = source.strip()
        summ = summary.strip()
        if not aid or not src or not summ:
            raise ValueError("actor_id, source, and summary must be non-empty")
        if not human_confirmed and next_phase in ("ACT", "CLOSED"):
            raise CareEpisodeTransitionError(f"Human confirmation required to enter {next_phase}")

        ts = _require_utc_iso(recorded_at, "recorded_at") if recorded_at else datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT current_phase FROM care_episodes WHERE episode_id = ?",
                (episode_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown episode_id: {episode_id}")
            current = row["current_phase"]
            if next_phase not in ALLOWED_TRANSITIONS[current]:
                raise CareEpisodeTransitionError(f"Invalid transition {current} -> {next_phase}")

            conn.execute(
                "UPDATE care_episodes SET current_phase = ?, updated_at_utc = ?, human_confirmed = ? WHERE episode_id = ?",
                (next_phase, ts, int(human_confirmed), episode_id),
            )
            conn.execute(
                """
                INSERT INTO care_episode_events (
                    episode_id, phase, actor_id, source, unit, data_state,
                    summary, payload_json, human_confirmed, recorded_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode_id,
                    next_phase,
                    aid,
                    src,
                    unit.strip() or "assessment",
                    data_state,
                    summ,
                    json.dumps(payload or {}, sort_keys=True),
                    int(human_confirmed),
                    ts,
                ),
            )
            conn.commit()
        return self.get_episode(episode_id)

    def get_episode(self, episode_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            ep = conn.execute("SELECT * FROM care_episodes WHERE episode_id = ?", (episode_id,)).fetchone()
            if ep is None:
                raise KeyError(f"Unknown episode_id: {episode_id}")
            events = conn.execute(
                "SELECT * FROM care_episode_events WHERE episode_id = ? ORDER BY event_id ASC",
                (episode_id,),
            ).fetchall()
        return {
            "episode_id": ep["episode_id"],
            "subject_id": ep["subject_id"],
            "actor_id": ep["actor_id"],
            "chief_concern": ep["chief_concern"],
            "current_phase": ep["current_phase"],
            "ai_assisted": bool(ep["ai_assisted"]),
            "human_confirmed": bool(ep["human_confirmed"]),
            "created_at_utc": ep["created_at_utc"],
            "updated_at_utc": ep["updated_at_utc"],
            "events": [
                {
                    "event_id": ev["event_id"],
                    "phase": ev["phase"],
                    "actor_id": ev["actor_id"],
                    "source": ev["source"],
                    "unit": ev["unit"],
                    "data_state": ev["data_state"],
                    "summary": ev["summary"],
                    "payload": json.loads(ev["payload_json"]),
                    "human_confirmed": bool(ev["human_confirmed"]),
                    "recorded_at_utc": ev["recorded_at_utc"],
                }
                for ev in events
            ],
        }
