"""Encyclopedia keyword search with synonym and body-system filtering (Q-0141)."""

from __future__ import annotations

from typing import Any


def search_encyclopedia(
    entries: list[dict[str, Any]],
    *,
    query: str = "",
    body_system: str | None = None,
    verified_only: bool = True,
) -> dict[str, Any]:
    """Query encyclopedia condition entries by title, synonyms, and body-system filter."""
    q = " ".join(query.strip().lower().split())
    bs_filter = body_system.strip().lower() if body_system else None

    eligible: list[dict[str, Any]] = []
    for entry in entries:
        if verified_only:
            if entry.get("verification_state") != "READY" or entry.get("review_state") != "APPROVED":
                continue
        if bs_filter:
            systems = [str(s).strip().lower() for s in entry.get("body_systems", [])]
            if bs_filter not in systems:
                continue
        eligible.append(entry)

    if not entries or (verified_only and not eligible and not q and not bs_filter):
        return {
            "status": "NO_DATA",
            "query": query,
            "body_system": body_system,
            "total_matches": 0,
            "results": [],
        }

    scored: list[tuple[int, str, dict[str, Any]]] = []
    for entry in eligible:
        title = str(entry.get("canonical_title", "")).lower()
        synonyms = [str(s).lower() for s in entry.get("synonyms", [])]
        symptoms = [str(s).lower() for s in entry.get("symptoms", [])]
        overview = str(entry.get("overview", "")).lower()

        if not q:
            score = 1
        elif q == title:
            score = 100
        elif any(q == syn for syn in synonyms):
            score = 90
        elif q in title:
            score = 80
        elif any(q in syn for syn in synonyms):
            score = 70
        elif any(q in sym for sym in symptoms):
            score = 50
        elif q in overview:
            score = 30
        else:
            continue

        scored.append((score, title, entry))

    scored.sort(key=lambda item: (-item[0], item[1]))
    results = [item[2] for item in scored]
    return {
        "status": "READY" if results else "NO_MATCH",
        "query": query,
        "body_system": body_system,
        "total_matches": len(results),
        "results": results,
    }
