# AETHERION — Quest navigation (live)

**Single source of truth for status:** each `quests/v1/Q-XXXX.md` on the canonical `main` branch. This page is a **navigation index**; it is not a second task database, scheduler, or release certificate. Every Quest keeps its own dependencies, owner, evidence, and independent reviewer gate.

**Recovery 14 November 2026:** This navigation page was shortened to remove contradictory, growing historic snapshots. **The previous 45 KB version was archived without content loss** at [QUEST_LOG history](docs/qa/QUEST_LOG_HISTORY_20261114_BEFORE_RECOVERY.md). Past Windows test reports remain available there with their original caveats and dates. No original Quest status or evidence was erased or set to DONE by this change.

## Current native entrypoint owner override (2026-11-15)

Public Desktop Home is the Open-MCT-style Mission Operations shell. The first-screen CTA is explicitly SIMULATED and opens the isolated Q-0484 briefing/demo; NASA MA-7 is a separate source-labelled archive. Login is reached only by selecting a protected real-data route, and that route resumes only after bearer-authenticated `GET /api/v1/auth/me`; subject context comes only from the flat `allowed_subjects` list, auto-selects only one authorized ID, and leaves zero/multiple IDs unselected. Home/sign-out return to Mission Operations. This supersedes the historical Q-0487 Login-first summary below. Preserve Q-0485/Q-0487 dependencies, StartupRuntime and existing ACL/provenance rules. Q-0487 is currently STALE with implementation/evidence preserved and `main.py` released; its prior RUNNING note below is historical. Active Q-0489 now owns `main.py` through `2026-11-16T03:00:00Z`, so Q-0485's already committed entrypoint diff remains draft work pending owner ACK/reconciliation and no merge is safe until then. Offscreen Qt CI is implementation evidence; physical Windows/150%-DPI acceptance belongs to Q-0488.

## Reconciled cross-branch coordination pointer (2026-11-14T18:50Z)

- **Super Quest & Pre-/Post-Sync Ledger:** **[Q-0488](quests/v1/Q-0488.md)** and **[docs/qa/unsynced_20261114/README.md](docs/qa/unsynced_20261114/README.md)** archive the pre-sync baseline measurements (`287 PASS / 14 FAIL`, `quest_board check` failing on missing `Q-0486`), reconcile **PR #9** ([Q-0486](quests/v1/Q-0486.md) released to `BLOCKED / PENDING`), **PR #10/#11** (`Q-0485` Open MCT shell + `UtcSamplePlot.set_points` visual switch fix), Windows QA fixes from `up.zip` ([WINDOWS_COMPLETION_REPORT_20261114.md](docs/qa/WINDOWS_COMPLETION_REPORT_20261114.md)), and **`98e92f5`** (`LoginPage.set_visuals`, `login_page.demo_requested -> show_hackathon_demo`, server wildcard guard, Mobile `export:android` + `getObservations(..., cursor)` fix). All reconciled Quests stay `review: PENDING` for independent review; see [SCREEN_STATUS](docs/SCREEN_STATUS.md).
- **Board & active upstream leases respected:** **488 contiguous specs (`Q-0001..Q-0488`)** pass strict `quest_board.py check`. Do **not** overwrite active upstream leases on [Q-0261](quests/v1/Q-0261.md) (`19:11Z`) or [Q-0487](quests/v1/Q-0487.md) (`19:08Z`). `apps/watch/` remains **`PLANNED ONLY`** (`README.md` only); CliFF remains honestly **`118/119 PARTIAL`** (`CLIFF-119` missing upstream).

## Coordinator status & contributor dispatch (2026-11-14T15:02Z)

Full verified audit across Server, Desktop, Mobile, Watch, CliFF 119, 3D Atlas, failing tests, and 9 contributor role tracks: **[COORDINATOR_AUDIT_AND_DISPATCH_20261114.md](docs/qa/COORDINATOR_AUDIT_AND_DISPATCH_20261114.md)** (verified baseline `de4afef`, rebased on `c242a18`).

