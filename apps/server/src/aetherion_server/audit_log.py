"""Append-only auditable record change log for engineering observations (Q-0042)."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from .sqlite_compat import connect_sqlite


class AuditLogStore:
    """Logs who changed an observation, why, and its previous/new metadata."""

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
                CREATE TABLE IF NOT EXISTS observation_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_id INTEGER NOT NULL,
                    actor_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    previous_metadata_json TEXT NOT NULL,
                    new_metadata_json TEXT NOT NULL,
                    changed_at_utc TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def record_change(
        self,
        *,
        observation_id: int,
        actor_id: str,
        reason: str,
        previous_metadata: dict[str, Any],
        new_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        if observation_id <= 0:
            raise ValueError("observation_id must be positive")
        actor = actor_id.strip()
        why = reason.strip()
        if not actor:
            raise ValueError("actor_id must be non-empty")
        if not why:
            raise ValueError("reason must be non-empty")
        if not previous_metadata:
            raise ValueError("previous_metadata must be non-empty")

        prev_json = json.dumps(previous_metadata, sort_keys=True)
        new_json = json.dumps(new_metadata, sort_keys=True)
        changed_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO observation_audit_log (
                    observation_id, actor_id, reason, previous_metadata_json, new_metadata_json, changed_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (observation_id, actor, why, prev_json, new_json, changed_at),
            )
            conn.commit()
            row_id = int(cur.lastrowid)

        return {
            "id": row_id,
            "observation_id": observation_id,
            "actor_id": actor,
            "reason": why,
            "previous_metadata": previous_metadata,
            "new_metadata": new_metadata,
            "changed_at_utc": changed_at,
        }

    def list_changes(self, *, observation_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM observation_audit_log WHERE observation_id = ? ORDER BY id ASC",
                (observation_id,),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["previous_metadata"] = json.loads(item.pop("previous_metadata_json"))
            item["new_metadata"] = json.loads(item.pop("new_metadata_json"))
            result.append(item)
        return result
