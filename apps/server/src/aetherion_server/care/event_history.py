"""Subject-scoped care episode transition history & restart persistence (Q-0092)."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from aetherion_server.sqlite_compat import connect_closing
from typing import Any

from aetherion_server.care.episode import CareEpisodeStore


class CareEventHistory:
    """Queries persisted care transitions by episode and subject ID across restarts."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        CareEpisodeStore(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = connect_closing(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def list_subject_transitions(
        self,
        subject_id: str,
        *,
        episode_id: str | None = None,
    ) -> list[dict[str, Any]]:
        sid = subject_id.strip()
        if not sid:
            raise ValueError("subject_id must be non-empty")

        sql = """
            SELECT
                e.event_id,
                e.episode_id,
                ep.subject_id,
                e.phase,
                e.actor_id,
                e.source,
                e.unit,
                e.data_state,
                e.summary,
                e.payload_json,
                e.human_confirmed,
                e.recorded_at_utc
            FROM care_episode_events e
            JOIN care_episodes ep ON ep.episode_id = e.episode_id
            WHERE ep.subject_id = ?
        """
        params: list[Any] = [sid]
        if episode_id is not None:
            eid = episode_id.strip()
            if not eid:
                raise ValueError("episode_id must be non-empty when provided")
            sql += " AND e.episode_id = ?"
            params.append(eid)
        sql += " ORDER BY e.event_id ASC"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "episode_id": row["episode_id"],
                "subject_id": row["subject_id"],
                "phase": row["phase"],
                "actor_id": row["actor_id"],
                "source": row["source"],
                "unit": row["unit"],
                "data_state": row["data_state"],
                "summary": row["summary"],
                "payload": json.loads(row["payload_json"]),
                "human_confirmed": bool(row["human_confirmed"]),
                "recorded_at_utc": row["recorded_at_utc"],
            }
            for row in rows
        ]

    def list_episodes_for_subject(self, subject_id: str) -> list[dict[str, Any]]:
        sid = subject_id.strip()
        if not sid:
            raise ValueError("subject_id must be non-empty")
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT episode_id, subject_id, actor_id, chief_concern, current_phase,
                       ai_assisted, human_confirmed, created_at_utc, updated_at_utc
                FROM care_episodes
                WHERE subject_id = ?
                ORDER BY created_at_utc ASC, episode_id ASC
                """,
                (sid,),
            ).fetchall()
        return [
            {
                "episode_id": r["episode_id"],
                "subject_id": r["subject_id"],
                "actor_id": r["actor_id"],
                "chief_concern": r["chief_concern"],
                "current_phase": r["current_phase"],
                "ai_assisted": bool(r["ai_assisted"]),
                "human_confirmed": bool(r["human_confirmed"]),
                "created_at_utc": r["created_at_utc"],
                "updated_at_utc": r["updated_at_utc"],
            }
            for r in rows
        ]
