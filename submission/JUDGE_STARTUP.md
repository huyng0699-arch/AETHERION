# AETHERION — Judge & Reviewer Startup Guide

**Team:** TRUY TINH · **Challenge:** [NASA Space Apps 2026 — Create Health Monitoring Software for Astronauts on Space Missions](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)

This guide provides exact, reproducible commands to install and verify the AETHERION local HTTP server, test suite, and native Windows desktop starter.

> **Important scope notice:** AETHERION is an early-stage independent hackathon prototype. It is **not** a NASA product, certified medical device, or packaged Windows `.exe` installer. Do not enter real patient or sensitive personal health data into the local prototype.

---

## 1. Windows 10/11 Full Setup & Launch (Server + Native Qt Desktop)

**Prerequisites:**
- Windows 10 or 11 (64-bit)
- Python 3.11 with `py.exe` launcher on `PATH`
- Git for Windows

**Step 1 — Clone and run the setup script (PowerShell):**
```powershell
git clone https://github.com/huyng0699-arch/AETHERION.git
cd AETHERION
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```
This creates `.venv`, installs `./apps/server` and `./apps/desktop` in editable mode, and verifies `import aetherion_server, aetherion_desktop`.

**Step 2 — Start the local HTTP server (PowerShell Window 1):**
```powershell
.\scripts\start_server.ps1
```
Underlying command:
```powershell
.\.venv\Scripts\python.exe -m uvicorn aetherion_server.main:app --host 127.0.0.1 --port 8765
```
Verify the server health endpoint:
- `http://127.0.0.1:8765/health` (expected JSON: `{"service":"aetherion-server","status":"ok"}`)
- `http://127.0.0.1:8765/docs` (FastAPI interactive OpenAPI documentation)

**Step 3 — Start the native PySide6 desktop app (PowerShell Window 2):**
```powershell
.\scripts\start_desktop.ps1
```
Underlying command:
```powershell
.\.venv\Scripts\python.exe -m aetherion_desktop
```
The desktop opens directly into the native Qt Mission Control window (not a browser wrapper) with persistent top navigation and an API connectivity indicator.

---

## 2. Headless Verification (Linux / macOS / CI)

A reviewer on Linux or macOS can reproduce the repository checks, server package tests, and knowledge audits without a Windows GUI:

```bash
python3 scripts/quest_board.py check
python3 scripts/lint_python.py
python3 -m unittest discover -s tests -v
```

To test the server package in an isolated virtual environment:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ./apps/server
.venv/bin/python -c "import aetherion_server; print('server import ok')"
```

---

## 3. Verification Boundaries & Honest Limitations

- **Headless vs. Windows GUI:** Unit tests, Quest board checks, NASA/medical registry audits, and Python syntax checks run headlessly on Linux. Native Windows Qt rendering and `setup_windows.ps1` execution require an actual Windows 10/11 session with PySide6 graphics runtime.
- **No packaged `.exe`:** Installation uses editable Python packages in `.venv` via `scripts/setup_windows.ps1`.
- **No live sensors or clinical certification:** Unauthenticated localhost API is for development/demo evaluation only.
- **Official submission rule:** Completing the official **Project tab** on the NASA Space Apps 2026 team page is required; this repository alone does not constitute a completed submission.
