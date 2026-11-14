"""Native Qt searchable JSON library browser backed by the existing HTTP server.

No browser wrapper, no fabricated full-text PDF and no unlicensed images loaded.
Integrate with the main AETHERION Portal after the current main.py owner releases it.
"""
from __future__ import annotations

import html
import json
import os

from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSplitter, QTextBrowser, QVBoxLayout, QWidget,
)


class KnowledgeBrowser(QWidget):
    """Real native Qt search screen for article text and ASTRA-authored symptom tags."""

    def __init__(self, parent=None, api_url: str | None = None):
        super().__init__(parent)
        self.setObjectName("aetherionKnowledgeBrowser")
        self.api_url = (api_url or os.environ.get(
            "AETHERION_API_URL", "http://127.0.0.1:8765")).rstrip("/")
        self.network = QNetworkAccessManager(self)
        self.current_items: dict[str, dict] = {}
        self.token = 0
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(18, 18, 18, 18)
        self.title = QLabel("THƯ VIỆN SỨC KHỎE  ·  NASA / TRIỆU CHỨNG")
        self.title.setObjectName("heading")
        self.root.addWidget(self.title)
        self.note = QLabel(
            "Tài liệu trích xuất có nguồn; không phải hướng dẫn điều trị hay thư viện đã kiểm định 100%."
        )
        self.note.setWordWrap(True)
        self.root.addWidget(self.note)
        filters = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItem("Tài liệu NASA CliFF", "articles")
        self.mode.addItem("819 triệu chứng tiếng Việt", "symptoms")
        self.mode.setAccessibleName("Chọn nguồn tra cứu")
        filters.addWidget(self.mode)
        self.query = QLineEdit()
        self.query.setPlaceholderText("Tìm theo bệnh, nội dung, triệu chứng, từ đồng nghĩa…")
        self.query.setAccessibleName("Nhập từ khóa tra cứu")
        filters.addWidget(self.query, 1)
        search_button = QPushButton("Tìm")
        search_button.clicked.connect(self.search)
        filters.addWidget(search_button)
        self.root.addLayout(filters)
        split = QSplitter(Qt.Orientation.Horizontal)
        self.results = QListWidget()
        self.results.setAccessibleName("Danh sách kết quả tra cứu")
        split.addWidget(self.results)
        self.reader = QTextBrowser()
        self.reader.setOpenExternalLinks(False)
        self.reader.anchorClicked.connect(self.open_source)
        self.reader.setAccessibleName("Nội dung nguồn tham khảo")
        split.addWidget(self.reader)
        split.setSizes([360, 850])
        self.root.addWidget(split, 1)
        self.status = QLabel("Chưa kết nối đến server thư viện.")
        self.status.setWordWrap(True)
        self.root.addWidget(self.status)
        self.debounce = QTimer(self)
        self.debounce.setInterval(260)
        self.debounce.setSingleShot(True)
        self.debounce.timeout.connect(self.search)
        self.query.textChanged.connect(lambda _: self.debounce.start())
        self.mode.currentIndexChanged.connect(self.search)
        self.results.currentItemChanged.connect(self.select_item)
        self.search()

    def _get(self, route: str, callback):
        url = QUrl(self.api_url + route)
        reply = self.network.get(QNetworkRequest(url))
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

    def search(self):
        self.token += 1
        token = self.token
        mode = self.mode.currentData()
        target = QUrl(self.api_url + "/api/v1/knowledge/" + mode)
        query = QUrlQuery()
        query.addQueryItem("query", self.query.text().strip())
        query.addQueryItem("limit", "100")
        target.setQuery(query)
        self.status.setText("Đang truy vấn backend…")
        self.current_items = {}
        self.results.clear()
        self.reader.setPlainText("")
        reply = self.network.get(QNetworkRequest(target))
        reply.finished.connect(lambda: self._complete_search(reply, mode, token))

    def _complete_search(self, reply, mode: str, token: int):
        if token != self.token:
            reply.deleteLater()
            return

        def received(data, error):
            if error or not isinstance(data, dict):
                self.status.setText("Không kết nối hoặc server lỗi: " + (error or "invalid response"))
                self.reader.setPlainText("Bật AETHERION Server để tra cứu. Không tạo kết quả giả.")
                return
            items = data.get("items", [])
            for row in items:
                label = row.get("title") if mode == "articles" else row.get("name")
                key = row.get("article_id") if mode == "articles" else label
                item = QListWidgetItem(str(label or key or "Không tên"))
                item.setData(Qt.ItemDataRole.UserRole, key)
                self.results.addItem(item)
                self.current_items[str(key)] = row
            self.status.setText(
                f"{data.get('matched', 0)} kết quả phù hợp • "
                f"{data.get('indexed', data.get('total_source_labels', 0))} mục trong nguồn"
            )
            if not items:
                self.reader.setPlainText("Không tìm thấy tài liệu phù hợp.")

        self._receive(reply, received)

    def select_item(self, current, _previous):
        if current is None:
            return
        key = str(current.data(Qt.ItemDataRole.UserRole))
        row = self.current_items.get(key)
        if not row:
            return
        if self.mode.currentData() == "symptoms":
            lines = [
                str(row.get("name", "")),
                "Từ đồng nghĩa: " + ", ".join(row.get("aliases", [])),
                "Nhóm: " + ", ".join(row.get("routes", [])),
                "Trạng thái kiểm duyệt: " + str(row.get("review_state", "unknown")),
                "Phân tầng ASTRA cũ: " + str(row.get("legacy_tier_unreviewed")),
                "",
                "Phân tầng cũ chỉ là nhãn thuật ngữ; không có giá trị chẩn đoán hoặc ra quyết định cấp cứu.",
            ]
            self.reader.setPlainText("\n".join(lines))
            return
        self.reader.setPlainText("Đang tải toàn văn JSON từ backend…")
        self._get("/api/v1/knowledge/articles/" + key,
                  lambda obj, err: self._show_article(obj, err, key))

    def _show_article(self, obj, error, key):
        current = self.results.currentItem()
        if current is None or current.data(Qt.ItemDataRole.UserRole) != key:
            return
        if error or not isinstance(obj, dict):
            self.reader.setPlainText("Không thể tải: " + (error or "invalid JSON"))
            return
        s = obj.get("summary", {})
        source = obj.get("source", {})
        title = html.escape(str(s.get("title") or key))
        chunks = [f"<h2>{title}</h2>",
                  "<p><b>Nguồn:</b> NASA IMM CliFF (metadata từ bản ghi JSON, chưa đối chiếu độc lập PDF gốc).</p>"]
        url = source.get("final_url") or source.get("source_url")
        if isinstance(url, str) and url.startswith(("https://", "http://")):
            safe = html.escape(url, quote=True)
            chunks.append(f'<p><a href="{safe}">Mở liên kết nguồn đã khai báo</a></p>')
        for section in obj.get("sections", []):
            chunks.append("<h3>" + html.escape(str(section.get("heading", ""))) + "</h3>")
            chunks.append("<p style='white-space:pre-wrap'>" +
                          html.escape(str(section.get("text_content", ""))).replace("\n", "<br>") + "</p>")
        for table in obj.get("tables", []):
            chunks.append("<h3>" + html.escape(str(table.get("title", "Bảng số liệu"))) + "</h3>")
            rows = table.get("rows", [])
            if isinstance(rows, list):
                chunks.append("<table border='1' cellpadding='4'>")
                for row in rows[:120]:
                    if isinstance(row, list):
                        chunks.append("<tr>" + "".join("<td>" + html.escape(str(cell)) + "</td>"
                                                         for cell in row[:20]) + "</tr>")
                chunks.append("</table>")
        refs = obj.get("references", [])
        chunks.append(f"<h3>Tài liệu tham khảo ({len(refs)})</h3><ol>")
        for ref in refs:
            chunks.append("<li>" + html.escape(str(ref.get("label", ""))) + "</li>")
        chunks.append("</ol>")
        chunks.append(f"<h3>Hình ảnh đã khai báo: {len(obj.get('media', []))}</h3>")
        chunks.append("<p>Hình ảnh nhị phân cần qua bộ kiểm định quyền và SHA trước khi trình bày.</p>")
        self.reader.setHtml("\n".join(chunks))

    def open_source(self, url: QUrl):
        if url.scheme() in ("https", "http"):
            QDesktopServices.openUrl(url)


def build_knowledge_browser(parent=None) -> KnowledgeBrowser:
    return KnowledgeBrowser(parent)
