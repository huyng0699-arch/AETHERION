"""Authenticated, subject-scoped Care journal API on the single AETHERION SQLite store.

Self-reports are UNVERIFIED, not diagnoses. No model may mark human actions done.
Routes deliberately use the existing session dependency rather than a second auth layer.
"""
from __future__ import annotations

import sqlite3
from aetherion_server.sqlite_compat import connect_closing
from pathlib import Path
from typing import Callable, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..security import is_subject_authorized
from ..store import get_subject
from .episode import CareEpisodeStore, CareEpisodeTransitionError


class BeginCare(BaseModel):
    subject_id: str = Field(min_length=1, max_length=80)
    chief_concern: str = Field(min_length=1, max_length=500)
    symptom_terms: list[str] = Field(default_factory=list, max_length=20)
    interview_answers: dict[str, str] = Field(default_factory=dict)
    explicit_consent: bool = False


class CareTransition(BaseModel):
    next_phase: Literal["EVALUATE", "ACT", "RECHECK", "GATHER", "CLOSED"]
    summary: str = Field(min_length=1, max_length=1000)
    action_status: Literal["DONE", "NOT_DONE", "CANNOT_DO"] | None = None
    outcome: Literal["BETTER", "UNCHANGED", "WORSE", "UNKNOWN"] | None = None
    human_confirmed: bool = False


def build_care_router(
    db_path: Callable[[], Path],
    require_session: Callable,
) -> APIRouter:
    """Build routes inside create_app so they reuse its authentication and database."""

    router = APIRouter(prefix="/api/v1/care", tags=["Care Journal"])

    def authorized_subject(session: dict, subject_id: str) -> str:
        subject_id = subject_id.strip()
        if not subject_id or not is_subject_authorized(
            session["role"], session["allowed_subjects"], subject_id
        ):
            raise HTTPException(status_code=403, detail="Subject not authorized")
        if get_subject(db_path(), subject_id) is None:
            raise HTTPException(status_code=404, detail="Subject not found")
        return subject_id

    def scoped_episode(session: dict, episode_id: str) -> tuple[CareEpisodeStore, dict]:
        # No episode content is disclosed before the subject permission gate.
        store = CareEpisodeStore(db_path())
        try:
            episode = store.get_episode(episode_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Care episode unavailable") from exc
        if not is_subject_authorized(
            session["role"], session["allowed_subjects"], episode["subject_id"]
        ):
            raise HTTPException(status_code=404, detail="Care episode unavailable")
        return store, episode

    @router.post("/episodes", status_code=201)
    def start_episode(
        item: BeginCare,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        subject_id = authorized_subject(session, item.subject_id)
        if item.explicit_consent is not True:
            raise HTTPException(status_code=422, detail="Explicit user consent is required")
        if not item.chief_concern.strip():
            raise HTTPException(status_code=422, detail="Concern must not be blank")
        if any(not x.strip() or len(x) > 120 for x in item.symptom_terms):
            raise HTTPException(status_code=422, detail="Invalid symptom term")
        if len(item.interview_answers) > 32 or any(
            len(k) > 80 or len(v) > 80 for k, v in item.interview_answers.items()
        ):
            raise HTTPException(status_code=422, detail="Interview answers exceed limits")
        store = CareEpisodeStore(db_path())
        episode = store.start_episode(
            subject_id=subject_id,
            actor_id=session["username"],
            chief_concern=item.chief_concern,
            source="explicit_user_report",
            data_state="UNVERIFIED",
            human_confirmed=True,
            ai_assisted=False,
            payload={
                "symptom_terms": item.symptom_terms,
                "interview_answers": item.interview_answers,
                "evidence_state": "SELF_REPORTED",
                "clinical_assessment": "NOT_ASSESSED",
            },
        )
        return {"episode": episode, "clinical_assessment": "NOT_ASSESSED"}

    @router.get("/episodes")
    def list_episodes(
        subject_id: str = Query(min_length=1, max_length=80),
        limit: int = Query(30, ge=1, le=100),
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        authorized_subject(session, subject_id)
        # Same canonical database as observations; only subject-owned rows returned.
        with connect_closing(db_path()) as connection:
            rows = connection.execute(
                "SELECT episode_id FROM care_episodes WHERE subject_id = ? "
                "ORDER BY updated_at_utc DESC, episode_id DESC LIMIT ?",
                (subject_id, limit),
            ).fetchall() if _has_care_table(connection) else []
        store = CareEpisodeStore(db_path())
        return {"subject_id": subject_id, "episodes": [
            store.get_episode(row[0]) for row in rows
        ]}

    @router.get("/episodes/{episode_id}")
    def read_episode(
        episode_id: str,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        _, episode = scoped_episode(session, episode_id)
        return {"episode": episode}

    @router.post("/episodes/{episode_id}/advance")
    def advance_episode(
        episode_id: str,
        item: CareTransition,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        store, old = scoped_episode(session, episode_id)
        if item.human_confirmed is not True:
            raise HTTPException(status_code=422, detail="Human confirmation required")
        if item.next_phase == "ACT" and item.action_status is None:
            raise HTTPException(status_code=422, detail="Action status required")
        if item.next_phase == "RECHECK" and item.outcome is None:
            raise HTTPException(status_code=422, detail="Recheck outcome required")
        if item.next_phase != "ACT" and item.action_status is not None:
            raise HTTPException(status_code=422, detail="Action status only belongs to ACT")
        if item.next_phase != "RECHECK" and item.outcome is not None:
            raise HTTPException(status_code=422, detail="Outcome only belongs to RECHECK")
        payload = {
            "clinical_assessment": "NOT_ASSESSED",
            "user_action_status": item.action_status,
            "user_reported_outcome": item.outcome,
            "previous_phase": old["current_phase"],
        }
        try:
            new = store.advance_phase(
                episode_id,
                next_phase=item.next_phase,
                actor_id=session["username"],
                source="human_confirmed_care_journal",
                summary=item.summary,
                unit="care_event",
                data_state="UNVERIFIED",
                payload=payload,
                human_confirmed=True,
            )
        except (CareEpisodeTransitionError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"episode": new, "clinical_assessment": "NOT_ASSESSED"}

    return router


def _has_care_table(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='care_episodes'"
    ).fetchone() is not None
