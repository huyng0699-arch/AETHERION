# AETHERION — Single agent instruction source

**Product:** AETHERION, Team TRUY TINH, NASA Space Apps 2026. **Canonical new design:** [docs/DESIGN_2026_11_14.md](docs/DESIGN_2026_11_14.md). **Source of truth for live Quest status:** each `quests/v1/Q-XXXX.md` file. **`QUEST_LOG.md` is only the navigation/coordination guide**, not a competing mutable task ledger.

## Mandatory startup (read narrowly)
1. Read this file, then `QUEST_LOG.md`, and only the relevant sections of `docs/DESIGN_2026_11_14.md`.
2. Run `python scripts/quest_board.py check` and `python scripts/quest_board.py ready`. Do not read all 300 Quest files into a prompt.
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
- **Legacy owner UX review dated 2026-11-14:** https://github.com/huyng0699-arch/NASA-Space-Apps/blob/main/docs/ux/ASTRA_UX_REACCEPTANCE_OPEN_SOURCE_20261114.md . This informs UX acceptance but does not restore the old web architecture or product name.
- Scientific source registry: `knowledge/nasa/SOURCES.md`, and actual verified files under `knowledge/nasa/`.
- README and install instructions: `README.md`, `docs/INSTALL_WINDOWS.md`.

**Rule of completion:** A Quest is not DONE because an agent says it is. Code, observed test evidence, relevant hardware proof and accepted requirements must agree.
