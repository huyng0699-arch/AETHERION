# AETHERION — Single agent instruction source

**Product:** AETHERION, Team TRUY TINH, NASA Space Apps 2026. **Canonical new design:** [docs/DESIGN_2026_11_14.md](docs/DESIGN_2026_11_14.md). **Source of truth for live Quest status:** each `quests/v1/Q-XXXX.md` file. **`QUEST_LOG.md` is only the navigation/coordination guide**, not a competing mutable task ledger.

## Owner override — parallel implementation with independent acceptance (14 November 2026)

**Latest user instruction:** A Quest does **not** have to wait for its predecessor's PASS to **start coding**. Every Quest still needs explicit acceptance criteria, genuine evidence, and a review by **an agent other than its implementer** before the final PASS. This section supersedes older "all dependencies DONE before work can start" language and acceptance shortcuts below and in older task templates; it does not cancel clinical safety checks.

### Separate three gates — START ≠ COMPONENT READY ≠ DONE

1. **START / PREPARE:** `READY` and `QUEUED` Quests may be claimed immediately, **even if `depends_on` includes unfinished Quests**. Keep their original dependency IDs; never delete links to pretend the prerequisites were satisfied. Set `status: RUNNING`, `execution_mode: PREPARE`, owner, run ID and lease; coordinate exact paths by compare-and-swap. `PLANNED` long-term work remains off unless separately authorized. If the dependency exposes an unwritten API, implement behind a typed adapter or feature flag and declare the assumption. No duplicate server, store, shell or overlapping writer.
2. **COMPONENT READY FOR REVIEW:** Implement a real component in its assigned scope. Record files and commit SHA, an actual test/run/inspection appropriate to the Quest, acceptance checks, known gaps and `review: PENDING`. The implementing agent may not self-approve. If end-to-end integration is blocked by a predecessor, record `implementation_state: COMPONENT_READY` and leave final `status: RUNNING` or `BLOCKED` with exact integration barrier; **do not report the entire user journey as complete**.
3. **FINAL PASS / DONE:** A different reviewing agent independently reads that Quest's original acceptance criteria, code diff, artifact and evidence. It marks `review: APPROVED` only after verifying the component and its required integration preconditions; `status: DONE` only when the complete Quest criterion is met. If a dependency is still incomplete, it may record `review: COMPONENT_APPROVED` but not falsely certify the dependent integration. If evidence fails, write `review: REWORK_REQUIRED`, exact defect, suggested fix, and return the task to the implementer without erasing prior progress.

### Clear acceptance remains mandatory

- Every Quest must identify **what changed, where, why it meets its specific outcome, and what was actually observed**; no arbitrary "PASS all" labels, screenshots of placeholders, fake imported NASA records or AI-generated claims of a running app.
- **Focused verification rather than blanket full-suite runs:** for low-risk visual/content work, inspect the actual rendered or imported artifact. For APIs/database/Qt linkages, run a minimal real interaction. For medical safety, patient privacy, provenance/copyright, offline medical library, 3D picking and Windows release, keep rigorous relevant tests/hardware evidence. Dedicated QA Quests own broader regression, not every developer Quest.
- No skipped/expected-failure test is a PASS. A working component without a tested integration is **component-ready**, not a released feature.
- **Independent reviewer must not be the implementer**, may not approve its own code or use a one-line status in place of observed evidence. Capture reviewer's distinct identity, UTC, reviewed commit and finding in the Quest. A reviewer can request changes without resetting other tasks.
- **Standing reviewer Quest:** [quests/review/REVIEW-0001.md](quests/review/REVIEW-0001.md) defines periodic independent acceptance. The [GitHub Actions review workflow](.github/workflows/quest-review-15m.yml) schedules a mechanical review-queue refresh roughly every 15 minutes; this does **not** itself instantiate an AI reviewer. A separately invoked review agent must read and judge the queued code. Scheduled GitHub Actions may be delayed or fail if repository Actions cannot run.

## Mandatory startup (read narrowly)
1. Read this file, then `QUEST_LOG.md`, and only the relevant sections of `docs/DESIGN_2026_11_14.md`.
2. Run `python scripts/quest_board.py check` and `python scripts/quest_board.py ready`. Do not read all 435 Quest files into a prompt.
3. Open a **single eligible READY Quest**; check its dependencies, current code, existing changes, and any RUNNING claims affecting exact files. The task is not authorization to modify unrelated parts of the repository.
4. Before editing, claim the Quest via its **current GitHub blob SHA** (compare-and-swap). Fill `owner`, unique `run_id`, `lease_until_utc`, the execution record's **exact owned paths**, and change `status` to `RUNNING`. Never assign yourself a task merely by describing work in chat. If a conflict occurs, refetch and reconcile.
5. Implement **only** the claimed outcome; test actual behavior; record command, exit status, commit SHA, screenshots/video for actual Windows UI, and blockers.
6. Mark `DONE` only after tests are run, prerequisites are genuinely DONE, any human review gate is approved, and evidence is recorded in the *same Quest file*. Update metadata `review: APPROVED`. Otherwise return to `READY` or mark `BLOCKED` with a reproducible reason.

## Dependency and phase rules

