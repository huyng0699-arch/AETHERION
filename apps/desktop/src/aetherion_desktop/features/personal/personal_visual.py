"""Premium native Personal Today composition, without fabricated health data.

Presentation-only component. Only authenticated/validated observation cards
provided by AuthorizedPersonalTodayPage may appear as measured values.
"""
from __future__ import annotations

from datetime import datetime

from ...localization import tr

# Exact named metric families only; never infer sensor capabilities from labels.
# The actual metric key is always retained alongside the reading.
TILES = (
    ("heart", "NHỊP TIM", "Nhịp tim", ("heart_rate", "pulse", "pulse_rate")),
    ("activity", "VẬN ĐỘNG", "Hoạt động", ("steps", "step_count", "activity_minutes", "active_minutes")),
    ("sleep", "GIẤC NGỦ", "Giấc ngủ", ("sleep_hours", "sleep_duration", "sleep_minutes")),
    ("mass", "KHỐI LƯỢNG", "Khối lượng cơ thể", ("body_mass", "body_weight", "weight")),
    ("energy", "NĂNG LƯỢNG", "Năng lượng", ("calories", "energy_kcal", "active_energy", "energy_expenditure")),
    ("mood", "TÂM TRẠNG", "Tâm trạng tự ghi nhận", ("mood", "mood_score", "self_reported_mood")),
)


def tile_for_metric(metric: str) -> str | None:
    normalized = metric.strip().lower().replace("-", "_").replace(" ", "_")
    for tile_id, _eyebrow, _title, aliases in TILES:
        if normalized in aliases:
            return tile_id
    return None


def _utc_timestamp(text: str) -> datetime:
    timestamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Timestamp needs source timezone")
    return timestamp


def latest_tiles(cards: tuple | list) -> dict[str, object]:
    """Select most recent per family, with original metric/scope/source intact."""
    latest: dict[str, object] = {}
    for card in cards:
        tile_id = tile_for_metric(card.metric)
        if tile_id is None:
            continue
        original = latest.get(tile_id)
        if original is None or _utc_timestamp(card.observed_at) > _utc_timestamp(original.observed_at):
            latest[tile_id] = card
    return latest


