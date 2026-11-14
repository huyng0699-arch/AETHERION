"""Cabin and vehicle environmental data store separated from personal health metrics (Q-0039)."""

from datetime import datetime, timezone
import math
from pathlib import Path
import sqlite3
from aetherion_server.sqlite_compat import connect_closing
from typing import Any

from aetherion_server.scope_guard import ENVIRONMENT_SCOPES, validate_metric_scope
from aetherion_server.unit_validator import validate_metric_range, validate_metric_unit


class EnvironmentStore:
    """Persists cabin/vehicle environmental metrics separately from crew personal health."""

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
                CREATE TABLE IF NOT EXISTS environment_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    observed_at_utc TEXT NOT NULL,
                    recorded_at_utc TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def record_environment_metric(
        self,
        *,
        subject_id: str,
        scope: str,
        metric: str,
        value: float,
        unit: str,
        source_id: str,
        observed_at: str,
    ) -> dict[str, Any]:
        sid = subject_id.strip()
        if not sid:
            raise ValueError("subject_id must be non-empty")
        if scope not in ENVIRONMENT_SCOPES:
            raise ValueError(f"EnvironmentStore requires CABIN, VEHICLE, or habitat scope; got {scope!r}")
        if not math.isfinite(float(value)):
            raise ValueError("value must be finite")
        validate_metric_scope(metric, scope)
        validate_metric_unit(metric, unit)
        validate_metric_range(metric, float(value), unit)
        dt = datetime.fromisoformat(observed_at)
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("observed_at must include timezone offset")
        observed_utc = dt.astimezone(timezone.utc).isoformat()
        recorded_utc = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO environment_observations (
                    subject_id, scope, metric, value, unit, source_id, observed_at_utc, recorded_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sid, scope, metric.strip(), float(value), unit.strip(), source_id.strip(), observed_utc, recorded_utc),
            )
            conn.commit()
            row_id = cur.lastrowid

        return {
            "id": row_id,
            "subject_id": sid,
            "scope": scope,
            "metric": metric.strip(),
            "value": float(value),
            "unit": unit.strip(),
            "source_id": source_id.strip(),
            "observed_at_utc": observed_utc,
            "recorded_at_utc": recorded_utc,
        }

    def list_environment_metrics(self, *, subject_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM environment_observations WHERE subject_id = ? ORDER BY observed_at_utc ASC, id ASC",
                (subject_id.strip(),),
            ).fetchall()
        return [dict(r) for r in rows]
