"""Explain what is unknown rather than producing a diagnosis (Q-0155)."""

from __future__ import annotations

from typing import Any


def explain_unknown_state(
    available_metrics: dict[str, dict[str, Any]] | None,
    requested_metrics: list[str],
) -> dict[str, Any]:
    """Summarize missing/stale/offline metrics honestly with zero diagnostic claims."""
    present = available_metrics or {}
    known: list[str] = []
    unknown: list[dict[str, str]] = []

    for metric in requested_metrics:
        obs = present.get(metric)
        if not obs or obs.get("value") is None:
            state = str(obs.get("verification_state", "NO_DATA")) if obs else "NO_DATA"
            unknown.append(
                {
                    "metric": metric,
                    "state": state,
                    "reason": f"{metric} is {state}; missing or unmeasured data is not normal/healthy and cannot support a diagnosis.",
                }
            )
        else:
            state = str(obs.get("verification_state", "UNVERIFIED"))
            if state in ("STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"):
                unknown.append(
                    {
                        "metric": metric,
                        "state": state,
                        "reason": f"{metric} is {state}; cannot be treated as current verified telemetry.",
                    }
                )
            else:
                known.append(metric)

    return {
        "diagnosis_produced": False,
        "known_metrics": known,
        "unknown_metrics": unknown,
        "summary": (
            f"{len(unknown)} metric(s) unknown/unverified; no diagnosis produced."
            if unknown
            else "All requested metrics have verified values; Guide provides educational context only, not a medical diagnosis."
        ),
    }
