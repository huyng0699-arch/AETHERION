"""Authenticated Server Admin control plane for the existing FastAPI app."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

from .admin_control import (
    backup_sqlite, probe_local_ai, test_local_model, read_ai_settings, recent_admin_events,
    save_ai_settings, system_overview, list_observed_sources, list_admin_users,
)


class AISettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["off", "local_only"] = "off"
    local_runtime: Literal["ollama"] = "ollama"
    local_url: str = Field(default="http://127.0.0.1:11434", max_length=140)
    local_model: str = Field(default="", max_length=120)
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    cloud_data_sharing: Literal[False] = False


def build_admin_router(
    database_path: Callable[[], Path],
    require_session: Callable,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/admin", tags=["server-admin"])

    def require_admin(session_and_token: tuple[dict, str] = Depends(require_session)) -> dict:
        session, _token = session_and_token
        if session.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Server administrator role required")
        return session

    @router.get("/overview")
    def overview(_admin: dict = Depends(require_admin)):
        return system_overview(database_path())

    @router.get("/ai/settings")
    def ai_settings(_admin: dict = Depends(require_admin)):
        return {"settings": read_ai_settings(database_path()),
                "cloud_provider": "NOT_IMPLEMENTED", "secrets_stored": False}

    @router.put("/ai/settings")
    def update_ai_settings(payload: AISettingsIn, admin: dict = Depends(require_admin)):
        try:
            saved = save_ai_settings(database_path(), payload.model_dump(), actor=admin["username"])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"settings": saved}

    @router.get("/ai/local/models")
    def local_models(_admin: dict = Depends(require_admin)):
        return probe_local_ai(read_ai_settings(database_path()))

    @router.post("/ai/local/test")
    def local_model_test(_admin: dict = Depends(require_admin)):
        return test_local_model(read_ai_settings(database_path()))

    @router.get("/sources")
    def observed_sources(_admin: dict = Depends(require_admin)):
        return list_observed_sources(database_path())

    @router.get("/users")
    def admin_users(_admin: dict = Depends(require_admin)):
        return list_admin_users(database_path())

    @router.get("/events")
    def events(_admin: dict = Depends(require_admin)):
        return {"events": recent_admin_events(database_path())}

    @router.post("/storage/backup")
    def backup(admin: dict = Depends(require_admin)):
        try:
            return backup_sqlite(database_path(), actor=admin["username"])
        except (OSError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail="Backup failed or storage unavailable") from exc

    return router
