"""Native AETHERION sign-in page with a public, real-data demo entry.

The widget owns only transient form/request state. It never persists a password
or bearer token; the shell receives a validated session through ``authenticated``.
"""
from __future__ import annotations

import ipaddress
import json
import os
from urllib.parse import urlsplit

from PySide6.QtCore import QByteArray, QTimer, QUrl, Qt, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


DEFAULT_API_URL = "http://127.0.0.1:8765"
LOGIN_TIMEOUT_MS = 15_000


_TEXT = {
    "en": {
        "eyebrow": "TRUY TINH  /  MISSION HEALTH",
        "title": "AETHERION",
        "subtitle": "Sign in for protected health routes, or open the public NASA MA-7 historical archive.",
        "server": "SERVER ADDRESS",
        "username": "USERNAME",
        "password": "PASSWORD",
        "server_placeholder": "http://127.0.0.1:8765",
        "username_placeholder": "Enter your username",
        "password_placeholder": "Enter your password",
        "server_hint": "Local loopback server only · HTTP or HTTPS",
        "sign_in": "Sign in",
        "signing_in": "Signing in…",
        "demo_hint": "Open the NASA MA-7 historical archive; no account is needed.",
        "archive_button": "NASA MA-7 archive",
        "err_url": "Enter a valid loopback server address, such as http://127.0.0.1:8765.",
        "err_credentials": "Enter both username and password.",
        "err_invalid_credentials": "The username or password was not accepted.",
        "err_forbidden": "This account is not allowed to sign in here.",
        "err_not_found": "The sign-in endpoint was not found on this server.",
        "err_timeout": "The server did not respond in time. Check the address and try again.",
        "err_network": "Could not reach the AETHERION server. Check that it is running.",
        "err_server": "The server could not complete sign-in. Try again shortly.",
        "err_response": "The server returned an invalid sign-in response.",
        "err_generic": "Sign-in failed. Check your connection and try again.",
    },
    "vi": {
        "eyebrow": "TRUY TINH  /  SỨC KHỎE NHIỆM VỤ",
        "title": "AETHERION",
        "subtitle": "Đăng nhập để mở chức năng sức khỏe cần quyền, hoặc xem kho lịch sử NASA MA-7 công khai.",
        "server": "ĐỊA CHỈ MÁY CHỦ",
        "username": "TÊN ĐĂNG NHẬP",
        "password": "MẬT KHẨU",
        "server_placeholder": "http://127.0.0.1:8765",
        "username_placeholder": "Nhập tên đăng nhập",
        "password_placeholder": "Nhập mật khẩu",
        "server_hint": "Chỉ máy chủ loopback trên thiết bị · HTTP hoặc HTTPS",
        "sign_in": "Đăng nhập",
        "signing_in": "Đang đăng nhập…",
        "demo_hint": "Xem kho lịch sử NASA MA-7; không cần tài khoản.",
        "archive_button": "Kho lưu trữ NASA MA-7",
        "err_url": "Nhập địa chỉ loopback hợp lệ, ví dụ http://127.0.0.1:8765.",
        "err_credentials": "Nhập cả tên đăng nhập và mật khẩu.",
        "err_invalid_credentials": "Tên đăng nhập hoặc mật khẩu không đúng.",
        "err_forbidden": "Tài khoản này không được phép đăng nhập tại đây.",
        "err_not_found": "Máy chủ không tìm thấy điểm cuối đăng nhập.",
        "err_timeout": "Máy chủ chưa phản hồi. Kiểm tra địa chỉ rồi thử lại.",
        "err_network": "Không kết nối được máy chủ AETHERION. Kiểm tra máy chủ đang chạy.",
        "err_server": "Máy chủ chưa thể hoàn tất đăng nhập. Thử lại sau ít phút.",
        "err_response": "Máy chủ trả về phản hồi đăng nhập không hợp lệ.",
        "err_generic": "Đăng nhập không thành công. Kiểm tra kết nối rồi thử lại.",
    },
}


