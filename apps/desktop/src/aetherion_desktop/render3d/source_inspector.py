"""Bilingual native anatomy source/credit inspector (Q-0134).

An approved manifest entry is not an independent legal audit. File hash checks
are distinguished from remote catalog assertions. Original author, license,
citation, version and SHA-256 stay unmodified; no clinical claim is generated.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Mapping
from urllib.parse import urlsplit

MAX_INSPECT_FILE_BYTES = 40 * 1024 * 1024
_HEX64 = re.compile(r"^[a-fA-F0-9]{64}$")
_TEXT = {
    "vi": {
        "title": "Chi tiết nguồn mô hình giải phẫu",
        "anatomy": "Cấu trúc", "author": "Tác giả", "license": "Giấy phép đã khai báo",
        "version": "Phiên bản được khai báo", "original_blob": "Git blob gốc",
        "source": "URL nguồn", "citation": "Trích dẫn khoa học",
        "sha": "SHA-256 dự kiến", "verification": "Kiểm tra tệp trên máy",
        "verified": "Đã kiểm tra SHA-256 tệp cục bộ",
        "not_verified": "Chưa xác minh tệp cục bộ; chỉ có metadata",
        "unknown": "Chưa được cung cấp", "open": "Mở nguồn HTTPS",
        "warning": "Chỉ phục vụ giáo dục. Metadata không thay thế thẩm định giấy phép hoặc xác nhận lâm sàng.",
    },
    "en": {
        "title": "Anatomy model source and credits",
        "anatomy": "Structure", "author": "Author", "license": "Declared license",
        "version": "Reported version", "original_blob": "Original Git blob",
        "source": "Source URL", "citation": "Scientific citation",
        "sha": "Expected SHA-256", "verification": "Local file verification",
        "verified": "Local file SHA-256 verified",
        "not_verified": "Local file not verified; metadata only",
        "unknown": "Not provided", "open": "Open HTTPS source",
        "warning": "Educational use only. Metadata does not establish license clearance or clinical validation.",
    },
}


@dataclass(frozen=True)
class SourceEvidence:
    anatomical_id: str
    author: str
    license: str
    version: str | None
    original_git_blob: str | None
    citation: str
    source_url: str
    expected_sha256: str
    local_hash_verified: bool


def source_evidence(model: Mapping) -> SourceEvidence:
    """Read the selected approved model; reject a forged/unsafe source URL."""
    if not isinstance(model, Mapping) or model.get("rights_status") != "APPROVED":
        raise ValueError("No rights-approved anatomy registry entry selected")
    keys = ("anatomical_id", "author", "license", "citation", "source_url", "sha256")
    if any(not isinstance(model.get(k), str) or not model[k].strip() for k in keys):
        raise ValueError("Missing credited scientific source metadata")
    url = model["source_url"].strip()
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or
            parsed.username is not None or parsed.password is not None):
        raise ValueError("Anatomy source URL must be credential-free HTTPS")
    digest = model["sha256"].strip()
    if not _HEX64.fullmatch(digest):
        raise ValueError("Invalid expected original model SHA-256")
    version = model.get("version")
    version = version.strip() if isinstance(version, str) and version.strip() else None
    original = model.get("original_git_blob")
    original = original.strip() if isinstance(original, str) and original.strip() else None
    verified = False
    local = model.get("resolved_path")
    if isinstance(local, str) and local:
        file = Path(local)
        try:
            if file.is_file() and 0 < file.stat().st_size <= MAX_INSPECT_FILE_BYTES:
                verified = hashlib.sha256(file.read_bytes()).hexdigest() == digest.lower()
        except OSError:
            verified = False
    return SourceEvidence(
        anatomical_id=model["anatomical_id"], author=model["author"],
        license=model["license"], version=version,
        original_git_blob=original, citation=model["citation"],
        source_url=url, expected_sha256=digest.lower(),
        local_hash_verified=verified,
    )


def build_source_inspector_dialog(evidence: SourceEvidence, parent=None, *, locale="vi"):
    """Show complete source text safely as selectable plain text in native Qt."""
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
        QPushButton, QVBoxLayout, QWidget,
    )
    from ..localization import normalize_locale

    labels = _TEXT[normalize_locale(locale)]
    dialog = QDialog(parent)
    dialog.setWindowTitle(labels["title"])
    dialog.setAccessibleName(labels["title"])
    dialog.resize(720, 420)
    layout = QVBoxLayout(dialog)
    grid = QFormLayout()
    rows = (
        ("anatomy", evidence.anatomical_id), ("author", evidence.author),
        ("license", evidence.license), ("version", evidence.version or labels["unknown"]),
        ("original_blob", evidence.original_git_blob or labels["unknown"]),
        ("source", evidence.source_url), ("citation", evidence.citation),
        ("sha", evidence.expected_sha256),
        ("verification", labels["verified"] if evidence.local_hash_verified else labels["not_verified"]),
    )
    for key, value in rows:
        widget = QLabel(value, dialog)
        widget.setWordWrap(True)
        widget.setTextFormat(Qt.TextFormat.PlainText)
        widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        widget.setAccessibleName(labels[key])
        grid.addRow(labels[key], widget)
    layout.addLayout(grid)
    warning = QLabel(labels["warning"], dialog)
    warning.setWordWrap(True)
    layout.addWidget(warning)
    bottom = QWidget(dialog)
    actions = QHBoxLayout(bottom)
    source_button = QPushButton(labels["open"], bottom)
    source_button.clicked.connect(
        lambda: QDesktopServices.openUrl(QUrl(evidence.source_url))
    )
    actions.addWidget(source_button)
    close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    close_buttons.rejected.connect(dialog.reject)
    actions.addWidget(close_buttons)
    layout.addWidget(bottom)
    return dialog
