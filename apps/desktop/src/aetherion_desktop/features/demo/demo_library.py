"""Native source-backed scientific library for the fully loaded hackathon demo."""
from __future__ import annotations

from html import escape
import json

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSplitter, QTextBrowser, QVBoxLayout, QWidget,
)

from ...localization import normalize_locale, tr


def _safe_url(value: object) -> str:
    if not isinstance(value, str):
        return ""
    url = QUrl(value)
    host = url.host().lower()
    if (url.scheme() != "https" or url.userName() or url.password()
            or not (host == "nasa.gov" or host.endswith(".nasa.gov")
                    or host == "spaceappschallenge.org"
                    or host.endswith(".spaceappschallenge.org"))):
        return ""
    return value


def _json_present(value: object, *, depth: int = 0) -> str:
    """Preserve NASA's exact content; escape every atom and bound nested HTML."""
    if depth > 8:
        return "<p>…</p>"
    if isinstance(value, str):
        return escape(value).replace("\n", "<br>")
    if isinstance(value, (float, int, bool)):
        return escape(str(value))
    if isinstance(value, dict):
        return "".join("<p><b>" + escape(str(k)) + "</b>: " +
                       _json_present(v, depth=depth+1) + "</p>" for k,v in value.items())
    if isinstance(value, list):
        return "<ul>" + "".join("<li>" + _json_present(v, depth=depth+1) +
                                 "</li>" for v in value) + "</ul>"
    return "—"


