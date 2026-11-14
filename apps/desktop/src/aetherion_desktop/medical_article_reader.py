"""Q-0426: native offline CliFF article reader (implementation, not clinical approval).

Only the existing local SQLite library is read. No network request, WebEngine,
generated clinical record, or claim that an imported record is verified.
The UI is constructed lazily so provenance queries can run without PySide6.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

DEFAULT_LIBRARY = (
    Path(__file__).resolve().parents[4]
    / "knowledge/nasa/cliff_119_2023/AETHERION_NASA_CLIFF_119.sqlite"
)
ALLOWED_RASTER = {"image/png", "image/jpeg", "image/webp"}


class LibraryUnavailable(RuntimeError):
    """Missing, unreadable, incompatible or corrupt local scientific database."""


@dataclass(frozen=True)
class ArticleBlock:
    kind: str
    ordinal: int
    heading: str
    text: str
    rows: tuple[tuple[str, ...], ...]
    page: str
    anchor: str


@dataclass(frozen=True)
class ArticleImage:
    media_id: str
    content: bytes
    mime: str
    caption: str
    alt_text: str
    attribution: str
    license_name: str
    source_url: str
    page: str


@dataclass(frozen=True)
class ArticleReference:
    label: str
    url: str
    page: str


@dataclass(frozen=True)
class OfflineArticle:
    article_id: str
    title: str
    category: str
    completeness: str
    source_state: str
    source_url: str
    source_license: str
    source_attribution: str
    source_sha256: str
    blocks: tuple[ArticleBlock, ...]
    images: tuple[ArticleImage, ...]
    image_warnings: tuple[str, ...]
    references: tuple[ArticleReference, ...]
    previous_id: str | None
    next_id: str | None


def _page(start: Any, end: Any = None) -> str:
    if start is None:
        return "Source page not supplied"
    if end is not None and end != start:
        return f"Source pages {start}-{end}"
    return f"Source page {start}"


def _table_rows(value: str) -> tuple[tuple[str, ...], ...]:
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError) as exc:
        raise LibraryUnavailable("Article table JSON is malformed") from exc
    if isinstance(parsed, dict):
        header = parsed.get("headers")
        rows = parsed.get("rows", [])
        if isinstance(header, list):
            rows = [header, *rows] if isinstance(rows, list) else None
    else:
        rows = parsed
    if not isinstance(rows, list) or any(not isinstance(row, list) for row in rows):
        raise LibraryUnavailable("Article table must contain ordered rows")
    if len(rows) > 10000 or any(len(row) > 100 for row in rows):
        raise LibraryUnavailable("Article table exceeds safe display limits")
    return tuple(tuple(str(cell) if cell is not None else "" for cell in row) for row in rows)


def load_article(db_path: str | Path, article_id: str) -> OfflineArticle:
    """Read an imported article without writing to SQLite or creating fake data."""
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise LibraryUnavailable("Offline scientific library file is missing; 0 verified articles available")
    if not isinstance(article_id, str) or not article_id.strip():
        raise ValueError("Select a specific imported article ID")
    try:
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            row = db.execute(
                """SELECT a.article_id,a.slot,a.display_title,a.category,
                   a.completeness_state,s.verification_state,s.source_url,
                   s.license_identifier,s.attribution,s.content_sha256
                   FROM articles a JOIN sources s ON a.source_id=s.source_id
                   WHERE a.article_id=?""", (article_id,)
            ).fetchone()
            if row is None:
                raise LibraryUnavailable("Article not found in local SQLite; no online fallback")
            items: list[ArticleBlock] = []
            for section in db.execute(
                """SELECT ordinal,heading,text_content,page_start,page_end,source_anchor
                   FROM article_sections WHERE article_id=? ORDER BY ordinal""", (article_id,)
            ):
                items.append(ArticleBlock(
                    "section", section["ordinal"], section["heading"], section["text_content"],
                    (), _page(section["page_start"], section["page_end"]),
                    section["source_anchor"] or "",
                ))
            for table in db.execute(
                """SELECT ordinal,title,rows_json,page_number,source_anchor
                   FROM article_tables WHERE article_id=? ORDER BY ordinal""", (article_id,)
            ):
                items.append(ArticleBlock(
                    "table", table["ordinal"], table["title"], "",
                    _table_rows(table["rows_json"]), _page(table["page_number"]),
                    table["source_anchor"] or "",
                ))
            items.sort(key=lambda b: (b.ordinal, 0 if b.kind == "section" else 1))
            images: list[ArticleImage] = []
            warnings: list[str] = []
            for media in db.execute(
                """SELECT media_id,data,mime_type,sha256,caption,alt_text,
                          attribution,license_identifier,source_url,page_number,usage_review
                   FROM media WHERE article_id=? ORDER BY ordinal""", (article_id,)
            ):
                media_id = str(media["media_id"])
                raw = bytes(media["data"])
                digest = hashlib.sha256(raw).hexdigest()
                fields = (
                    media["caption"], media["alt_text"], media["attribution"],
                    media["license_identifier"], media["source_url"],
                )
                if media["usage_review"] != "APPROVED":
                    warnings.append(f"{media_id}: image not independently rights-approved")
                    continue
                if digest != media["sha256"] or not all(isinstance(v, str) and v.strip() for v in fields):
                    warnings.append(f"{media_id}: corrupted bytes or incomplete image attribution")
                    continue
                if media["mime_type"] not in ALLOWED_RASTER:
                    warnings.append(f"{media_id}: format needs a separate verified native decoder")
                    continue
                if len(raw) > 25 * 1024 * 1024:
                    warnings.append(f"{media_id}: image exceeds safe display size")
                    continue
                images.append(ArticleImage(
                    media_id, raw, media["mime_type"], media["caption"], media["alt_text"],
                    media["attribution"], media["license_identifier"], media["source_url"],
                    _page(media["page_number"]),
                ))
            references = tuple(ArticleReference(
                ref["label"], ref["citation_url"], _page(ref["page_number"])
            ) for ref in db.execute(
                """SELECT label,citation_url,page_number FROM source_references
                   WHERE article_id=? ORDER BY ordinal""", (article_id,)
            ))
            earlier = db.execute(
                "SELECT article_id FROM articles WHERE slot < ? ORDER BY slot DESC LIMIT 1",
                (row["slot"],)
            ).fetchone()
            later = db.execute(
                "SELECT article_id FROM articles WHERE slot > ? ORDER BY slot LIMIT 1",
                (row["slot"],)
            ).fetchone()
            return OfflineArticle(
                article_id=row["article_id"], title=row["display_title"],
                category=row["category"], completeness=row["completeness_state"],
                source_state=row["verification_state"], source_url=row["source_url"],
                source_license=row["license_identifier"], source_attribution=row["attribution"],
                source_sha256=row["content_sha256"] or "NOT VERIFIED",
                blocks=tuple(items), images=tuple(images), image_warnings=tuple(warnings),
                references=references, previous_id=earlier["article_id"] if earlier else None,
                next_id=later["article_id"] if later else None,
            )
    except (sqlite3.DatabaseError, OSError) as exc:
        raise LibraryUnavailable("Unable to read local scientific library safely") from exc


def build_medical_article_reader(db_path: str | Path = DEFAULT_LIBRARY, parent=None):
    """Build a genuine native QWidget. Call page.open_article(article_id).

    Navigation/page host is responsible for presenting this view; Q-0437 owns
    the main window, so this component intentionally does not edit it.
    """
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QTableWidget, QTableWidgetItem,
    )

    def label(text: str, *, heading: bool = False) -> QLabel:
        widget = QLabel(text)
        widget.setTextFormat(Qt.TextFormat.PlainText)
        widget.setWordWrap(True)
        widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if heading:
            font = widget.font()
            font.setBold(True)
            font.setPointSize(max(12, font.pointSize() + 2))
            widget.setFont(font)
        return widget

    class MedicalArticleReaderPage(QWidget):
        back_requested = Signal()

        def __init__(self, parent_widget=None):
            super().__init__(parent_widget)
            self.database_path = Path(db_path)
            self.current_article: OfflineArticle | None = None
            outer = QVBoxLayout(self)
            toolbar = QHBoxLayout()
            back = QPushButton("Back to library")
            back.clicked.connect(lambda checked=False: self.back_requested.emit())
            toolbar.addWidget(back)
            self.previous = QPushButton("Previous article")
            self.previous.clicked.connect(lambda: self._navigate(-1))
            toolbar.addWidget(self.previous)
            self.next = QPushButton("Next article")
            self.next.clicked.connect(lambda: self._navigate(1))
            toolbar.addWidget(self.next)
            outer.addLayout(toolbar)
            self.scroll = QScrollArea(self)
            self.scroll.setWidgetResizable(True)
            self.container = QWidget()
            self.content = QVBoxLayout(self.container)
            self.scroll.setWidget(self.container)
            outer.addWidget(self.scroll, 1)
            self._clear()
            self.content.addWidget(label("Select a locally imported article to read."))
            self.previous.setEnabled(False)
            self.next.setEnabled(False)

        def _clear(self) -> None:
            while self.content.count():
                child = self.content.takeAt(0)
                widget = child.widget()
                if widget is not None:
                    widget.deleteLater()

        def _navigate(self, direction: int) -> None:
            document = self.current_article
            if document is None:
                return
            target = document.previous_id if direction < 0 else document.next_id
            if target:
                self.open_article(target)

        def open_article(self, article_id: str) -> bool:
            self._clear()
            try:
                document = load_article(self.database_path, article_id)
            except (LibraryUnavailable, ValueError) as exc:
                self.current_article = None
                self.previous.setEnabled(False)
                self.next.setEnabled(False)
                self.content.addWidget(label(f"Article unavailable: {exc}"))
                return False
            self.current_article = document
            self.previous.setEnabled(bool(document.previous_id))
            self.next.setEnabled(bool(document.next_id))
            self.content.addWidget(label(document.title, heading=True))
            self.content.addWidget(label(
                f"Category: {document.category} | Content: {document.completeness}"
                f" | NASA/source verification: {document.source_state}"
            ))
            self.content.addWidget(label(
                "Scientific reference only; not clinically validated treatment guidance. "
                "Labels in an imported file are not independent NASA verification."
            ))
            self.content.addWidget(label(
                f"Original source: {document.source_url}\n"
                f"Attribution: {document.source_attribution}\n"
                f"License: {document.source_license}\n"
                f"Original SHA-256: {document.source_sha256}"
            ))
            if not document.blocks:
                self.content.addWidget(label("No original source text or tables were imported."))
            for block in document.blocks:
                self.content.addWidget(label(block.heading, heading=True))
                self.content.addWidget(label(
                    f"{block.page} | Source anchor: {block.anchor or 'not provided'}"
                ))
                if block.kind == "section":
                    self.content.addWidget(label(block.text))
                else:
                    row_count = len(block.rows)
                    columns = max((len(row) for row in block.rows), default=0)
                    if row_count and columns:
                        table = QTableWidget(row_count, columns, self.container)
                        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                        for r, row in enumerate(block.rows):
                            for c, value in enumerate(row):
                                table.setItem(r, c, QTableWidgetItem(value))
                        table.setMinimumHeight(min(360, max(100, row_count * 32 + 40)))
                        table.setAccessibleName(block.heading)
                        self.content.addWidget(table)
                    else:
                        self.content.addWidget(label("No rows in imported source table."))
            self.content.addWidget(label("Rights-reviewed source illustrations", heading=True))
            if not document.images:
                self.content.addWidget(label("No rights-approved offline images available."))
            for illustration in document.images:
                pixmap = QPixmap()
                if not pixmap.loadFromData(illustration.content):
                    self.content.addWidget(label(
                        f"{illustration.media_id}: invalid image bytes; display withheld."
                    ))
                    continue
                picture = QLabel()
                picture.setPixmap(pixmap.scaledToWidth(
                    min(720, max(1, pixmap.width())),
                    Qt.TransformationMode.SmoothTransformation
                ))
                picture.setAccessibleName(illustration.alt_text)
                self.content.addWidget(picture)
                self.content.addWidget(label(
                    f"{illustration.caption}\nAlt: {illustration.alt_text}\n"
                    f"{illustration.page} | Attribution: {illustration.attribution}\n"
                    f"License: {illustration.license_name} | Source: {illustration.source_url}"
                ))
            for warning in document.image_warnings:
                self.content.addWidget(label(f"Image withheld: {warning}"))
            self.content.addWidget(label("Citations", heading=True))
            if not document.references:
                self.content.addWidget(label("No source citations were imported."))
            for ref in document.references:
                self.content.addWidget(label(f"{ref.label} | {ref.page}\n{ref.url}"))
            self.content.addStretch()
            self.scroll.verticalScrollBar().setValue(0)
            return True

    return MedicalArticleReaderPage(parent)
