"""Native first-launch runtime: reuse/start local Server and preseed Demo SQLite.

Server and fictional demo remain separate security boundaries:
* only start a packaged local Python server on the stock 127.0.0.1:8765 URL
* never create a default password or account or write to the server's store
* Q-0484's synthetic SQLite fixture is generated in its OWN worker thread
* failure remains a truthful offline or unavailable state, never a fake health

No imported server application object or direct cross-process database write.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, QProcess, QThread, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from .features.demo.synthetic_patients import build_demo_database, demo_stats

DEFAULT_SERVER_URL = "http://127.0.0.1:8765"


def _may_autostart_server(api_url: str) -> bool:
    """Local default only: custom URLs, LAN, HTTPS and explicit opt-out are off."""
    if os.environ.get("AETHERION_AUTOSTART_LOCAL_SERVER", "1").strip().lower() in (
            "0", "off", "false", "no"):
        return False
    if os.environ.get("AETHERION_API_URL", DEFAULT_SERVER_URL).rstrip("/") != DEFAULT_SERVER_URL:
        return False
    try:
        parsed = urlsplit(api_url)
        return (
            parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
            and parsed.port == 8765 and parsed.path in ("", "/")
            and not parsed.query and not parsed.fragment
            and parsed.username is None and parsed.password is None
        )
    except (TypeError, ValueError):
        return False


def _local_python() -> str | None:
    """Never relaunch a frozen executable with Python module flags."""
    override = os.environ.get("AETHERION_SERVER_PYTHON", "").strip()
    if override:
        p = Path(override)
        if p.is_file() and p.stem.lower().startswith("python"):
            return str(p.resolve())
        return None
    if getattr(sys, "frozen", False):
        return None
    python = Path(sys.executable)
    if not python.is_file() or not python.stem.lower().startswith("python"):
        return None
    if importlib.util.find_spec("uvicorn") is None or importlib.util.find_spec("aetherion_server") is None:
        return None
    return str(python.resolve())


class _SeedFictionalCrew(QThread):
    """The only background creator; never uses the authenticated server SQLite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats: dict | None = None
        self.failure = ""

    def run(self):
        try:
            # Idempotent per UTC day, with the Q-0484 demo-only path guard.
            build_demo_database()
            stats = demo_stats()
            if not stats.get("is_synthetic") or stats.get("subjects") != 5:
                raise RuntimeError("Synthetic crew dataset validation failed")
            if stats.get("days") != 540 or stats.get("metrics") != 12:
                raise RuntimeError("Synthetic history does not match expected coverage")
            self.stats = stats
        except (OSError, ValueError, RuntimeError, Exception) as error:
            # Do not reveal any patient contents / credentials in UI.
            self.failure = type(error).__name__


class StartupRuntime(QObject):
    """Child-service lifecycle with async probes and one asynchronous demo seed."""

    server_ready = Signal()
    server_unavailable = Signal(str)
    demo_ready = Signal(dict)
    demo_unavailable = Signal(str)

    def __init__(self, api_url: str = DEFAULT_SERVER_URL, parent=None):
        super().__init__(parent)
        self.api_url = str(api_url).rstrip("/")
        self._network = QNetworkAccessManager(self)
        self._probe_reply: QNetworkReply | None = None
        self._attempts = 0
        self._server = QProcess(self)
        self._server.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._server.errorOccurred.connect(self._process_error)
        self._server.finished.connect(self._server_finished)
        self._retry = QTimer(self)
        self._retry.setInterval(450)
        self._retry.timeout.connect(self._probe)
        self._server_started = False
        self._server_is_ready = False
        self._last_server_error = ""
        self._seed = _SeedFictionalCrew(self)
        self._seed.finished.connect(self._seed_finished)
        self._seed_started = False
        self._demo_stats: dict | None = None
        self._waiting_demo_callbacks = []

    def begin(self):
        """Call after the Qt main window is constructed; never block UI."""
        if not self._seed_started:
            self._seed_started = True
            self._seed.start()
        if _may_autostart_server(self.api_url):
            self._probe()

    def _probe(self):
        if self._probe_reply is not None:
            return
        self._attempts += 1
        request = QNetworkRequest(QUrl(self.api_url + "/health"))
        request.setTransferTimeout(1700)
        self._probe_reply = self._network.get(request)
        self._probe_reply.finished.connect(self._probe_finished)

    def _probe_finished(self):
        reply = self._probe_reply
        self._probe_reply = None
        if reply is None:
            return
        error = reply.error()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        try:
            payload = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except (UnicodeDecodeError, ValueError, TypeError):
            payload = {}
        reply.deleteLater()
        if (error == QNetworkReply.NetworkError.NoError and status == 200
                and isinstance(payload, dict)
                and payload.get("service") == "aetherion-server"
                and payload.get("status") == "ok"):
            self._server_is_ready = True
            self._retry.stop()
            self.server_ready.emit()
            return
        if self._server_started:
            if self._attempts >= 24 or self._server.state() == QProcess.ProcessState.NotRunning:
                self._retry.stop()
                self.server_unavailable.emit(self._last_server_error or "LOCAL_SERVER_START_FAILED")
            return
        if error != QNetworkReply.NetworkError.ConnectionRefusedError:
            # A listening foreign service, a timeout or an invalid /health
            # response must NEVER be overwritten with another server process.
            self.server_unavailable.emit("LOCAL_SERVER_ADDRESS_UNAVAILABLE")
            return
        self._start_local_server()

    def _start_local_server(self):
        if self._server_started or not _may_autostart_server(self.api_url):
            return
        executable = _local_python()
        if executable is None:
            self.server_unavailable.emit("LOCAL_SERVER_PYTHON_NOT_INSTALLED")
            return
        self._server_started = True
        self._server.setProgram(executable)
        self._server.setArguments([
            "-m", "uvicorn", "aetherion_server.main:app",
            "--host", "127.0.0.1", "--port", "8765",
            "--log-level", "warning",
        ])
        self._server.start()
        self._retry.start()

    def _process_error(self, _error):
        if not self._server_is_ready:
            self._last_server_error = "LOCAL_SERVER_PROCESS_ERROR"
            self._retry.stop()
            self.server_unavailable.emit(self._last_server_error)

    def _server_finished(self, _code, _status):
        self._retry.stop()
        if not self._server_is_ready:
            self.server_unavailable.emit(self._last_server_error or "LOCAL_SERVER_EXITED")

    def _seed_finished(self):
        self._demo_stats = self._seed.stats
        if self._seed.stats is not None:
            self.demo_ready.emit(dict(self._seed.stats))
        else:
            self.demo_unavailable.emit(self._seed.failure or "SYNTHETIC_DATA_UNAVAILABLE")
        callbacks = self._waiting_demo_callbacks
        self._waiting_demo_callbacks = []
        for callback in callbacks:
            callback(self._demo_stats is not None)

    def request_demo_ready(self, callback):
        """Run callback only after the background writer has closed SQLite.

        Callbacks receive a boolean; the owning widget may present an error
        or independently retry using Q-0484's existing public start() contract.
        """
        if self._seed.isRunning():
            self._waiting_demo_callbacks.append(callback)
        else:
            callback(self._demo_stats is not None)

    def stop(self):
        """Release only the service this exact app launched, never an external one."""
        self._retry.stop()
        if self._server.state() != QProcess.ProcessState.NotRunning:
            self._server.terminate()
            if not self._server.waitForFinished(1500):
                self._server.kill()
                self._server.waitForFinished(700)
        if self._seed.isRunning():
            self._seed.wait(5000)
