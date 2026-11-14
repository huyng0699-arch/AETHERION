"""AETHERION Knowledge Observatory — source-first native Qt scientific reader.

The only content sources are AETHERION Server's existing knowledge endpoints.
NASA extracted JSON is not misrepresented as verified source PDFs or medical
advice; original English articles and Vietnamese symptom terms are untouched.
"""
from __future__ import annotations

import html
import json
import math
import os

from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery, QRectF, QSize
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPen, QRadialGradient
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QProgressBar, QPushButton, QSplitter, QTextBrowser,
    QVBoxLayout, QWidget,
)

from .localization import normalize_locale, tr
from .visual_theme import THEMES, palette_for


class KnowledgeOrb(QWidget):
    """Low-rate, decorative native orbital sculpture; not an anatomy 3D model."""

    def __init__(self, parent=None, *, theme="daybreak", mode="light",
                 reduce_motion=False, intensity=48):
        super().__init__(parent)
        self.setFixedSize(154, 154)
        self.theme = theme if theme in THEMES else "daybreak"
        self.mode = mode
        self.reduce_motion = bool(reduce_motion)
        self.intensity = max(0, min(int(intensity), 100))
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(70)
        self.timer.timeout.connect(self._advance)

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_animation()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def set_visuals(self, theme, mode, reduce_motion, intensity):
        self.theme = theme if theme in THEMES else "daybreak"
        self.mode = mode
        self.reduce_motion = bool(reduce_motion)
        self.intensity = max(0, min(int(intensity), 100))
        self._sync_animation()
        self.update()

    def _sync_animation(self):
        if self.isVisible() and not self.reduce_motion and self.intensity > 0:
            if not self.timer.isActive():
                self.timer.start()
        else:
            self.timer.stop()

    def _advance(self):
        self.phase = (self.phase + 0.004 + self.intensity / 11000.0) % 1.0
        self.update()

    def paintEvent(self, event):
        palette = palette_for(self.theme, self.mode)
        primary = QColor(palette.accent)
        second = QColor(palette.second)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        painter.translate(cx, cy)

        aura = QRadialGradient(0, 0, 72)
        soft = QColor(second)
        soft.setAlpha(33 if self.mode != "dark" else 52)
        aura.setColorAt(0, soft)
        transparent = QColor(soft)
        transparent.setAlpha(0)
        aura.setColorAt(1, transparent)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(aura)
        painter.drawEllipse(QRectF(-72, -72, 144, 144))

        for j, angle in enumerate((-28, 52, 110)):
            painter.save()
            painter.rotate(angle + (self.phase * 28 if j == 0 else 0))
            edge = QColor(primary if j % 2 else second)
            edge.setAlpha(115 if self.mode == "dark" else 85)
            painter.setPen(QPen(edge, 1.45))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(-58, -21, 116, 42))
            theta = math.tau * (self.phase + j / 3.0)
            px, py = 58 * math.cos(theta), 21 * math.sin(theta)
            painter.setBrush(primary if j % 2 else second)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(px - 3, py - 3, 6, 6))
            painter.restore()

        core = QRadialGradient(-13, -16, 57)
        core.setColorAt(0.0, QColor("#FFFFFF"))
        core.setColorAt(0.15, QColor(second).lighter(160))
        core.setColorAt(0.58, QColor(primary))
        core.setColorAt(1.0, QColor(palette.top))
        painter.setBrush(core)
        contour = QColor(primary)
        contour.setAlpha(145)
        painter.setPen(QPen(contour, 1.25))
        painter.drawEllipse(QRectF(-34, -34, 68, 68))
        painter.end()


