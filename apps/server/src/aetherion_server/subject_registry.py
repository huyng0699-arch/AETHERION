"""Fail-closed subject registry and identity lookup (Q-0037)."""

from dataclasses import dataclass

from aetherion_server.scope_guard import ALL_ALLOWED_SCOPES


class UnknownSubjectError(KeyError):
    """Raised when a requested subject_id is not registered."""


@dataclass(frozen=True)
class SubjectIdentity:
    subject_id: str
    scope: str
    display_name: str
    active: bool = True


class SubjectRegistry:
    """In-memory fail-closed subject registry; never silently selects another profile."""

    def __init__(self) -> None:
        self._subjects: dict[str, SubjectIdentity] = {}

    def register(self, *, subject_id: str, scope: str, display_name: str, active: bool = True) -> SubjectIdentity:
        sid = subject_id.strip()
        if not sid:
            raise ValueError("subject_id must be non-empty")
        normalized_scope = scope.strip()
        if normalized_scope not in ALL_ALLOWED_SCOPES:
            raise ValueError(f"Unsupported scope '{scope}'")
        name = display_name.strip()
        if not name:
            raise ValueError("display_name must be non-empty")
        identity = SubjectIdentity(
            subject_id=sid,
            scope=normalized_scope,
            display_name=name,
            active=active,
        )
        self._subjects[sid] = identity
        return identity

    def get_exact(self, subject_id: str) -> SubjectIdentity:
        sid = subject_id.strip()
        if not sid or sid not in self._subjects:
            raise UnknownSubjectError(f"Unknown subject_id: {subject_id!r}")
        return self._subjects[sid]
