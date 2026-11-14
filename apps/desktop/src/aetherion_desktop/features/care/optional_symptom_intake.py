"""Native, OPTIONAL symptom intake widget (Q-0094).

This QWidget collects no information on SKIP. Report generation is an in-memory
draft only; the Care API persistence path is not connected and must not be
claimed until authenticated server integration has passed independent review.
"""
from __future__ import annotations

from datetime import datetime, timezone


def build_optional_symptom_intake(parent=None):
    """Construct opt-in native Qt report form without requiring symptoms."""
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import (
        QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QTextEdit, QVBoxLayout, QWidget,
    )

    class OptionalSymptomIntake(QWidget):
        skipped = Signal()
        draft_ready = Signal(object)

        def __init__(self):
            super().__init__(parent)
            root = QVBoxLayout(self)
            title = QLabel("Tùy chọn: chia sẻ một mối quan tâm về sức khỏe")
            title.setObjectName("heading")
            root.addWidget(title)
            description = QLabel(
                "Bạn có thể bỏ qua hoàn toàn. Việc không trả lời KHÔNG được hiểu "
                "là khỏe mạnh, không có triệu chứng hoặc mất ý thức."
            )
            description.setWordWrap(True)
            root.addWidget(description)

            form = QFormLayout()
            self.subject_id = QLineEdit()
            self.subject_id.setAccessibleName("Authorized subject ID for optional report")
            self.subject_id.setMaxLength(80)
            self.subject_id.setPlaceholderText("Mã hồ sơ đã được cấp quyền")
            form.addRow("Mã hồ sơ (nếu báo cáo)", self.subject_id)

            self.actor_id = QLineEdit()
            self.actor_id.setAccessibleName("Reporter ID for optional report")
            self.actor_id.setMaxLength(80)
            form.addRow("Người báo cáo", self.actor_id)

            self.answer = QComboBox()
            self.answer.addItem("Chọn nếu muốn báo cáo", None)
            self.answer.addItem("Có mối quan tâm", "YES")
            self.answer.addItem("Không có mối quan tâm được báo cáo", "NO")
            self.answer.addItem("Không rõ", "UNKNOWN")
            form.addRow("Bạn muốn báo cáo?", self.answer)

            self.impact = QComboBox()
            for label, code in (
                ("Chưa xác định", "UNKNOWN"),
                ("Không ảnh hưởng", "NONE"),
                ("Ảnh hưởng nhẹ (tự báo cáo)", "MILD"),
                ("Ảnh hưởng vừa (tự báo cáo)", "MODERATE"),
                ("Ảnh hưởng nhiều (tự báo cáo)", "SEVERE"),
            ):
                self.impact.addItem(label, code)
            form.addRow("Mức ảnh hưởng tự đánh giá", self.impact)

            self.note = QTextEdit()
            self.note.setAccessibleName("Optional self-reported concern details")
            self.note.setPlaceholderText("Thông tin tự nguyện; không nhập dữ liệu bệnh nhân thật vào prototype.")
            self.note.setMaximumHeight(115)
            form.addRow("Mô tả thêm (không bắt buộc)", self.note)
            root.addLayout(form)

            self.consent = QCheckBox("Tôi đồng ý tạo bản nháp tự báo cáo trong bộ nhớ ứng dụng")
            self.consent.setChecked(False)
            root.addWidget(self.consent)

            controls = QHBoxLayout()
            skip = QPushButton("Bỏ qua — không tạo bản ghi")
            skip.setAccessibleName("Skip optional symptom report without any record")
            skip.clicked.connect(self.skip)
            controls.addWidget(skip)
            prepare = QPushButton("Xem bản nháp tự báo cáo")
            prepare.clicked.connect(self.prepare_draft)
            controls.addWidget(prepare)
            root.addLayout(controls)

            self.status = QLabel(
                "Không bắt buộc nhập triệu chứng. Chưa có chức năng lưu Care API ở màn hình này."
            )
            self.status.setWordWrap(True)
            root.addWidget(self.status)
            root.addStretch(1)

        def skip(self) -> None:
            """Erase any unsent text and emit NO report or health classification."""
            self.subject_id.clear()
            self.actor_id.clear()
            self.note.clear()
            self.consent.setChecked(False)
            self.answer.setCurrentIndex(0)
            self.impact.setCurrentIndex(0)
            self.status.setText("Đã bỏ qua. KHÔNG tạo bản ghi; trạng thái sức khỏe vẫn chưa biết.")
            self.skipped.emit()

        def prepare_draft(self) -> None:
            """Create local-only draft; no server request and no hidden upload."""
            answer = self.answer.currentData()
            subject = self.subject_id.text().strip()
            actor = self.actor_id.text().strip()
            note = self.note.toPlainText()
            if answer not in ("YES", "NO", "UNKNOWN"):
                self.status.setText("Hãy chọn câu trả lời tự nguyện, hoặc nhấn Bỏ qua.")
                return
            if not self.consent.isChecked():
                self.status.setText("Bạn phải đồng ý trước khi tạo bản nháp.")
                return
            if not subject or not actor or len(note) > 2000:
                self.status.setText("Mã hồ sơ và người báo cáo là bắt buộc khi chọn báo cáo; mô tả tối đa 2000 ký tự.")
                return
            if any(ord(c) < 32 and c not in "\r\n\t" for c in note):
                self.status.setText("Mô tả có ký tự điều khiển không được hỗ trợ.")
                return
            report = {
                "kind": "USER_REPORTED_CONCERN" if answer == "YES" else "VOLUNTARY_USER_CHECKIN",
                "subject_id": subject,
                "actor_id": actor,
                "answer": answer,
                "impact": self.impact.currentData(),
                "note": note.replace("\r\n", "\n").strip(),
                "source_id": "manual_user_report",
                "scope": "personal",
                "verification_state": "SELF_REPORTED",
                "quality": "UNVERIFIED",
                "reported_at": datetime.now(timezone.utc).isoformat(),
                "clinical_assessment": None,
                "persistence_state": "NOT_SAVED",
            }
            self.status.setText(
                "Bản nháp được tạo trong bộ nhớ — CHƯA LƯU lên Server, "
                "chưa đánh giá lâm sàng. Thoát màn hình sẽ không lưu dữ liệu."
            )
            self.draft_ready.emit(report)

    return OptionalSymptomIntake()
