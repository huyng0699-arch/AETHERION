# AETHERION — Screen Status, Historical QA & Current Evidence / Trạng thái màn hình

## Authoritative current review status — 2026-11-15 (PR #13)

This dated block is the current evidence snapshot for this review. Older dated QA sections below are preserved as historical records from their stated branches, machines, files and commits; they do not prove the current PR screen was opened or visually accepted.

- **GitHub references (product-code review snapshot):** PR #13 was draft at code head [`69b9234`](https://github.com/huyng0699-arch/AETHERION/commit/69b9234fcc32b1a08bf929b908692dd6b61bb7d0); the live `main` at that checkpoint was `c27e530edffbd2af7f51361de0cdb2c048cb3c56`. The code snapshot was 50 ahead / 4 behind, merge base `bd5eefd67df5af6e42176c1b88cfd35e612634bd`. Later commits in this status update only edit this documentation path and do not change the product code reviewed.
- **Runner evidence:** GitHub lint/render checks ended before a runner or workflow steps were assigned because of the repository account billing/spending restriction. There is no CI test/render result from those runs.
- **Local review environment:** No AETHERION application window was open during this review. The available local AETHERION folder has a broken Git HEAD (`.git/HEAD` points to `refs/heads/.invalid`) and does not contain the current PR's `tests/test_startup_runtime_q0487.py` or `quests/v1/Q-0485.md`; it cannot provide a checkout-based run of this PR.
- **Screenshot evidence:** The previously referenced baseline PNG `C:\Users\Admin\Documents\Codex\2026-11-09\m-repository-huyng0699-arch-nasa-v\AETHERION\outputs\ui-review\pending\portal-user-provided-20261114.png` is absent from the available local workspace. No fresh after-fix screenshot was inspected. No screen has been accepted or marked changed, and no screenshot has been moved to `outputs/ui-review/changed`.
- **Range behavior:** PR commits `3fb0c38` and `b52d1d1` add shared 1-minute / 366-day bounds and an authored VI/EN regression test. Source readback is not a runtime test; the test is **authored, not run**.
- **Shared time-conductor integration:** An independent Q-0477 review reports that shell synchronization is currently one-way from Home to Monitor, Home's initial range can be emitted before the connection is ready, and Monitor-to-Home updates are not wired. The PR's Home 1-minute–366-day validation is a range-boundary fix only; it does **not** complete a shared Open-MCT time conductor. This integration remains pending Q-0489/main.py ownership reconciliation and must not be inferred from the range fix.
- **Protected-route gate:** Q-0485 still requires bearer `GET /api/v1/auth/me` verification with the flat `allowed_subjects` contract and auto-selection only when exactly one authorized ID exists. Current branch `main.py` blob `0f26a309b716e9acd252638a52a39730e3bf4ee3` instead requests `/api/v1/subjects` and lacks the required `/auth/me` verified-session handoff. This is a source mismatch, not an observed test failure. Q-0489 owns `main.py` and `quests/v1/Q-0489.md` through `2026-11-16T03:00:00Z`; wait for its narrow ACK/release before reconciliation. Preserve the acceptance test and leave this gate pending.
- **Screen disposition:** Visual acceptance is pending for every screen in this review. Keep screenshots out of `changed` until a reviewer inspects a fresh render and accepts the exact screen.

---

## Historical public-entry and auth handoff checkpoint — 2026-11-15 (superseded by the current status above)

The current product direction is public Mission Operations Home → explicit SIMULATED Demo, with NASA MA-7 as a separate historical archive. Protected routes return to Login, then resume only after bearer-authenticated `GET /api/v1/auth/me`; subject context is derived only from its flat `allowed_subjects` list. Auto-select exactly one authorized ID; keep zero/multiple IDs visibly unselected. Sign-out must clear the outer and Mission Control sessions, and Ask AI must restore local `account:<username>` identity. Q-0487 is currently **STALE** with its implementation/evidence preserved; physical Windows/runtime proof belongs only to Q-0488.

