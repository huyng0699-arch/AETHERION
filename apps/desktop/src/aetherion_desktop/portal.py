"""AETHERION native Qt Portal (D00), intentionally independent of HTTP availability.

The Portal presents destinations, never synthetic physiological values. Features
without working integrations remain explicitly labelled as unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortalCard:
    route: str
    title: str
    summary: str


PORTAL_CARDS: tuple[PortalCard, ...] = (
    PortalCard("health", "Sức khỏe của tôi", "Số đo và hồ sơ của bạn, chỉ sau khi được cấp quyền."),
    PortalCard("monitor", "Theo dõi & ECG", "Xem bản ghi; ECG chỉ khả dụng khi có nguồn thực."),
    PortalCard("assistant", "Hỏi AI về sức khỏe", "AI chưa được kết nối; không cung cấp chẩn đoán tự động."),
    PortalCard("science", "Khám phá khoa học", "Mở thư viện tài liệu ngoại tuyến có dẫn nguồn."),
    PortalCard("crew", "Phi hành đoàn", "Bảng điều khiển cần đăng nhập và quyền truy cập."),
)

PORTAL_ROUTES = frozenset(card.route for card in PORTAL_CARDS)


def build_portal_page(parent=None):
    """Construct a real Qt landing page; no API call and no automatic sign-in."""
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
    )

    class PortalPage(QWidget):
        route_requested = Signal(str)

        def __init__(self):
            super().__init__(parent)
            self.setObjectName("aetherionPortal")
            root = QVBoxLayout(self)
            root.setContentsMargins(18, 14, 18, 18)
            root.setSpacing(16)

            heading = QLabel("Chào mừng đến AETHERION")
            heading.setObjectName("heading")
            heading.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            root.addWidget(heading)
            intro = QLabel("Chọn một không gian làm việc. Dữ liệu sức khỏe chỉ hiển thị khi có nguồn và quyền truy cập.")
            intro.setObjectName("detail")
            intro.setWordWrap(True)
            intro.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            root.addWidget(intro)

            grid = QGridLayout()
            grid.setHorizontalSpacing(16)
            grid.setVerticalSpacing(14)
            for index, card in enumerate(PORTAL_CARDS):
                panel = QFrame()
                panel.setObjectName("surface")
                content = QVBoxLayout(panel)
                content.setContentsMargins(22, 17, 22, 17)
                content.setSpacing(10)
                action = QPushButton(card.title)
                action.setAccessibleName(card.title)
                action.setMinimumHeight(44)
                action.clicked.connect(lambda checked=False, key=card.route: self.route_requested.emit(key))
                content.addWidget(action)
                description = QLabel(card.summary)
                description.setObjectName("detail")
                description.setWordWrap(True)
                content.addWidget(description)
                content.addStretch()
                row, column = divmod(index, 2)
                if index == 4:
                    grid.addWidget(panel, 2, 0, 1, 2)
                else:
                    grid.addWidget(panel, row, column)
            root.addLayout(grid, 1)
            note = QLabel("Hoạt động ngoại tuyến được hỗ trợ; kết nối server không bắt buộc để mở Trang đầu.")
            note.setObjectName("detail")
            note.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            root.addWidget(note)

    return PortalPage()
