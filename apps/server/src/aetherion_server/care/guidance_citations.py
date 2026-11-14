"""Source-linked non-diagnostic educational guidance filter for Care (Q-0096)."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_CLIFF_SQLITE_PATH = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "AETHERION_NASA_CLIFF_119.sqlite"

NON_DIAGNOSTIC_NOTICE = {
    "vi": "Chỉ là tài liệu giáo dục tham khảo có trích dẫn nguồn NASA CliFF; không phải chẩn đoán hoặc phác đồ điều trị.",
    "en": "Educational reference only with verified NASA CliFF citations; not a clinical diagnosis or treatment protocol.",
}


def filter_approved_educational_actions(
    actions: list[dict[str, Any]],
    *,
    sqlite_path: Path | None = None,
) -> dict[str, Any]:
    """Allow only approved, non-diagnostic educational actions backed by verified CliFF citations."""
    db_path = sqlite_path or DEFAULT_CLIFF_SQLITE_PATH
    verified_articles: dict[str, dict[str, str]] = {}
    if db_path.is_file():
        try:
            with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as conn:
                for art_id, title, source_id in conn.execute(
                    "SELECT article_id, display_title, source_id FROM articles"
                ):
                    if art_id and title and source_id:
                        verified_articles[str(art_id)] = {
                            "display_title": str(title),
                            "source_id": str(source_id),
                        }
        except sqlite3.Error:
            # A missing, corrupt, or incompatible catalog must never authorize guidance.
            verified_articles.clear()

    approved_actions: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for idx, action in enumerate(actions):
        action_id = str(action.get("action_id") or f"action-{idx}")
        if not action.get("approved", False):
            rejected.append({"action_id": action_id, "reason": "not_approved"})
            continue
        if action.get("diagnostic_claim", False) or action.get("prescriptive_treatment", False):
            rejected.append({"action_id": action_id, "reason": "diagnostic_or_prescriptive_disallowed"})
            continue

        article_id = str(action.get("article_id") or "").strip()
        if not article_id or article_id not in verified_articles:
            rejected.append({"action_id": action_id, "reason": "missing_or_unverified_citation"})
            continue

        meta = verified_articles[article_id]
        approved_actions.append(
            {
                "action_id": action_id,
                "label_en": str(action.get("label_en") or ""),
                "label_vi": str(action.get("label_vi") or ""),
                "article_id": article_id,
                "citation_title": meta["display_title"],
                "source_id": meta["source_id"],
                "educational_only": True,
                "diagnostic_claim": False,
                "notice": dict(NON_DIAGNOSTIC_NOTICE),
            }
        )

    return {
        "status": "READY" if approved_actions else "NO_DATA",
        "approved_actions": approved_actions,
        "rejected": rejected,
        "notice": dict(NON_DIAGNOSTIC_NOTICE),
    }