def build_personal_visual(page) -> None:
    """Replace the old plain table with a scrolling native health workspace."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
    from PySide6.QtWidgets import (
        QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
        QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QTableWidget,
        QVBoxLayout, QWidget,
    )

    class HealthTileFrame(QFrame):
        """A quiet orbital glow behind *real* data; no invented medical chart."""

        ACCENTS = ("#80DCD5", "#8CAEFF", "#CAB0FC", "#81D8E8", "#E9C7A0", "#E0A7D4")

        def __init__(self, index: int):
            super().__init__()
            self.setObjectName("surface")
            self._accent = QColor(self.ACCENTS[index])

        def paintEvent(self, event):
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            w = self.width()
            glow = QLinearGradient(w * 0.55, 0, w, self.height() * 0.65)
            c1 = QColor(self._accent)
            c1.setAlpha(0)
            c2 = QColor(self._accent)
            c2.setAlpha(18)
            glow.setColorAt(0, c1)
            glow.setColorAt(1, c2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 14, 14)
            top = QColor(self._accent)
            top.setAlpha(155)
            painter.setPen(QPen(top, 2))
            painter.drawLine(21, 2, max(22, int(w * 0.29)), 2)
            painter.end()

    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    scroll = QScrollArea(page)
    scroll.setObjectName("personalScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    outer.addWidget(scroll)
    page.workspace_scroll = scroll
    content = QWidget()
    content.setObjectName("personalWorkspace")
    content.setMinimumWidth(0)
    scroll.setWidget(content)
    root = QVBoxLayout(content)
    root.setContentsMargins(30, 22, 30, 30)
    root.setSpacing(16)

    eyebrow = QLabel("AETHERION  /  PERSONAL HEALTH")
    eyebrow.setObjectName("eyebrow")
    root.addWidget(eyebrow)
    hero = QHBoxLayout()
    hero.setSpacing(20)
    left = QVBoxLayout()
    left.setSpacing(7)
    head = QLabel("Sức khỏe của tôi")
    page.hero_title = head
    head.setObjectName("heroTitle")
    head.setWordWrap(True)
    left.addWidget(head)
    desc = QLabel(
        "Tổng quan số đo có nguồn và thời điểm rõ ràng. "
        "Không cần khai triệu chứng nếu bạn không muốn."
    )
    desc.setObjectName("heroCopy")
    desc.setWordWrap(True)
    left.addWidget(desc)
    hero.addLayout(left, 1)
    right = QLabel("01  /  TODAY\n\nDATA-LED  •  HUMAN-CENTERED")
    right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    right.setObjectName("pageHint")
    hero.addWidget(right)
    root.addLayout(hero)

    identity = QFrame()
    identity.setObjectName("surface")
    strip = QHBoxLayout(identity)
    strip.setContentsMargins(19, 12, 19, 12)
    strip.setSpacing(14)
    identity_column = QVBoxLayout()
    section = QLabel("HỒ SƠ ĐANG XEM")
    section.setObjectName("eyebrow")
    identity_column.addWidget(section)
    page.subject_label = QLabel("Chưa chọn hồ sơ — vào Phi hành đoàn để đăng nhập")
    page.subject_label.setTextFormat(Qt.TextFormat.PlainText)
    page.subject_label.setObjectName("pageHint")
    page.subject_label.setAccessibleName("Exact selected crew subject")
    page.subject_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    identity_column.addWidget(page.subject_label)
    strip.addLayout(identity_column, 1)
    page.refresh_button = QPushButton("Làm mới dữ liệu")
    page.refresh_button.setAccessibleName("Làm mới hồ sơ hiện tại từ server")
    page.refresh_button.setObjectName("primaryAction")
    page.refresh_button.clicked.connect(page.refresh)
    strip.addWidget(page.refresh_button)
    root.addWidget(identity)

    page.status_label = QLabel("NO_DATA — chưa yêu cầu bản ghi cá nhân")
    page.status_label.setTextFormat(Qt.TextFormat.PlainText)
    page.status_label.setObjectName("pageHint")
    page.status_label.setWordWrap(True)
    page.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    root.addWidget(page.status_label)

    tiles_head = QHBoxLayout()
    subtitle = QLabel("TỔNG QUAN THEO LĨNH VỰC")
    subtitle.setObjectName("eyebrow")
    tiles_head.addWidget(subtitle)
    tiles_head.addStretch()
    subhint = QLabel("Chưa đo ≠ Bình thường")
    subhint.setObjectName("pageHint")
    tiles_head.addWidget(subhint)
    root.addLayout(tiles_head)

    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(14)
    page.metric_tiles = {}
    page.metric_tile_headers = {}
    for i, (tile_id, label, title, _aliases) in enumerate(TILES):
        panel = HealthTileFrame(i)
        panel.setMinimumHeight(154)
        v = QVBoxLayout(panel)
        v.setContentsMargins(19, 14, 19, 15)
        v.setSpacing(6)
        title_row = QHBoxLayout()
        num = QLabel(f"{i + 1:02d}  /  {tr(page.ui_language, f'personal.tile.{tile_id}')}")
        page.metric_tile_headers[tile_id] = num
        num.setObjectName("eyebrow")
        title_row.addWidget(num)
        title_row.addStretch(1)
        marker = QLabel("◇")
        marker.setObjectName("eyebrow")
        title_row.addWidget(marker)
        v.addLayout(title_row)
        value = QLabel("Chưa có dữ liệu")
        value.setObjectName("heading")
        value.setWordWrap(True)
        v.addWidget(value)
        provenance = QLabel("Chưa có bản ghi hợp lệ trong hồ sơ này")
        provenance.setTextFormat(Qt.TextFormat.PlainText)
        provenance.setObjectName("cardDescription")
        provenance.setWordWrap(True)
        provenance.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(provenance, 1)
        action = QPushButton("Xem bản ghi  ↗")
        action.setObjectName("navButton")
        action.setEnabled(False)
        action.setAccessibleName(f"Xem bản ghi của {title}")
        action.clicked.connect(lambda checked=False, key=tile_id: page.focus_metric_tile(key))
        v.addWidget(action)
        grid.addWidget(panel, i // 3, i % 3)
        page.metric_tiles[tile_id] = (value, provenance, action)
    for i in range(3):
        grid.setColumnStretch(i, 1)
    root.addLayout(grid)

    data = QFrame()
    data.setObjectName("contentPanel")
    records = QVBoxLayout(data)
    records.setContentsMargins(18, 16, 18, 18)
    records.setSpacing(12)
    filter_row = QHBoxLayout()
    filter_row.addWidget(QLabel("BẢN GHI CHI TIẾT"))
    filter_row.addStretch(1)
    page.origin_filter = QComboBox()
    page.origin_filter.setAccessibleName("Filter records by documented origin")
    page.origin_filter.addItem("Tất cả nguồn bản ghi", "all")
    page.origin_filter.addItem("Do người dùng tự ghi nhận", "self")
    page.origin_filter.addItem("Nguồn đã kiểm chứng", "verified")
    page.origin_filter.addItem("Nguồn chưa xác minh", "unverified")
    page.origin_filter.currentIndexChanged.connect(page._render_rows)
    filter_row.addWidget(page.origin_filter)
    records.addLayout(filter_row)
    page.table = QTableWidget(0, 8)
    page.table.setHorizontalHeaderLabels(
        ["Chỉ số", "Giá trị", "Thời gian", "Nguồn", "Phạm vi", "Chất lượng", "Kiểm chứng", "Loại bản ghi"]
    )
    page.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    page.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    page.table.setAlternatingRowColors(True)
    page.table.setAccessibleName("Selected person's authenticated observations")
    page.table.verticalHeader().setVisible(False)
    page.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    for i, width in enumerate((150, 125, 220, 175, 110, 120, 140, 155)):
        page.table.setColumnWidth(i, width)
    page.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    page.table.setMinimumHeight(230)
    records.addWidget(page.table)
    root.addWidget(data)

    page.note = QLabel(
        "Không cần khai triệu chứng. Thiếu số đo không chứng minh sức khỏe bình thường "
        "hay bất thường; dữ liệu nghiên cứu NASA không phải sinh hiệu trực tiếp."
    )
    page.note.setObjectName("pageHint")
    page.note.setWordWrap(True)
    root.addWidget(page.note)
    page.records_panel = data


def update_personal_tiles(page, cards: tuple | list) -> None:
    """Present only validated cards currently visible under provenance filter."""
    selected = latest_tiles(cards)
    for tile_id, (value, provenance, button) in page.metric_tiles.items():
        card = selected.get(tile_id)
        if card is None:
            value.setText(tr(page.ui_language, "personal.noData"))
            provenance.setText(tr(page.ui_language, "personal.filteredNoData"))
            button.setEnabled(False)
            continue
        # Exact original metric/source/time/quality must remain visible.
        value.setText(card.reading)
        provenance.setText(
            f"{card.metric}  ·  {card.scope}  ·  {card.quality} / {card.verification_state}\n"
            + tr(page.ui_language, "personal.metricSource", source=card.source_id,
               observed=card.observed_at)
        )
        button.setEnabled(True)
