# AETHERION — Quest navigation (live)

**Single source of truth for status:** each `quests/v1/Q-XXXX.md` on the canonical `main` branch. This page is a **navigation index**; it is not a second task database, scheduler, or release certificate. Every Quest keeps its own dependencies, owner, evidence, and independent reviewer gate.

**Recovery 14 November 2026:** This navigation page was shortened to remove contradictory, growing historic snapshots. **The previous 45 KB version was archived without content loss** at [QUEST_LOG history](docs/qa/QUEST_LOG_HISTORY_20261114_BEFORE_RECOVERY.md). Past Windows test reports remain available there with their original caveats and dates. No original Quest status or evidence was erased or set to DONE by this change.

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
| New Mission Operations Home | [Q-0485](quests/v1/Q-0485.md) | Compact, native mission workspace rather than rejected five oversized cards |
| Clearly synthetic patient Demo | [Q-0484](quests/v1/Q-0484.md), [Q-0478](quests/v1/Q-0478.md) | Demo explanation → 5 fictional patients/540-day data, separately from actual 1962 NASA MA-7 archive |
| Monitoring / ECG | [Q-0477](quests/v1/Q-0477.md), [Q-0481](quests/v1/Q-0481.md) | Fix Qt paint-crash evidence, authorize ECG API and verify real behavior on Windows |
| NASA CliFF 119 offline documents | [Q-0421](quests/v1/Q-0421.md), [Q-0425](quests/v1/Q-0425.md), [Q-0426](quests/v1/Q-0426.md), [Q-0427](quests/v1/Q-0427.md), [Q-0435](quests/v1/Q-0435.md) | Actual source, media rights, SQLite import, complete offline reader and native verification |
| Independent acceptance | [REVIEW-0001](quests/review/REVIEW-0001.md) | Different reviewing agent must assess real evidence; never self-approve |

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
