"""AETHERION searchable scientific library and symptom interview API (no second server)."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from . import anatomy_catalog, knowledge_catalog
from .symptom_interview import ai_status, next_question

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge and Symptom Intake"])
_ARTICLE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class IntakeRequest(BaseModel):
    symptoms: list[str] = Field(min_length=1, max_length=20)
    answers: dict[str, str] = Field(default_factory=dict, max_length=50)
    use_ai: bool = False
    allow_cloud: bool = False

    @field_validator("symptoms")
    @classmethod
    def _bound_symptoms(cls, values: list[str]) -> list[str]:
        for item in values:
            if len(item) > 120:
                raise ValueError("Symptom identifier exceeds 120 characters")
        return values

    @field_validator("answers")
    @classmethod
    def _bound_answers(cls, values: dict[str, str]) -> dict[str, str]:
        if len(values) > 50:
            raise ValueError("Too many answer entries")
        for key, val in values.items():
            if len(key) > 64 or len(val) > 64:
                raise ValueError("Answer key/value exceeds 64 characters")
        return values


@router.get("/status")
def get_status():
    return knowledge_catalog.status()


@router.get("/articles")
def search_articles(query: str = Query("", max_length=200),
                    limit: int = Query(30, ge=1, le=100),
                    category: str = Query("", max_length=100)):
    return knowledge_catalog.articles(query, limit, category)


@router.get("/articles/{article_id}")
def get_article(article_id: str):
    if not _ARTICLE_ID_RE.fullmatch(article_id):
        raise HTTPException(404, "Article unavailable or invalid ID")
    result = knowledge_catalog.article(article_id)
    if result is None:
        raise HTTPException(404, "Article unavailable or invalid ID")
    return result


@router.get("/symptoms")
def search_symptoms(query: str = Query("", max_length=200),
                    route: str = Query("", max_length=80),
                    limit: int = Query(30, ge=1, le=100)):
    return knowledge_catalog.symptoms(query, limit, route)


@router.get("/interview/ai-status")
def get_ai_status():
    # Never return API keys or environment variable content.
    return ai_status()


@router.post("/interview/next")
def interview_next(req: IntakeRequest):
    # Stateless: does not persist symptoms or forward them to cloud by default.
    # An actual model is invoked only when explicitly requested/configured.
    return next_question(req.symptoms, req.answers,
                         use_ai=req.use_ai, allow_cloud=req.allow_cloud)


@router.get("/anatomy/models")
def list_anatomy_models():
    return anatomy_catalog.list_approved_models()


@router.get("/anatomy/models/{anatomical_id}/file")
def get_anatomy_model_file(anatomical_id: str):
    resolved = anatomy_catalog.resolve_approved_model_file(anatomical_id)
    if resolved is None:
        raise HTTPException(404, "Approved anatomical model unavailable")
    mesh_path, meta = resolved
    return FileResponse(
        path=mesh_path,
        media_type=meta["content_type"],
        filename=meta["filename"],
        headers={
            "ETag": f'"{meta["sha256"]}"',
            "X-Content-Sha256": meta["sha256"],
        },
    )
