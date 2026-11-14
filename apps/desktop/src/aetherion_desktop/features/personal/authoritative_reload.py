"""Reload Personal records from the authenticated AETHERION server after restart.

No session or medical records are persisted by this transport. The caller must
reauthenticate; use a worker thread if invoking from a native Qt GUI. The UI's
VI/EN catalog translates the returned machine status, not source data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import math
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

_MAX_RESPONSE_BYTES = 1_048_576
# A numeric record must never surface with a permission/error/no-data marker.
# These are data availability states, not valid measured-value provenance.
_MEASUREMENT_QUALITY = frozenset({"READY", "STALE", "UNVERIFIED"})
_PERSONAL_SCOPES = frozenset({"CREW", "crew", "personal"})


@dataclass(frozen=True)
class PersonalReload:
    """Only a validated authenticated HTTP 200 can carry observations."""

    status: str
    subject_id: str
    observations: tuple[dict[str, Any], ...]
    http_status: int | None
    has_more: bool

    @property
    def source_is_server(self) -> bool:
        return self.http_status == 200 and self.status in {"READY", "NO_DATA"}


def build_authoritative_url(api_base: str, subject_id: str, *, limit: int = 50) -> str:
    if not isinstance(api_base, str):
        raise ValueError("API base URL required")
    parsed = urlsplit(api_base)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("configure a plain HTTP(S) API base without credentials or paths")
    if (
        not isinstance(subject_id, str)
        or not 1 <= len(subject_id.strip()) <= 80
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in subject_id)
    ):
        raise ValueError("an explicit valid subject ID is required")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")
    return api_base.rstrip("/") + "/api/v1/observations?" + urlencode(
        {"subject_id": subject_id.strip(), "limit": limit, "order": "desc"}
    )


def _has_timezone(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.tzinfo is not None and parsed.utcoffset() is not None
    except ValueError:
        return False


def _validated_records(payload: object, subject: str) -> tuple[tuple[dict[str, Any], ...], bool]:
    if not isinstance(payload, dict) or payload.get("subject_id") != subject:
        raise ValueError("response subject identity mismatch")
    items = payload.get("observations")
    if not isinstance(items, list):
        raise ValueError("missing server observations array")
    more = payload.get("has_more", False)
    if not isinstance(more, bool):
        raise ValueError("invalid has_more")
    for item in items:
        if not isinstance(item, dict) or item.get("subject_id") != subject:
            raise ValueError("cross-subject observation")
        fields = ("metric", "unit", "source_id", "scope", "quality", "verification_state")
        if any(not isinstance(item.get(k), str) or not item[k].strip() for k in fields):
            raise ValueError("measurement provenance is incomplete")
        if item["quality"] not in _MEASUREMENT_QUALITY:
            raise ValueError("numeric measurement has unsafe availability/quality status")
        if item["scope"] not in _PERSONAL_SCOPES:
            raise ValueError("non-personal observation cannot appear in Personal Health")
        reading = item.get("value")
        if (
            isinstance(reading, bool)
            or not isinstance(reading, (int, float))
            or not math.isfinite(reading)
            or not _has_timezone(item.get("observed_at"))
        ):
            raise ValueError("invalid value or measured-at timestamp")
        received_at = item.get("received_at")
        if received_at is not None:
            if not _has_timezone(received_at):
                raise ValueError("invalid received-at provenance")
            measured = datetime.fromisoformat(item["observed_at"].replace("Z", "+00:00"))
            received = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
            if received < measured:
                raise ValueError("receipt precedes observation")
        if item.get("verification_state") == "TEST_FIXTURE" or item.get("scope") == "engineering_test":
            raise ValueError("test fixture cannot appear as personal records")
        if item["source_id"].lower().startswith(("nasa_osdr:", "research:")):
            raise ValueError("research evidence cannot be presented as personal telemetry")
    return tuple(dict(item) for item in items), more


def reload_personal_from_server(
    api_base: str,
    subject_id: str,
    access_token: str,
    *,
    opener=urlopen,
    timeout: float = 5.0,
    limit: int = 50,
) -> PersonalReload:
    """Load only server records for an explicitly reauthenticated session.

    Run in a Qt worker, never block the UI thread. A 401/403 or network error
    returns NO data, never an in-memory snapshot or made-up healthy state.
    """
    target = build_authoritative_url(api_base, subject_id, limit=limit)
    subject = subject_id.strip()
    if (
        not isinstance(access_token, str)
        or not 1 <= len(access_token) <= 2048
        or any(ord(char) < 33 or ord(char) > 126 for char in access_token)
    ):
        raise ValueError("re-authenticate with an actual bearer session token")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= 30:
        raise ValueError("invalid network timeout")
    request = Request(
        target,
        method="GET",
        headers={
            "Authorization": "Bearer " + access_token,
            "Accept": "application/json",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )
    try:
        with opener(request, timeout=timeout) as response:
            http_status = response.getcode()
            if http_status != 200:
                status = "DENIED" if http_status in (401, 403) else (
                    "OFFLINE" if http_status == 503 else "ERROR"
                )
                return PersonalReload(status, subject, (), http_status, False)
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        status = "DENIED" if error.code in (401, 403) else (
            "OFFLINE" if error.code == 503 else "ERROR"
        )
        return PersonalReload(status, subject, (), error.code, False)
    except (URLError, TimeoutError, OSError):
        return PersonalReload("OFFLINE", subject, (), None, False)

    if len(raw) > _MAX_RESPONSE_BYTES:
        return PersonalReload("ERROR", subject, (), 200, False)
    try:
        payload = json.loads(raw.decode("utf-8"))
        records, has_more = _validated_records(payload, subject)
    except (UnicodeDecodeError, ValueError, TypeError):
        return PersonalReload("ERROR", subject, (), 200, False)
    return PersonalReload("READY" if records else "NO_DATA", subject, records, 200, has_more)
