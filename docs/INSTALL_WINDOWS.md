# AETHERION — Install, run and package the native Windows desktop

**Status:** native source and reproducible Windows packaging scripts are committed; an actual signed/reviewed EXE, Windows screenshot and independent release approval are **NOT** yet in evidence. Do not treat a source commit or an unexecuted GitHub Actions job as a successful Windows build.

This is **two separate applications**, not a browser wrapper: a local HTTP AETHERION Server and a PySide6 Desktop. An optional Server Control GUI manages the local server. The desktop opens at the five-card Portal with a top horizontal menu and a persisted Vietnamese / English selector. No credentials, medical observations, AI model weights or user database are shipped inside the EXE.

## Prerequisites

- Windows 10/11 x64 with an interactive desktop session.
- Python 3.11–3.13 x64, Git for Windows, and initial Internet access to install dependencies.
- The owner's authenticated access to the **private** `huyng0699-arch/AETHERION` repository.
- Enough free disk space for PySide6, PyInstaller and optional verified image assets.

## Clone and install

In **PowerShell**:

```powershell
git clone https://github.com/huyng0699-arch/AETHERION.git
cd AETHERION
.\scripts\setup_windows.ps1
```

The setup installs the Server and Desktop into `.venv`. On Windows systems where local script execution is blocked, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

## Run from source — server and desktop remain independent

Start the API in PowerShell window 1:

```powershell
.\scripts\start_server.ps1
```

Start the **native** PySide6 desktop in window 2:

```powershell
.\scripts\start_desktop.ps1
```

The desktop starts at the Portal, **not** an automatic Mission Control intake page. The HTTP health check uses `http://127.0.0.1:8765/health`. When the server is unavailable, the app must show an offline state, **not** fabricate health observations. The local user must sign in before viewing authorized personal records. Language switching changes presentation only.

An optional separately launched Server Control GUI:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".\apps\server[admin]"
.\.venv\Scripts\python.exe -m aetherion_server.admin_gui
```

## Build a distributable *candidate* EXE on a real Windows machine

```powershell
.\.venv\Scripts\python.exe -m pip install "pyinstaller>=6,<7"
.\scripts\build_windows.ps1
```

The build script checks that the package imports, creates a dedicated PyInstaller launcher, bundles the five original NASA spaceflight-hazard JSON references and attempts to construct a separate **read-only** CliFF SQLite library by processing source-backed records and verifying cited media hashes. An article that cannot be imported safely is recorded as rejected; missing slots are **not** invented. The original structured JSON is not rewritten.

The build emits:

```text
dist/AETHERION-Desktop/
  AETHERION-Desktop.exe
  _internal/...                     # PyInstaller native dependencies and NASA hazards
  data/knowledge/nasa/cliff_119_2023/
    AETHERION_NASA_CLIFF_119.sqlite  # only when source-backed import succeeds
    medical-manifest.json            # actual count, missing slots and SHA256
  build-evidence.json                # EXE hash and GUI smoke result
```

The default build launches the candidate and checks whether a **real Win32 top-level window handle** becomes visible. If the process exits or no window is created, the script fails and records `FAILED_OR_NO_INTERACTIVE_DESKTOP`; it does **not** print a false PASS. When a window is visible, the status is `WINDOW_HANDLE_OBSERVED`, not full UX acceptance. Inspect the five Portal buttons, top navigation, theme selector, VI/EN toggle, NASA Explore offline references, and connection loss/reconnect manually.

The optional flags are:

```powershell
.\scripts\build_windows.ps1 -RequireLibrary
.\scripts\build_windows.ps1 -SkipSmoke
```

`-RequireLibrary` makes an unusable local CliFF import a build blocker. `-SkipSmoke` is for automated packaging on a noninteractive runner; it must **not** be counted as having booted a visible Windows window.

The accompanying workflow `.github/workflows/windows-candidate.yml` can be launched manually in GitHub Actions and uploads an **unsigned candidate** folder. If GitHub Actions has no runner assigned, its failure is an infrastructure gate, not evidence the EXE was built or code tested.

## Scientific library provenance and limitations

- The content counts are whatever the current importer actually accepts; **not** automatically 119. Inspect `medical-manifest.json`, including `missing_or_rejected_slots`, `import_status`, `sqlite_sha256` and `original_pdf_archive_verified=false`.
- Original NASA PDFs, independent NASA approval of the extracted JSON, and clinical treatment safety are **not** certified by this build. Original source text is shown in English; the UI is bilingual.
- The five NASA hazard references are research context, never astronaut telemetry. Other native modules that require a live server remain unavailable when disconnected.
- Never package actual patient records, the Server SQLite database, passwords, personal tokens, or API keys.
- Use `scripts/release_readiness.py --scope release` and independent Windows acceptance before declaring the product release-ready.

## Troubleshooting

| Observed symptom | Next check |
| --- | --- |
| GitHub Actions fails in 1–3 seconds with no runner and no steps | Check repository/account Actions billing, execution permissions, quota and runner availability in GitHub; re-run only after the external issue is resolved |
| Python/PySide6 import failure | Use a supported x64 Python, rerun `setup_windows.ps1`, inspect the dependency error |
| No EXE after PyInstaller | Read the PyInstaller failure; the script exits nonzero before a success claim |
| EXE exists but no GUI window appears | Inspect `build-evidence.json`, Windows Qt plugin errors and stderr/debug console; do not mark Q-0002 or Q-0010 DONE |
| CliFF catalog says MISSING or 0/119 | Check `data/knowledge/nasa/cliff_119_2023/` and the import manifest for actual records, source images, missing bytes or license/hash errors |
| NASA hazard reference missing | Verify the actual five `_internal/knowledge/nasa/hazards/*.json` files were packaged |
| Server offline | Start Server independently and check the configured loopback API/port; an offline state is expected when no server runs |
| Language switch does not update content | Distinguish UI chrome from unchanged, original-language scientific text; the latter must not be silently retranslated |

This project is not a medical device or substitute for emergency medical care.
