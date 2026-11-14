"""Responsive, native Mission Control surface for Q-0072.

Presentation only: it does not authenticate, write observations or synthesize
crew, health status, clinical incidents or trends. The parent page supplies
the existing authenticated HTTP handlers and observation parser.
"""
from __future__ import annotations


def install_mission_layout(page, api_url: str) -> None:
    """Build a scrollable Qt Mission view, with horizontal scrolling for wide data.

    The page's existing sign_in/add_subject/refresh_subject/open_selected_personal
    and request-validation methods remain authoritative.
    """
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
        QLabel, QLineEdit, QListWidget, QPushButton, QScrollArea, QSizePolicy,
        QTabWidget, QTableWidget, QVBoxLayout, QWidget,
    )
    from .event_list import build_mission_events_widget

    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    scroller = QScrollArea(page)
    scroller.setObjectName("missionScroll")
    scroller.setFrameShape(QFrame.Shape.NoFrame)
    scroller.setWidgetResizable(True)
    scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroller.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    outer.addWidget(scroller)

    content = QWidget()
    content.setObjectName("missionContent")
    content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    scroller.setWidget(content)
    root = QVBoxLayout(content)
    root.setContentsMargins(30, 22, 30, 28)
    root.setSpacing(16)

    top = QHBoxLayout()
    mission_label = QLabel("AETHERION  /  CREW OPERATIONS")
    mission_label.setObjectName("eyebrow")
    top.addWidget(mission_label)
    top.addStretch()
    indicator = QLabel("DỮ LIỆU CHỈ TỪ NGUỒN ĐƯỢC CẤP QUYỀN")
    indicator.setObjectName("pageHint")
    top.addWidget(indicator)
    root.addLayout(top)

    title = QLabel("Mission Control")
    title.setObjectName("heroTitle")
    title.setAccessibleName("Mission Control")
    root.addWidget(title)
    lead = QLabel(
        "Một nơi để theo dõi các bản ghi có nguồn, thời gian và danh tính rõ ràng. "
        "Không suy đoán tình trạng sức khỏe khi chưa có dữ liệu."
    )
    lead.setObjectName("heroCopy")
    lead.setWordWrap(True)
    root.addWidget(lead)

    summary = QFrame()
    summary.setObjectName("surface")
    summary_grid = QGridLayout(summary)
    summary_grid.setContentsMargins(18, 14, 18, 14)
    summary_grid.setHorizontalSpacing(16)
    summary_grid.setVerticalSpacing(12)

    def summary_item(label: str, initial: str, index: int):
        wrap = QWidget()
        box = QVBoxLayout(wrap)
        box.setContentsMargins(6, 3, 6, 3)
        box.setSpacing(5)
        name = QLabel(label)
        name.setObjectName("eyebrow")
        name.setWordWrap(True)
        box.addWidget(name)
        value = QLabel(initial)
        value.setTextFormat(Qt.TextFormat.PlainText)
        value.setObjectName("heading")
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(value)
        summary_grid.addWidget(wrap, index // 2, index % 2)
        return value

    page.focus = summary_item("01 / HỒ SƠ ĐƯỢC CHỌN", "Chưa chọn", 0)
    page.record_count = summary_item("02 / BẢN GHI CÓ NGUỒN", "Chưa có", 1)
    page.latest = summary_item("03 / THỜI ĐIỂM QUAN SÁT", "Chưa có", 2)
    page.source_count = summary_item("04 / NGUỒN DỮ LIỆU", "Chưa có", 3)
    root.addWidget(summary)

    auth = QFrame()
    auth.setObjectName("surface")
    auth_layout = QVBoxLayout(auth)
    auth_layout.setContentsMargins(19, 15, 19, 18)
    auth_layout.setSpacing(9)
    auth_heading = QLabel("01  /  Kết nối hồ sơ được cấp quyền")
    auth_heading.setObjectName("eyebrow")
    auth_layout.addWidget(auth_heading)
    auth_note = QLabel("Đăng nhập bằng tài khoản server nội bộ. Thông tin không được lưu trong giao diện.")
    auth_note.setObjectName("pageHint")
    auth_note.setWordWrap(True)
    auth_layout.addWidget(auth_note)

    auth_grid = QGridLayout()
    auth_grid.setHorizontalSpacing(9)
    auth_grid.setVerticalSpacing(9)
    page.username = QLineEdit()
    page.username.setPlaceholderText("Tên tài khoản cục bộ")
    page.username.setAccessibleName("Tên tài khoản đăng nhập")
    page.password = QLineEdit()
    page.password.setPlaceholderText("Mật khẩu")
    page.password.setAccessibleName("Mật khẩu đăng nhập")
    page.password.setEchoMode(QLineEdit.EchoMode.Password)
    login = QPushButton("Đăng nhập")
    login.setObjectName("primaryAction")
    login.setAccessibleName("Đăng nhập vào AETHERION Server")
    login.clicked.connect(page.sign_in)
    page.password.returnPressed.connect(page.sign_in)
    auth_grid.addWidget(page.username, 0, 0)
    auth_grid.addWidget(page.password, 0, 1)
    auth_grid.addWidget(login, 0, 2)
    auth_grid.setColumnStretch(0, 2)
    auth_grid.setColumnStretch(1, 2)
    auth_grid.setColumnStretch(2, 1)
    auth_layout.addLayout(auth_grid)

    page.status = QLabel("CHƯA XÁC THỰC  ·  Không suy ra trạng thái sức khỏe")
    page.status.setTextFormat(Qt.TextFormat.PlainText)
    page.status.setObjectName("pageHint")
    page.status.setWordWrap(True)
    page.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    auth_layout.addWidget(page.status)
    root.addWidget(auth)

    selector = QFrame()
    selector.setObjectName("surface")
    selector_layout = QVBoxLayout(selector)
    selector_layout.setContentsMargins(19, 15, 19, 18)
    selector_layout.setSpacing(9)
    title2 = QLabel("02  /  Chọn hồ sơ và làm mới số đo")
    title2.setObjectName("eyebrow")
    selector_layout.addWidget(title2)

    select_grid = QGridLayout()
    select_grid.setHorizontalSpacing(9)
    select_grid.setVerticalSpacing(9)
    page.subject_input = QLineEdit()
    page.subject_input.setPlaceholderText("ID hồ sơ đã được cấp quyền (không tự tạo)")
    page.subject_input.setAccessibleName("ID hồ sơ được cấp quyền")
    page.subject_input.returnPressed.connect(page.add_subject)
    select_grid.addWidget(page.subject_input, 0, 0, 1, 2)
    add = QPushButton("Mở hồ sơ")
    add.clicked.connect(page.add_subject)
    select_grid.addWidget(add, 0, 2)
    page.refresh = QPushButton("Làm mới từ Server")
    page.refresh.clicked.connect(page.refresh_subject)
    select_grid.addWidget(page.refresh, 1, 0, 1, 2)
    page.open_personal_button = QPushButton("Xem hồ sơ sức khỏe cá nhân")
    page.open_personal_button.setAccessibleName("Open selected subject in Personal Health")
    page.open_personal_button.clicked.connect(page.open_selected_personal)
    select_grid.addWidget(page.open_personal_button, 1, 2)
    select_grid.setColumnStretch(0, 1)
    select_grid.setColumnStretch(1, 1)
    select_grid.setColumnStretch(2, 1)
    selector_layout.addLayout(select_grid)

    page.subjects = QListWidget()
    page.subjects.setMaximumHeight(74)
    page.subjects.setAccessibleName("Các ID hồ sơ đã chọn trong phiên")
    page.subjects.currentTextChanged.connect(page.refresh_subject)
    selector_layout.addWidget(page.subjects)
    root.addWidget(selector)

    dataset = QFrame()
    dataset.setObjectName("surface")
    data_layout = QVBoxLayout(dataset)
    data_layout.setContentsMargins(18, 14, 18, 18)
    data_heading = QLabel("03  /  Quan sát và sự kiện")
    data_heading.setObjectName("eyebrow")
    data_layout.addWidget(data_heading)
    page.tabs = QTabWidget()
    page.tabs.setDocumentMode(True)
    page.table = QTableWidget(0, 7)
    page.table.setHorizontalHeaderLabels(
        ["Chỉ số", "Giá trị", "Thời gian ghi nhận", "Nguồn", "Phạm vi", "Chất lượng", "Kiểm chứng"]
    )
    page.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    page.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    page.table.setAlternatingRowColors(True)
    page.table.setAccessibleName("Recorded observations and provenance")
    page.table.verticalHeader().setVisible(False)
    page.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    for i, width in enumerate((145, 135, 230, 185, 110, 135, 150)):
        page.table.setColumnWidth(i, width)
    page.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    page.table.setMinimumHeight(260)
    page.tabs.addTab(page.table, "Dữ liệu quan sát")
    page.events_widget = build_mission_events_widget()
    page.tabs.addTab(page.events_widget, "Nhật ký sự kiện")
    data_layout.addWidget(page.tabs)
    root.addWidget(dataset)

    page.technical = QLabel(
        "Trạng thái thiết bị và báo cáo lâm sàng là hai loại sự kiện khác nhau. "
        "Không có kết nối hay bản ghi không đồng nghĩa với tình trạng cấp cứu."
    )
    page.technical.setObjectName("pageHint")
    page.technical.setWordWrap(True)
    root.addWidget(page.technical)


def update_summary(page, *, subject: str = "", count: int | None = None,
                   latest: str = "", sources: int | None = None):
    """Update presentation from validated, authorized API output only."""
    from ...localization import tr
    language = getattr(page, "ui_language", "vi")
    page.focus.setText(subject or tr(language, "mission.noneSelected"))
    page.record_count.setText(str(count) if count is not None else tr(language, "mission.none"))
    page.latest.setText(latest or tr(language, "mission.none"))
    page.source_count.setText(str(sources) if sources is not None else tr(language, "mission.none"))
