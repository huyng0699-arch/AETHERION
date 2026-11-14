"""Read-only, offline CliFF article index and native Qt view (Q-0425).

No NASA content is bundled or synthesized here. A database must be supplied by
an independently verified importer. This module never writes to the library.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
from typing import Iterator

MAX_ARTICLES = 119
LIBRARY_NAME = "AETHERION_NASA_CLIFF_119.sqlite"


def default_library_path() -> Path:
    override = os.environ.get("AETHERION_CLIFF_LIBRARY_PATH")
    if override:
        return Path(override).expanduser()
    return (Path(__file__).resolve().parents[4] / "knowledge" / "nasa"
            / "cliff_119_2023" / LIBRARY_NAME)


@dataclass(frozen=True)
class ArticleSummary:
    article_id: str
    slot: int
    title: str
    category: str
    completeness: str
    source_state: str
    source_url: str


@dataclass(frozen=True)
class CatalogSnapshot:
    state: str  # READY, EMPTY, MISSING, ERROR
    articles: tuple[ArticleSummary, ...]
    message: str
    total: int = 0


@contextmanager
def _readonly_connection(path: Path) -> Iterator[sqlite3.Connection]:
    # mode=ro fails if missing: never create an empty database on the user's behalf.
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


class OfflineMedicalCatalog:
    """Tiny SQLite read model. Source metadata is a claim, not clinical review."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else default_library_path()

    def list_articles(self, search: str = "") -> CatalogSnapshot:
        if not self.path.is_file():
            return CatalogSnapshot("MISSING", (), "Library file not installed. 0/119 articles available.")
        try:
            with _readonly_connection(self.path) as db:
                # A corrupt/unrelated SQLite file is not a valid medical library.
                tables = {r[0] for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                if not {"articles", "sources", "library_info"}.issubset(tables):
                    return CatalogSnapshot("ERROR", (), "Invalid library schema; no articles displayed.")
                kind = db.execute(
                    "SELECT value FROM library_info WHERE key='library_kind'"
                ).fetchone()
                if kind is None or kind[0] != "NASA_CLIFF_119_MEDICAL_REFERENCE":
                    return CatalogSnapshot("ERROR", (), "Unrecognized library identity; no articles displayed.")
                rows = db.execute("""
                    SELECT a.article_id, a.slot, a.display_title, a.category,
                           a.completeness_state, s.verification_state, s.source_url
                    FROM articles a JOIN sources s ON s.source_id = a.source_id
                    ORDER BY a.slot, a.article_id
                    LIMIT ?
                """, (MAX_ARTICLES + 1,)).fetchall()
                if len(rows) > MAX_ARTICLES:
                    return CatalogSnapshot("ERROR", (), "Unexpected article count; library needs audit.")
                all_articles = tuple(ArticleSummary(
                    article_id=r["article_id"], slot=r["slot"],
                    title=r["display_title"], category=r["category"],
                    completeness=r["completeness_state"],
                    source_state=r["verification_state"], source_url=r["source_url"]
                ) for r in rows)
        except (OSError, sqlite3.Error):
            return CatalogSnapshot("ERROR", (), "Cannot read or validate library; no articles displayed.")

        term = search.strip().casefold()
        shown = tuple(a for a in all_articles
                      if not term or term in a.title.casefold() or term in a.category.casefold())
        if not all_articles:
            return CatalogSnapshot("EMPTY", (), "No imported articles. 0/119 available.", 0)
        return CatalogSnapshot("READY", shown, "Local article index (not clinical validation).",
                               len(all_articles))


def build_medical_library_page(parent=None):
    """Create an actual Qt widget; Python model remains testable without Qt installed."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
        QPushButton, QSplitter, QVBoxLayout, QWidget,
    )

    class MedicalLibraryPage(QWidget):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.catalog = OfflineMedicalCatalog()
            self.current_articles: dict[str, ArticleSummary] = {}
            layout = QVBoxLayout(self)
            layout.setContentsMargins(18, 24, 18, 16)
            heading = QLabel("Medical Library · Offline CliFF index")
            heading.setObjectName("heading")
            layout.addWidget(heading)
            self.status = QLabel("")
            self.status.setWordWrap(True)
            layout.addWidget(self.status)
            tools = QHBoxLayout()
            self.search = QLineEdit()
            self.search.setPlaceholderText("Find an imported article or category")
            self.search.setAccessibleName("Search medical library titles and categories")
            tools.addWidget(self.search, 1)
            refresh = QPushButton("Refresh library")
            refresh.clicked.connect(self.reload)
            tools.addWidget(refresh)
            layout.addLayout(tools)
            split = QSplitter(Qt.Orientation.Horizontal)
            self.items = QListWidget()
            self.items.setAccessibleName("Imported medical reference articles")
            split.addWidget(self.items)
            detail = QWidget()
            detail_layout = QVBoxLayout(detail)
            self.detail = QLabel("Select an imported article to view its source status.")
            self.detail.setWordWrap(True)
            self.detail.setTextFormat(Qt.TextFormat.PlainText)
            self.detail.setAlignment(Qt.AlignmentFlag.AlignTop)
            detail_layout.addWidget(self.detail)
            detail_layout.addStretch()
            split.addWidget(detail)
            split.setSizes([420, 600])
            layout.addWidget(split, 1)
            warning = QLabel("Research reference only · Not a diagnosis, medical device, or NASA endorsement")
            warning.setWordWrap(True)
            layout.addWidget(warning)
            self.search.textChanged.connect(self.reload)
            self.items.itemSelectionChanged.connect(self.show_selection)
            self.reload()

        def reload(self) -> None:
            snapshot = self.catalog.list_articles(self.search.text())
            self.current_articles = {a.article_id: a for a in snapshot.articles}
            self.items.clear()
            self.status.setText(f"{snapshot.total}/{MAX_ARTICLES} locally indexed · {snapshot.message}")
            for article in snapshot.articles:
                item = QListWidgetItem(f"{article.slot:03d}  {article.title}  [{article.completeness}]")
                item.setData(Qt.ItemDataRole.UserRole, article.article_id)
                self.items.addItem(item)
            if snapshot.state != "READY":
                self.detail.setText(snapshot.message)
            elif not snapshot.articles:
                self.detail.setText("No matching imported article. Search does not query the internet.")
            else:
                self.detail.setText("Select a local article. Full-text reader and figures require separate verification.")

        def show_selection(self) -> None:
            item = self.items.currentItem()
            if item is None:
                return
            article = self.current_articles.get(item.data(Qt.ItemDataRole.UserRole))
            if article is None:
                return
            self.detail.setText(
                f"{article.title}\n\nCategory: {article.category}\n"
                f"Import completeness flag: {article.completeness}\n"
                f"Source verification flag: {article.source_state}\n"
                f"Source: {article.source_url}\n\n"
                "Flags describe imported metadata, not independent clinical validation. "
                "Full article text and image viewer are not yet implemented."
            )

    return MedicalLibraryPage(parent)
