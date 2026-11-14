# AETHERION first-run: default local Server and pre-seeded fictional crew

> Current Login entry: **Demo** opens the real NASA source briefing and archive, as specified for the mobile/desktop login flow. The existing **SIMULATED** route and its isolated preparation remain reachable through the native workspace; they do not replace the historical NASA source or populate the authoritative health store. See `MOBILE_DELIVERY_20261115.md` for scoped observed results.

**Scope:** Native Windows/PySide6 desktop first launch. This does not turn the Windows app into a browser wrapper or merge its independent Server binary with the GUI.

## First launch from the installed Python environment

Launch `scripts/start_desktop.ps1` after running `scripts/setup_windows.ps1` once.

The first screen remains the native **Sign in** form with the clearly visible **Demo** action. The API address defaults to `http://127.0.0.1:8765`. The UI constructs the shell and then starts two **asynchronous** jobs without blocking Login:

1. **Local HTTP Server:** test the exact AETHERION `/health` response on the default loopback port. If a genuine AETHERION Server is already listening, reuse it. If the port actively refuses connections and a Python environment with installed `aetherion_server` and `uvicorn` is available, launch `python -m uvicorn aetherion_server.main:app --host 127.0.0.1 --port 8765 --log-level warning` as an app-owned child. Probe until it responds. Do not create another listener if the port is occupied by another service or responds incorrectly. Only the process owned by this Desktop launch is terminated on exit.
2. **SIMULATED crew data:** in a separate QThread, call the existing Q-0484 `build_demo_database()`, then read back `demo_stats()`. This creates or reuses the **dedicated** `~/.aetherion/demo/synthetic_patients_v1.sqlite3` test fixture: five wholly fictional subjects `DEMO-P001…DEMO-P005`, **540 calendar days**, twelve types of synthetic measurements, with deliberate missing days and explicit `synthetic=1 / TEST_FIXTURE / engineering_test` flags. It must never touch `~/.aetherion/observations.sqlite3`, the authenticated Server API, or NASA MA-7 archival values.

**Login Demo** now routes to `SimulatedDemoBriefing`. Start waits for the background seed to finish and calls the unchanged Q-0484 `PatientDemo.start()` in the persistent Mission Operations center. The briefing contains a separate NASA link; the NASA MA-7 1962 archive is **genuine historical research** and is never used as fictional patient history.

**Authorization is not bypassed:** the local service does not create an administrator, operator or universal password. Clinical Server routes still require a real account provisioned through the existing secure bootstrap procedure. Demo may be viewed without signing into patient data. No test entries are written to the authoritative health database.

## Overrides and troubleshooting

| Setting | Behavior |
| --- | --- |
| `AETHERION_API_URL` unset | First-run default `http://127.0.0.1:8765` |
| `AETHERION_API_URL` explicitly custom | No automatic local Server launch; preserve provided address |
| `AETHERION_AUTOSTART_LOCAL_SERVER=0` | Disable automatic Server launch; pre-seed fictional Demo normally |
| `AETHERION_SERVER_PYTHON=C:\\path\\to\\python.exe` | Optional Python executable override when an installed server exists outside the Desktop interpreter |
| An existing AETHERION Server on the default port | Reuse; never kill it when Desktop exits |
| Another service on default port, server startup failure or missing packages | Report offline/unavailable, **never** claim a successful connection; keep offline SIMULATED demo available |
| A frozen/packaged Windows EXE without separately installed Python Server | Do not recursively execute the GUI as Python; a packaged Server launcher must be supplied separately |

The existing `scripts/start_server.ps1` remains valid for manual operation. There is still **one** HTTP Server application and **one** authoritative health store, not a second Demo Server.

## Verification and current evidence

This change was committed through GitHub's contents API and inspected at the source level. **No new Windows/Qt process or real local SQLite database was created by this ChatGPT runtime**, which has no PySide6 package or connection to the owner's desktop. Do not mark the startup end-to-end behavior DONE until a fresh Windows session proves: one local listener; nonblocking Login; HTTP /health eventually online or truthful offline; 5 fictional subjects; 540-day timeline with deliberate missing days; source and SQLite physical separation; VI/EN and all five Q-0484 tabs; no access to authenticated health records without login.

The first-run user experience and default demo generation can be verified using the normal `scripts/start_desktop.ps1` command; `scripts/start_server.ps1` need not run first when all server dependencies are installed.

