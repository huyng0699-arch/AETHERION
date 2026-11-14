"""Rate-limited, subject-locked incremental Mission API refresh coordinator.

The Qt shell owns the actual authenticated QNetworkAccessManager and timer.
This component never stores bearer tokens or invents records. Follow-up pages
use server-provided opaque cursors; refreshed data is revalidated by Q-0062.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit

from .crew_data_state import state_from_server_response


@dataclass(frozen=True)
class RefreshRequest:
    sequence: int
    subject_id: str
    url: str
    since: str | None
    cursor: str | None


class MissionRefresh:
    """Poll on a caller's timer without request storms or stale cross-user replies."""

    def __init__(self, api_base: str, *, poll_seconds: int = 30, limit: int = 100):
        url = urlsplit(api_base)
        if (url.scheme not in ("http", "https") or not url.hostname or url.username or
                url.password or url.query or url.fragment or url.path not in ("", "/")):
            raise ValueError("invalid configured server base URL")
        if poll_seconds < 10 or not 1 <= limit <= 500:
            raise ValueError("polling must be >=10 seconds and pages must be 1..500")
        self._base = api_base.rstrip("/")
        self._poll_seconds = poll_seconds
        self._limit = limit
        self._subject_id: str | None = None
        self._active: RefreshRequest | None = None
        self._request_sequence = 0
        self._last_started: datetime | None = None
        self._latest_at: str | None = None
        self._page_cursor: str | None = None
        self._page_since: str | None = None
        self._records: dict[int, dict] = {}
        self._status = "NO_DATA"

    def select_subject(self, subject_id: str | None) -> None:
        """Changing subject invalidates in-flight replies and the old subject cache."""
        if subject_id is not None:
            if (not isinstance(subject_id, str) or not 1 <= len(subject_id.strip()) <= 80 or
                    any(ord(c) < 32 for c in subject_id)):
                raise ValueError("invalid explicit subject ID")
            subject_id = subject_id.strip()
        if self._subject_id != subject_id:
            self._subject_id = subject_id
            self._active = None
            self._last_started = None
            self._latest_at = None
            self._page_cursor = None
            self._page_since = None
            self._records.clear()
            self._status = "NO_DATA"
            self._request_sequence += 1

    @staticmethod
    def _utc(now: datetime) -> datetime:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("refresh clock needs timezone")
        return now.astimezone(timezone.utc)

    def next_request(self, *, now: datetime) -> RefreshRequest | None:
        """Return None when idle, busy or inside a rate-limit window."""
        now = self._utc(now)
        if self._subject_id is None or self._active is not None:
            return None
        delay = 1 if self._page_cursor else self._poll_seconds
        if self._last_started is not None and (now - self._last_started).total_seconds() < delay:
            return None
        self._request_sequence += 1
        since = self._page_since if self._page_cursor else self._latest_at
        parameters = {"subject_id": self._subject_id, "order": "asc", "limit": self._limit}
        if since:
            parameters["since"] = since
        if self._page_cursor:
            parameters["cursor"] = self._page_cursor
        request = RefreshRequest(self._request_sequence, self._subject_id,
                                 self._base + "/api/v1/observations?" + urlencode(parameters),
                                 since, self._page_cursor)
        self._active = request
        self._last_started = now
        return request

    def accept_response(self, request: RefreshRequest, code: int | None,
                        payload: object, *, now: datetime) -> str:
        """Consume only the latest request for the still-selected subject.

        A malformed page is rejected atomically without partially merging data.
        """
        now = self._utc(now)
        if self._active != request or self._subject_id != request.subject_id:
            return "IGNORED_SUPERSEDED"
        self._active = None
        if code in (401, 403):
            self.select_subject(None)
            self._status = "DENIED"
            return self._status
        if code != 200:
            self._status = "OFFLINE" if code is None or code == 503 else "ERROR"
            self._records.clear()  # last-known-display policy is a separate Quest
            self._page_cursor = None
            self._page_since = None
            return self._status
        snapshot = state_from_server_response(request.subject_id, 200, payload, now=now)
        if snapshot.status == "ERROR" or not isinstance(payload, dict):
            self._status = "ERROR"
            return self._status
        page = payload.get("observations")
        if not isinstance(page, list):
            self._status = "ERROR"
            return self._status
        incoming: dict[int, dict] = {}
        for record in page:
            if not isinstance(record, dict):
                self._status = "ERROR"
                return self._status
            ident = record.get("id")
            if isinstance(ident, bool) or not isinstance(ident, int) or ident <= 0:
                self._status = "ERROR"
                return self._status
            if ident in incoming and incoming[ident] != record:
                self._status = "ERROR"
                return self._status
            incoming[ident] = record.copy()
        if any(ident in self._records and self._records[ident] != raw
               for ident, raw in incoming.items()):
            self._status = "ERROR"
            return self._status  # server ID must be immutable; never silently overwrite
        self._records.update(incoming)
        # Limit cached scope; all entries remain validated by Q-0062 on display.
        if len(self._records) > 500:
            ordered = sorted(self._records.items(), key=lambda kv: (kv[1]["observed_at"], kv[0]),
                             reverse=True)[:500]
            self._records = dict(ordered)
        next_cursor = payload.get("next_cursor")
        more = payload.get("has_more") is True
        if more:
            self._page_since = request.since
            self._page_cursor = next_cursor
        else:
            self._page_since = None
            self._page_cursor = None
            if self._records:
                timestamps = [datetime.fromisoformat(r["observed_at"].replace("Z", "+00:00"))
                              for r in self._records.values()]
                self._latest_at = max(timestamps).astimezone(timezone.utc).isoformat()
        self._status = snapshot.status
        return self._status

    def visible_state(self, *, now: datetime):
        """Revalidate merged persisted results before showing any cached health values."""
        now = self._utc(now)
        subject = self._subject_id
        if subject is None:
            return None
        if self._status in {"ERROR", "OFFLINE", "DENIED"}:
            return state_from_server_response(subject, None if self._status == "OFFLINE" else 500, now=now)
        payload = {"subject_id": subject, "observations": list(self._records.values()),
                   "has_more": False, "next_cursor": None}
        return state_from_server_response(subject, 200, payload, now=now)

    @property
    def selected_subject_id(self) -> str | None:
        return self._subject_id
