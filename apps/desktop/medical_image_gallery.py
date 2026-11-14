"""Offline Qt-native medical image viewer; never fetches remote assets.

A host supplies verified image bytes and source metadata from the local library.
No NASA/clinical image is bundled by this component.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)


@dataclass(frozen=True)
class GalleryImage:
    data: bytes
    sha256_hex: str
    caption: str
    alt_text: str
    author: str
    license_name: str
    source_url: str

    def verified_pixmap(self) -> QPixmap:
        if sha256(self.data).hexdigest().lower() != self.sha256_hex.lower():
            raise ValueError("Image integrity mismatch")
        if not all((self.alt_text.strip(), self.caption.strip(),
                    self.author.strip(), self.license_name.strip(),
                    self.source_url.strip())):
            raise ValueError("Image attribution and accessibility metadata required")
        image = QImage.fromData(self.data)
        if image.isNull():
            raise ValueError("Unsupported or damaged image bytes")
        return QPixmap.fromImage(image)


class _PanZoomView(QGraphicsView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self._item = QGraphicsPixmapItem()
        self.scene().addItem(self._item)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHints(self.renderHints())
        self.setAccessibleName("Offline medical illustration, scroll to zoom and drag to pan")

    def show_pixmap(self, pixmap: QPixmap) -> None:
        self._item.setPixmap(pixmap)
        self.scene().setSceneRect(self._item.boundingRect())
        self.resetTransform()
        self.fitInView(self._item, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        event.accept()


class MedicalImageGallery(QDialog):
    """Keyboard-accessible local image gallery. Escape closes the dialog."""

    def __init__(self, images: list[GalleryImage], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Medical library — offline images")
        self.resize(850, 650)
        self._images = list(images)
        self._index = 0
        self._view = _PanZoomView(self)
        self._caption = QLabel(self)
        self._caption.setWordWrap(True)
        self._caption.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._attribution = QLabel(self)
        self._attribution.setWordWrap(True)
        self._attribution.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._status = QLabel(self)
        self._previous = QPushButton("Previous", self)
        self._next = QPushButton("Next", self)
        self._previous.clicked.connect(lambda: self.navigate(-1))
        self._next.clicked.connect(lambda: self.navigate(1))
        reset = QPushButton("Fit image", self)
        reset.clicked.connect(self._fit)
        controls = QHBoxLayout()
        for button in (self._previous, reset, self._next):
            controls.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(self._view, 1)
        layout.addWidget(self._caption)
        layout.addWidget(self._attribution)
        layout.addWidget(self._status)
        layout.addLayout(controls)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=lambda: self.navigate(-1))
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=lambda: self.navigate(1))
        self._render()

    def _fit(self) -> None:
        self._view.fitInView(self._view.scene().sceneRect(),
                             Qt.AspectRatioMode.KeepAspectRatio)

    def navigate(self, delta: int) -> None:
        target = self._index + delta
        if 0 <= target < len(self._images):
            self._index = target
            self._render()

    def _render(self) -> None:
        count = len(self._images)
        self._previous.setEnabled(self._index > 0)
        self._next.setEnabled(self._index + 1 < count)
        if not count:
            self._caption.setText("No verified offline images available.")
            self._attribution.clear()
            self._status.setText("0 images")
            self._view.show_pixmap(QPixmap())
            return
        entry = self._images[self._index]
        self._status.setText(f"Image {self._index + 1} of {count}")
        try:
            pixmap = entry.verified_pixmap()
        except ValueError as exc:
            self._view.show_pixmap(QPixmap())
            self._caption.setText("Image unavailable: integrity or metadata check failed.")
            self._attribution.setText(str(exc))
            return
        self._view.show_pixmap(pixmap)
        self._view.setAccessibleDescription(entry.alt_text)
        self._caption.setText(f"{entry.caption}\nAlt text: {entry.alt_text}")
        self._attribution.setText(
            f"Author: {entry.author} | License: {entry.license_name}\n"
            f"Source: {entry.source_url} | SHA-256: {entry.sha256_hex}"
        )
