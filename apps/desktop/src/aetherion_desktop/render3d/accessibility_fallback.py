"""Native keyboard-operable 2D anatomy *list*, not a pretend 3D mesh viewer.

The existing atlas3d.approved_models() verifies local mesh bytes and license
metadata before they may be listed here. Rendering needs Qt widgets only:
no OpenGL, VTK, PyVistaQt or GPU requirement. No clinical interpretation,
patient observations or simulated medical content.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlsplit

from ..localization import normalize_locale, tr


@dataclass(frozen=True)
class AccessibleAnatomyEntry:
    anatomical_id: str
    title_vi: str
    title_en: str
    source_url: str
    author: str
    license: str
    sha256: str

    def title(self, locale: str) -> str:
        return self.title_en if normalize_locale(locale) == "en" else self.title_vi


def prepare_accessible_entries(verified_models: Iterable[Mapping]) -> tuple[AccessibleAnatomyEntry, ...]:
    """Project only SHA-verified source-backed models into a stable 2D index.

    Callers must supply records from atlas3d.approved_models(), not arbitrary
    remote catalogs. A record without a checked local file is not displayed.
    """
    entries = {}
    for record in verified_models:
        if not isinstance(record, Mapping) or record.get("rights_status") != "APPROVED":
            continue
        ident = record.get("anatomical_id")
        source = record.get("source_url")
        author = record.get("author")
        license_name = record.get("license")
        digest = record.get("sha256")
        filename = record.get("resolved_path")
        if not all(isinstance(s, str) and s.strip() for s in
                   (ident, source, author, license_name, digest, filename)):
            continue
        parts = urlsplit(source)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            continue
        if not isinstance(digest, str) or len(digest) != 64 or any(
                ch not in "0123456789abcdefABCDEF" for ch in digest):
            continue
        if not Path(filename).is_file():
            continue
        # The owning loader already hashed the entire file. Never accept a
        # remote catalog entry that merely *claims* it is approved.
        title_vi = str(record.get("title_vi") or ident)
        title_en = str(record.get("title_en") or ident)
        entries[ident] = AccessibleAnatomyEntry(
            ident, title_vi, title_en, source, author, license_name, digest.lower()
        )
    return tuple(entries[key] for key in sorted(entries))


def build_accessible_anatomy_2d(parent=None, *, locale="vi"):
    """Create the genuine 2D fallback without requiring any 3D libraries.

    The caller inserts the returned QWidget in the existing Desktop shell.
    Unsupported GPUs still allow list, selection, keyboard, provenance and
    opening the source; the UI clearly calls this a 2D fallback.
    """
    from PySide6.QtCore import Qt, QUrl, Signal
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QAbstractItemView, QFrame, QHBoxLayout, QLabel, QListWidget,
        QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
    )
    from ..atlas3d import approved_models

    entries = prepare_accessible_entries(approved_models())
    by_id = {entry.anatomical_id: entry for entry in entries}

    class AnatomyFallback2D(QWidget):
        structure_selected = Signal(str)

        def __init__(self):
            super().__init__(parent)
            self.locale = normalize_locale(locale)
            self.setObjectName("aetherionAnatomy2D")
            self.setAccessibleName("2D")
            lay = QVBoxLayout(self)
            lay.setContentsMargins(16, 12, 16, 12)

            self.heading = QLabel()
            lay.addWidget(self.heading)
            self.warning = QLabel()
            self.warning.setWordWrap(True)
            lay.addWidget(self.warning)

            self.structures = QListWidget(self)
            self.structures.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.structures.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.structures.currentItemChanged.connect(self._selected)
            self.structures.itemActivated.connect(self._activate)
            lay.addWidget(self.structures, 1)

            detail_frame = QFrame(self)
            detail_lay = QHBoxLayout(detail_frame)
            self.provenance = QLabel()
            self.provenance.setWordWrap(True)
            self.provenance.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            detail_lay.addWidget(self.provenance, 1)
            self.source_button = QPushButton()
            self.source_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.source_button.clicked.connect(self._open_source)
            detail_lay.addWidget(self.source_button)
            lay.addWidget(detail_frame)
            QWidget.setTabOrder(self.structures, self.source_button)

            self.set_locale(self.locale)

        def current_id(self) -> str | None:
            selected = self.structures.currentItem()
            if selected is None:
                return None
            ident = selected.data(Qt.ItemDataRole.UserRole)
            return ident if ident in by_id else None

        def set_locale(self, language: str) -> None:
            """Change the presentation only; never mutate source or identity."""
            self.locale = normalize_locale(language)
            selected = self.current_id()
            self.heading.setText(tr(self.locale, "main.landing.atlas.title") + " · 2D")
            self.heading.setAccessibleName(self.heading.text())
            self.warning.setText(tr(self.locale, "explore.sourceNotice"))
            self.source_button.setText(tr(self.locale, "mission.source"))
            self.source_button.setAccessibleName(tr(self.locale, "mission.source"))
            self.structures.setAccessibleName(self.heading.text())
            self.structures.blockSignals(True)
            self.structures.clear()
            for entry in entries:
                item = QListWidgetItem(entry.title(self.locale))
                item.setData(Qt.ItemDataRole.UserRole, entry.anatomical_id)
                item.setToolTip(entry.source_url)
                self.structures.addItem(item)
                if entry.anatomical_id == selected:
                    self.structures.setCurrentItem(item)
            if selected is None and entries:
                self.structures.setCurrentRow(0)
            self.structures.blockSignals(False)
            self._selected()
            if not entries:
                self.provenance.setText(tr(self.locale, "main.landing.unavailable"))

        def _selected(self, *_):
            ident = self.current_id()
            record = by_id.get(ident)
            self.source_button.setEnabled(record is not None)
            if record is None:
                return
            # These fields are unchanged metadata from the SHA-checked model.
            self.provenance.setText(
                tr(self.locale, "mission.source") + ": " +
                record.author + " · " + record.license + " · SHA-256 " +
                record.sha256[:16] + "…\n" +
                tr(self.locale, "explore.sourceNotice")
            )

        def _activate(self, item):
            ident = item.data(Qt.ItemDataRole.UserRole)
            if ident in by_id:
                self.structure_selected.emit(ident)

        def _open_source(self):
            entry = by_id.get(self.current_id())
            if entry is not None:
                QDesktopServices.openUrl(QUrl(entry.source_url))

    return AnatomyFallback2D()
