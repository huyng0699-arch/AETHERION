---
id: REVIEW-0001
kind: RECURRING_INDEPENDENT_ACCEPTANCE
status: READY
cadence: 15m
reviewer_role: independent_agent
scope: AETHERION
owner: null
---

# REVIEW-0001 — Independent Quest acceptance review

## Mission

**Every review cycle, a separate agent checks implementation claims by other agents** against the exact original Quest acceptance requirements and the current GitHub HEAD. This is a **standing recurring review Quest**, not an implementation task added to the numbered 435-item backlog.

**Parallel build is authorized:** `QUEUED` implementation Quests can start in `PREPARE` despite unmet dependencies. Their final integrated DONE still requires real acceptance. Do not mistakenly penalize an agent merely because an upstream Quest has not passed.

## Review cycle (15 minutes)

1. Read the root `AGENTS.md`, `QUEST_LOG.md` and **the latest queue artifact** from the workflow `quest-review-15m.yml`. Fetch current branch HEAD and the relevant Quest file; do not rely on a previously cached snapshot.
2. Prioritize `implementation_state: COMPONENT_READY`, `review: PENDING`, recent `DONE` transitions, and any suspicious / incomplete `DONE`. Keep existing agent claims intact; never take over an implementing agent's files.
3. Identify the implementer's `owner` and `run_id`. **The reviewer must be a different agent** and use a separate reviewer ID/run ID. No self-approval.
4. Read the **original acceptance** in that Quest. Inspect the **changed code, actual reference source or output** and the claimed evidence. Trace concrete UI/API/data behavior where relevant, not merely tests or agent's declaration.
5. Decide:
   - `APPROVED`: original criteria met, required integration correct, actual evidence present. Set `review: APPROVED` and `status: DONE` only when end-to-end prerequisites relevant to acceptance are satisfied.
   - `COMPONENT_APPROVED`: the isolated component works, but integration blocked by unfinished dependencies. Leave final status not DONE.
   - `REWORK_REQUIRED`: inspectable defect or missing functionality. Record concise reproduction, file/line, owner and required fix. Return to implementing agent.
   - `BLOCKED`: cannot actually assess due to missing hardware, source/rights or inaccessible evidence. Describe the exact blocker, without inventing PASS.
6. In the reviewed Quest, append reviewer ID, UTC time, reviewed Git SHA, real evidence, decision and next action. Update using the current file blob SHA (compare-and-swap). A reviewer may update the Quest metadata but **must not modify the implementer's owned code** unless assigned a separate fix Quest.
7. At the next scheduled cycle, reassess new evidence and rework. Do not repeatedly approve the same unchanged commit as new work. Old decisions remain available as an audit trail.

## Acceptance contract for this standing Quest

- New review queue produced from actual `quests/v1/` metadata and real Git state.
- Each reviewed Quest cites its original criteria, inspected paths and commit.
- The review decision is authored by someone **other than** the implementing agent.
- No automatic `DONE` without code/output verification, and no invented Windows/device test or NASA source.
- Re-evaluate on subsequent cycles when file/content/commit changes; issue report captures what has changed.
- Publication of a queue report alone is **not** independent agent review.

## Scheduling and actual execution

`.github/workflows/quest-review-15m.yml` uses `*/15 * * * *` to generate and publish a **mechanical acceptance queue**. GitHub scheduled runs can start late, be throttled or fail. **GitHub Actions does not itself summon a separate AI agent.** A distinct live Codex/reviewer service must be connected to read the queue and carry out steps 1–7; without that service, record `REVIEW_PENDING` rather than claiming a human/AI review occurred.

The workflow updates a **single standing GitHub Issue** when the repository permits issue writing and uploads the newest report as an Actions artifact. The agent reviewing Quests must use current GitHub HEAD, not the issue text alone.
