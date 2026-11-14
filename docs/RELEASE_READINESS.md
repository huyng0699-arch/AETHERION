# AETHERION — Evidence-based release readiness

**Snapshot:** 2026-11-14 06:31 UTC. **Decision: NOT READY for an independently demonstrated Windows distribution or an asserted complete NASA submission.** This document is a snapshot, not an automatically updated certificate.

The script [release_readiness.py](../scripts/release_readiness.py) reads live Quest metadata whenever run. It **never** declares a release authorized. Exit 0 only means all *recorded documentary gates* within the selected scope report independently accepted evidence; a separate reviewer still must verify actual software, Windows run and official submission.

## Observed repository gates

| Gate | Quest | Live state at inspection | Evidence-based interpretation |
| --- | --- | --- | --- |
| Native Windows boot | Q-0002 | READY | No verified Windows session or native boot acceptance |
| Clean Windows install | Q-0003 | READY | No clean-install proof |
| Separate server/desktop + reconnect | Q-0004 | QUEUED | Runtime journey not accepted |
| Versioned secure local configuration | Q-0005 | RUNNING, COMPONENT_READY | Eight local tests passed; independent Windows check/review pending |
| Distributable Windows EXE | Q-0010 | QUEUED | No accepted EXE/hash or cold start; INSTALL_WINDOWS documents a developer prototype |
| Authenticated observations API | Q-0047 | DONE, reviewer recorded self-verification | Code evidence exists but violates independent reviewer gate |
| Native Mission Control | Q-0061 | BLOCKED | Headless tests exist; native Windows interaction not proven |
| Persisted care journey | Q-0091 | QUEUED | No integrated acceptance |
| NASA scientific source trace | Q-0106 | DONE, reviewer recorded self-check | Needs an independent source/provenance audit |
| Green real CI | Q-0241 | RUNNING; lease in task expired | Latest inspected GitHub Actions lint/server tests failed at 06:28 UTC; retrieved jobs contained no steps and job-log access returned 404. **Do not classify as PASS.** |
| Official Team TRUY TINH + Project tab | Q-0256 | BLOCKED | Team URL and actual Project-tab completion not verified |
| Full 119-condition offline medical library | Q-0435 | QUEUED | Optional dedicated library certification, not implied by schema/reader source code |

The items above describe what was **observed in the repository's task records**; they are not direct hardware tests. Some tasks marked DONE were self-reviewed under older procedures. The current AGENTS.md requires a different reviewer, so the auditor intentionally rejects self-approval.

## Reproduce the assessment

Run from a clone at the intended Git commit:

\`\`\`powershell
py -3.11 scripts\release_readiness.py --scope demo --output release-demo.json
py -3.11 scripts\release_readiness.py --scope release --output release-package.json
py -3.11 scripts\release_readiness.py --scope library --output release-library.json
\`\`\`

- \`demo\`: minimal NASA-facing evidence, including official association with the challenge.
- \`release\`: server/desktop Windows package with safe startup and actual CI.
- \`library\`: complete offline medical-library acceptance separately from the demo.
- Exit **2**: at least one documentary gate missing or unverified; see JSON.
- Exit **0**: metadata gate complete **only**. The JSON still sets \`release_authorized=false\`, since it has not reproduced any Windows artifact, medical evidence, or submission.

**Next required evidence:** native Windows install/run logs with hashes, API connect/disconnect/reconnect, a trustworthy EXE SHA-256, non-skipped CI, separate reviewer findings, authentic NASA material licenses/provenance, and the real Project-tab confirmation. No real patient data may be used for validation.

The earlier AETHERION project/repository is not used as a code/content source by this audit.