class DemoFullScienceLibrary(QWidget):
    """Full local research record reader, never a medical-judgement engine."""
    back_requested = Signal()

    def __init__(self, parent=None, *, locale="vi"):
        super().__init__(parent)
        self.language = normalize_locale(locale)
        self.bundle = None
        self.current_kind = "cliff"
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 19, 25, 19)
        root.setSpacing(12)

        header = QHBoxLayout()
        self.breadcrumb = QLabel()
        self.breadcrumb.setObjectName("eyebrow")
        header.addWidget(self.breadcrumb, 1)
        self.back_button = QPushButton()
        self.back_button.setObjectName("navButton")
        self.back_button.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_button)
        root.addLayout(header)

        self.title = QLabel()
        self.title.setObjectName("heroTitle")
        root.addWidget(self.title)
        self.description = QLabel()
        self.description.setObjectName("pageHint")
        self.description.setWordWrap(True)
        root.addWidget(self.description)

        controls = QFrame()
        controls.setObjectName("surface")
        r = QHBoxLayout(controls)
        r.setContentsMargins(13, 11, 13, 11)
        self.kind = QComboBox()
        self.kind.setMinimumWidth(230)
        self.kind.currentIndexChanged.connect(self._populate)
        r.addWidget(self.kind)
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.setMaxLength(120)
        self.search.textChanged.connect(self._populate)
        r.addWidget(self.search, 1)
        self.total = QLabel("—")
        self.total.setObjectName("connectionPill")
        r.addWidget(self.total)
        root.addWidget(controls)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(7)
        left = QFrame()
        left.setObjectName("contentPanel")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(11, 11, 11, 11)
        self.items = QListWidget()
        self.items.setSpacing(3)
        self.items.currentItemChanged.connect(self._selected)
        left_layout.addWidget(self.items)
        split.addWidget(left)
        right = QFrame()
        right.setObjectName("contentPanel")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(11, 11, 11, 11)
        self.reader = QTextBrowser()
        self.reader.setOpenExternalLinks(False)
        self.reader.anchorClicked.connect(self._open_source)
        right_layout.addWidget(self.reader)
        split.addWidget(right)
        split.setSizes([355, 950])
        root.addWidget(split, 1)

        self.warning = QLabel()
        self.warning.setWordWrap(True)
        self.warning.setObjectName("pageHint")
        root.addWidget(self.warning)
        self.set_locale(locale)

    def t(self, key: str, **parameters) -> str:
        return tr(self.language, "demo.full." + key, **parameters)

    def set_locale(self, language: str):
        self.language = normalize_locale(language)
        self.breadcrumb.setText(self.t("breadcrumb"))
        self.back_button.setText(self.t("back"))
        self.title.setText(self.t("title"))
        self.description.setText(self.t("description"))
        self.search.setPlaceholderText(self.t("search"))
        self.search.setAccessibleName(self.t("searchAccessible"))
        self.items.setAccessibleName(self.t("itemsAccessible"))
        self.reader.setAccessibleName(self.t("readerAccessible"))
        self.warning.setText(self.t("warning"))
        selected = self.kind.currentData()
        self.kind.blockSignals(True)
        self.kind.clear()
        for key in ("cliff", "hazards", "symptoms"):
            self.kind.addItem(self.t("kind." + key), key)
        self.kind.setCurrentIndex(max(0, self.kind.findData(selected)))
        self.kind.blockSignals(False)
        self._populate()

    def set_bundle(self, bundle: dict):
        """Install validated objects loaded by the worker in one atomic UI step."""
        self.bundle = bundle
        self._populate()

    def show_kind(self, kind: str):
        i = self.kind.findData(kind)
        if i >= 0:
            self.kind.setCurrentIndex(i)
        else:
            self._populate()

    def _records(self):
        if not self.bundle:
            return ()
        key = self.kind.currentData()
        return self.bundle.get({"cliff":"articles", "hazards":"hazards",
                                "symptoms":"glossary"}.get(key,"articles"), ())

    def _populate(self, *_):
        records = self._records()
        kind = self.kind.currentData() or "cliff"
        term = self.search.text().strip().casefold()
        self.items.blockSignals(True)
        self.items.clear()
        for index, record in enumerate(records):
            if kind == "cliff":
                ident = str(record.get("article_id") or "")
                name = str(record.get("display_title") or ident)
                searchable = (name + " " + str(record.get("category") or "") +
                              " " + ident).casefold()
                label = ident + "   " + name
            elif kind == "hazards":
                name = str(record.get("title") or record.get("hazard_id") or "")
                searchable = name.casefold()
                label = name
            else:
                name = str(record.get("name") or "")
                aliases = record.get("aliases")
                searchable = (name + " " + " ".join(str(x) for x in aliases
                                                     if isinstance(x, str))
                              if isinstance(aliases, list) else name).casefold()
                label = name
            if term and term not in searchable:
                continue
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, index)
            self.items.addItem(item)
        self.items.blockSignals(False)
        self.total.setText(self.t("matchCount", count=self.items.count(),
                                  total=len(records)))
        if self.items.count():
            self.items.setCurrentRow(0)
        else:
            self.reader.setPlainText(self.t("empty"))

    def _selected(self, current, _previous):
        if current is None:
            return
        index = current.data(Qt.ItemDataRole.UserRole)
        records = self._records()
        if not isinstance(index, int) or not 0 <= index < len(records):
            return
        kind = self.kind.currentData()
        if kind == "cliff":
            self._show_cliff(records[index])
        elif kind == "hazards":
            self._show_hazard(records[index])
        else:
            self._show_symptom(records[index])

    def _show_cliff(self, article):
        heading = escape(str(article.get("display_title") or article.get("article_id")))
        source = article.get("source") or {}
        ident = str(article.get("article_id"))
        parts = ["<h2>" + heading + "</h2>",
                 "<p><b>" + escape(ident) + "</b> · " +
                 escape(str(article.get("category", ""))) + "</p>",
                 "<p><em>" + escape(self.t("cliffCaveat")) + "</em></p>"]
        original = _safe_url(source.get("final_url") or source.get("source_url"))
        if original:
            parts.append('<p><a href="' + escape(original, quote=True) + '">' +
                         escape(self.t("source")) + "</a></p>")
        for section in article.get("sections", []):
            if isinstance(section, dict):
                parts.append("<h3>" + escape(str(section.get("heading") or "")) +
                             "</h3><p>" + _json_present(section.get("text_content", "")) +
                             "</p>")
        for table in article.get("tables", []):
            if not isinstance(table, dict):
                continue
            parts.append("<h3>" + escape(str(table.get("title", ""))) + "</h3>")
            cells = table.get("rows")
            if isinstance(cells, list):
                parts.append('<table border="1" cellpadding="5">')
                for row in cells:
                    if isinstance(row, list):
                        parts.append("<tr>" + "".join("<td>" + _json_present(v) +
                                     "</td>" for v in row) + "</tr>")
                parts.append("</table>")
        references = article.get("references", [])
        parts.append("<h3>" + escape(self.t("references")) + "</h3>")
        if isinstance(references, list):
            for citation in references:
                parts.append("<p>" + _json_present(citation) + "</p>")
        parts.append("<p><em>" + escape(self.t("imageNotice")) + "</em></p>")
        self.reader.setHtml("\n".join(parts))

    def _show_hazard(self, record):
        parts = ["<h2>" + escape(str(record.get("title", ""))) + "</h2>",
                 "<p><em>" + escape(self.t("hazardCaveat")) + "</em></p>"]
        for key, value in record.items():
            if key == "primary_sources":
                parts.append("<h3>" + escape(self.t("source")) + "</h3>")
                if isinstance(value, list):
                    for source in value:
                        if not isinstance(source, dict):
                            continue
                        link = _safe_url(source.get("url"))
                        if link:
                            parts.append('<p><a href="' + escape(link, quote=True) + '">' +
                                         escape(str(source.get("publisher") or "NASA")) +
                                         "</a></p>")
            elif key not in ("schema_version", "hazard_id", "quest_id"):
                parts.append("<h4>" + escape(key.replace("_", " ").title()) + "</h4>")
                parts.append(_json_present(value))
        self.reader.setHtml("\n".join(parts))

    def _show_symptom(self, record):
        parts = ["<h2>" + escape(str(record.get("name", ""))) + "</h2>",
                 "<p><em>" + escape(self.t("symptomCaveat")) + "</em></p>"]
        for key, value in record.items():
            if key in ("initialReason", "tier"):
                continue  # Unreviewed clinical claims must not be promoted to advice.
            parts.append("<p><b>" + escape(key) + ":</b> " + _json_present(value) + "</p>")
        self.reader.setHtml("\n".join(parts))

    def _open_source(self, url: QUrl):
        if _safe_url(url.toString()):
            QDesktopServices.openUrl(url)
