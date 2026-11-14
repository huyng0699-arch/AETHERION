"""Consented symptom-interview episode persistence with subject isolation and audit trail (Q-0447)."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
import uuid


class ConsentRequiredError(PermissionError):
    """Raised when persistence is attempted without explicit user consent or auth."""


class SubjectIsolationError(PermissionError):
    """Raised when a caller attempts to read another subject's interview episodes."""


class ConsentedInterviewStore:
    """SQLite-backed store for explicitly consented symptom-interview episodes."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS consented_interview_episodes (
                    episode_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    consent_granted INTEGER NOT NULL CHECK(consent_granted = 1),
                    consent_recorded_utc TEXT NOT NULL,
                    symptoms_json TEXT NOT NULL,
                    answers_provenance_json TEXT NOT NULL,
                    interview_state TEXT NOT NULL,
                    cloud_exported INTEGER NOT NULL DEFAULT 0 CHECK(cloud_exported = 0),
                    created_utc TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS interview_persistence_audit (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    episode_id TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    details_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_interview_subject
                    ON consented_interview_episodes(subject_id, created_utc);
                """
            )

    def save_consented_episode(
        self,
        *,
        subject_id: str,
        actor_id: str,
        consent_granted: bool,
        symptoms: list[str],
        answers_with_provenance: list[dict[str, str]],
        interview_state: str,
        cloud_exported: bool = False,
    ) -> dict[str, Any]:
        """Persist an interview episode ONLY when explicit consent and authenticated actor exist."""
        if not consent_granted:
            raise ConsentRequiredError("Explicit user consent is required to persist an interview episode.")
        if not actor_id.strip() or not subject_id.strip():
            raise ConsentRequiredError("Authenticated actor_id and subject_id are required.")
        if cloud_exported:
            raise ValueError("Covert or automatic cloud export of persisted interview episodes is prohibited.")

        now_utc = datetime.now(timezone.utc).isoformat()
        episode_id = f"INT-{uuid.uuid4().hex[:12]}"
        normalized_answers = []
        for item in answers_with_provenance:
            qid = str(item.get("question_id", "")).strip()
            val = str(item.get("answer", "")).strip()
            ts = str(item.get("recorded_at_utc", now_utc)).strip()
            if not qid or not val:
                raise ValueError("Each persisted answer must include question_id and answer.")
            normalized_answers.append(
                {
                    "question_id": qid,
                    "answer": val,
                    "recorded_at_utc": ts,
                    "source_actor_id": actor_id.strip(),
                }
            )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO consented_interview_episodes (
                    episode_id, subject_id, actor_id, consent_granted, consent_recorded_utc,
                    symptoms_json, answers_provenance_json, interview_state, cloud_exported, created_utc
                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, 0, ?)
                """,
                (
                    episode_id,
                    subject_id.strip(),
                    actor_id.strip(),
                    now_utc,
                    json.dumps(list(symptoms), ensure_ascii=False),
                    json.dumps(normalized_answers, ensure_ascii=False),
                    interview_state.strip(),
                    now_utc,
                ),
            )
            conn.execute(
                """
                INSERT INTO interview_persistence_audit (
                    episode_id, subject_id, actor_id, action, timestamp_utc, details_json
                ) VALUES (?, ?, ?, 'PERSIST_CONSENTED_INTERVIEW', ?, ?)
                """,
                (
                    episode_id,
                    subject_id.strip(),
                    actor_id.strip(),
                    now_utc,
                    json.dumps({"answer_count": len(normalized_answers), "cloud_exported": False}),
                ),
            )
        return {
            "episode_id": episode_id,
            "subject_id": subject_id.strip(),
            "actor_id": actor_id.strip(),
            "consent_granted": True,
            "cloud_exported": False,
            "created_utc": now_utc,
        }

    def list_subject_episodes(
        self,
        *,
        subject_id: str,
        requesting_subject_id: str,
        is_clinician_authorized: bool = False,
    ) -> list[dict[str, Any]]:
        """Read persisted interview episodes with strict subject isolation."""
        if not is_clinician_authorized and subject_id.strip() != requesting_subject_id.strip():
            raise SubjectIsolationError("Cross-subject interview access denied.")
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT episode_id, subject_id, actor_id, consent_granted, consent_recorded_utc,
                       symptoms_json, answers_provenance_json, interview_state, cloud_exported, created_utc
                FROM consented_interview_episodes
                WHERE subject_id = ?
                ORDER BY created_utc ASC
                """,
                (subject_id.strip(),),
            ).fetchall()
        return [
            {
                "episode_id": r["episode_id"],
                "subject_id": r["subject_id"],
                "actor_id": r["actor_id"],
                "consent_granted": bool(r["consent_granted"]),
                "consent_recorded_utc": r["consent_recorded_utc"],
                "symptoms": json.loads(r["symptoms_json"]),
                "answers_with_provenance": json.loads(r["answers_provenance_json"]),
                "interview_state": r["interview_state"],
                "cloud_exported": bool(r["cloud_exported"]),
                "created_utc": r["created_utc"],
            }
            for r in rows
        ]

    def list_audit_events(self, episode_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT audit_id, episode_id, subject_id, actor_id, action, timestamp_utc, details_json
                FROM interview_persistence_audit
                WHERE episode_id = ?
                ORDER BY audit_id ASC
                """,
                (episode_id,),
            ).fetchall()
        return [dict(r) for r in rows]
