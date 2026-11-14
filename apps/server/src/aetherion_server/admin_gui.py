"""AETHERION Server Control — native Qt client for the existing HTTP service.

Install: pip install -e "apps/server[admin]"
Start:   aetherion-admin
An administrator must first be bootstrapped locally via aetherion-bootstrap.
The GUI never stores passwords/tokens, never invents live source/device status,
and can stop only a server process it explicitly started itself.
"""
from __future__ import annotations

import json
import sys
from urllib.parse import urlsplit

from PySide6.QtCore import QProcess, QSettings, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QSpinBox,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

STRINGS = {
    "vi": {
        "title": "AETHERION  /  ĐIỀU KHIỂN MÁY CHỦ",
        "endpoint": "Máy chủ HTTP", "start": "Khởi động máy chủ", "stop": "Dừng tiến trình đã mở",
        "check": "Kiểm tra dịch vụ", "username": "Tài khoản", "password": "Mật khẩu",
        "login": "Đăng nhập quản trị", "logout": "Khóa quản trị",
        "overview": "Tổng quan", "ai": "AI cục bộ", "sources": "Thành phần",
        "storage": "Dữ liệu", "events": "Nhật ký",
        "refresh": "Làm mới dữ liệu thật", "load_models": "Lấy danh sách mô hình", "test_model": "Kiểm tra AI thực tế",
        "save": "Lưu cấu hình AI", "backup": "Sao lưu SQLite ngay",
        "mode": "Chế độ AI", "local_url": "API Ollama cục bộ",
        "model": "Mô hình", "timeout": "Giới hạn chờ (giây)",
        "off": "Tắt AI", "local_only": "Chỉ dùng AI cục bộ",
        "not_ready": "Chưa đăng nhập; các mục quản trị đã khóa",
        "server_offline": "Không thể kết nối máy chủ",
        "server_online": "Máy chủ đã phản hồi /ready", "signed_in": "Đã xác thực quản trị",
        "forbidden": "Tài khoản không có quyền admin",
        "bad_target": "Chỉ cho phép http://127.0.0.1:PORT hoặc http://[::1]:PORT.",
        "failed": "Yêu cầu thất bại", "saved": "Đã lưu vào cơ sở dữ liệu máy chủ",
        "backup_ok": "Đã tạo bản sao SQLite có kiểm tra toàn vẹn",
        "ai_cloud": "Cloud AI chưa hỗ trợ: khóa bí mật và sự đồng ý chia sẻ dữ liệu phải có cơ chế an toàn trước khi kích hoạt.",
        "model_offline": "Ollama chưa sẵn sàng hoặc mô hình chưa được cài.",
        "missing_model": "Hãy lấy danh sách mô hình thật trước khi bật AI cục bộ.",
        "no_invented_data": "Dữ liệu chưa có nguồn xác thực được hiển thị là chưa kết nối, không phải bằng 0.",
        "bootstrap": "Chưa có tài khoản? Chạy lệnh cục bộ: aetherion-bootstrap --username admin --password <mật-khẩu-mạnh> --role admin",
        "process_notice": "Chỉ dừng được tiến trình do cửa sổ này khởi động.",
    },
    "en": {
        "title": "AETHERION  /  SERVER CONTROL",
        "endpoint": "HTTP server", "start": "Start server", "stop": "Stop owned process",
        "check": "Check service", "username": "Username", "password": "Password",
        "login": "Administrator sign in", "logout": "Lock administration",
        "overview": "Overview", "ai": "Local AI", "sources": "Subsystems",
        "storage": "Data", "events": "Audit events",
        "refresh": "Refresh live records", "load_models": "Discover installed models", "test_model": "Test actual AI inference",
        "save": "Save AI settings", "backup": "Back up SQLite now",
        "mode": "AI mode", "local_url": "Local Ollama API",
        "model": "Model", "timeout": "Timeout (seconds)",
        "off": "AI disabled", "local_only": "Local AI only",
        "not_ready": "Not authenticated; admin controls are locked",
        "server_offline": "Cannot reach server",
        "server_online": "Server answered /ready", "signed_in": "Administrator authenticated",
        "forbidden": "Account does not have admin role",
        "bad_target": "Only http://127.0.0.1:PORT or http://[::1]:PORT is allowed.",
        "failed": "Request failed", "saved": "Saved in the server database",
        "backup_ok": "Created integrity-checked SQLite snapshot",
        "ai_cloud": "Cloud AI unavailable: secure secret storage and consent-aware data policy must be implemented first.",
        "model_offline": "Ollama is offline or the selected model is not installed.",
        "missing_model": "Discover an installed model before enabling local AI.",
        "no_invented_data": "Missing verified sources remain disconnected, never zero-valued mock readings.",
        "bootstrap": "No account yet? Run locally: aetherion-bootstrap --username admin --password <strong-password> --role admin",
        "process_notice": "Only the process started by this window can be stopped.",
    },
}


class AdminWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("TRUY TINH", "AETHERION Server Control")
        self.locale = str(self.settings.value("ui/language", "vi"))
        if self.locale not in STRINGS:
            self.locale = "vi"
        self.access_token = ""
        self.network = QNetworkAccessManager(self)
        self.owned_server = QProcess(self)
        self.owned_server.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.owned_server.errorOccurred.connect(
            lambda _error: self._status(self.owned_server.errorString()))
        self.owned_server.finished.connect(lambda *_: self._status(self.t("server_offline")))
        self.setMinimumSize(1000, 700)
        self.resize(1280, 800)
        self._build()
        self._translate()
        self._status(self.t("not_ready"))
        QTimer.singleShot(150, self.check_service)

    def t(self, key: str) -> str:
        return STRINGS[self.locale][key]

    def _button(self, callback):
        button = QPushButton()
        button.clicked.connect(callback)
        button.setMinimumHeight(38)
        return button

    def _build(self):
        root = QWidget()
        main = QVBoxLayout(root)
        main.setContentsMargins(26, 22, 26, 20)
        main.setSpacing(16)
        header = QHBoxLayout()
        self.heading = QLabel()
        self.heading.setObjectName("heading")
        header.addWidget(self.heading, 1)
        self.locale_combo = QComboBox()
        self.locale_combo.addItem("Tiếng Việt", "vi")
        self.locale_combo.addItem("English", "en")
        self.locale_combo.setCurrentIndex(0 if self.locale == "vi" else 1)
        self.locale_combo.currentIndexChanged.connect(self.change_locale)
        header.addWidget(self.locale_combo)
        main.addLayout(header)

        connection = QHBoxLayout()
        self.endpoint_label = QLabel()
        connection.addWidget(self.endpoint_label)
        self.endpoint = QLineEdit(str(self.settings.value("server/url", "http://127.0.0.1:8765")))
        self.endpoint.setMinimumWidth(240)
        connection.addWidget(self.endpoint, 1)
        self.check_button = self._button(self.check_service)
        connection.addWidget(self.check_button)
        self.start_button = self._button(self.start_server)
        connection.addWidget(self.start_button)
        self.stop_button = self._button(self.stop_server)
        connection.addWidget(self.stop_button)
        main.addLayout(connection)

        credentials = QHBoxLayout()
        self.username_label = QLabel()
        credentials.addWidget(self.username_label)
        self.username = QLineEdit()
        self.username.setMaximumWidth(170)
        credentials.addWidget(self.username)
        self.password_label = QLabel()
        credentials.addWidget(self.password_label)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setMaximumWidth(220)
        self.password.returnPressed.connect(self.login)
        credentials.addWidget(self.password)
        self.login_button = self._button(self.login)
        credentials.addWidget(self.login_button)
        self.logout_button = self._button(self.logout)
        credentials.addWidget(self.logout_button)
        credentials.addStretch()
        main.addLayout(credentials)

        self.status = QLabel()
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        main.addWidget(self.status)

        self.tabs = QTabWidget()
        main.addWidget(self.tabs, 1)

        overview = QWidget()
        overview_layout = QVBoxLayout(overview)
        self.overview_text = QTextEdit()
        self.overview_text.setReadOnly(True)
        self.overview_refresh = self._button(self.refresh)
        overview_layout.addWidget(self.overview_refresh)
        overview_layout.addWidget(self.overview_text, 1)
        self.tabs.addTab(overview, "")

        ai = QWidget()
        ai_layout = QVBoxLayout(ai)
        form = QFormLayout()
        self.mode_label = QLabel()
        self.ai_mode = QComboBox()
        self.ai_mode.addItem("", "off")
        self.ai_mode.addItem("", "local_only")
        form.addRow(self.mode_label, self.ai_mode)
        self.local_label = QLabel()
        self.local_url = QLineEdit("http://127.0.0.1:11434")
        form.addRow(self.local_label, self.local_url)
        self.model_label = QLabel()
        self.models = QComboBox()
        self.models.setEditable(True)
        self.models.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        form.addRow(self.model_label, self.models)
        self.timeout_label = QLabel()
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 30)
        self.timeout.setValue(5)
        form.addRow(self.timeout_label, self.timeout)
        ai_layout.addLayout(form)
        ai_actions = QHBoxLayout()
        self.models_button = self._button(self.load_models)
        ai_actions.addWidget(self.models_button)
        self.save_button = self._button(self.save_ai)
        ai_actions.addWidget(self.save_button)
        self.test_button = self._button(self.test_ai)
        ai_actions.addWidget(self.test_button)
        ai_actions.addStretch()
        ai_layout.addLayout(ai_actions)
        self.ai_result = QTextEdit()
        self.ai_result.setReadOnly(True)
        ai_layout.addWidget(self.ai_result, 1)
        self.cloud_notice = QLabel()
        self.cloud_notice.setWordWrap(True)
        ai_layout.addWidget(self.cloud_notice)
        self.tabs.addTab(ai, "")

        sources = QWidget()
        sources_layout = QVBoxLayout(sources)
        self.source_text = QTextEdit()
        self.source_text.setReadOnly(True)
        sources_layout.addWidget(self.source_text)
        self.tabs.addTab(sources, "")

        storage = QWidget()
        storage_layout = QVBoxLayout(storage)
        self.backup_button = self._button(self.backup)
        storage_layout.addWidget(self.backup_button)
        self.storage_text = QTextEdit()
        self.storage_text.setReadOnly(True)
        storage_layout.addWidget(self.storage_text)
        self.tabs.addTab(storage, "")

        events = QWidget()
        events_layout = QVBoxLayout(events)
        self.events_button = self._button(self.load_events)
        events_layout.addWidget(self.events_button)
        self.events_text = QTextEdit()
        self.events_text.setReadOnly(True)
        events_layout.addWidget(self.events_text)
        self.tabs.addTab(events, "")

        self.notice = QLabel()
        self.notice.setWordWrap(True)
        main.addWidget(self.notice)
        self.setCentralWidget(root)
        self.tabs.setEnabled(False)
        self.logout_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.setStyleSheet("""
            QWidget { background: #0a1224; color: #e6f0ff; font-size: 14px; }
            QLabel#heading { color: #a6e8ff; font-size: 25px; font-weight: 750; }
            QLabel#status { background: #162a45; border: 1px solid #335578;
                            border-radius: 9px; padding: 12px; }
            QLineEdit, QSpinBox, QComboBox, QTextEdit, QTabWidget::pane {
                background: #11213a; border: 1px solid #34516f; border-radius: 7px;
                padding: 8px; selection-background-color: #226f9c;
            }
            QPushButton { background: #174b70; border: 1px solid #3184a6;
                          border-radius: 8px; padding: 8px 12px; font-weight: 600; }
            QPushButton:hover { background: #216a91; }
            QPushButton:disabled { background: #25334a; color: #8a98a8; border-color: #33465d; }
            QTabBar::tab { padding: 11px 18px; background: #152b49; margin-right: 3px; }
            QTabBar::tab:selected { background: #1b7297; }
        """)

    def _translate(self):
        self.setWindowTitle(self.t("title"))
        for widget, key in (
            (self.heading, "title"), (self.endpoint_label, "endpoint"),
            (self.start_button, "start"), (self.stop_button, "stop"),
            (self.check_button, "check"), (self.username_label, "username"),
            (self.password_label, "password"), (self.login_button, "login"),
            (self.logout_button, "logout"), (self.overview_refresh, "refresh"),
            (self.mode_label, "mode"), (self.local_label, "local_url"),
            (self.model_label, "model"), (self.timeout_label, "timeout"),
            (self.models_button, "load_models"), (self.save_button, "save"),
            (self.test_button, "test_model"),
            (self.backup_button, "backup"), (self.events_button, "refresh"),
            (self.cloud_notice, "ai_cloud"),
        ):
            widget.setText(self.t(key))
        for index, key in enumerate(("overview", "ai", "sources", "storage", "events")):
            self.tabs.setTabText(index, self.t(key))
        self.ai_mode.setItemText(0, self.t("off"))
        self.ai_mode.setItemText(1, self.t("local_only"))
        self.notice.setText(self.t("no_invented_data") + "\n" + self.t("process_notice")
                            + "\n" + self.t("bootstrap"))

    def change_locale(self):
        self.locale = str(self.locale_combo.currentData())
        self.settings.setValue("ui/language", self.locale)
        self._translate()

    def _status(self, message: str):
        self.status.setText(message)

    def _base_url(self) -> str:
        parsed = urlsplit(self.endpoint.text().strip())
        if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}
                or parsed.username or parsed.password or parsed.path not in {"", "/"}
                or parsed.query or parsed.fragment):
            raise ValueError(self.t("bad_target"))
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError(self.t("bad_target")) from exc
        if port is None or not 1 <= port <= 65535:
            raise ValueError(self.t("bad_target"))
        address = "127.0.0.1" if parsed.hostname == "127.0.0.1" else "[::1]"
        return f"http://{address}:{port}"

    def request(self, method: str, path: str, payload=None, callback=None, authenticated=True):
        try:
            base = self._base_url()
        except ValueError as exc:
            self._status(str(exc))
            return
        if authenticated and not self.access_token:
            self._status(self.t("not_ready"))
            return
        self.settings.setValue("server/url", base)
        request = QNetworkRequest(QUrl(base + path))
        request.setRawHeader(b"Accept", b"application/json")
        if authenticated:
            request.setRawHeader(b"Authorization", ("Bearer " + self.access_token).encode())
        request.setTransferTimeout(5000)
        if method == "GET":
            reply = self.network.get(request)
        else:
            data = json.dumps(payload or {}).encode("utf-8")
            request.setRawHeader(b"Content-Type", b"application/json")
            if method == "POST":
                reply = self.network.post(request, data)
            else:
                reply = self.network.sendCustomRequest(request, method.encode(), data)

        def finished():
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            raw = bytes(reply.readAll())
            error = reply.error()
            reply.deleteLater()
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except (ValueError, UnicodeError):
                body = {}
            if error != QNetworkReply.NetworkError.NoError or not isinstance(code, int) or code >= 400:
                message = body.get("detail", "") if isinstance(body, dict) else ""
                self._status(f"{self.t('failed')} (HTTP {code or 0}): {str(message)[:260] or reply.errorString()}")
                if code == 401 and authenticated:
                    self._clear_token()
                return
            if callback:
                callback(body)
        reply.finished.connect(finished)

    def check_service(self):
        self.request("GET", "/ready", callback=lambda data: self._status(self.t("server_online")
                     if data.get("status") == "ready" else self.t("server_offline")), authenticated=False)

    def start_server(self):
        if self.owned_server.state() != QProcess.ProcessState.NotRunning:
            return
        try:
            base = self._base_url()
        except ValueError as exc:
            self._status(str(exc))
            return
        port = str(urlsplit(base).port)
        self.owned_server.start(sys.executable, [
            "-m", "uvicorn", "aetherion_server.main:app",
            "--host", "127.0.0.1", "--port", port,
        ])
        self.stop_button.setEnabled(True)
        QTimer.singleShot(1100, self.check_service)

    def stop_server(self):
        if self.owned_server.state() != QProcess.ProcessState.NotRunning:
            self.owned_server.terminate()
            if not self.owned_server.waitForFinished(1500):
                self.owned_server.kill()
            self._clear_token()
        self.stop_button.setEnabled(False)

    def login(self):
        username, password = self.username.text().strip(), self.password.text()
        self.password.clear()
        if not username or not password:
            self._status(self.t("failed"))
            return
        self.request("POST", "/api/v1/auth/login",
                     {"username": username, "password": password},
                     callback=self._logged_in, authenticated=False)

    def _logged_in(self, response):
        user = response.get("user") or {}
        if user.get("role") != "admin":
            self._status(self.t("forbidden"))
            self._clear_token()
            return
        token = response.get("access_token", "")
        if not isinstance(token, str) or not token:
            self._status(self.t("failed"))
            return
        self.access_token = token
        self.tabs.setEnabled(True)
        self.logout_button.setEnabled(True)
        self._status(self.t("signed_in") + ": " + str(user.get("username", "")))
        self.refresh()

    def _clear_token(self):
        self.access_token = ""
        self.tabs.setEnabled(False)
        self.logout_button.setEnabled(False)

    def logout(self):
        if self.access_token:
            self.request("POST", "/api/v1/auth/logout", payload={}, authenticated=True)
        self._clear_token()
        self._status(self.t("not_ready"))

    def refresh(self):
        self.request("GET", "/api/v1/admin/overview", callback=self._overview)
        self.request("GET", "/api/v1/admin/ai/settings", callback=self._ai_settings)

    def _overview(self, body):
        self.overview_text.setPlainText(json.dumps({
            "service": body.get("service"), "api_version": body.get("api_version"),
            "database": body.get("database"), "counts": body.get("counts"),
            "subsystems": body.get("subsystems"),
        }, ensure_ascii=False, indent=2))
        self.source_text.setPlainText(json.dumps({
            "knowledge": body.get("knowledge"), "subsystems": body.get("subsystems"),
        }, ensure_ascii=False, indent=2))
        self.storage_text.setPlainText(json.dumps({
            "database": body.get("database"), "records": body.get("counts"),
        }, ensure_ascii=False, indent=2))

    def _ai_settings(self, body):
        data = body.get("settings") or {}
        index = self.ai_mode.findData(data.get("mode", "off"))
        self.ai_mode.setCurrentIndex(max(0, index))
        self.local_url.setText(str(data.get("local_url", "http://127.0.0.1:11434")))
        self.models.setCurrentText(str(data.get("local_model", "")))
        self.timeout.setValue(int(data.get("timeout_seconds", 5)))

    def load_models(self):
        self.request("GET", "/api/v1/admin/ai/local/models", callback=self._models_loaded)

    def _models_loaded(self, data):
        self.ai_result.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        selected = self.models.currentText()
        self.models.clear()
        self.models.addItems(data.get("models") or [])
        if selected:
            self.models.setCurrentText(selected)
        if not data.get("model_ready"):
            self._status(self.t("model_offline"))

    def save_ai(self):
        model = self.models.currentText().strip()
        mode = str(self.ai_mode.currentData())
        if mode == "local_only" and not model:
            self._status(self.t("missing_model"))
            return
        body = {
            "mode": mode, "local_runtime": "ollama",
            "local_url": self.local_url.text().strip(),
            "local_model": model, "timeout_seconds": self.timeout.value(),
            "cloud_data_sharing": False,
        }
        self.request("PUT", "/api/v1/admin/ai/settings", payload=body,
                     callback=lambda _: self._save_finished())

    def _save_finished(self):
        self._status(self.t("saved"))
        self.request("GET", "/api/v1/admin/ai/settings", callback=self._ai_settings)

    def test_ai(self):
        self.request("POST", "/api/v1/admin/ai/local/test", payload={},
                     callback=lambda result: self._ai_test_finished(result))

    def _ai_test_finished(self, result):
        self.ai_result.setPlainText(json.dumps(result, ensure_ascii=False, indent=2))
        self._status(str(result.get("status", "UNKNOWN")))

    def backup(self):
        self.request("POST", "/api/v1/admin/storage/backup", payload={},
                     callback=lambda result: self._backup_finished(result))

    def _backup_finished(self, result):
        self._status(self.t("backup_ok") + ": " + str(result.get("filename", "")))
        self.storage_text.append(json.dumps(result, ensure_ascii=False))

    def load_events(self):
        self.request("GET", "/api/v1/admin/events",
                     callback=lambda data: self.events_text.setPlainText(
                         json.dumps(data.get("events", []), ensure_ascii=False, indent=2)))

    def closeEvent(self, event):
        self.access_token = ""
        # QProcess owns only this window-spawned server; avoid an orphan/Qt crash.
        if self.owned_server.state() != QProcess.ProcessState.NotRunning:
            self.stop_server()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    window = AdminWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