def _normalize_loopback_base_url(value: str) -> str:
    """Return a root HTTP(S) URL whose host is an explicit loopback address."""
    raw = str(value or "").strip()
    if not raw or any(char.isspace() or ord(char) < 32 for char in raw):
        raise ValueError("loopback_url")
    try:
        parsed = urlsplit(raw)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError("loopback_url") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("loopback_url")
    if not host or parsed.username is not None or parsed.password is not None:
        raise ValueError("loopback_url")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("loopback_url")
    if parsed.netloc.endswith(":") or (port is not None and not 1 <= port <= 65535):
        raise ValueError("loopback_url")

    if host.casefold() != "localhost":
        try:
            if not ipaddress.ip_address(host).is_loopback:
                raise ValueError("loopback_url")
        except ValueError as exc:
            raise ValueError("loopback_url") from exc

    return f"{parsed.scheme.lower()}://{parsed.netloc}".rstrip("/")


class LoginPage(QWidget):
    """Login view for AETHERION's native shell.

    Signals:
        authenticated: validated ``POST /api/v1/auth/login`` JSON and the
            normalized loopback server base URL. The parent owns the session.
        demo_requested: open the public NASA demo without requiring credentials.
    """

    authenticated = Signal(dict, str)
    demo_requested = Signal()

    def set_visuals(self, theme_name: str, mode: str, high_contrast: bool = False, accent_override: str = "") -> None:
        from .visual_theme import palette_for
        palette = palette_for(theme_name, mode, high_contrast, accent_override)
        self.demo_button.setStyleSheet(
            "QPushButton { background: " + palette.surface_alt + "; color: " + palette.accent
            + "; border: 1px solid " + palette.accent + "; border-radius: 12px; padding: 10px 24px; font-weight: 700; }"
            + "QPushButton:hover { background: " + palette.card_hover + "; }"
        )

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        network: QNetworkAccessManager | None = None,
        api_url: str | None = None,
        locale: str = "en",
        timeout_ms: int = LOGIN_TIMEOUT_MS,
    ) -> None:
        super().__init__(parent)
        self.network = network or QNetworkAccessManager(self)
        self.timeout_ms = max(1_000, int(timeout_ms))
        self._reply: QNetworkReply | None = None
        self._timed_out = False
        self._busy = False
        self._locale = "en"
        self._visible_error = ""

        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._abort_timed_out_request)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(34, 28, 34, 28)
        outer.setSpacing(0)
        outer.addStretch(1)

        centered = QHBoxLayout()
        centered.addStretch(1)
        self.card = QFrame(self)
        self.card.setObjectName("contentPanel")
        self.card.setMinimumWidth(460)
        self.card.setMaximumWidth(560)
        self.card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(34, 30, 34, 30)
        card_layout.setSpacing(14)

        self.eyebrow = QLabel(self.card)
        self.eyebrow.setObjectName("eyebrow")
        card_layout.addWidget(self.eyebrow)

        self.title = QLabel(self.card)
        self.title.setObjectName("heroTitle")
        card_layout.addWidget(self.title)

        self.subtitle = QLabel(self.card)
        self.subtitle.setObjectName("heroCopy")
        self.subtitle.setWordWrap(True)
        card_layout.addWidget(self.subtitle)

        card_layout.addSpacing(4)

        self.server_label = self._field_label(self.card)
        card_layout.addWidget(self.server_label)
        self.server_input = QLineEdit(self.card)
        self.server_input.setMinimumHeight(42)
        self.server_input.setClearButtonEnabled(True)
        self.server_input.setAutoFillBackground(False)
        self.server_input.setAccessibleName("AETHERION server base URL")
        configured_url = api_url or os.environ.get("AETHERION_API_URL", DEFAULT_API_URL)
        self.server_input.setText(str(configured_url).strip())
        card_layout.addWidget(self.server_input)

        self.server_hint = QLabel(self.card)
        self.server_hint.setObjectName("pageHint")
        card_layout.addWidget(self.server_hint)

        form = QHBoxLayout()
        form.setSpacing(14)
        user_column = QVBoxLayout()
        user_column.setSpacing(6)
        self.username_label = self._field_label(self.card)
        self.username_input = QLineEdit(self.card)
        self.username_input.setMinimumHeight(42)
        self.username_input.setClearButtonEnabled(True)
        self.username_input.setAccessibleName("Username")
        user_column.addWidget(self.username_label)
        user_column.addWidget(self.username_input)
        form.addLayout(user_column, 1)

        password_column = QVBoxLayout()
        password_column.setSpacing(6)
        self.password_label = self._field_label(self.card)
        self.password_input = QLineEdit(self.card)
        self.password_input.setMinimumHeight(42)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setAccessibleName("Password")
        self.password_input.returnPressed.connect(self._submit_login)
        password_column.addWidget(self.password_label)
        password_column.addWidget(self.password_input)
        form.addLayout(password_column, 1)
        card_layout.addLayout(form)

        self.error_label = QLabel(self.card)
        self.error_label.setObjectName("pageHint")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #D44747; font-weight: 700;")
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        self.sign_in_button = QPushButton(self.card)
        self.sign_in_button.setObjectName("primaryAction")
        self.sign_in_button.setMinimumHeight(48)
        self.sign_in_button.setDefault(True)
        self.sign_in_button.clicked.connect(self._submit_login)
        actions.addWidget(self.sign_in_button, 2)

        self.demo_button = QPushButton("", self.card)
        self.demo_button.setObjectName("navButton")
        self.demo_button.setMinimumHeight(48)
        self.demo_button.setAccessibleName("NASA MA-7 archive")
        self.demo_button.clicked.connect(self._open_demo)
        actions.addWidget(self.demo_button, 1)
        card_layout.addLayout(actions)

        self.demo_hint = QLabel(self.card)
        self.demo_hint.setObjectName("pageHint")
        self.demo_hint.setWordWrap(True)
        card_layout.addWidget(self.demo_hint)

        centered.addWidget(self.card, 1)
        centered.addStretch(1)
        outer.addLayout(centered, 0)
        outer.addStretch(1)

        self.setTabOrder(self.server_input, self.username_input)
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.sign_in_button)
        self.setTabOrder(self.sign_in_button, self.demo_button)
        self.set_locale(locale)

    @staticmethod
    def _field_label(parent: QWidget) -> QLabel:
        label = QLabel(parent)
        label.setObjectName("eyebrow")
        return label

    def set_locale(self, locale: str) -> None:
        """Update user-facing text while retaining entered values."""
        self._locale = "vi" if str(locale or "").lower().startswith("vi") else "en"
        text = _TEXT[self._locale]
        self.eyebrow.setText(text["eyebrow"])
        self.title.setText(text["title"])
        self.subtitle.setText(text["subtitle"])
        self.server_label.setText(text["server"])
        self.username_label.setText(text["username"])
        self.password_label.setText(text["password"])
        self.server_input.setPlaceholderText(text["server_placeholder"])
        self.username_input.setPlaceholderText(text["username_placeholder"])
        self.password_input.setPlaceholderText(text["password_placeholder"])
        self.server_hint.setText(text["server_hint"])
        self.demo_hint.setText(text["demo_hint"])
        self.demo_button.setText(text["archive_button"])
        self.demo_button.setAccessibleName(text["archive_button"])
        self.sign_in_button.setText(text["signing_in"] if self._busy else text["sign_in"])
        self._refresh_error_text()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.server_input.setEnabled(not busy)
        self.username_input.setEnabled(not busy)
        self.password_input.setEnabled(not busy)
        self.sign_in_button.setEnabled(not busy)
        text = _TEXT[self._locale]
        self.sign_in_button.setText(text["signing_in"] if busy else text["sign_in"])

    def _show_error(self, key: str) -> None:
        self._visible_error = key
        self._refresh_error_text()

    def _refresh_error_text(self) -> None:
        if not self._visible_error:
            self.error_label.clear()
            self.error_label.hide()
            return
        self.error_label.setText(_TEXT[self._locale].get(self._visible_error, _TEXT[self._locale]["err_generic"]))
        self.error_label.show()

    def _submit_login(self) -> None:
        if self._busy:
            return
        self._visible_error = ""
        self._refresh_error_text()

        try:
            base_url = _normalize_loopback_base_url(self.server_input.text())
        except ValueError:
            self._show_error("err_url")
            self.server_input.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            self._show_error("err_credentials")
            (self.username_input if not username else self.password_input).setFocus(Qt.FocusReason.OtherFocusReason)
            return

        self.server_input.setText(base_url)
        request = QNetworkRequest(QUrl(f"{base_url}/api/v1/auth/login"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(QByteArray(b"Accept"), QByteArray(b"application/json"))
        # Do not forward credentials through an HTTP redirect, if supported by
        # the bundled Qt version. The server is expected to answer this URL.
        try:
            request.setAttribute(
                QNetworkRequest.Attribute.RedirectPolicyAttribute,
                QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
            )
        except (AttributeError, TypeError):
            pass

        payload = json.dumps(
            {"username": username, "password": password},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        self._set_busy(True)
        self._timed_out = False
        self._reply = self.network.post(request, QByteArray(payload))
        reply = self._reply
        reply.finished.connect(lambda current=reply, base=base_url: self._finish_login(current, base))
        self._timeout_timer.start(self.timeout_ms)

    def _abort_timed_out_request(self) -> None:
        reply = self._reply
        if reply is None:
            return
        self._timed_out = True
        reply.abort()

    def _finish_login(self, reply: QNetworkReply, base_url: str) -> None:
        if reply is not self._reply:
            reply.deleteLater()
            return
        self._timeout_timer.stop()
        timed_out = self._timed_out
        self._timed_out = False
        self._reply = None
        self._set_busy(False)

        status_value = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        status = int(status_value) if status_value is not None else 0
        try:
            body = bytes(reply.readAll())
            payload = json.loads(body.decode("utf-8")) if body else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        network_error = reply.error()
        reply.deleteLater()

        if timed_out:
            self._show_error("err_timeout")
            return
        if status < 200 or status >= 300:
            if status == 401:
                self._show_error("err_invalid_credentials")
            elif status == 403:
                self._show_error("err_forbidden")
            elif status == 404:
                self._show_error("err_not_found")
            elif status >= 500:
                self._show_error("err_server")
            elif status == 0 or network_error != QNetworkReply.NetworkError.NoError:
                self._show_error("err_network")
            else:
                self._show_error("err_generic")
            return

        if not isinstance(payload, dict):
            self._show_error("err_response")
            return
        token = payload.get("access_token")
        expires_at = payload.get("expires_at")
        user = payload.get("user")
        if (
            not isinstance(token, str)
            or not token.strip()
            or not isinstance(expires_at, str)
            or not expires_at.strip()
            or not isinstance(user, dict)
            or not isinstance(user.get("username"), str)
            or not user["username"].strip()
        ):
            self._show_error("err_response")
            return

        self.password_input.clear()
        self._visible_error = ""
        self._refresh_error_text()
        self.authenticated.emit(payload, base_url)

    def _open_demo(self) -> None:
        # If the user selects Demo mid-request, cancel sign-in so its late
        # response cannot unexpectedly replace the public demo screen.
        reply = self._reply
        if reply is not None:
            self._reply = None
            self._timeout_timer.stop()
            self._timed_out = False
            self._set_busy(False)
            reply.abort()
        self._visible_error = ""
        self._refresh_error_text()
        self.demo_requested.emit()