- **Board & tooling verified:** `1e228106` repaired `Q-0483` `depends_on: []` -> `quest_board.py check` **PASS (485/485)**, `tests/test_quest_board.py` **7/7 PASS**, `lint_python.py` **490/490**, `audit_bilingual.py` **761 VI / 761 EN**, `smoke_server.py` **PASS**, CliFF SQLite pack **118/119** (`393,748,480` B, `CLIFF-119` empty). Live counts: `DONE: 217`, `BLOCKED: 104`, `PLANNED: 93`, `STALE: 50`, `QUEUED: 18`, `RUNNING: 2`, `READY: 1` (`P0: 111`, `P1: 247`, `P2: 95`, `P3: 32`).
- **Priority reopens & lease cleanup:** Reopened 4 verified regressions to `STALE / REWORK_REQUIRED` (**`Q-0016`** OpenAPI 10 vs 45 paths, **`Q-0096`** clinical safety fail-open in `guidance_citations.py:52`, **`Q-0261`** diagram vs `Q-0197` Expo app, **`Q-0458`** Samsung SEFT trailer in `medical_image_rights.py:113`); preserved `antigravity-reviewer` `COMPONENT_APPROVED` on `Q-0122/0124/0133/0134` (`c242a189`) and `Q-0444/0445/0460/0471` (`01c9e2b6`, transitioning to `BLOCKED` after supplementary 9/9 test check); synced 19 reviewed `DONE` SHAs (`Q-0420..0431`, `Q-0439..0476`); released 45 expired/`null` `RUNNING` leases -> `STALE`; updated `Q-0319`/`Q-0321` URLs (`Q-0457`). Also noted `apps/mobile` `npm ci --dry-run` `EUSAGE` lockfile drift (`Q-0197`) and `apps/watch/` `PLANNED ONLY`.
- **Active coordination locks — DO NOT OVERWRITE:** Active leases [`Q-0180`](quests/v1/Q-0180.md) (`15:10:00Z`) and [`Q-0268`](quests/v1/Q-0268.md) (`15:23:00Z`); Draft PR #9 (`Q-0486`); Draft PR #10 (`import/windows-tested-fixes-20261114` — `ClosingConnection`, `QUrl`, `QPalette`, UIA); Issue #8 (`Q-0477`/`Q-0485` UTC sync & `nasa_ma7.py` `QUrl`). Contributors claim 1–3 exact `owned_paths` via CAS on `main` using the role tracks in **[the dispatch guide](docs/qa/COORDINATOR_AUDIT_AND_DISPATCH_20261114.md)**.

## Current commands — always read the live repository

```powershell
python scripts/quest_board.py check
python scripts/quest_board.py stats
python scripts/quest_board.py ready
python scripts/quest_board.py running
python scripts/quest_parallel_candidates.py --limit 40
python scripts/quest_review_queue.py --output quest-review-report.md
```

**Important:** `check` is strict (invalid frontmatter, missing/duplicate Quest ID, invalid status, unknown/self/circular dependency, DONE without approved review, or RUNNING without ownership => nonzero). The `stats`, `ready`, `running`, `json` and parallel-selector commands are **read-only and resilient**: one malformed Quest must not hide the entire work queue. They print warnings; a successful listing is **not** a clean integrity check. Do not infer a current PASS from an old test report or an Actions job that failed before acquiring a runner.

Quest IDs and counts evolve. At the most recent full directory inspection before recovery, the backlog contained **485 contiguous Quest files Q-0001–Q-0485**. This is a dated snapshot, **not a current counter**; use `stats` and the actual `quests/v1/` directory.

## High-priority work navigation

