# AETHERION — Platform Test & Remediation Audit (2026-11-14)

**Audit scope:** Full repository functional & test verification across **Server**, **Desktop**, **Mobile**, **Watch**, and **CI/Tooling** on `main` (Python 3.11.2, isolated venv with `apps/server`, `apps/desktop`, `fastapi==0.162.7`, `pydantic==2.14.3`, `uvicorn==0.54.0`, `PySide6==6.12.0`, `httpx==0.28.1`, `pytest==9.2.0`).

> **Note:** All findings below are directly observed from running commands and tests in this environment. No unverified platform or device is claimed as working.

---

## 1. Summary by Target Platform

| Platform | Current State | Blocking Issues Found | Related Quests |
| --- | --- | --- | --- |
| **Server** (`apps/server`) | Boots & serves `/health`, `/api/v1/auth/login`, `POST /api/v1/observations`; **fails 422 validation & smoke test** | 1) Pydantic v2 `ValueError` not JSON-serializable in `validation_exception_handler` (breaks 6 test suites)<br>2) `scripts/smoke_server.py` fails `GET /api/v1/observations` (missing `include_non_live=true`)<br>3) Server Control GUI & Local/Cloud AI/Telegram UI (`DESIGN_2026_11_14.md` §4) not implemented | `Q-0001`, `Q-0004`, `Q-0046`–`Q-0060`, `Q-0436` |
| **Desktop** (`apps/desktop`) | Headless `PySide6` (`AetherionWindow`) boots & switches 8 pages (`PortalPage`, `MissionControlPage`, `AuthorizedPersonalTodayPage`, `MedicalLibraryPage`, 4 placeholders) | 1) Body Atlas, Explore, Care Journey, Medical Guide are placeholder `QWidget`s<br>2) `medical_image_gallery.py` & `medical_source_audit.py` sit at `apps/desktop/` root instead of `src/aetherion_desktop/`<br>3) V3 animated themes, Server Control, Windows EXE (`Q-0010`/`Q-0011`) & live Windows boot (`Q-0002`) incomplete | `Q-0002`, `Q-0010`, `Q-0011`, `Q-0091`–`Q-0105`, `Q-0121`–`Q-0135`, `Q-0436` |
| **Mobile** (`apps/mobile`) | **Not implemented** (`README.md` only) | No Android/mobile project, runtime, build, or API client code exists yet | `Q-0196`–`Q-0210` (`PLANNED` / `P2`) |
| **Watch** (`apps/watch`) | **Not implemented** (`README.md` only) | No Wear OS/watch project, build, or sensor adapter code exists yet | `Q-0181`–`Q-0195` (`PLANNED` / `P2`) |

---

## 2. Exact Test & Script Failures Observed

### 2.1 Syntax, Lint & NASA Registry Checks (PASS)
- `python3 scripts/lint_python.py` → **PASS** (`Checked 334 Python file(s), 0 errors`)
- `python3 scripts/validate_nasa_registry.py` → **PASS** (`5 NASA source registry items verified`)
- `python3 scripts/audit_nasa_truthfulness.py` → **PASS** (`0 violations`)
- `QT_QPA_PLATFORM=offscreen` `AetherionWindow()` init & 8-page switch → **PASS**

### 2.2 Server & Smoke Failures (FIX REQUIRED)
1. **Pydantic v2 422 handler crash (`apps/server/src/aetherion_server/main.py:187`)**
   - `validation_exception_handler` returns `JSONResponse(status_code=422, content={"detail": exc.errors()})`.
   - Under `pydantic>=2.0`, `exc.errors()` contains `ctx: {"error": ValueError(...)}` when custom validators raise `ValueError`, causing `TypeError: Object of type ValueError is not JSON serializable`.
   - **Breaks 6 `unittest` suites:**
     - `tests/test_contract_provenance_classification.py`
     - `tests/test_contract_scope.py`
     - `tests/test_contract_timestamp_units.py`
     - `tests/test_core_validation.py`
     - `tests/test_server_kernel.py`
     - `tests/test_server_observations_post.py`
   - **Fix:** Sanitize `exc.errors()` (e.g. `jsonable_encoder(exc.errors(), custom_encoder={Exception: str})` or convert `ctx` values to `str`) in `validation_exception_handler`.

2. **`scripts/smoke_server.py` assertion failure (`scripts/smoke_server.py:137-140`)**
   - Posts observation with `scope="engineering_test"` (non-live), then queries `GET /api/v1/observations?subject_id=SMOKE-1` without `include_non_live=true`.
   - Server defaults to `include_non_live=False`, returning `0` observations and failing `assert get_status == 200 and len(get_body["observations"]) == 1`.
   - **Fix:** Pass `include_non_live=true` in `scripts/smoke_server.py` (or test both default exclusion and `include_non_live=true`).

