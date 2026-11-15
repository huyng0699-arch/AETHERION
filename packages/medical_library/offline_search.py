"""Read-only, offline NASA CliFF article search (Q-0428).

No network access, no patient data, no synthetic medical records.
FTS5 is used when available; LIKE is the deterministic fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3


@dataclass(frozen=True)
class SearchHit:
    article_id: str
    slot: int
    title: str
    category: str
    section_count: int
    image_count: int


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            return super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Offline library does not exist: {path}")
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, factory=_ClosingConnection)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def _has_fts5_table(db: sqlite3.Connection) -> bool:
    row = db.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='article_search' AND type='table'"
    ).fetchone()
    return bool(row and int(row[0]) > 0)


def _fts5_match_expression(term: str) -> str | None:
    """Convert raw user query into safe quoted FTS5 prefix tokens (implicit AND)."""
    tokens = _TOKEN_RE.findall(term)
    if not tokens:
        return None
    escaped_tokens = [f'"{tok.replace(chr(34), chr(34) * 2)}"*' for tok in tokens]
    return " ".join(escaped_tokens)


def categories(db_path: str | Path) -> list[str]:
    """Return available categories, never fabricated from the 119-slot index."""
    with _connect(db_path) as db:
        return [r[0] for r in db.execute(
            "SELECT DISTINCT category FROM articles "
            "WHERE trim(category) <> '' ORDER BY category COLLATE NOCASE"
        )]


def _base_where(category: str | None, complete_only: bool) -> tuple[list[str], list[object]]:
    where: list[str] = []
    params: list[object] = []
    if complete_only:
        where.append("a.completeness_state = 'COMPLETE'")
    if category:
        where.append("a.category = ?")
        params.append(category)
    return where, params


def _rows_to_hits(rows: list[sqlite3.Row]) -> list[SearchHit]:
    return [
        SearchHit(
            r["article_id"],
            r["slot"],
            r["display_title"],
            r["category"],
            r["section_count"],
            r["image_count"],
        )
        for r in rows
    ]


def search_detailed(
    db_path: str | Path,
    query: str = "",
    *,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
    complete_only: bool = True,
) -> tuple[list[SearchHit], str]:
    """Search articles and return ``(hits, backend_used)`` (``fts5``, ``like``, or ``filter``)."""
    if not 1 <= limit <= 119 or offset < 0:
        raise ValueError("limit must be 1..119 and offset nonnegative")
    term = query.strip()
    if len(term) > 256:
        raise ValueError("query exceeds 256 characters")

    with _connect(db_path) as db:
        where, params = _base_where(category, complete_only)
        if not term:
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
            rows = db.execute(sql, [*params, limit, offset]).fetchall()
            return _rows_to_hits(rows), "filter"

        fts_expr = _fts5_match_expression(term)
        if fts_expr and _has_fts5_table(db):
            fts_where = [*where, "article_search MATCH ?"]
            fts_predicate = " AND ".join(fts_where)
            fts_sql = f"""
                SELECT a.article_id, a.slot, a.display_title, a.category,
                       (SELECT COUNT(*) FROM article_sections s WHERE s.article_id=a.article_id) AS section_count,
                       (SELECT COUNT(*) FROM media m WHERE m.article_id=a.article_id
                        AND m.usage_review='APPROVED') AS image_count
                FROM article_search
                JOIN articles a ON a.article_id = article_search.article_id
                WHERE {fts_predicate}
                ORDER BY bm25(article_search), a.slot
                LIMIT ? OFFSET ?
            """
            try:
                rows = db.execute(fts_sql, [*params, fts_expr, limit, offset]).fetchall()
                if rows:
                    return _rows_to_hits(rows), "fts5"
            except sqlite3.OperationalError:
                pass

        # Escaped literal LIKE fallback: supports substring search and non-FTS5 SQLite builds.
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        like_where = [
            *where,
            "(a.display_title LIKE ? ESCAPE '\\' COLLATE NOCASE "
            "OR EXISTS (SELECT 1 FROM article_sections s "
            "WHERE s.article_id=a.article_id "
            "AND s.text_content LIKE ? ESCAPE '\\' COLLATE NOCASE))",
        ]
        like_predicate = " AND ".join(like_where)
        like_sql = f"""
            SELECT a.article_id, a.slot, a.display_title, a.category,
                   (SELECT COUNT(*) FROM article_sections s WHERE s.article_id=a.article_id) AS section_count,
                   (SELECT COUNT(*) FROM media m WHERE m.article_id=a.article_id
                    AND m.usage_review='APPROVED') AS image_count
            FROM articles a
            WHERE {like_predicate}
            ORDER BY a.slot
            LIMIT ? OFFSET ?
        """
        rows = db.execute(like_sql, [*params, like, like, limit, offset]).fetchall()
        return _rows_to_hits(rows), "like"


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

    Uses FTS5 full-text search when indexed, falling back deterministically to escaped
    literal LIKE when FTS5 is absent or a substring pattern is queried.
    """
    hits, _ = search_detailed(
        db_path,
        query,
        category=category,
        limit=limit,
        offset=offset,
        complete_only=complete_only,
    )
    return hits


def search_status(db_path: str | Path) -> dict[str, object]:
    """Report actual coverage without treating empty/partial databases as complete."""
    with _connect(db_path) as db:
        n = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        complete = db.execute(
            "SELECT COUNT(*) FROM articles WHERE completeness_state='COMPLETE'"
        ).fetchone()[0]
        fts = _has_fts5_table(db)
        return {"articles": n, "complete_articles": complete,
                "expected": 119, "fts5_available": fts,
                "library_complete": n == 119 and complete == 119}
