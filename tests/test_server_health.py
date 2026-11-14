"""Behavioral process-level test for Q-0046 GET /health."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class ServerHealthBehavioralTests(unittest.TestCase):
    def test_live_health_and_stopped_process_rejection(self) -> None:
        port = _free_port()
        url = f"http://127.0.0.1:{port}/health"
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            src_path = str(ROOT / "apps" / "server" / "src")
            env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
            env["AETHERION_DB_PATH"] = str(Path(tmp) / "health.sqlite3")

            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "aetherion_server.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--log-level",
                    "warning",
                ],
                cwd=str(ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 15.0
                payload = None
                while time.monotonic() < deadline:
                    if proc.poll() is not None:
                        self.fail(f"Server exited early with code {proc.returncode}")
                    try:
                        with urlopen(url, timeout=2) as resp:
                            self.assertEqual(resp.status, 200)
                            payload = json.loads(resp.read().decode("utf-8"))
                            break
                    except Exception:
                        time.sleep(0.2)
                self.assertEqual(payload, {"service": "aetherion-server", "status": "ok"})
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)

            # Stopped process must NOT masquerade as healthy
            with self.assertRaises((URLError, ConnectionRefusedError, OSError)):
                urlopen(url, timeout=2)


if __name__ == "__main__":
    unittest.main()
