"""AETHERION searchable scientific library and symptom interview API (no second server)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from . import knowledge_catalog
from .symptom_interview import ai_status, next_question

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge and Symptom Intake"])


class IntakeRequest(BaseModel):
    symptoms: list[str] = Field(min_length=1, max_length=20)
    answers: dict[str, str] = Field(default_factory=dict)
    use_ai: bool = False
    allow_cloud: bool = False


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
