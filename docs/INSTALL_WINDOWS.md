# Install AETHERION on Windows — developer starter

**Scope:** These instructions install the **current developer prototype**, not a released Windows installer. It consists of a local Python API and an independently launched native PySide6 desktop app. A packaged `.exe` does not yet exist.

## Requirements

- Windows 10 or 11 (64-bit).
- Python 3.11, including `py.exe`; during installation check *Add Python to PATH* and *Install launcher*.
- Git for Windows.
- Internet for initial dependency installation. After installation, the health endpoint and desktop shell can run locally; no broader offline medical capability is claimed.

## Installation

Open **PowerShell**:

```powershell
git clone https://github.com/huyng0699-arch/AETHERION.git
cd AETHERION
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

The script creates `.venv`, installs server and desktop packages in editable mode, and checks their importability. It does not install drivers, device integrations or medical AI models.

### Manual alternative

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .\apps\server -e .\apps\desktop
```

## Start the system

**PowerShell window 1** — API:

```powershell
.\scripts\start_server.ps1
```

Expected endpoint: `http://127.0.0.1:8765/health`, returning JSON such as `{"service":"aetherion-server","status":"ok"}` if the process is running.

**PowerShell window 2** — Windows desktop:

```powershell
.\scripts\start_desktop.ps1
```

The desktop should open a **native AETHERION Mission Control window** with top navigation and an API connection check. If no observations exist, it reports **no data** rather than displaying invented readings.

## First tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Invoke-RestMethod http://127.0.0.1:8765/health
```

The local API documentation is at `http://127.0.0.1:8765/docs`. Only test with non-sensitive, development-purpose data. The POST observation API is an engineering input interface, **not a verified medical device connector**.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `py -3.11` not found | Install Python 3.11 with the Windows launcher; use `py -0p` to list versions |
| PowerShell execution policy blocks a script | Use `powershell -ExecutionPolicy Bypass -File .\scripts\start_server.ps1` or the direct `.venv\Scripts\python.exe` commands |
| Desktop says API offline | Start the server first; inspect port 8765 and `AETHERION_API_URL` |
| PySide6 import or Qt plugin error | Confirm 64-bit Python, reinstall desktop dependency and check system graphics/Qt runtime |
| Port 8765 occupied | Stop the conflicting process; do not expose the unauthenticated prototype to external networks |
| Git clone fails on private repository | Authenticate GitHub account with access; publication is a separate repository decision |

## Limitations

No production authentication, encryption-at-rest, clinician-approved guidance, real wearable input, released EXE, medical validation or flight qualification exists at this scaffold stage. **Never use for patient care or sensitive clinical records.**
