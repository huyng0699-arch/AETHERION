# Q-0270 — Release proof preparation (NOT a frozen release)

**State:** PREPARE only · 2026-11-15 (ICT) · `review: PENDING`. This document is an evidence-collection contract, not a release, NASA Project-tab submission, public demo confirmation, or medical/flight certification.

## Pinned baseline, not final submission

- Observed `main` HEAD **before claim**: `55a94eb42586b1d8b7c6e3be1161f37024a77873` ([commit](https://github.com/huyng0699-arch/AETHERION/commit/55a94eb42586b1d8b7c6e3be1161f37024a77873)).
- Claim commit: `65f31cf10ed488de9e2cff3308b6c1b6f8dd3023`. Subsequent work can change `main`; **neither SHA is the final submitted release**.
- Required dependencies: `Q-0260` (public demo) and `Q-0106` (Windows executable). Preserve both links; acceptance cannot be finalized while either is unverified.
- Coordination: [Issue #8](https://github.com/huyng0699-arch/AETHERION/issues/8) requires a native Mission Operations Home with prominent SIMULATED Demo and a distinct NASA MA-7 historical archive. [PR #9](https://github.com/huyng0699-arch/AETHERION/pull/9), [PR #10](https://github.com/huyng0699-arch/AETHERION/pull/10), and [PR #11](https://github.com/huyng0699-arch/AETHERION/pull/11) were open at preparation time; **do not treat unmerged PR content as part of the pinned main release**.

## Evidence to capture at actual freeze

| Gate | Required observable evidence | Current finding |
| --- | --- | --- |
| Source identity | Final `main` SHA, commit URL, clean checkout, UTC freeze time; source readback after freeze | **PENDING** — only provisional baseline above |
| Windows artifact | Exact EXE path, file SHA-256, version, native Windows startup/interaction and log on the same SHA | **PENDING** — owner-reported earlier EXE is not this pinned release |
| Native Desktop | Real 1040×650 / 150% DPI Windows screenshots, route clickthrough, both vi/en, accessible Demo | **PENDING** — offscreen Qt images are not Windows evidence |
| Synthetic isolation | Separate demo SQLite file; read back 5 fictional profiles, 540 days and 12 metric families; prove authenticated store unaffected | **PENDING** — never mix with live patient records |
| NASA provenance | NASA MA-7 (1962), 83 archival values, independent historical labeling; CliFF 119 actual rights/source completeness | **PENDING** — CliFF packaging reported 118/119, not 119/119 |
| HTTP / identity / safety | Focused authenticated API, consent, admin-role, cloud disable, SQLite close/WinError 32 and clinical safety regressions | **PENDING** — Issue #12 documents Cloud AI disable/environment fallback concern |
| Public demo | Public HTTPS URL, unauthenticated external access test with UTC, screenshots and exact SHA/version | **PENDING** — GitHub repository URL is not a public demo |
| NASA submission | Human-controlled Project tab confirmation and final publicly visible project entry, matching the frozen artifact | **PENDING** — no automated submission is authorized |
| Independent review | Reviewer different from implementer, reviewed SHA, date UTC, findings and disposition in Q-0270 | **PENDING** |

## Repeatable local capture protocol (execute only at actual release)

On a clean checkout of the *actual* submission commit, record commands and their real outputs, never a predicted PASS:

```powershell
git rev-parse HEAD
git status --porcelain
Get-FileHash .\path\to\AETHERION-Desktop.exe -Algorithm SHA256
python scripts/quest_board.py check
```

Record `Get-FileHash` only after the Windows executable exists. Collect native Windows interaction screenshots and separate SQLite/HTTP readbacks with the same pinned commit. The independent reviewer must compare those artifacts with the published demo and NASA Project-tab version. Do not publish patient identifiers, API keys, or private screenshots.

## Freeze decision

**NOT FROZEN / NOT SUBMITTED / NOT APPROVED.** Next action: after Q-0260 and Q-0106 are independently accepted and release PRs are reconciled, pin the actual final SHA, capture the above observed evidence, obtain a distinct reviewer decision, and only then update Q-0270. This PREPARE document cannot substitute for official NASA Project-tab submission.
