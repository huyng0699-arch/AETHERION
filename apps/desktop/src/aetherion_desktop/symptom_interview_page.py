"""AETHERION native symptom-search and structured interview panel.

Use only on a protected local development instance. No diagnosis, no medical
risk clearance, no implicit cloud data transfer.
"""
from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt, QUrl, QUrlQuery
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)


class SymptomInterviewPage(QWidget):
    def __init__(self, parent=None, api_url: str | None = None):
        super().__init__(parent)
        self.setObjectName("aetherionSymptomInterview")
        self.setStyleSheet("""
            QWidget#aetherionSymptomInterview { background: #081627; color: #e9f2ff; }
            QLabel#heading { color: #e9f5ff; font-size: 23px; font-weight: 700; }
            QLabel, QCheckBox { color: #b9cde2; }
            QLineEdit, QComboBox, QListWidget { background: #10263d; color: #f1f7ff;
                border: 1px solid #31516b; border-radius: 10px; padding: 10px; }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background: #205374; }
            QPushButton { background: #17658a; color: #ffffff; border: none;
                padding: 11px 18px; border-radius: 9px; font-weight: 600; }
            QPushButton:hover { background: #227da5; }
        """)
        self.api_url = (api_url or os.environ.get(
            "AETHERION_API_URL", "http://127.0.0.1:8765")).rstrip("/")
        self.net = QNetworkAccessManager(self)
        self.answers: dict[str, str] = {}
        self.active_symptoms: list[str] = []
        self.question_id: str | None = None
        layout = QVBoxLayout(self)
        title = QLabel("KHAI THÁC TRIỆU CHỨNG  ·  AETHERION")
        title.setObjectName("heading")
        layout.addWidget(title)
        self.notice = QLabel(
            "Hỏi bệnh có cấu trúc; không tự chẩn đoán, không dùng nhãn phân tầng cũ "
            "để kết luận cấp cứu. Không nhập thông tin định danh thật vào bản thử nghiệm."
        )
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        entry = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Ví dụ: đau đầu, khó thở, loét miệng…")
        self.search.setAccessibleName("Nhập triệu chứng tiếng Việt")
        entry.addWidget(self.search, 1)
        find = QPushButton("Tra triệu chứng")
        find.clicked.connect(self.find)
        entry.addWidget(find)
        layout.addLayout(entry)
        self.hits = QListWidget()
        self.hits.setMaximumHeight(150)
        self.hits.setAccessibleName("Các triệu chứng được tìm thấy")
        layout.addWidget(self.hits)
        self.selection = QLabel("Chọn một triệu chứng để bắt đầu hỏi.")
        layout.addWidget(self.selection)
        self.question = QLabel("")
        self.question.setWordWrap(True)
        layout.addWidget(self.question)
        self.answers_box = QComboBox()
        self.answers_box.setAccessibleName("Trả lời câu hỏi hiện tại")
        layout.addWidget(self.answers_box)
        choice_row = QHBoxLayout()
        self.use_ai = QCheckBox("Cho phép AI chọn câu hỏi (cần cấu hình server)")
        choice_row.addWidget(self.use_ai)
        self.allow_cloud = QCheckBox("Đồng ý gửi nhãn triệu chứng và câu trả lời tới AI đám mây")
        choice_row.addWidget(self.allow_cloud)
        layout.addLayout(choice_row)
        next_button = QPushButton("Trả lời và hỏi tiếp")
        next_button.clicked.connect(self.advance)
        layout.addWidget(next_button)
        self.state = QLabel("Không có dữ liệu khai thác được lưu trên server.")
        self.state.setWordWrap(True)
        layout.addWidget(self.state)
        layout.addStretch()
        self.hits.itemClicked.connect(self.select_symptom)

    def _request(self, method: str, route: str, payload: dict | None, callback):
        url = QUrl(self.api_url + route)
        headers = QNetworkRequest(url)
        headers.setRawHeader(b"Content-Type", b"application/json")
        if method == "POST":
            reply = self.net.post(headers, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        else:
            reply = self.net.get(headers)
        reply.finished.connect(lambda: self._receive(reply, callback))

    def _receive(self, reply, callback):
        error = reply.errorString() if reply.error() else None
        try:
            body = json.loads(bytes(reply.readAll()).decode("utf-8")) if not error else None
        except (ValueError, UnicodeError):
            body, error = None, "Định dạng JSON không hợp lệ"
        reply.deleteLater()
        callback(body, error)

    def find(self):
        url = QUrl("/api/v1/knowledge/symptoms")
        query = QUrlQuery()
        query.addQueryItem("query", self.search.text().strip())
        query.addQueryItem("limit", "25")
        url.setQuery(query)
        self._request("GET", url.toString(), None, self._show_hits)

    def _show_hits(self, body, error):
        self.hits.clear()
        if error or not isinstance(body, dict):
            self.state.setText("Lỗi server hoặc chưa khởi chạy: " + str(error))
            return
        for row in body.get("items", []):
            name = row.get("name")
            item = QListWidgetItem(str(name))
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.hits.addItem(item)
        self.state.setText(f"Đã tìm thấy {body.get('matched', 0)} triệu chứng phù hợp.")

    def select_symptom(self, item):
        text = str(item.data(Qt.ItemDataRole.UserRole))
        self.active_symptoms = [text]
        self.answers = {}
        self.selection.setText("Đang hỏi về: " + text)
        self._ask()

    def advance(self):
        if self.question_id and self.answers_box.currentData():
            self.answers[self.question_id] = self.answers_box.currentData()
        self._ask()

    def _ask(self):
        if not self.active_symptoms:
            self.state.setText("Chọn triệu chứng trước.")
            return
        request = {"symptoms": self.active_symptoms, "answers": self.answers,
                   "use_ai": self.use_ai.isChecked(), "allow_cloud": self.allow_cloud.isChecked()}
        self._request("POST", "/api/v1/knowledge/interview/next", request, self._show_question)

    def _show_question(self, data, error):
        if error or not isinstance(data, dict):
            self.state.setText("Không thể tiếp tục, server không phản hồi: " + str(error))
            return
        self.question_id = None
        q = data.get("next_question")
        self.answers_box.clear()
        if q:
            self.question_id = q["id"]
            self.question.setText(q["text"])
            for answer in q.get("answers", []):
                self.answers_box.addItem(answer, answer)
        else:
            self.question.setText("Đã hoàn thành các câu hỏi có cấu trúc hiện có.")
        self.state.setText(
            "Trạng thái: " + str(data.get("state")) +
            " | AI: " + str(data.get("model_status")) +
            "\n" + str(data.get("recommendation", ""))
        )


def build_symptom_interview(parent=None) -> SymptomInterviewPage:
    return SymptomInterviewPage(parent)
