"""Self-reported health observation store separated from sensor readings (Q-0038)."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from aetherion_server.scope_guard import ENVIRONMENT_METRICS
from aetherion_server.sqlite_compat import connect_sqlite


class SelfReportStore:
    """Persists subjective crew self-reports separately from sensor telemetry."""

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
                CREATE TABLE IF NOT EXISTS self_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    symptom TEXT NOT NULL,
                    severity_scale INTEGER NOT NULL,
                    notes TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    reported_at_utc TEXT NOT NULL,
                    recorded_at_utc TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def record_self_report(
        self,
        *,
        subject_id: str,
        symptom: str,
        severity_scale: int,
        notes: str,
        reported_at: str,
        scope: str = "CREW",
    ) -> dict[str, Any]:
        sid = subject_id.strip()
        if not sid:
            raise ValueError("subject_id must be non-empty")
        if scope != "CREW":
            raise ValueError("Self-reports must use CREW scope")
        sym = symptom.strip()
        if not sym:
            raise ValueError("symptom must be non-empty")
        if sym.lower() in ENVIRONMENT_METRICS:
            raise ValueError(f"Environmental metric '{symptom}' cannot be logged as a crew self-report")
        if not isinstance(severity_scale, int) or severity_scale < 1 or severity_scale > 10:
            raise ValueError("severity_scale must be an integer between 1 and 10")

        dt = datetime.fromisoformat(reported_at)
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("reported_at must include timezone offset")
        reported_utc = dt.astimezone(timezone.utc).isoformat()
        recorded_utc = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO self_reports (
                    subject_id, scope, symptom, severity_scale, notes, source_kind, reported_at_utc, recorded_at_utc
                ) VALUES (?, ?, ?, ?, ?, 'SELF_REPORT', ?, ?)
                """,
                (sid, scope, sym, severity_scale, notes.strip(), reported_utc, recorded_utc),
            )
            conn.commit()
            row_id = cur.lastrowid

        return {
            "id": row_id,
            "subject_id": sid,
            "scope": scope,
            "symptom": sym,
            "severity_scale": severity_scale,
            "notes": notes.strip(),
            "source_kind": "SELF_REPORT",
            "reported_at_utc": reported_utc,
            "recorded_at_utc": recorded_utc,
        }

    def list_self_reports(self, *, subject_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM self_reports WHERE subject_id = ? ORDER BY reported_at_utc ASC, id ASC",
                (subject_id.strip(),),
            ).fetchall()
        return [dict(r) for r in rows]