Q-0485 has a draft-branch Mission Control session handoff/reset and a focused auth/route test wired into the existing offscreen workflow. **No test or render pass is claimed yet.** The current Q-0489 lease owns `main.py` and `quests/v1/Q-0489.md` through `2026-11-16T03:00:00Z`; its ACK/release and Quest metadata reconciliation are required before merging the preserved Q-0485 entrypoint patch. GitHub Actions jobs previously stopped before runner steps because of billing; this is not a source-test result. The branch's visual and route acceptance remains pending.

---

**Historical QA snapshot — Post-Sync Integrated QA (recorded against `98e92f5` + `up.zip` + `PR #9` + `PR #11`, Linux `QT_QPA_PLATFORM=offscreen` + PySide6 `6.12.0` + Python `3.11`; not current-head acceptance):**  
- **Cold-start Login -> Public NASA Demo -> Operations Home (`Q-0487` / `98e92f5` + `Q-0485`):** `AetherionWindow` opens on bilingual [`LoginPage`](file:///home/antigravity/huyng0699-arch/AETHERION/apps/desktop/src/aetherion_desktop/login_page.py) (`set_visuals` styled `Demo` button, card width `460–560 px`). `login_page.demo_button` opens the genuine historical NASA archive briefing ([`hackathon_demo_page`](file:///home/antigravity/huyng0699-arch/AETHERION/apps/desktop/src/aetherion_desktop/features/demo/nasa_ma7.py)), while `operations_home_page.demo` (`DEMO FOR HACKATHON`) opens [`SimulatedDemoBriefing`](file:///home/antigravity/huyng0699-arch/AETHERION/apps/desktop/src/aetherion_desktop/features/demo/synthetic_briefing.py) -> Start -> isolated 5-patient / 540-day / 12-metric (`31,610` rows) SQLite explorer inside the persistent Open MCT-style `Browse / Workspace / Inspect` shell.
- **3-way `mission_ops_home.py` & `main.py` crash/lifecycle fixes:** Resolved PR #11 `set_visuals()` `AttributeError` (`self.utc_chart.set_points(self.utc_chart._points, self.theme, self.mode, index_offset=self.utc_chart._index_offset)`), preserved `QTimeZone.utc()`, Inspector `ScrollBarAlwaysOff`, `_browse_selected()`, `care_guide`, `time_range_changed` -> `MonitoringWorkspace.sync_utc_window` (`Q-0477` ACL preserved), `_api_url` propagation for `AuthorizedPersonalTodayPage`, `shiboken6.isValid`, and `closeEvent` timer/reply/`StartupRuntime.stop()` cleanup.
- **Rendered PNG & live verifier evidence:** 9 re-rendered post-rebase captures in [docs/qa/unsynced_20261114/postsync_preview/](docs/qa/unsynced_20261114/postsync_preview/) visually inspected (`1040×650`, `1360×850`, `1600×900`, Light/Dark theme switch clean, single Time Conductor outside Monitoring); [`scripts/verify_native_login.py`](scripts/verify_native_login.py) passed **`8/8 (100%)`** against real loopback HTTP bearer auth.
- **Scopes still PENDING (`BLOCKED` / `review: PENDING`):** Fresh physical **Windows** re-build/re-capture after merged `98e92f5` (`WINDOWS_150_DPI_INTERACTIVE_CLICKTHROUGH`), Windows EXE code signing, physical Android LAN device run (`apps/mobile/` verified via `tsc --noEmit`, `export:web`, `export:android:js`, `verify_mobile_state.mjs` `14/14`, `verify_mobile_web.mjs --api-only` `18/18`, `verify_mobile_clients.mjs` `9/9`, `verify_mobile_acl.py` `6/6`), `CLIFF-119` upstream slot (`118/119 PARTIAL`), and independent human/external reviewer sign-off.

---

**Historical Windows QA & build verification snapshot (from `up.zip`, pre-`98e92f5`; not current-head acceptance):** 2026-11-14 (Windows 10 `10.0.19045`, Python 3.13.14, PySide6 6.12.0, PyVista, PyInstaller 6.22.3).  
**Evidence class:** Live Windows Qt rendering (`QWidget.grab()` connected to real local FastAPI/uvicorn server), Windows UI Automation offline probes on both source launch and compiled `AETHERION-Desktop.exe`, headless `tests/` suite, and governance/audit checks. Independent human/external reviewer sign-off remains `PENDING`.

## Historical Windows Runtime & Visual QA Update — 2026-11-14

### Resolved integration & UI/visual findings (verified on Windows)

- **Shared UTC window (`Q-0477` / `Q-0485`):** `MonitoringWorkspace.sync_utc_window(start_iso, end_iso)` implemented in `apps/desktop/src/aetherion_desktop/native_workspaces.py` and wired from `operations_home_page.time_range_changed` in `main.py`, preserving subject/token ACL gating (does not query without existing authorized subject + bearer token).
- **Care Guide route wiring (`Q-0465`):** `care_guide` added to `mission_ops_home.py` (`ROUTE_IDS`, clinical navigation group, VI/EN labels) and mounted in `main.py` (`attach_feature("care_guide", self.care_page)` + `show_care_guide()`). `CareWorkspace` step selector laid out in a 2×2 `QGridLayout` to eliminate horizontal scrollbar overflow at `1040×650`.
- **Mission Operations & Library selection (`Q-0430` / `Q-0485`):** `_browse_selected()` (`mission_ops_home.py`) and `show_selection()` / `open_selected_article()` (`medical_library.py`) now resolve `selectedItems()[0]` before falling back to `currentItem()`, matching Qt UIA point-click behavior reliably.
- **MA-7 UTC & link fixes (`Q-0478` / `Q-0485`):** `QUrl` imported in `features/demo/nasa_ma7.py`; `QTimeZone.utc()` replaces deprecated `setTimeSpec(Qt.TimeSpec.UTC)` in `mission_ops_home.py` and `ecg_page.py`.
- **Visual/i18n defects caught by real Qt captures and fixed:**
  - `visual_theme.py`: added `QDateTimeEdit` / `QAbstractSpinBox` styling + `QPalette` + `QScrollArea` transparent viewport fix (fixed invisible white-on-white `TIME CONDUCTOR` date fields in Dark mode).
  - `i18n/{en,vi}.json`: corrected swapped `"personal.metricSource"` strings (`"Source: ..."` in `en.json`, `"Nguồn: ..."` in `vi.json`).
  - `personal_visual.py` (`Q-0087`): switched domain tiles to 2 columns with `setMinimumWidth(0)` and `setWordWrap(True)` cleanly fitting `1040×650`.
  - `medical_library.py`: enabled `setWordWrap(True)` on the catalog heading (`1040×650` non-clipping).
  - `atlas3d.py`: separated toolbar selector row and action buttons row cleanly + hid overlapping VTK picking banner overlay (`show_message=False`).
  - `mission_ops_home.py`: enabled `ScrollBarAlwaysOff` + `Stretch` headers + `resizeRowsToContents()` on the right Inspector table.
- **Packaged Windows EXE & UIA verification:**
  - `scripts/build_windows.ps1` exited `0`: bundled `knowledge/anatomy/`, generated `AETHERION_NASA_CLIFF_119.sqlite` (`118/119 PARTIAL`, missing `CLIFF-119` upstream PDF/URL), built `AETHERION-Desktop.exe` (`15,128,073` bytes, SHA-256 `1ac92d650d8154d2e591cd185df291d54859a166702c25d66b60f47bece8578b`, `native_gui_smoke: WINDOW_HANDLE_OBSERVED`).
  - Packaged EXE UIA check (`AETHERION_API_URL=http://127.0.0.1:1`): opened `AETHERION · TRUY TINH`, navigated to `Thư viện y khoa` -> `Trở về thư viện`, and navigated to `Cơ thể 3D` -> `Đặt lại góc nhìn`.
  - `scripts/smoke_cliff_windows_offline.ps1` exited `0` (`WINDOWS_NATIVE_PROBE_PASSED_REVIEW_PENDING`, `docs/qa/windows-cliff-evidence/q0430-20261114T174601Z.json`).

### Remaining limitations & gates

- **Desktop GDI capture limitation:** Win32 `CopyFromScreen` raises `"The handle is invalid"` inside non-interactive background shells (`build_windows.ps1` warns cleanly), and Win32 `PrintWindow` captured white client pixels in `q0430-*.png`; actual rendered Qt pixels across Light (`vi`, `1040×650`) and Dark (`en`, `1360×850`) were captured via real Windows `QWidget.grab()` and visually inspected.
- **Unresolved external/review gates:** `CLIFF-119` upstream record remains missing (`118/119`), EXE is unsigned, Windows 150% DPI interactive sign-off & independent external review remain `PENDING`. `apps/mobile/` excluded per user directive.

---

**Prior authoring audit (preserved for traceability):** 2026-11-14, P0 persistent hosted Mission Operations and original-phase NASA table; source only, no Qt screenshot.  
**Evidence class:** GitHub file SHA and source inspection only. PySide6 unavailable in this runtime; **no new Linux offscreen or Windows screenshot and no runtime acceptance**.

## Historical source SHA after MA-7 selection consistency patch

- `mission_ops_home.py` latest committed blob: `9e338397d9f61d63ac2ad4b420e31af8a67c80c2` — [`b14978623ee530cc292048a412d4f02a927cff59`](https://github.com/huyng0699-arch/AETHERION/commit/b14978623ee530cc292048a412d4f02a927cff59). The original NASA phase-comparison table now retains the selected metric in the source measurement table and Inspect when switching report phases, and measurement selection drives the same comparison metric. Values and source labels remain read-only.
- [Q-0486 PR #9](https://github.com/huyng0699-arch/AETHERION/pull/9) was inspected but **not imported or edited**: its telemetry widget has UTC time-axis semantics, unsuitable for MA-7's categorical phase/timepoint records without verified UTC timestamps.
- `main.py` blob remains `9889e109c52943064bf27dfb8a4f8e2284db18de` for the persistent-shell integration. Existing Q-0477 internal Monitoring controls remain independent. **Offscreen Qt and Windows visual acceptance still PENDING.**

---

## Historical P0 source checkpoint — persistent Mission Operations (2026-11-14)

**Owner override:** Browse/Workspace/Inspect and bottom UTC conductor must persist throughout normal native routes, not just cold-start Home; the five-card Portal and duplicate horizontal top navigation are explicitly rejected. This is the user's **actual app visual**, not the Server Admin page.

| P0 issue | Code integration on `main` | What is *not* proven |
| --- | --- | --- |
| Browse route previously left Mission Operations | `mission_ops_home.py` [`907a8bff`](https://github.com/huyng0699-arch/AETHERION/commit/907a8bff925c5c5754ab2f2cbcf2dfc705cd441b) adds `attach_feature` / `show_hosted`; `main.py` [`ec0a4399`](https://github.com/huyng0699-arch/AETHERION/commit/ec0a4399995d37cbcfe009987ebbd2b010dc7216) reparents already-constructed native QWidget instances into persistent center Workspace | Qt windowing, reparenting visual behavior, 1040×650 and 150% DPI still **PENDING** |
| Monitoring / Health / ECG / Chat / other routes | All **13 existing routes** point to their original widgets inside central stack, with native signals and authorized identity/access pathways intact in source; Monitoring still calls its existing `refresh()` | Actual HTTP permission and clickthrough not performed |
| Briefing and NASA left the shell | Both `SIMULATED briefing → Start → PatientDemo` and distinct real NASA MA-7 archival widget now mount inside center Workspace, preserving Browse and Inspect | No tested synthetic SQLite COUNT(*), five-tab GUI, original NASA QUrl link fix, or visual acceptance |
| Cluttered duplicate global navigation and status | The old topBar's horizontal route buttons, AETHERION brand and connection pill are hidden, including on resize; global appearance/language/settings/help stay visible. The one displayed status pill in Operations is derived from actual HTTP `/health` reply | Actual post-fix screenshot **PENDING** |
| Unreadable NASA QPainter bars (no phase, value, unit, axis) | **Removed** unlabelled bars from authentic MA-7 report view. Categorical phase-comparison **table** now displays exact original report timepoint, numeric/string value or missing state, unit and qualifier; click a phase to update original measurement table and right Inspect | Source-level view only; table legibility at minimum window and native clickthrough **PENDING** |
| Monitor and Home time ranges | Home Time Conductor has explicit UTC bounds and controls its own validated UTC workspace. Q-0477 Monitoring widget's time controls remain independent. Requested narrow API ACK in [Issue #8 comment #6877383276](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6877383276). | **Not synced** until Q-0477 owner explicitly approves a safe public API, then integration and tests |

**Current source SHAs:** `main.py` blob `9889e109c52943064bf27dfb8a4f8e2284db18de` (commit `ec0a4399`); `mission_ops_home.py` blob `c6c874e0becdd3015a33facfacc53656918fbe68` (commit `907a8bff`). Q-0485 remains RUNNING/IN_PROGRESS/review PENDING.

**Verification boundary:** focused **13/13 GitHub static contract checks** passed for presence of centralized host mappings, existing refresh/subject handoff, new QStackedWidget usage, source-readable NASA categorical table, and absence of topBar duplicate navigation reappearing on resize. No PySide6 Qt/offscreen screenshot, Windows screen, QA clickthrough or independent visual acceptance was obtained; **do not claim visual PASS or DONE.** Previous install attempts were unsuccessful in this runtime. External reviewer must verify rendering, all route switches, source boundaries, VI/EN, theme/reduced motion and minimum window ergonomics.

---

## Historical corrected native Home layout (GitHub source only; 2026-11-14)

**Commit:** [`b92e1a9daac3c8ba036774e6b27aeef7b32633ae`](https://github.com/huyng0699-arch/AETHERION/commit/b92e1a9daac3c8ba036774e6b27aeef7b32633ae) · `mission_ops_home.py` blob `d39354c4b7571847cf6ffc3eb79572573e9533d2`.

The owner’s updated NASA Open MCT direction supersedes five-card Portal / horizontal-menu-only presentation **for the first native app screen**; no implication for Admin HTML, legacy routes or medical access rules.

| Owner correction | Implemented source behavior | Runtime evidence |
| --- | --- | --- |
| Correct cold start | `_choose("home")`; Mission Workspace overview, NASA MA-7 remains separate Browse object | GitHub inspected; Qt/Windows visual **PENDING** |
| Fixed bottom Time Conductor | Controls and UTC status placed *below* the three-pane splitter, above footer; explicit UTC bounds retained for table, discrete plot and Inspect | Source inspection only; no Q-0477 Monitoring filter sync |
| Inspect at 1040 px | Non-collapsible three-pane splitter; left min 177 logical px, center min 405 px, right Inspect min 205 px; horizontal pixel scroll for long properties | Geometry source constraints present; real 1040px / 150% DPI render **PENDING** |
| Correct Home Inspect | Mission properties show unselected subject/source, UTC scope and authorization requirement, not NASA MA-7 claimed as active source | GitHub inspected; interaction **PENDING** |
| Route and data separation | 13 real feature routes intact; prominent Demo → SIMULATED briefing → Q-0484; authentic NASA MA-7 independent | Wiring unchanged; Windows clickthrough **PENDING** |

**Focused structural checks: 15/15 passed** against current source and unchanged `main.py` blob `15274eef60ff1a69a920d10fd32d4763264ed67b`. These are source assertions, not a test of final appearance. PySide6/PyQt6 are not installed in this runtime and a temporary-venv PySide6 installation returned no matching distribution; **no valid Qt offscreen screenshot or Windows after-fix screenshot exists from this run**. The owner-supplied original Windows screenshot remains an explicitly rejected baseline.

**Next acceptance:** fresh Windows GUI capture after fix, browse/Inspect selection, verify conductor does not obscure data at min 1040×650 and 150% DPI, full simulated 5-patient / 540-day SQLite test, source NASA archive and link, VI/EN/themes, actual permissions, independent reviewer. Q-0485 remains `RUNNING / IN_PROGRESS / review PENDING` — do not mark PASS.

---

## Historical Q-0485 source-only workspace review — 2026-11-14

**Owner visual override:** The old SPEC/AGENTS five-card and horizontal-menu-only design language is superseded **only for the first native app screen**. The target is the actual Browse → Workspace → Inspect layout from the NASA Open MCT user-facing information architecture, with one time conductor. This is an implementation requirement, **not** a claim that AETHERION itself is NASA Open MCT or that its appearance has passed.

**Code on `main` (not Windows visual evidence):**
- `57a4d17ceab9862a7a7365c5412ff1629c151e0b`: removed the ornamental `OrbitPanel`; added interactive left Browse object tree, center historical NASA MA-7 report tables/source-derived bars and empty authorized UTC panel, right selected-source properties/Inspect, one shared UTC window, and the pinned **DEMO FOR HACKATHON** action.
- `c66cb536bbd7648eda0e15ab95e675609fe8bd30`: focused source-level fixes for missing Qt `QRectF` import, explicit UTC editor time specification, searchable Browse tree, and metric/source controls. No original NASA values were altered.
- `9517e5dfabd0fe07e21fc42a9e7d9ee3f6b7e6b3`: UTC chart uses only one metric/unit/source family; table, chart and Inspect share the selected UTC bounds and filters. **This optional host-supplied UTC adapter is not yet bound to authenticated Monitoring**; Q-0477 owns that integration, and no claim of live records is made.
- **MA-7 source boundaries:** the 19 historical report timepoints and 83 published numeric/non-null observations have no universally verifiable absolute UTC timestamps. Their original stage labels/mean/qualifier/source-page metadata remain visible, and the UTC Time Conductor does **not** assign invented dates to report phases. The authorized UTC panel shows an honest empty state unless a trusted controller provides actual UTC-stamped observations.
- All 13 existing feature-route keys remain bound through unchanged `main.py` (`dc49fe9` + readiness refinement `83355ec`). The pinned Demo opens SIMULATED briefing → explicit Start → Q-0484 isolated five-patient, 540-day SQLite experience. NASA MA-7 is a separate archival action, never a synthetic stream.
- **Visual proof: PENDING.** An offscreen Qt render was attempted in this runtime, but PySide6 is absent and installing it into a temporary Python virtual environment failed (`No matching distribution found for PySide6` in this environment); therefore **no valid Linux offscreen screenshot was produced**, and **no Windows desktop was launched**. The owner's previously supplied five-card Windows screenshot remains *before-fix rejected evidence*. A fresh Windows after-fix screenshot and independent clickthrough are still required.

### Workspace-specific QA still open

- Render at 1040×650 and 150% DPI: verify tree, UTC conductor, table and Inspector stay usable without clipping; compare actual native visual to owner's Open MCT requirement.
- Confirm Browse selection changes center view/Inspect, report-group and metric selection update real source values, UTC search/presets/filter boundaries do not invent samples, and time controls are explicitly UTC.
- Verify Demo enters briefing before any synthetic SQLite seed; read back seeded patient data from the dedicated database and test all five tabs. Verify the NASA archival path and all 13 existing routes separately, including VI/EN and theme/reduced-motion behavior.
- Independent reviewer signs off actual native interactions. **Q-0485 remains RUNNING/COMPONENT IN PROGRESS (or COMPONENT_READY once current owner releases), review PENDING; never infer DONE from source inspection.**

---

## Owner-approved first-view architecture

The native Windows app opens **Mission Operations**, a native PySide6 workspace informed by mission-operations information architecture. The old Portal with five oversized cards and orange bottom Demo banner is **not the accepted main visual**.

The historical screenshot at:
`C:\Users\Admin\Documents\Codex\2026-11-09\m-repository-huyng0699-arch-nasa-v\AETHERION\outputs\ui-review\pending\portal-user-provided-20261114.png`
is **before-fix evidence**. A new actual Windows after-fix screenshot **does not yet exist in this evidence record**.

| Screen / route | Source implementation | GitHub status | Native Windows render |
| --- | --- | --- | --- |
| Cold-start Mission Operations | `mission_ops_home.py`; mounted first in `main.py` | Wired in `dc49fe906a2b1669edd4fcfa038ea8c9c3efa478` | **PENDING** |
| Prominent DEMO FOR HACKATHON CTA | `MissionOperationsHome.demo` and independent SIMULATED signal | Wired to briefing | **PENDING** |
| SIMULATED source briefing | `features/demo/synthetic_briefing.py` | Dedicated bilingual native page; explicit Start required | **PENDING** |
| Fully navigable fictional scenario | `synthetic_patient_ui.py` and `synthetic_patients.py`, Q-0484-owned | Q-0485 wires Start to `PatientDemo.start()` / Back to briefing | **PENDING** |
| Fictional SQLite 540 days × 5 IDs × 12 metric types | `Path.home()/.aetherion/demo/synthetic_patients_v1.sqlite3` | Q-0484 source has deterministic generator; **SQLite readback not performed here** | **PENDING** |
| Genuine NASA Mercury MA-7 archive | `nasa_ma7.py` + `ma7_source.json`, Q-0478 | Separate archive signal, NASA briefing and 83 sourced historical values preserved | **PENDING** |
| Scientific NASA CliFF / hazard / glossary archive | `demo_catalog.py`, `demo_library.py`, `demo_hub.py` | Source-backed local catalog; actual available file count must be shown | **PENDING** |
| Legacy five-card Portal | `portal.py` | Retained only under `Alt+Shift+Home`; no longer cold-start Home | Existing screenshot is **REJECTED** |
| Authenticated mission, personal, monitoring, ECG, AI, interview, care | Existing source widgets / real Server | Mission Operations routes bind existing safe handlers, no demo import | **PENDING** |
| NASA Explore, science browser, medical library, atlas, settings | Existing app widgets | Mission Operations routes bind existing handlers | **PENDING** |

### Click journey / Hành trình bắt buộc

```
App launch → Mission Operations (first screen)
  DEMO FOR HACKATHON → SIMULATED briefing → Start
    → Q-0484 PatientDemo: Crew | Personal | Monitoring | History | Data source
       → isolated synthetic SQLite only; Back → briefing
  NASA · MA-7 → original NASA source briefing → historical measured-value explorer
  Navigator → 13 existing real/sourced feature handlers, retaining authorization
```

**Boundary:** the 83 reported NASA MA-7 observations are authentic *historical* values, **not simulated**; fictional patient scenario data are synthetic, **not NASA or live patient telemetry**. Neither collection should be uploaded to authenticated observations. The simulated values do not constitute medical advice, risk classification or original ECG.

## Ownership and QA gates

- GitHub Issue [#8](https://github.com/huyng0699-arch/AETHERION/issues/8), comment [#6876351829](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6876351829), grants only Home/Demo `main.py` integration by Q-0477/Q-0480/Q-0481 owners. Comment [#6876297980](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6876297980) approves routing to Q-0484 without writing its modules. Q-0478 previously released shared Home paths.
- **No modifications to shared VI/EN catalog JSON**, Q-0484 synthetic modules, original NASA values, API permissions, or old Portal internals by Q-0485.
- Q-0485 remains **COMPONENT_READY / review PENDING**, not `DONE`. This document reports code integration, not accepted screen quality.
- **Windows acceptance outstanding:** start an actual Windows PySide6 build at 1040×650 and 150% DPI; capture the first screen after-fix; click Demo → briefing → Start; confirm 5 tabs, five fictional subjects, 540-day range and seeded SQLite readback; navigate Back and real NASA archive; verify all 13 routes plus VI/EN, visual themes, reduced motion, keyboard access, and no accidental patient-store writes.
- An independent reviewer must validate the fresh screenshot and interaction evidence before final DONE. No screenshot has been generated or fabricated in this commit.

## Focused NASA source-link defect requiring owning-agent fix

Source readback found `nasa_ma7.py` uses `QDesktopServices.openUrl(QUrl(...))` without an available `QUrl` import in `build_hackathon_demo()` or module globals. **Until the Q-0478/Q-0484 file owner imports `QUrl` with an ACK and SHA/CAS, original PDF/OSDR/official resource link clicks are a suspected `NameError` failure.** This is not proof of a Windows crash; no native click was attempted. See [Issue #8 comment 6876928259](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6876928259). Q-0485 must not edit this multiply-owned source file without narrow authorization.