class KnowledgeBrowser(QWidget):
    """Source-backed native search and article reading with bilingual UI chrome."""

    def __init__(self, parent=None, api_url: str | None = None, *, locale="vi",
                 theme="daybreak", mode="light", reduce_motion=False, intensity=48):
        super().__init__(parent)
        self.setObjectName("aetherionKnowledgeBrowser")
        self.language = normalize_locale(locale)
        self.theme_name = theme
        self.mode_name = mode
        self.api_url = (api_url or os.environ.get(
            "AETHERION_API_URL", "http://127.0.0.1:8765")).rstrip("/")
        self.network = QNetworkAccessManager(self)
        self.current_items: dict[str, dict] = {}
        self.token = 0

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(28, 20, 28, 20)
        self.root.setSpacing(13)

        hero = QFrame()
        hero.setObjectName("contentPanel")
        hero_row = QHBoxLayout(hero)
        hero_row.setContentsMargins(26, 14, 24, 14)
        hero_row.setSpacing(12)
        hero_copy = QVBoxLayout()
        hero_copy.setSpacing(7)
        self.eyebrow = QLabel()
        self.eyebrow.setObjectName("eyebrow")
        hero_copy.addWidget(self.eyebrow)
        self.title = QLabel()
        self.title.setObjectName("heroTitle")
        self.title.setWordWrap(True)
        hero_copy.addWidget(self.title)
        self.lead = QLabel()
        self.lead.setObjectName("heroCopy")
        self.lead.setWordWrap(True)
        hero_copy.addWidget(self.lead)
        hero_row.addLayout(hero_copy, 1)
        self.orb = KnowledgeOrb(self, theme=theme, mode=mode,
                                reduce_motion=reduce_motion, intensity=intensity)
        hero_row.addWidget(self.orb)
        self.root.addWidget(hero)

        dashboard = QHBoxLayout()
        dashboard.setSpacing(12)
        self.source_label = QLabel()
        self.source_label.setObjectName("connectionPill")
        dashboard.addWidget(self.source_label, 2)
        self.matches_label = QLabel("—")
        self.matches_label.setObjectName("connectionPill")
        dashboard.addWidget(self.matches_label, 1)
        self.indexed_label = QLabel("—")
        self.indexed_label.setObjectName("connectionPill")
        dashboard.addWidget(self.indexed_label, 1)
        self.root.addLayout(dashboard)

        controls = QFrame()
        controls.setObjectName("surface")
        filter_row = QHBoxLayout(controls)
        filter_row.setContentsMargins(12, 9, 12, 9)
        filter_row.setSpacing(10)
        self.mode = QComboBox()
        self.mode.setMinimumWidth(235)
        self.mode.setAccessibleName("Knowledge source")
        filter_row.addWidget(self.mode)
        self.query = QLineEdit()
        self.query.setMaxLength(200)
        self.query.setClearButtonEnabled(True)
        filter_row.addWidget(self.query, 1)
        self.search_button = QPushButton()
        self.search_button.setObjectName("primaryAction")
        self.search_button.clicked.connect(self.search)
        filter_row.addWidget(self.search_button)
        self.root.addWidget(controls)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setMaximumHeight(3)
        self.progress.setTextVisible(False)
        self.progress.hide()
        self.root.addWidget(self.progress)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setHandleWidth(8)

        results_panel = QFrame()
        results_panel.setObjectName("contentPanel")
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(14, 12, 14, 14)
        results_layout.setSpacing(10)
        self.results_heading = QLabel()
        self.results_heading.setObjectName("eyebrow")
        results_layout.addWidget(self.results_heading)
        self.results = QListWidget()
        self.results.setSpacing(4)
        self.results.setUniformItemSizes(False)
        self.results.setAccessibleName("Knowledge search results")
        results_layout.addWidget(self.results, 1)
        split.addWidget(results_panel)

        reader_panel = QFrame()
        reader_panel.setObjectName("contentPanel")
        reader_layout = QVBoxLayout(reader_panel)
        reader_layout.setContentsMargins(14, 12, 14, 14)
        reader_layout.setSpacing(10)
        self.reader_heading = QLabel()
        self.reader_heading.setObjectName("eyebrow")
        reader_layout.addWidget(self.reader_heading)
        self.reader = QTextBrowser()
        self.reader.setOpenExternalLinks(False)
        self.reader.anchorClicked.connect(self.open_source)
        self.reader.setAccessibleName("Source-backed scientific reader")
        reader_layout.addWidget(self.reader, 1)
        split.addWidget(reader_panel)
        split.setSizes([380, 910])
        split.setChildrenCollapsible(False)
        self.root.addWidget(split, 1)

        self.status = QLabel()
        self.status.setObjectName("pageHint")
        self.status.setWordWrap(True)
        self.root.addWidget(self.status)
        self.note = QLabel()
        self.note.setObjectName("pageHint")
        self.note.setWordWrap(True)
        self.root.addWidget(self.note)

        self.debounce = QTimer(self)
        self.debounce.setInterval(280)
        self.debounce.setSingleShot(True)
        self.debounce.timeout.connect(self.search)
        self.query.textChanged.connect(lambda _: self.debounce.start())
        self.mode.currentIndexChanged.connect(self.search)
        self.results.currentItemChanged.connect(self.select_item)
        self._retranslate()
        self.search()

    def t(self, key: str, **vars) -> str:
        return tr(self.language, "observatory." + key, **vars)

    def set_locale(self, locale: str):
        self.language = normalize_locale(locale)
        self._retranslate()
        self.search()

    def set_visuals(self, theme, mode, reduce_motion=False, intensity=48):
        self.theme_name, self.mode_name = theme, mode
        self.orb.set_visuals(theme, mode, reduce_motion, intensity)
        selected = self.results.currentItem()
        if selected is not None:
            self.select_item(selected, None)

    def _retranslate(self):
        self.eyebrow.setText(self.t("eyebrow"))
        self.title.setText(self.t("hero"))
        self.lead.setText(self.t("lead"))
        selected_mode = self.mode.currentData()
        self.mode.blockSignals(True)
        self.mode.clear()
        self.mode.addItem(self.t("mode.articles"), "articles")
        self.mode.addItem(self.t("mode.symptoms"), "symptoms")
        self.mode.setCurrentIndex(1 if selected_mode == "symptoms" else 0)
        self.mode.blockSignals(False)
        self.mode.setAccessibleName(self.t("query.accessible"))
        self.query.setPlaceholderText(self.t("query"))
        self.query.setAccessibleName(self.t("query.accessible"))
        self.search_button.setText(self.t("search"))
        self.results_heading.setText(self.t("results"))
        self.reader_heading.setText(self.t("reader"))
        self.results.setAccessibleName(self.t("search.accessible"))
        self.reader.setAccessibleName(self.t("reader.accessible"))
        self.note.setText(self.t("note"))
        self.source_label.setText(self.t("status.disconnected"))
        self.matches_label.setText(self.t("matches") + "  —")
        self.indexed_label.setText(self.t("indexed") + "  —")
        self.status.setText(self.t("offline"))
        self.reader.setPlainText(self.t("reader.empty"))

    def _get(self, route: str, callback):
        reply = self.network.get(QNetworkRequest(QUrl(self.api_url + route)))
        reply.finished.connect(lambda: self._receive(reply, callback))

    def _receive(self, reply, callback):
        try:
            if reply.error():
                callback(None, reply.errorString())
                return
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            callback(data, None)
        except (ValueError, UnicodeError) as exc:
            callback(None, str(exc))
        finally:
            reply.deleteLater()

    def search(self, *_):
        self.token += 1
        token = self.token
        mode = self.mode.currentData()
        target = QUrl(self.api_url + "/api/v1/knowledge/" + mode)
        query = QUrlQuery()
        query.addQueryItem("query", self.query.text().strip())
        query.addQueryItem("limit", "100")
        target.setQuery(query)
        self.status.setText(self.t("loading"))
        self.source_label.setText(self.t("status.disconnected"))
        self.matches_label.setText(self.t("matches") + "  —")
        self.indexed_label.setText(self.t("indexed") + "  —")
        self.current_items = {}
        self.results.clear()
        self.reader.setPlainText(self.t("reader.empty"))
        self.progress.show()
        reply = self.network.get(QNetworkRequest(target))
        reply.finished.connect(lambda: self._complete_search(reply, mode, token))

    def _complete_search(self, reply, mode: str, token: int):
        if token != self.token:
            reply.deleteLater()
            return
        self.progress.hide()

        def received(data, error):
            if error or not isinstance(data, dict) or not isinstance(data.get("items"), list):
                self.status.setText(self.t("failure", error=error or "Invalid response"))
                self.reader.setPlainText(self.t("offline"))
                self.source_label.setText(self.t("status.disconnected"))
                return
            items = data["items"]
            for row in items:
                if not isinstance(row, dict):
                    continue
                label = row.get("title") if mode == "articles" else row.get("name")
                key = row.get("article_id") if mode == "articles" else label
                if not isinstance(key, str) or not key:
                    continue
                words = row.get("text_words", 0)
                sections = row.get("sections", 0)
                item = QListWidgetItem(
                    (self.t("card.article", id=key) if mode == "articles"
                     else self.t("card.symptom")) +
                    "\n" + str(label or self.t("card.fallback")) +
                    (("\n" + self.t("card.words", words=words, sections=sections))
                     if mode == "articles" else "")
                )
                item.setSizeHint(QSize(330, 80 if mode == "articles" else 62))
                item.setData(Qt.ItemDataRole.UserRole, key)
                self.results.addItem(item)
                self.current_items[key] = row
            indexed = data.get("indexed", data.get("total_source_labels"))
            matched = data.get("matched")
            if not isinstance(indexed, int) or not isinstance(matched, int):
                self.status.setText(self.t("failure", error="Invalid index counts"))
                self.source_label.setText(self.t("status.disconnected"))
                self.results.clear()
                return
            self.source_label.setText(self.t("status.connected"))
            self.matches_label.setText(f"{self.t('matches')}  {matched}")
            self.indexed_label.setText(f"{self.t('indexed')}  {indexed}")
            self.status.setText(self.t("summary", matched=matched, indexed=indexed))
            if not self.current_items:
                self.reader.setPlainText(self.t("empty"))

        self._receive(reply, received)

    def select_item(self, current, _previous):
        if current is None:
            return
        key = current.data(Qt.ItemDataRole.UserRole)
        row = self.current_items.get(str(key))
        if not row:
            return
        if self.mode.currentData() == "symptoms":
            self._show_symptom(row)
            return
        # Only stable ID (CLIFF-###) can be sent as a path component.
        if not isinstance(key, str) or len(key) != 9 or not key.startswith("CLIFF-") or not key[6:].isdigit():
            self.reader.setPlainText(self.t("article.failure", error="Invalid ID"))
            return
        self.reader.setPlainText(self.t("article.loading"))
        self._get("/api/v1/knowledge/articles/" + key,
                  lambda obj, err: self._show_article(obj, err, key))

    def _document_header(self, title: str) -> list[str]:
        p = palette_for(self.theme_name, self.mode_name)
        font_family = html.escape(self.font().family() or "Segoe UI", quote=True)
        return [
            f'<html><head><style>'
            f'body{{font-family:"{font_family}",sans-serif;color:{p.text};background:{p.surface};line-height:1.5;}}'
            f'table{{border-collapse:collapse;width:100%;margin:8px 0;border:1px solid {p.border};}}'
            f'th,td{{border:1px solid {p.border};padding:6px 10px;text-align:left;color:{p.text};}}'
            f'tr:nth-child(even){{background:{p.surface_alt};}}'
            f'a{{color:{p.accent};}}'
            f'</style></head><body>',
            '<div style="padding:10px 4px;">',
            '<p style="color:' + p.accent + ';font-weight:700;font-size:12px;">' +
            html.escape(self.t("eyebrow")) + '</p>',
            '<h1 style="font-size:24px;color:' + p.text + ';">' + html.escape(title) + '</h1>',
        ]

    def _show_symptom(self, row):
        title = str(row.get("name") or self.t("card.fallback"))
        chunks = self._document_header(title)
        def details(key, val):
            chunks.append('<p><b>' + html.escape(self.t(key)) + ':</b> ' +
                          html.escape(str(val)) + '</p>')
        details("symptom.aliases", ", ".join(str(x) for x in row.get("aliases", [])))
        details("symptom.routes", ", ".join(str(x) for x in row.get("routes", [])))
        details("symptom.review", row.get("review_state", "UNKNOWN"))
        details("symptom.legacy", row.get("legacy_tier_unreviewed", "UNKNOWN"))
        chunks.append('<p><em>' + html.escape(self.t("symptom.notice")) + '</em></p></div></body></html>')
        self.reader.setHtml("\n".join(chunks))

    def _show_article(self, obj, error, key):
        current = self.results.currentItem()
        if current is None or current.data(Qt.ItemDataRole.UserRole) != key:
            return
        if error or not isinstance(obj, dict):
            self.reader.setPlainText(self.t("article.failure", error=error or "Invalid JSON"))
            return
        summary = obj.get("summary")
        source = obj.get("source")
        if not isinstance(summary, dict) or not isinstance(source, dict):
            self.reader.setPlainText(self.t("article.failure", error="Invalid article metadata"))
            return
        if summary.get("article_id") != key:
            self.reader.setPlainText(self.t("article.failure", error="Article identity mismatch"))
            return
        title = str(summary.get("title") or key)
        chunks = self._document_header(title)
        chunks.append('<p><b>' + html.escape(self.t("article.note")) + '</b></p>')
        chunks.append('<h3>' + html.escape(self.t("article.source")) + '</h3>')
        chunks.append('<p>' + html.escape(key) + ' · ' +
                      html.escape(str(summary.get("category", ""))) + '</p>')
        source_url = source.get("final_url") or source.get("source_url")
        if isinstance(source_url, str) and source_url.startswith("https://"):
            safe = html.escape(source_url, quote=True)
            chunks.append('<p><a href="' + safe + '">' +
                          html.escape(self.t("article.open")) + '</a></p>')
        else:
            chunks.append('<p>' + html.escape(self.t("source.unknown")) + '</p>')

        chunks.append('<h3>' + html.escape(self.t("article.sections")) + '</h3>')
        sections = obj.get("sections")
        if isinstance(sections, list):
            for section in sections:
                if not isinstance(section, dict):
                    continue
                chunks.append('<h3>' + html.escape(str(section.get("heading", ""))) + '</h3>')
                chunks.append('<p style="white-space:pre-wrap">' +
                              html.escape(str(section.get("text_content", ""))).replace("\n", "<br>") + '</p>')
        chunks.append('<h3>' + html.escape(self.t("article.tables")) + '</h3>')
        tables = obj.get("tables")
        if isinstance(tables, list):
            for table in tables:
                if not isinstance(table, dict):
                    continue
                chunks.append('<h4>' + html.escape(str(table.get("title", ""))) + '</h4>')
                rows = table.get("rows")
                if isinstance(rows, list):
                    chunks.append('<table border="1" cellpadding="5">')
                    for row in rows[:120]:
                        if isinstance(row, list):
                            chunks.append("<tr>" + "".join("<td>" + html.escape(str(cell)) +
                                          "</td>" for cell in row[:20]) + "</tr>")
                    chunks.append("</table>")
        refs = obj.get("references")
        chunks.append('<h3>' + html.escape(self.t("article.references")) + '</h3><ol>')
        if isinstance(refs, list):
            for ref in refs[:250]:
                if isinstance(ref, dict):
                    chunks.append('<li>' + html.escape(str(ref.get("label", ""))) + '</li>')
        chunks.append("</ol>")
        chunks.append('<h3>' + html.escape(self.t("article.images")) + '</h3>')
        chunks.append('<p>' + html.escape(self.t("article.images.notice")) + '</p>')
        chunks.append('<p><em>' + html.escape(self.t("safety")) + '</em></p></div></body></html>')
        self.reader.setHtml("\n".join(chunks))

    def open_source(self, url: QUrl):
        if (url.scheme().lower() == "https" and url.host()
                and not url.userName() and not url.password()):
            QDesktopServices.openUrl(url)


def build_knowledge_browser(parent=None, **kwargs) -> KnowledgeBrowser:
    return KnowledgeBrowser(parent, **kwargs)
