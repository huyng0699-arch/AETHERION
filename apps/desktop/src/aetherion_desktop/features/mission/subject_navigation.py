"""Session-scoped Mission ↔ Personal routing, without stale health disclosure.

This standalone controller holds only a subject identifier, never API tokens,
medical values or permissions. The desktop caller must first obtain an actual
200 response from the protected subject API and pass the matched ID.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteState:
    view: str
    selected_subject_id: str | None
    message: str


class MissionPersonalNavigation:
    """Keep an authorized selection across view switches, clear on auth loss."""

    def __init__(self) -> None:
        self._generation: int | None = None
        self._subject_id: str | None = None
        self._view: str = "PORTAL"  # owner-corrected Portal-first startup

    def _state(self, message: str) -> RouteState:
        return RouteState(self._view, self._subject_id, message)

    def begin_session(self, generation: int) -> RouteState:
        """Pass an incrementing NONSECRET generation on a real successful login."""
        if isinstance(generation, bool) or not isinstance(generation, int) or generation <= 0:
            raise ValueError("session generation must be a positive integer, not a secret")
        if self._generation != generation:
            self._subject_id = None
            self._view = "PORTAL"
            self._generation = generation
        return self._state("Authenticated session — no subject inferred")

    def select_from_authorized_response(self, subject_id: str, response_subject_id: str,
                                        status_code: int, generation: int) -> RouteState:
        """Accept a selected ID only from the matching *protected* server response.

        The caller must issue the API request using its actual bearer session;
        200 here is not itself proof of authorization if the caller fakes it.
        """
        if self._generation is None or generation != self._generation:
            self.expire_session()
            return self._state("DENIED — session changed, selection cleared")
        if (status_code != 200 or not isinstance(subject_id, str) or
                not isinstance(response_subject_id, str) or subject_id != response_subject_id or
                not 1 <= len(subject_id.strip()) <= 80 or any(ord(c) < 32 for c in subject_id)):
            self._subject_id = None
            self._view = "MISSION"
            return self._state("DENIED — no authorized matching profile")
        self._subject_id = subject_id.strip()
        self._view = "MISSION"
        return self._state("Exact source-backed subject selected")

    def to_personal(self) -> RouteState:
        if self._generation is None or self._subject_id is None:
            return self._state("DENIED — choose a subject via an authorized request")
        self._view = "PERSONAL"
        return self._state("Selection preserved for Personal view; reload protected data")

    def back_to_mission(self) -> RouteState:
        if self._generation is None:
            self._view = "PORTAL"
            return self._state("DENIED — sign in to reopen protected Mission view")
        self._view = "MISSION"
        return self._state("Returned to Mission; selection preserved within session")

    def expire_session(self) -> RouteState:
        self._generation = None
        self._subject_id = None
        self._view = "PORTAL"
        return self._state("Session ended; subject selection and protected view cleared")

    def on_http_auth_error(self, status_code: int) -> RouteState:
        if status_code in (401, 403):
            return self.expire_session()
        return self._state("No authentication state change")

    def current(self) -> RouteState:
        return self._state("Current in-memory navigation state; not an authorization claim")