| Workstream | Live Quest records | Unresolved acceptance obligation |
| --- | --- | --- |
| Quest ledger / CI | [Q-0001](quests/v1/Q-0001.md), [Q-0241](quests/v1/Q-0241.md) | Strict graph check, functioning read-only lists and actual CI runner-backed pass |
| Native desktop / Windows EXE | [Q-0002](quests/v1/Q-0002.md), [Q-0003](quests/v1/Q-0003.md), [Q-0010](quests/v1/Q-0010.md) | Real Windows startup, packaged EXE/hash, screenshots and independent review |
| New Mission Operations Home | [Q-0485](quests/v1/Q-0485.md) | P0 persistent Browse / hosted native Workspace / Inspect + bottom UTC controls; 13 routes and Demo preserved, live Qt/Windows acceptance PENDING |
| Default first-run Server + ready SIMULATED crew Demo | [Q-0487](quests/v1/Q-0487.md) | Auto-probe/reuse/start 127.0.0.1:8765 in installed native Python; preseed five fictional profiles/540 days in separate SQLite; runtime/Windows acceptance PENDING |
| Clearly synthetic patient Demo | [Q-0484](quests/v1/Q-0484.md), [Q-0478](quests/v1/Q-0478.md) | Demo explanation → 5 fictional patients/540-day data, separately from actual 1962 NASA MA-7 archive |
| Monitoring / ECG | [Q-0477](quests/v1/Q-0477.md), [Q-0481](quests/v1/Q-0481.md) | Q-0477 now has an interactive UTC conductor, authenticated paged telemetry, plot/table sync, source/quality legend, explicit gap segmentation, hover/zoom/pan; [headless QA geometry](docs/evidence/q0477_monitor_headless_gap_model.png) is **not** a Qt screenshot. Native Windows/render, API paging and independent review remain pending. |
| NASA CliFF 119 offline documents | [Q-0421](quests/v1/Q-0421.md), [Q-0425](quests/v1/Q-0425.md), [Q-0426](quests/v1/Q-0426.md), [Q-0427](quests/v1/Q-0427.md), [Q-0435](quests/v1/Q-0435.md) | Actual source, media rights, SQLite import, complete offline reader and native verification |
| Independent acceptance | [REVIEW-0001](quests/review/REVIEW-0001.md) | Different reviewing agent must assess real evidence; never self-approve |

## P0 Mission Operations is now a persistent native shell (source only; 2026-11-14)

