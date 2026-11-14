"""Authorized subject discovery and an optional local mobile-web entrypoint."""
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, Query
from .security import is_subject_authorized
from .store import _connect


def build_client_router(db_path: Callable[[], Path], require_session: Callable) -> APIRouter:
    router = APIRouter(tags=["Client integration"])

    @router.get("/api/v1/subjects")
    def subjects(identity: tuple[dict, str] = Depends(require_session),
                 limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0)):
        session, _ = identity
        with _connect(db_path()) as conn:
            rows = conn.execute("SELECT subject_id, display_name, scope, role_label, created_at FROM subjects ORDER BY display_name, subject_id").fetchall()
        authorized = [dict(row) for row in rows if is_subject_authorized(session["role"], session["allowed_subjects"], row["subject_id"])]
        page = authorized[offset:offset + limit]
        return {"subjects": page, "total": len(authorized), "has_more": offset + len(page) < len(authorized), "next_offset": offset + len(page)}

    return router