### 2.3 CI & Test Runner Mismatches (FIX REQUIRED)
3. **9 test modules require `pytest` while CI runs `unittest` (`.github/workflows/server-tests.yml:21`)**
   - `tests/test_encyclopedia_*.py` (6 modules) and `tests/test_guide_*.py` (3 modules) `import pytest` and fail with `ModuleNotFoundError: No module named 'pytest'` under `python -m unittest discover -s tests`.
   - When run with `pytest`, all **64 tests pass**.
   - **Fix:** Install `pytest` in `.github/workflows/server-tests.yml` (and document it) or convert those 9 modules to `unittest`.

### 2.4 Quest Board Tooling Failure (FIX REQUIRED)
4. **`scripts/quest_board.py` crashes on `quests/v1/Q-0436.md` (`scripts/quest_board.py:13,26`)**
   - `parse_quest()` rejects multi-line YAML lists (`owned_paths:\n  - quests/v1/Q-0436.md`) with `ValueError: malformed metadata`.
   - `EXPECTED_COUNT = 435` is outdated (repository now has `Q-0001`–`Q-0436`, i.e. 436 quests).
   - **Breaks 3 tests in `tests/test_quest_board.py`** (`test_count_and_dependencies`, `test_every_stream_is_nonempty`, `test_no_premature_done`).

### 2.5 Medical Library & Submission Doc Failures (FIX REQUIRED)
5. **`tests/test_cliff_044_sepsis.py` image integrity error**
   - Fails with `scripts.medical_image_rights.ImageRightsError: JPEG missing end marker`.
   - **Fix:** Re-fetch or repair the JPEG asset for `Q-0344` / CliFF 044 Sepsis and verify its SHA-256 + JPEG EOI marker (`0xFFD9`).

6. **`tests/test_submission_sources_and_licenses.py` stale SHA-256**
   - `submission/SOURCES_AND_LICENSES.md` lists `THIRD_PARTY_NOTICES.md` SHA-256 as `51340c054a6b870580cbe0521ce8481b208b9826177be5947874ab088c516c30`, whereas the actual file SHA-256 is `ff0866bf46313f9831275cae83919c52b14dc500f01f034219e4bdf6a1a9e96a`.
   - **Fix:** Update the SHA-256 in `submission/SOURCES_AND_LICENSES.md` (`Q-0264`).

### 2.6 Desktop Module Placement & Unfinished Screens
7. **`apps/desktop/medical_image_gallery.py` and `apps/desktop/medical_source_audit.py`**
   - Located at `apps/desktop/` root instead of `apps/desktop/src/aetherion_desktop/`, so they are not packaged with `aetherion-desktop` and `medical_image_gallery.py` fails standalone `spec_from_file_location` import (`@dataclass` module lookup).
8. **Placeholder Desktop views:** Body Atlas (`Q-0121`–`Q-0135`), Explore (`Q-0106`–`Q-0120`), Care Journey (`Q-0091`–`Q-0105`), Medical Guide (`Q-0151`–`Q-0165`), and Server Control / V3 themes (`Q-0436`).

### 2.7 GitHub Actions 1–3s Failure Investigation (`Q-0454`)
- **Observed GitHub Actions API state (`2026-11-14T09:28Z`):**
  - Recent runs on `main` (e.g. `43580681886` `Python server tests`, `43580681811` `Python syntax and lint`, `43580656181`, `43580645378`) all terminate in **2–3 seconds** with `status: completed`, `conclusion: failure`.
  - Querying `/actions/runs/{id}/jobs` (e.g. job `132404564373`, `132404564118`) shows **`runner_name: ""`** and **`steps: []` (0 steps executed)**.
  - Querying `/actions/jobs/132404564373/logs` returns **`HTTP 404`** (`BlobNotFound: The specified blob does not exist`).
- **Root-cause distinction:** These 1–3s failures are **GitHub Actions platform / runner-provisioning failures** (no `ubuntu-latest` runner was ever allocated, and no workflow step or test command ran), **not** Python lint or test assertion failures.
- **Policy impact:** Do **not** force all development or Quest progress through broken GitHub Actions runner provisioning; verify locally with focused commands (`lint_python.py`, `unittest`/`pytest`, `smoke_server.py`) as specified in `AGENTS.md`.

---

## 3. Recommended Fix Order for Contributors

1. **Unblock Server & CI (`Q-0001`, `Q-0241`):** Fix `validation_exception_handler` in `apps/server/src/aetherion_server/main.py`, fix `scripts/smoke_server.py`, fix `scripts/quest_board.py` for `Q-0436`, and add `pytest` to `.github/workflows/server-tests.yml`.
2. **Fix Data/Doc Regressions:** Repair CliFF 044 JPEG asset (`Q-0344`) and update `THIRD_PARTY_NOTICES.md` SHA-256 in `submission/SOURCES_AND_LICENSES.md` (`Q-0264`).
3. **Complete Desktop & Windows Packaging (`Q-0002`, `Q-0004`, `Q-0010`, `Q-0011`, `Q-0436`):** Move root desktop modules into `src/aetherion_desktop/`, replace placeholder tabs, and verify native Windows EXE startup.
4. **Activate Mobile & Watch (`Q-0196`–`Q-0210`, `Q-0181`–`Q-0195`):** Currently `PLANNED` (`P2`); prioritize if Mobile/Watch clients are needed alongside Server & Desktop.
