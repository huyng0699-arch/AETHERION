"""Privacy-safe machine-readable operational logging for AETHERION (Q-0013)."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import re
from typing import Any

REDACTED = "[REDACTED]"

SENSITIVE_KEYS = frozenset({
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "password",
    "secret",
    "api_key",
    "bearer",
    "cookie",
    "subject_id",
    "patient_id",
    "display_name",
    "symptom",
    "symptoms",
    "note",
    "notes",
    "clinical_note",
    "answers",
    "transcript",
    "observation_value",
    "value",
})

_SECRET_PATTERNS = (
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-+/=]{8,}", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{10,}"), "[REDACTED_KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{10,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{10,}"), "[REDACTED_KEY]"),
    (re.compile(r"(password|token|api_key|secret)\s*[:=]\s*[^\s,;]+", re.IGNORECASE), r"\1=[REDACTED]"),
)


def sanitize_text(text: str) -> str:
    cleaned = text
    for pattern, repl in _SECRET_PATTERNS:
        cleaned = pattern.sub(repl, cleaned)
    return cleaned


def sanitize_value(value: Any, *, key: str | None = None) -> Any:
    if key is not None and key.strip().lower() in SENSITIVE_KEYS:
        return REDACTED
    if isinstance(value, dict):
        return {str(k): sanitize_value(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_value(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


class PrivacySafeJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON with UTC timestamps, severity, and redacted fields."""

    def format(self, record: logging.LogRecord) -> str:
        ts_utc = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        extra_fields = getattr(record, "ops_fields", None)
        payload: dict[str, Any] = {
            "ts_utc": ts_utc,
            "severity": record.levelname,
            "logger": record.name,
            "event": sanitize_text(record.getMessage()),
        }
        if isinstance(extra_fields, dict) and extra_fields:
            payload["fields"] = sanitize_value(extra_fields)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_privacy_safe_logger(name: str = "aetherion.ops", stream: Any = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(PrivacySafeJsonFormatter())
    logger.addHandler(handler)
    return logger


def emit_ops_log(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    logger.log(level, event, extra={"ops_fields": fields})
