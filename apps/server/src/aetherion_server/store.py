"""Local-only engineering observation store; not for patient information."""

from pathlib import Path
import sqlite3
from typing import Any


def initialize(path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_obs_subject_time "
            "ON observations(subject_id, observed_at)"
        )


def add_observation(path: str | Path, item: dict[str, Any]) -> int:
    initialize(path)
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO observations
            (subject_id, metric, value, unit, source, observed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item["subject_id"], item["metric"], item["value"],
                item["unit"], item["source"], item["observed_at"],
            ),
        )
        return int(cursor.lastrowid)


def list_observations(path: str | Path, subject_id: str, limit: int = 100) -> list[dict[str, Any]]:
    initialize(path)
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, subject_id, metric, value, unit, source, observed_at, created_at
            FROM observations WHERE subject_id = ?
            ORDER BY observed_at DESC, id DESC LIMIT ?
            """,
            (subject_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]