- `READY` means eligible to claim now, **only** if all declared dependencies are DONE. `QUEUED` becomes READY when verified prerequisites close. `PLANNED` is a post-hackathon or future research track; never start it merely to increase Quest throughput.
- Priorities: `P0` must-have for NASA 2026 challenge; `P1` enhancement for judging; `P2` post-hackathon; `P3` Earth/Mars 2050 aspiration. P0 is a prioritized backlog, **not a guarantee all 67 tasks fit the hackathon**.
- Historical ASTRA implementation, NASA datasets, CliFF archives and linked research are **references**, not permission to clone a second product or count past PASS as new AETHERION acceptance.
- **No competing entrypoints:** one HTTP server, one authoritative observation store, one independent native Windows desktop application, future separately packaged mobile/watch clients. No website wrapped as the Windows app.
- User-visible screens must contain working controls or explicitly label an unavailable feature, with no false 3D, live sensor or diagnosis claim.

## Concurrency / leases
- One writer per **exact file path**; source folders are not exclusive ownership. Agents working separate Quest files must still detect overlapping intended code changes.
- Share only the current GitHub branch and committed work. Read the HEAD, other RUNNING claims and relevant diffs before any write; preserve updates from others. Never force-push, reset, mass-reformat shared files or overwrite a newer version.
- Lease is **60 minutes** from the latest valid START/ALIVE recorded in the Quest. Record meaningful `ALIVE` heartbeat around 30 minutes; after expiry another invoked agent can mark the attempt `STALE`, preserve work, and re-claim with a new run ID. An expired clock **does not prove** a process has stopped.
- A task claim does not spawn agents or make them work in the background; actual agent invocations are required.
- On shared `main`, write a short set of scoped files, commit, then integrate the newest upstream HEAD before trying to advance a branch pointer. Rebase/merge carefully; never destroy another writer's changes.
- If prerequisites become invalid or a shared path is already claimed, mark `BLOCKED` with exact evidence and seek coordination.

## Engineering acceptance
- Actual non-skipped unit, contract, integration and UI tests must pass on the commit being accepted. Python tests are **not evidence** of an actual Windows EXE running; attach real native Windows session logs and/or screenshot/video hashes where required.
- Qt desktop opens **directly** into a top-menu Mission Control dashboard; menu above app content. Genuine 3D requires depth-buffered mesh geometry, orbit, zoom, pan and triangle/object picking; otherwise call it 2D.
- One actual source/subject/time/unit/scope/quality trail per observation. Distinguish READY, NO_DATA, STALE, OFFLINE, DENIED, ERROR and UNVERIFIED. Missing sensor or user response does not mean unconsciousness. NASA research is not live human telemetry.
- Required intended care flow: **GATHER → EVALUATE → ACT → RECHECK**, with persisted identity and human agency. Deterministic safety must continue when optional AI is disabled.
- Do not use test fixtures or fake patient data as real, misstate CliFF 119 as 119 verified downloaded NASA originals, imply flight/clinical certification, or manufacture API/device integrations.
- Include actual source URL, author, license terms, versions, SHA for copied NASA/third-party material and explicit AI-tool disclosures in the final submission. An open repository is not a substitute for completing NASA's official Project tab.
- Preserve the current `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, user files, secrets and separate research contributions. No destructive changes or production deployment without owner authorization.

## Narrow source reading
- **Official challenge:** https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/
- **Current product spec:** `docs/PRODUCT_SPEC.md`; **architecture:** `docs/ARCHITECTURE.md`.
- Scientific source registry: `knowledge/nasa/SOURCES.md`, and actual verified files under `knowledge/nasa/`.
- README and install instructions: `README.md`, `docs/INSTALL_WINDOWS.md`.

**Rule of completion:** A Quest is not DONE because an agent says it is. Code, observed test evidence, relevant hardware proof and accepted requirements must agree.

## Mandatory new medical-library Quest directive (2026-11-14)
- **Only AETHERION is allowed as the code/content repository.** The owner's older GitHub projects and old authored clinical content are explicitly OFF-LIMITS: do not read, import, copy, summarize or derive medical text, code, assets, or condition mapping from them. Public NASA original CliFF 119 and independent correctly licensed sources only.
- **119 individual ingestion Quests:** `Q-0301`–`Q-0419` (see `quests/CLIFF_119_INDEX.md`); 16 native PySide6 medical-library Quests: `Q-0420`–`Q-0435`. Claim by exact path and lease per standard procedure. The rendered NASA table shows 118 named sources and one unresolved item; never fabricate the 119th or invent source URLs.
- **Medical imagery quality:** Each article should contain condition-relevant images from verified licensable sources beyond NASA's own embedded figures where feasible. Prefer at least three meaningful clinical/anatomical/diagnostic illustrations, more when justified. Every binary image must have license, author, direct file URL, attribution, clinical caption, alt text, SHA-256 and local BLOB representation. Missing lawful images must be documented, not fabricated/padded. Treat medical image accuracy as a review gate.
- **Single offline library:** `knowledge/nasa/cliff_119_2023/AETHERION_NASA_CLIFF_119.sqlite`; preserve ordered text, headings, tables, figures, citations, original PDF page locations and source versions. Native Qt desktop Medical Library App View with top menu; no web-wrapper and no fake data when library empty.
- **Never mark DONE from a plan or index-only test.** Real source bytes/page content and authentic image/media evidence, a populated SQLite record, actual tests and offline Windows reader proof are required. Until they exist, status remains READY/BLOCKED.