**MA-7 categorical source-view follow-up:** commit [`b14978623ee530cc292048a412d4f02a927cff59`](https://github.com/huyng0699-arch/AETHERION/commit/b14978623ee530cc292048a412d4f02a927cff59) keeps the selected report phase, the metric table and right Inspect consistent; current Home blob `9e338397d9f61d63ac2ad4b420e31af8a67c80c2`. [Q-0486 PR #9](https://github.com/huyng0699-arch/AETHERION/pull/9) is a UTC telemetry widget and was not imported into categorical MA-7 research. No Qt image or source-output visual PASS; full [SCREEN_STATUS](docs/SCREEN_STATUS.md).



**Owner-overridden layout:** Browse navigation, center Workspace and right Inspect with bottom UTC Time Conductor persist when opening existing native features; the old five-card Portal and duplicate topBar horizontal route buttons are not the app's primary UI.

- Q-0485 `mission_ops_home.py` commit [`907a8bff`](https://github.com/huyng0699-arch/AETHERION/commit/907a8bff925c5c5754ab2f2cbcf2dfc705cd441b) adds native QWidget hosting in the central Workspace and replaces unreadable MA-7 QPainter source bars with a categorical **original report phase / value / unit / qualifier** comparison table. Historic MA-7 does **not** acquire fabricated UTC timestamps.
- Q-0485 `main.py` commit [`ec0a4399`](https://github.com/huyng0699-arch/AETHERION/commit/ec0a4399995d37cbcfe009987ebbd2b010dc7216) reparents original Health/Monitor/ECG/Chat/Interview/Care/NASA/Atlas/Settings, SIMULATED briefing and PatientDemo into the central stack and leaves their original HTTP and identity logic unchanged. **Only Browse is the visible route navigator**; the topBar retains appearance, language, settings and help. A single /health status pill appears inside Mission Operations.
- **Unresolved:** Home UTC bounds and Q-0477 Monitoring time filters are **not connected**. [Issue #8 comment #6877383276](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6877383276) asks Q-0477 owner for a narrow public UTC setter contract. No `native_workspaces.py`, `monitoring_time.py`, Q-0484 module, shared i18n, or NASA raw-data file was changed.
- **Source evidence only:** focused 13/13 static assertions passed; no GUI/offscreen or Windows render, no actual synthetic SQLite DB readback, no authenticated HTTP clickthrough or independent visual approval. Historical status at that checkpoint: [Q-0485 RUNNING / review PENDING](quests/v1/Q-0485.md), detailed [SCREEN_STATUS](docs/SCREEN_STATUS.md). Current Q-0487 is STALE, implementation/evidence preserved, and `main.py` released; see its live Quest. Do not infer DONE from the commit.

---

## Latest Q-0485 native Home visual direction (2026-11-14)

Owner override: the rejected five oversized Portal cards / horizontal-menu-only first-view guidance is superseded **for native Home layout only**. Q-0485 implemented NASA Open MCT-aligned object tree on the left, usable data workspace in the center, source properties/Inspect on the right, and one **bottom** UTC Time Conductor. The initial selected item is Mission Workspace overview, **not** NASA MA-7. NASA MA-7 is a distinct historical source object and remains separate from the prominent **DEMO FOR HACKATHON → SIMULATED briefing → fictional Q-0484 patient app**. Existing 13 feature routes and their authorization remain unchanged.

- Latest source commit [`b92e1a9daac3c8ba036774e6b27aeef7b32633ae`](https://github.com/huyng0699-arch/AETHERION/commit/b92e1a9daac3c8ba036774e6b27aeef7b32633ae); `mission_ops_home.py` blob `d39354c4b7571847cf6ffc3eb79572573e9533d2`. Inspector remains at least 205 logical px with horizontal scrolling at a 1040px window. The shared UTC bounds affect only authorized UTC source data supplied to the Home workspace, **not** Q-0477 Monitoring filters without that owner's ACK, and NASA MA-7 receives no fabricated UTC timestamps.
- Static code readback: **15/15 structural assertions passed**, not Qt runtime validation. `main.py` integration is unchanged and was previously committed (`dc49fe9` / `83355ec`).
- **No offscreen Qt image or fresh Windows screenshot**: PySide6/PyQt6 unavailable, attempted venv installation did not find a distribution. Real 1040×650 / 150% DPI UI, clickthrough, source-link correction and independent reviewer remain pending. Full evidence and current Quest status: [Q-0485](quests/v1/Q-0485.md), [SCREEN_STATUS](docs/SCREEN_STATUS.md). Do not mark DONE.

---

## Owner Windows ZIP reconciliation — draft PR #10 (2026-11-14)

**Source:** owner-uploaded private `AETHERION-main-win-changes-20261114.zip`, SHA-256 `aaefb8144958770e66701b01bf0871dbdf9f92700928c2e85432a59fb9a72951` (75 entries). This was **safely unpacked and compared** to current AETHERION files before selectively importing. **No wholesale source replacement, stale Quest status overwrite or release approval.**

- **Pending code review:** [PR #10 — selective owner Windows fixes](https://github.com/huyng0699-arch/AETHERION/pull/10) on branch `import/windows-tested-fixes-20261114` (33 changed source/test/QA files at PR creation). Branch adds Windows-safe SQLite connection closing across stores/APIs, reader/medical search, ECG UTC/QUrl fixes, Qt palette/reader/atlas guards, safer /health timeout and PyInstaller descendant-window UIAutomation detection. Existing Mission Operations Q-0485, newer Quest metadata, separate Q-0486 PR #9 and current `docs/SCREEN_STATUS.md` were **not replaced**.
- **Owner-reported QA in private ZIP:** real Windows 10/Python 3.13.14/PySide6/PyInstaller; EXE `AETHERION-Desktop.exe` built as onedir (15,066,021 bytes; SHA-256 `402426c0e9aa62926c32f841baa9d451bd0310e8af20182beb0884dfde02f632`), focused **64/64** Windows tests passed, native 16-route/screen and API checks; offline CliFF SQLite **118/119** records, 321 stored image rows tagged rights-approved, **CLIFF-119 unresolved**. These are **user-supplied historical Windows observations**, not retested on the PR branch or proof that all original NASA PDFs/licenses/clinical content passed review.
- **Evidence limitation:** the archived Q-0430 Win32 `PrintWindow` screenshot has **a blank widget client area**; it cannot verify rendering. Fifteen separate Qt `QWidget.grab()` PNG images exist in the original ZIP but their binary bytes are **not uploaded to GitHub by this text connector**. The detailed provenance, test/build evidence and outstanding actions are documented **in PR #10 branch** at [`docs/qa/WINDOWS_OWNER_ZIP_RECONCILIATION_20261114.md`](https://github.com/huyng0699-arch/AETHERION/blob/import/windows-tested-fixes-20261114/docs/qa/WINDOWS_OWNER_ZIP_RECONCILIATION_20261114.md). Do not link the not-yet-uploaded PNGs as repository files.
- **Next gate:** an independent reviewer resolves overlap with current Quest owners, runs focused Windows SQLite/Qt/ECG/EXE tests at a pinned merged SHA, attaches original photo/test evidence via a binary-capable upload, and then determines acceptance in each Quest. **PR #10 is DRAFT and not merged into main; `review: PENDING` is not `DONE`.** The main `QUEST_LOG.md` remains a short navigation page, not a parallel task ledger.

---


## Scoped integrity fixes — attribution SHA-256 and Quest YAML (2026-11-14)

- **Submission metadata corrected on main:** [commit 311c59e](https://github.com/huyng0699-arch/AETHERION/commit/311c59e26447518b08c5974c1e2457405f23a48e) replaces the stale SHA-256 of `THIRD_PARTY_NOTICES.md` in `submission/SOURCES_AND_LICENSES.md`; exact SHA-256 was recomputed from current source bytes, and all four current published digests were checked by GitHub read-back. Original Q-0264 approval was not altered; a pinned Python submission check and independent reviewer are still required.
- **Quest Board duplicate-key regression corrected on main:** [Q-0065 metadata fix](https://github.com/huyng0699-arch/AETHERION/commit/daf3aae2526f558874cd304e2d42efc605153be2) and [Q-0072 metadata fix](https://github.com/huyng0699-arch/AETHERION/commit/c619c4625604aed2a69d6a5bc98601b83405a544) remove only the shadowing null `run_id` and `lease_until_utc` lines; original owner, evidence, review and BLOCKED integration gates remain unchanged. GitHub readback shows exactly one key of each type, **not** proof of a complete `quest_board.py check` PASS.
- **Concurrency correction:** Q-0486 is already owned by [open PR #9](https://github.com/huyng0699-arch/AETHERION/pull/9) and not yet on main. Two temporary Q-0487/Q-0488 remediation Quest files were **archived in full before deletion** to avoid introducing missing Q-0486 in the contiguous live Quest ledger. [Full archived original claims and code evidence](docs/qa/QUEST_LEDGER_METADATA_REMEDIATIONS_20261114.md). The latest GitHub directory scan after this correction confirmed **485/485 contiguous Quest IDs (Q-0001–Q-0485)**; as always, this count is a snapshot, not a permanent counter. No PR #9 file, other agent's approval or clinical evidence was changed.

## Q-0487 — First launch auto-local Server and pre-seeded fictional crew (historical snapshot; current Quest STALE, 2026-11-15)

- User directive: first launch should default to local HTTP Server, and fictional astronaut-demo history should be ready without a manual data import. First screen **remains Login**; its Demo now routes to **SIMULATED briefing → Start → five fictional Q-0484 profiles**.
- [`startup_runtime.py`](apps/desktop/src/aetherion_desktop/startup_runtime.py) attempts a verified loopback `/health` response before launching a child `uvicorn` on 127.0.0.1:8765 if the port refuses connections and the server Python package is installed. Custom URL and external port owners are respected. No default account/password or second authoritative patient store.
- The separate demo SQLite `~/.aetherion/demo/synthetic_patients_v1.sqlite3` is preseeded asynchronously through unchanged Q-0484 `build_demo_database()`, then read back with `demo_stats()`. No synthetic records are written to the authenticated Server; NASA MA-7 remains real historical research. Startup does not block the main Qt thread.
- Code commits: [`09982ded`](https://github.com/huyng0699-arch/AETHERION/commit/09982dedecd13510ea154f34cd0f3c2bfe4691fc), [`64f274d9`](https://github.com/huyng0699-arch/AETHERION/commit/64f274d904e663516b7a1dcfa64721d2f5f65dc4), [`9bf41583`](https://github.com/huyng0699-arch/AETHERION/commit/9bf41583c642e8500f6180b613c321dca29733c3), [`b1e4a330`](https://github.com/huyng0699-arch/AETHERION/commit/b1e4a3306ba6cfa6df30e5ef54b66d0a847e0a68), plus updated `scripts/start_desktop.ps1`.
- **Evidence boundary:** GitHub code/static inspection only; no Qt/Windows Server process or demo SQLite readback from the user's environment. [Q-0487](quests/v1/Q-0487.md) `RUNNING / review PENDING`; see [First-run guide](docs/FIRST_RUN_LOCAL_SERVER_DEMO.md). No PASS/DONE claim.

---

## Engineering and source-of-truth references

- [AGENTS.md](AGENTS.md): active owner overrides, scoped Quest leases, review rules. **START ≠ COMPONENT READY ≠ DONE**. Work only in `huyng0699-arch/AETHERION`, no branch or import from older project repositories.
- [Owner design](docs/DESIGN_2026_11_14.md): updated native Portal, operations UX, Server/Desktop separation and actual interactive controls.
- [Bilingual policy](docs/LANGUAGE_POLICY.md): Vietnamese + English; preserve original NASA texts and original Vietnamese symptom IDs.
- [Release readiness](docs/RELEASE_READINESS.md): documentary release gates, not proof of a working EXE.
- [Bug triage](docs/BUGFIX_TRIAGE_20261114.md): technical faults and known Windows test reports.
- [Complete historical Quest log](docs/qa/QUEST_LOG_HISTORY_20261114_BEFORE_RECOVERY.md): all pre-recovery snapshots and older remediation tables, preserved exactly.

## Data and review invariants

- NASA MA-7 historical measurements are real archival context, not live astronaut telemetry; fictional patient data is explicitly **SIMULATED** and isolated from the real health records. Do not mix them or mislabel provenance.
- Source CliFF articles, text, images, hashes and licenses are preserved in their original language and provenance. Scientific content is not silently validated or translated by a UI switch.
- An implementation with no genuine Windows/device/clinical validation remains `COMPONENT_READY` or `BLOCKED`; only an independent reviewer may approve a truly satisfied Quest. GitHub Actions failing with `runner_id=0` and zero steps does not constitute a Python test result.

**Maintenance:** Record acceptance and owner coordination inside the relevant `quests/v1/Q-XXXX.md`; put lengthy test snapshots in dated `docs/qa/` documents. Keep this root index concise so it cannot become a growing, contradictory second ledger.
