"""Read-only, offline NASA CliFF article search (Q-0428).

No network access, no patient data, no synthetic medical records.
FTS5 is used when available; LIKE is the deterministic fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from contextlib import closing
import sqlite3


@dataclass(frozen=True)
class SearchHit:
    article_id: str
    slot: int
    title: str
    category: str
    section_count: int
    image_count: int


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Offline library does not exist: {path}")
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def categories(db_path: str | Path) -> list[str]:
    """Return available categories, never fabricated from the 119-slot index."""
    with closing(_connect(db_path)) as db:
        return [r[0] for r in db.execute(
            "SELECT DISTINCT category FROM articles "
            "WHERE trim(category) <> '' ORDER BY category COLLATE NOCASE"
        )]


def search(
    db_path: str | Path,
    query: str = "",
    *,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
    complete_only: bool = True,
) -> list[SearchHit]:
    """Search genuine stored article titles and sections, with optional category.

    Uses parameter binding throughout. This method does not claim provenance
    validation; release audits must independently validate NASA source and rights.
    """
    if not 1 <= limit <= 119 or offset < 0:
        raise ValueError("limit must be 1..119 and offset nonnegative")
    term = query.strip()
    if len(term) > 256:
        raise ValueError("query exceeds 256 characters")
    where = []
    params: list[object] = []
    if complete_only:
        where.append("a.completeness_state = 'COMPLETE'")
    if category:
        where.append("a.category = ?")
        params.append(category)
    if term:
        # Escaped literal LIKE: user input never becomes SQL or FTS syntax.
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        where.append(
            "(a.display_title LIKE ? ESCAPE '\\' COLLATE NOCASE "
            "OR EXISTS (SELECT 1 FROM article_sections s "
            "WHERE s.article_id=a.article_id "
            "AND s.text_content LIKE ? ESCAPE '\\' COLLATE NOCASE))"
        )
        params.extend((like, like))
    predicate = " AND ".join(where) if where else "1=1"
    sql = f"""
        SELECT a.article_id, a.slot, a.display_title, a.category,
               (SELECT COUNT(*) FROM article_sections s WHERE s.article_id=a.article_id) AS section_count,
               (SELECT COUNT(*) FROM media m WHERE m.article_id=a.article_id
                AND m.usage_review='APPROVED') AS image_count
        FROM articles a
        WHERE {predicate}
        ORDER BY a.slot
        LIMIT ? OFFSET ?
    """
    params.extend((limit, offset))
    with closing(_connect(db_path)) as db:
        rows = db.execute(sql, params).fetchall()
    return [SearchHit(r["article_id"], r["slot"], r["display_title"],
                      r["category"], r["section_count"], r["image_count"])
            for r in rows]


def search_status(db_path: str | Path) -> dict[str, object]:
    """Report actual coverage without treating empty/partial databases as complete."""
    with closing(_connect(db_path)) as db:
        n = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        complete = db.execute(
            "SELECT COUNT(*) FROM articles WHERE completeness_state='COMPLETE'"
        ).fetchone()[0]
        fts = db.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE name='article_search' AND type='table'"
        ).fetchone()[0] > 0
        return {"articles": n, "complete_articles": complete,
                "expected": 119, "fts5_available": fts,
                "library_complete": n == 119 and complete == 119}
