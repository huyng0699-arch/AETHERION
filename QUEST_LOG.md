# AETHERION — Quest control board

**Scope:** 300 distinct, executable Quest specifications on `main`, numbered **Q-0001 through Q-0300**. Each task's live metadata is stored **only in its own `quests/v1/Q-XXXX.md`**. This root file is navigational and does not claim task completion.

## Current canonical product
- AETHERION is a **new product and name**, not ASTRA. Legacy material dated November 14, 2026 is reference-only.
- The native Windows app has its **top menu above the application content**, opens straight to Mission Control, and talks to a separate local-first HTTP server. Mobile and Wearable are independent planned clients.
- Every data point is source-backed or explicitly UNKNOWN/UNVERIFIED; historical NASA records are never passed off as live astronaut vital signs.
- The hackathon **ends on November 15, 2026 at 23:59 local time**; full P2/P3 development is not required for initial submission. Use the 2026 official Project tab to submit.

## Live status commands
```bash
python scripts/quest_board.py check
python scripts/quest_board.py stats
python scripts/quest_board.py ready
python scripts/quest_board.py running
```

The index pages below are initial listings; individual Quest status is authoritative. There are **300** tasks, organized into **20 independent workstreams**, 15 each.

| Stream | Quest range | Meaning |
| --- | --- | --- |
| Foundation | [0001–0015](quests/INDEX_001_015.md) | Build, native startup, CI, packaging |
| API contracts | [0016–0030](quests/INDEX_016_030.md) | Versioned schemas and client contracts |
| Core data | [0031–0045](quests/INDEX_031_045.md) | Source identity, scope, SQLite and provenance |
| HTTP server | [0046–0060](quests/INDEX_046_060.md) | API routes, persistence, typed events |
| Mission | [0061–0075](quests/INDEX_061_075.md) | Crew-wide native Qt mission dashboard |
| Personal | [0076–0090](quests/INDEX_076_090.md) | Personal health Today view |
| Care | [0091–0105](quests/INDEX_091_105.md) | GATHER → EVALUATE → ACT → RECHECK |
| NASA science | [0106–0120](quests/INDEX_106_120.md) | Real NASA datasets, five hazards and citations |
| Body Atlas 3D | [0121–0135](quests/INDEX_121_135.md) | True native 3D anatomy and renderer evaluation |
| Encyclopedia | [0136–0150](quests/INDEX_136_150.md) | Verified 119-condition/CliFF mapping and reader |
| Guide | [0151–0165](quests/INDEX_151_165.md) | Offline scientific guide, no mandatory AI |
| Safety | [0166–0180](quests/INDEX_166_180.md) | Assistance, human reports, ACK and privacy |
| Wearable | [0181–0195](quests/INDEX_181_195.md) | Future Wear OS and genuine device proof |
| Mobile | [0196–0210](quests/INDEX_196_210.md) | Future independent Android companion |
| AI gateway | [0211–0225](quests/INDEX_211_225.md) | Optional local/cloud AI with safety boundaries |
| Devices | [0226–0240](quests/INDEX_226_240.md) | Real source/device adapter contracts |
| QA | [0241–0255](quests/INDEX_241_255.md) | Unit/API/native Windows E2E proof |
| NASA submission | [0256–0270](quests/INDEX_256_270.md) | English submission, NASA data, 30s demo, citations |
| Earth health | [0271–0285](quests/INDEX_271_285.md) | Future public-health product |
| Mars 2050 | [0286–0300](quests/INDEX_286_300.md) | Long-term research and qualification gates |

## Initial handoff and emergency priority

At backlog creation, no Quest has been tested or accepted by these new task files. **No DONE is implied.** `READY` tasks are independently claimable after checking ownership; `QUEUED` tasks require their dependencies; `PLANNED` tasks are intentionally non-hackathon.

For a short path to a credible NASA submission, prioritize:
**Q-0001** (CI), **Q-0002** (actual Windows native boot), **Q-0016** (schema), **Q-0031** (observation provenance after schema), **Q-0047** (real observations endpoint), **Q-0061/0062** (Mission UI), **Q-0076/0077** (Personal UI), **Q-0091–0095** (Care), **Q-0106–0109** (real NASA sources), **Q-0241–0246** (tests), and **Q-0256–0265** (submission).

These are **dependencies and priorities, not parallel agents already running**. Read the actual Quest links and claim according to `AGENTS.md`.

## Design and science references

- [Current design 2026-11-14](docs/DESIGN_2026_11_14.md)
- [Official NASA 2026 challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)
- [NASA 2026 event schedule](https://www.spaceappschallenge.org/2026/)
- [Original older UX audit, not the new source of instructions](https://github.com/huyng0699-arch/NASA-Space-Apps/blob/main/docs/ux/ASTRA_UX_REACCEPTANCE_OPEN_SOURCE_20261114.md)

Review owner and current state **on GitHub at HEAD** before each task claim. This file is not a daemon or automatic task runner.
