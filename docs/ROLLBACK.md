# AETHERION Package & Release Rollback Procedure

This document defines how to roll back a broken Windows AETHERION build or local Python environment to the previous verified release **without losing SQLite health, care, or audit data**.

## 1. Core Data-Preservation Boundary

All persistent user, observation, care episode, safety incident, and audit records reside in the SQLite database file (`AETHERION_DB_PATH`, default under the user/local data directory) and **never** inside the executable or `.venv` install directory.

- **Do NOT delete** `AETHERION_DB_PATH` (or its `-wal` / `-shm` files while the server is running).
- **Do NOT overwrite** `knowledge/nasa/cliff_119_2023/AETHERION_NASA_CLIFF_119.sqlite` or `knowledge/symptoms/ASTRA_819_REFERENCE.json` with unverified drafts.

## 2. Pre-Upgrade / Pre-Rollback Backup

Before replacing any release binary or upgrading packages:

1. Stop `aetherion-desktop` and `aetherion-server` cleanly (`Ctrl+C` on the uvicorn terminal).
2. Create an atomic SQLite backup using the server admin endpoint (while running) or `sqlite3` / file copy (after stopping):
   - Admin API: `POST /api/v1/admin/storage/backup` (requires `admin` session).
   - Manual PowerShell (with server stopped):
     ```powershell
     Copy-Item $env:AETHERION_DB_PATH "$env:AETHERION_DB_PATH.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
     ```

## 3. Rolling Back a Windows Packaged Release (`AETHERION.exe` / ZIP)

1. Stop the running `AETHERION.exe` and `aetherion-server` processes.
2. Verify the SHA-256 of the previous known-good release archive against its recorded release checksum (`Get-FileHash <archive>.zip -Algorithm SHA256`).
3. Rename the broken application folder (e.g., `AETHERION-broken`) rather than deleting it until rollback is verified.
4. Extract/reinstall the previous verified release into the install location.
5. Point `AETHERION_DB_PATH` (or leave the default data directory unchanged) to the existing SQLite database.
6. Start the server (`scripts\start_server.ps1`) and desktop (`scripts\start_desktop.ps1`), then verify:
   - `GET /health` returns `200 OK` with the expected previous `version`.
   - Existing subjects, observations, and care episodes remain readable.

## 4. Rolling Back a Source / `.venv` Installation

1. Stop both processes.
2. Check out the previous known-good git tag or commit SHA:
   ```powershell
   git checkout <previous-verified-tag-or-sha>
   ```
3. Reinstall editable packages without touching the SQLite database:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -e apps\server -e apps\desktop
   ```
4. Re-run `.\.venv\Scripts\python.exe -m aetherion_server.runtime_config --check` and start the server + desktop.
