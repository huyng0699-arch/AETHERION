"""Local-first AETHERION HTTP server with provenance persistence and session auth."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
import math
import os
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator, model_validator

from .availability import compute_availability
from .bootstrap import bootstrap_from_env, default_database_path
from .runtime_config import read_runtime_config
from .scope_guard import validate_metric_scope
from .security import DEFAULT_SESSION_TTL_SECONDS, is_subject_authorized, verify_password
from .unit_validator import validate_metric_range, validate_metric_unit
from .store import (
    check_readiness,
    create_session,
    get_active_session,
    get_subject,
    get_user_by_username,
    ingest_observation,
    initialize,
    query_observations,
    query_observations_page,
    revoke_session,
    upsert_subject,
)

AllowedScope = Literal["CREW", "CABIN", "VEHICLE", "crew", "habitat", "personal", "engineering_test"]
AllowedQuality = Literal["READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"]
AllowedVerificationState = Literal["UNVERIFIED", "SELF_REPORTED", "DEVICE_UNVERIFIED", "TEST_FIXTURE"]

_bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class SubjectIn(BaseModel):
    subject_id: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    scope: AllowedScope = "CREW"
    role_label: str = Field(default="crew_member", min_length=1, max_length=60)

    @field_validator("subject_id")
    @classmethod
    def reject_permission_wildcard(cls, value: str) -> str:
        if value.strip() == "*":
            raise ValueError("The permission wildcard is not a subject identifier")
        return value

    @field_validator("subject_id", "display_name", "role_label")
    @classmethod
    def require_non_blank_subject(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank")
        return stripped


class ObservationIn(BaseModel):
    subject_id: str = Field(min_length=1, max_length=80)
    scope: AllowedScope = "crew"
    metric: str = Field(min_length=1, max_length=80)
    value: float
    unit: str = Field(min_length=1, max_length=40)
    source_id: str | None = Field(default=None, min_length=1, max_length=120)
    source: str | None = Field(default=None, min_length=1, max_length=120)
    observed_at: datetime
    quality: AllowedQuality = "UNVERIFIED"
    verification_state: AllowedVerificationState = "UNVERIFIED"
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("subject_id", "metric", "unit")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank")
        return stripped

    @field_validator("value")
    @classmethod
    def require_finite_value(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("value must be a finite number")
        return value

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a time-zone offset")
        return value

    @model_validator(mode="after")
    def require_source_identifier(self) -> "ObservationIn":
        resolved = (self.source_id or self.source or "").strip()
        if not resolved:
            raise ValueError("source_id or source is required")
        self.source_id = resolved
        self.source = (self.source or resolved).strip()
        validate_metric_scope(self.metric, self.scope)
        validate_metric_unit(self.metric, self.unit)
        validate_metric_range(self.metric, self.value, self.unit)
        return self


def database_path() -> Path:
    return default_database_path()


def _resolve_session_ttl(override: int | None) -> int:
    if override is not None:
        return override
    raw = os.environ.get("AETHERION_SESSION_TTL_SECONDS")
    if raw:
        try:
            parsed = int(raw)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return DEFAULT_SESSION_TTL_SECONDS


def create_app(
    db_path: str | Path | None = None,
    *,
    session_ttl_seconds: int | None = None,
) -> FastAPI:
    # Fail before the HTTP listener opens, including direct 'uvicorn ...:app' usage.
    read_runtime_config()

    def get_db_path() -> Path:
        return Path(db_path) if db_path is not None else default_database_path()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        target = get_db_path()
        initialize(target)
        bootstrap_from_env(target)
        yield

    application = FastAPI(
        title="AETHERION API",
        description="Local-first health data foundation; not clinical decision support",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Development-only Expo Web origins. Disabled by default and never wildcarded.
    if os.environ.get("AETHERION_ENABLE_DEV_CORS", "").strip() == "1":
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:8081", "http://127.0.0.1:8081"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
            expose_headers=["X-Request-Id"],
            max_age=600,
        )

    # One database factory for auth, observations, admin and interview AI routing.
    application.state.admin_database_path = get_db_path

    _status_codes = {
        401: ("UNAUTHORIZED", "Authenticate via POST /api/v1/auth/login and provide a valid Bearer token."),
        403: ("FORBIDDEN", "Use an account authorized for the requested subject_id."),
        404: ("NOT_FOUND", "Verify the requested resource identifier exists."),
        422: ("VALIDATION_ERROR", "Fix the invalid request fields shown in detail and retry."),
        503: ("SERVICE_UNAVAILABLE", "Check database readiness via GET /ready and retry."),
    }

    @application.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        code, action = _status_codes.get(
            exc.status_code,
            ("HTTP_ERROR", "Check request parameters and server status."),
        )
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={
                "error": {
                    "code": code,
                    "status": exc.status_code,
                    "message": str(exc.detail),
                    "action": action,
                },
                "detail": exc.detail,
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = jsonable_encoder(exc.errors(), custom_encoder={Exception: str})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "status": 422,
                    "message": "Request validation failed",
                    "action": "Fix the invalid request fields shown in detail and retry.",
                },
                "detail": errors,
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "status": 500,
                    "message": "Internal server error",
                    "action": "Retry the request or inspect local server logs.",
                },
                "detail": "Internal server error",
            },
        )

    def require_session(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    ) -> tuple[dict, str]:
        if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = credentials.credentials
        session = get_active_session(get_db_path(), token)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or revoked session token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return session, token

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"service": "aetherion-server", "status": "ok"}

    @application.get("/ready")
    def ready() -> dict[str, str]:
        try:
            info = check_readiness(get_db_path())
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database not ready: {exc}",
            ) from exc
        return {"service": "aetherion-server", "status": "ready", "database": info["database"]}

    @application.post("/api/v1/auth/login")
    def login(payload: LoginRequest):
        target = get_db_path()
        initialize(target)
        bootstrap_from_env(target)
        user = get_user_by_username(target, payload.username.strip())
        if user is None or not user["active"] or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        ttl = _resolve_session_ttl(session_ttl_seconds)
        token_info = create_session(target, user_id=user["id"], ttl_seconds=ttl)
        return {
            **token_info,
            "user": {
                "username": user["username"],
                "role": user["role"],
                "allowed_subjects": user["allowed_subjects"],
            },
        }

    @application.post("/api/v1/auth/logout")
    def logout(session_and_token: tuple[dict, str] = Depends(require_session)):
        _, token = session_and_token
        revoke_session(get_db_path(), token)
        return {"status": "logged_out"}

    @application.get("/api/v1/auth/me")
    def auth_me(session_and_token: tuple[dict, str] = Depends(require_session)):
        session, _ = session_and_token
        return {
            "username": session["username"],
            "role": session["role"],
            "allowed_subjects": session["allowed_subjects"],
            "expires_at": session["expires_at"],
        }

    @application.post("/api/v1/subjects", status_code=status.HTTP_201_CREATED)
    def register_subject(
        payload: SubjectIn,
        session_and_token: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = session_and_token
        if not is_subject_authorized(session["role"], session["allowed_subjects"], payload.subject_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to register subject '{payload.subject_id}'",
            )
        subject = upsert_subject(
            get_db_path(),
            subject_id=payload.subject_id,
            display_name=payload.display_name,
            scope=payload.scope,
            role_label=payload.role_label,
        )
        return {"subject": subject}

    @application.get("/api/v1/subjects/{subject_id}")
    def read_subject(
        subject_id: str,
        session_and_token: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = session_and_token
        if not is_subject_authorized(session["role"], session["allowed_subjects"], subject_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access subject '{subject_id}'",
            )
        subject = get_subject(get_db_path(), subject_id)
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject '{subject_id}' not found",
            )
        return {"subject": subject}

    @application.get("/api/v1/subjects/{subject_id}/summary")
    def subject_summary(
        subject_id: str,
        stale_after_seconds: int = Query(3600, ge=1, le=2_592_000),
        session_and_token: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = session_and_token
        if not is_subject_authorized(session["role"], session["allowed_subjects"], subject_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access subject '{subject_id}'",
            )
        items = query_observations(
            get_db_path(),
            subject_id,
            include_non_live=False,
            order="desc",
            limit=500,
        )
        summary = compute_availability(items, stale_after_seconds=stale_after_seconds)
        return {"subject_id": subject_id, **summary}

    @application.get("/api/v1/observations")
    def observations(
        subject_id: str = Query(min_length=1, max_length=80),
        scope: AllowedScope | None = Query(default=None),
        metric: str | None = Query(default=None, min_length=1, max_length=80),
        include_non_live: bool = Query(default=False),
        order: Literal["asc", "desc"] = Query(default="desc"),
        since: datetime | None = Query(default=None),
        until: datetime | None = Query(default=None),
        cursor: str | None = Query(default=None),
        limit: int = Query(100, ge=1, le=500),
        session_and_token: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = session_and_token
        if not is_subject_authorized(session["role"], session["allowed_subjects"], subject_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access subject '{subject_id}'",
            )
        try:
            page = query_observations_page(
                get_db_path(),
                subject_id,
                scope=scope,
                metric=metric,
                include_non_live=include_non_live,
                order=order,
                since=since.isoformat() if since is not None else None,
                until=until.isoformat() if until is not None else None,
                cursor=cursor,
                limit=limit,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        return {
            "subject_id": subject_id,
            "order": order,
            "observations": page["observations"],
            "has_more": page["has_more"],
            "next_cursor": page["next_cursor"],
            "note": "Observations preserve recorded provenance; no automated clinical diagnosis is provided.",
        }

    @application.get("/api/v1/observations/series")
    def observation_series(
        subject_id: str = Query(min_length=1, max_length=80),
        metric: str = Query(min_length=1, max_length=80),
        scope: AllowedScope | None = Query(default=None),
        include_non_live: bool = Query(default=False),
        order: Literal["asc", "desc"] = Query(default="asc"),
        since: datetime | None = Query(default=None),
        until: datetime | None = Query(default=None),
        limit: int = Query(200, ge=1, le=500),
        session_and_token: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = session_and_token
        if not is_subject_authorized(session["role"], session["allowed_subjects"], subject_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access subject '{subject_id}'",
            )
        items = query_observations(
            get_db_path(),
            subject_id,
            scope=scope,
            metric=metric,
            include_non_live=include_non_live,
            order=order,
            since=since.isoformat() if since is not None else None,
            until=until.isoformat() if until is not None else None,
            limit=limit,
        )
        return {
            "subject_id": subject_id,
            "metric": metric,
            "order": order,
            "points": items,
            "count": len(items),
        }

    @application.post("/api/v1/observations", status_code=status.HTTP_201_CREATED)
    def create_observation(
        item: ObservationIn,
        response: Response,
        idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
        session_and_token: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = session_and_token
        if not is_subject_authorized(session["role"], session["allowed_subjects"], item.subject_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to record observations for subject '{item.subject_id}'",
            )
        record = item.model_dump(mode="json")
        if idempotency_key_header and not record.get("idempotency_key"):
            record["idempotency_key"] = idempotency_key_header.strip() or None
        obs_id, created_new, stored = ingest_observation(
            get_db_path(),
            record,
            created_by=session["username"],
        )
        if not created_new:
            response.status_code = status.HTTP_200_OK
        return {
            "id": obs_id,
            "status": "stored" if created_new else "idempotent_replay",
            "idempotent_replay": not created_new,
            "observation": stored,
        }

    from .knowledge_api import router as knowledge_router
    application.include_router(knowledge_router)
    from .source_registry import router as source_registry_router
    application.include_router(source_registry_router)
    from .safety_api import build_safety_router
    application.include_router(build_safety_router(get_db_path, require_session, server_version="0.2.0"))
    from .care.http_api import build_care_router
    application.include_router(build_care_router(get_db_path, require_session))
    from .admin_api import build_admin_router
    application.include_router(build_admin_router(get_db_path, require_session))
    # Two independent feature routers; same canonical DB, bearer session and ACL.
    from .ecg.http_api import build_ecg_router
    application.include_router(build_ecg_router(get_db_path, require_session))
    from .assistant_chat import build_assistant_router
    application.include_router(build_assistant_router(get_db_path, require_session))
    from .client_routes import build_client_router
    application.include_router(build_client_router(get_db_path, require_session))
    @application.api_route("/api/{unmatched_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], include_in_schema=False)
    def unknown_api_route(unmatched_path: str):
        raise HTTPException(status_code=404, detail="Unknown API route")
    # An explicit local export shares this API origin; no extra backend/store.
    mobile_web_dir = os.environ.get("AETHERION_MOBILE_WEB_DIR", "").strip()
    if mobile_web_dir:
        from fastapi.staticfiles import StaticFiles
        web_path = Path(mobile_web_dir).resolve()
        if not (web_path / "index.html").is_file():
            raise ValueError("AETHERION_MOBILE_WEB_DIR must contain the Expo index.html export")
        application.mount("/", StaticFiles(directory=str(web_path), html=True), name="mobile-web")
    return application


app = create_app()


def run() -> None:
    import uvicorn

    config = read_runtime_config()
    uvicorn.run(app, host=config.host, port=config.port)

