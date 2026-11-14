"""Pure validation for passing a subject/session between native Qt screens.

This is not a server authorization check; the server enforces access on reads.
"""
from __future__ import annotations


def checked_personal_handoff(subject_id: str, access_token: str) -> tuple[str, str]:
    """Keep the exact selected identity, fail closed on missing context."""
    if not isinstance(subject_id, str):
        raise ValueError("Subject ID is required")
    subject = subject_id.strip()
    if not (1 <= len(subject) <= 80) or any(ord(c) < 32 for c in subject):
        raise ValueError("Subject ID must have 1-80 printable characters")
    if not isinstance(access_token, str) or not access_token.strip():
        raise ValueError("An authenticated local session is required")
    if "\r" in access_token or "\n" in access_token:
        raise ValueError("Session token cannot contain line breaks")
    return subject, access_token
