# Q-0268 — NASA Space Apps 2026 claim-to-evidence matrix (working draft)

**Evidence snapshot:** 2026-11-14 UTC; repository `huyng0699-arch/AETHERION`, inspected `main` near commit `e7a15f5713b1daba0e61c4b51008d5264b83f2f8`. This is a **source-document traceability audit**, not a jury score, NASA validation, clinical approval, a verified Windows run, or an official submission.

## Protocol and scoring

Read the repository's current `AGENTS.md`, `QUEST_LOG.md`, `docs/DESIGN_2026_11_14.md`, `docs/LANGUAGE_POLICY.md`, `submission/README.md`, `submission/SOURCES_AND_LICENSES.md`, and relevant Quest statuses from `main`. Distinguish (1) an authored claim, (2) a source artifact, (3) observed runtime proof, and (4) outstanding independent verification. This matrix does **not** invent an official NASA scoring rubric or assign points.

Legend: **SOURCE_ONLY** = linked material or code exists but its claimed end-to-end behavior is not independently observed; **OWNER_REPORTED** = historical user-provided observation, not reproduced on pinned current `main`; **MISSING_GATE** = necessary verification not present; **NOT_APPLICABLE** = no claim made.

| Judge-facing claim / requirement | Traceable current evidence | Verification classification | Missing gate / safe wording |
| --- | --- | --- | --- |
| Astronaut health-monitoring relevance | [Official 2026 challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/); [submission proposition](README.md) | SOURCE_ONLY | Relevance is a design rationale, not a demonstration of flight-ready medical capability |
| Native Windows mission-operations UI | `apps/desktop/src/aetherion_desktop/mission_ops_home.py`; Q-0485 source/implementation notes in `QUEST_LOG.md` | SOURCE_ONLY; Windows results in owner ZIP are OWNER_REPORTED | Pin a merged commit, capture authentic native screen/interaction and VI/EN at 1040×650 and 150% DPI; do not show the rejected five-card design as the new Home |
| Demo for hackathon | Q-0484/Q-0485 and [Issue #8](https://github.com/huyng0699-arch/AETHERION/issues/8) | SOURCE_ONLY | Confirm isolated SQLite contains the intended five **fictional** profiles × 540 days × 12 metrics and is visibly labelled SIMULATED; never present it as a clinical or astronaut dataset |
| NASA MA-7 historical archive | Q-0478, Q-0485 and current navigation notes in `QUEST_LOG.md` | SOURCE_ONLY | Validate archive 1962 attribution and the 83-value mapping against source bytes; never blend with demo fixtures or call it live astronaut telemetry |
| NASA scientific provenance | `knowledge/nasa/source_registry.json`; [sources and licenses](SOURCES_AND_LICENSES.md) | SOURCE_ONLY | Independently check original links, source rights, hashes and exact transformations before asserting verified science content in the demo |
| NASA CliFF medical library | [official IMM documentation](https://www.nasa.gov/integrated-medical-model-documentation/); `knowledge/nasa/cliff_119_2023/`; [Issue #6](https://github.com/huyng0699-arch/AETHERION/issues/6) | SOURCE_ONLY; owner's offline SQLite 118/119 report is OWNER_REPORTED | Resolve missing 119th, authenticate original PDFs and individual image rights, verify page anchors and actual offline native reader; do not call 119 originals fully verified |
| Local HTTP + SQLite observation path | `apps/server/`, `submission/README.md`; Windows owner ZIP reconciliation described in `QUEST_LOG.md` | SOURCE_ONLY; selected Windows checks OWNER_REPORTED | Focused authenticated API + restart/readback on pinned current SHA, verify subject isolation, source, quality and timestamps |
| Bilingual VI/EN UI | [language policy](../docs/LANGUAGE_POLICY.md), `apps/desktop/src/aetherion_desktop/i18n/vi.json`, `en.json` | SOURCE_ONLY | Verify language switch/persistence and visible strings in native runtime; scientific originals must remain unchanged |
| Offline/reliability/Windows distribution | [PR #10](https://github.com/huyng0699-arch/AETHERION/pull/10) (draft), Windows build/verification scripts | OWNER_REPORTED for supplied historical EXE; not reproduced on current main | Merge/review without overwriting concurrent owners; cold start, hash, offline and WinError 32 regressions at pinned EXE commit |
| Privacy and medical safety | `AGENTS.md` acceptance contract; Q-0252 evidence in its Quest | SOURCE_ONLY for this audit | Verify identity, authorization, fail-closed behavior and no false clinical inference under targeted tests; independent safety review |
| Third-party attribution | `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, [license inventory](SOURCES_AND_LICENSES.md) | SOURCE_ONLY | Re-audit installed/bundled dependencies and NASA/media rights for the exact released build |
| Public judge access and official Project tab | [submission checklist](README.md); Q-0260 remains READY at this snapshot | MISSING_GATE | Obtain an actual publicly reachable demo and permissions audit; only project owner submits on official Project tab |

## Do-not-claim boundaries

- The owner-reported Windows ZIP results and its screenshots are **not** tests executed by this Quest author, and draft PR #10 is **not** a merged Windows release.
- The independent reviewer queue ([Issue #7](https://github.com/huyng0699-arch/AETHERION/issues/7)) does not by itself grant PASS.
- The unresolved Q-0260 public demo link and Q-0106 science dependency remain open; keep Q-0268 in PREPARE pending final acceptance.
- NASA original texts, historical observations, synthetic fixtures and unreviewed symptom aliases are distinct classes; no cross-class promotion without verified provenance.

## Follow-up for the independent reviewer

At a pinned merged `main` SHA, review each row's actual artifact, reproduce the minimal appropriate API/SQLite and Windows GUI checks, compare NASA/media licenses against original source files, verify judge-accessible URLs and official submission state with owner-provided proof, and record a separate reviewer identity and decision in Q-0268. Until then, this matrix is a working evidence map, not a passed submission scorecard.
