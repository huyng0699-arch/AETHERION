"""Consent-gated retention for sensitive Guide inputs (Q-0163)."""

from __future__ import annotations

from typing import Any


class GuideConsentLog:
    """In-memory audit log that never retains sensitive Guide input without explicit consent."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record_interaction(
        self,
        *,
        subject_id: str,
        user_input: str,
        is_sensitive: bool,
        explicit_retention_consent: bool = False,
    ) -> dict[str, Any]:
        retain_raw = (not is_sensitive) or explicit_retention_consent
        entry = {
            "subject_id": subject_id,
            "retained": retain_raw,
            "redacted": is_sensitive and not explicit_retention_consent,
            "input_text": user_input if retain_raw else "[REDACTED_NO_CONSENT]",
        }
        if retain_raw:
            self._records.append(entry)
        return entry

    def list_retained(self) -> list[dict[str, Any]]:
        return list(self._records)
