# AETHERION — Backend modules, file ownership and integration map

## What is already committed

| Path | Responsibility | Actual status |
| --- | --- | --- |
| `knowledge/symptoms/ASTRA_819_REFERENCE.json` | Owner-imported exact 819 symptom labels, IDs and aliases | In repo, Git SHA verified; tiers unreviewed |
| `knowledge/nasa/cliff_119_2023/records/*.json` | NASA CliFF-derived article texts, tables, citations | Local JSON records exist; original PDF hashes not independently verified |
| `apps/server/src/aetherion_server/knowledge_catalog.py` | Read-only full-text and symptom search, article status | Code committed; runtime interaction not independently accepted |
| `apps/server/src/aetherion_server/knowledge_api.py` | FastAPI endpoints `/api/v1/knowledge/*` | Included in existing `create_app()` |
| `apps/server/src/aetherion_server/symptom_interview.py` | Structured question selection, local Ollama/cloud opt-in | Real adapter code; model connection not verified |
| `apps/desktop/src/aetherion_desktop/knowledge_browser.py` | Native Qt search result and scientific article view | Widget coded, **not yet wired to Portal** |
| `apps/desktop/src/aetherion_desktop/symptom_interview_page.py` | Native Qt symptom search and questionnaire | Widget coded, **not yet wired to Portal** |
| `apps/desktop/src/aetherion_desktop/atlas3d.py` | Optional native PyVistaQt mesh viewport | Adapter coded, **no approved anatomical mesh included** |
| `knowledge/anatomy/approved_models.json` | Copyright-checked mesh registry | Intentionally empty; not actual 3D atlas |
| `docs/KNOWLEDGE_AI_BACKEND.md` | Local setup, endpoints, privacy and limitations | Documentation |
| `docs/ATLAS_3D_REUSE.md` | Reuse library strategy; real asset license limits | Documentation |

## Ownership and roles

1. **Knowledge backend agent:** `knowledge_catalog.py`, `knowledge_api.py`, indexing and read-only docs.
2. **Native Qt UX agent:** `knowledge_browser.py`, `symptom_interview_page.py`, integrating with the current Portal owner; never edits two shells.
3. **Clinical vocabulary agent:** imports symptom synonyms and maintains provenance. Cannot activate legacy tier clinical decisions without review.
4. **AI interview agent:** structured state, local/provider API, constrained allowed question IDs; not permitted to change safety rules.
5. **Clinical/safety reviewer:** reviews time-critical red-flag logic, rights, personal information flow, and human escalation.
6. **Medical library agent:** imports sources into one offline SQLite, preserves full text/tables/figures/image BLOB rights.
7. **Atlas mesh/licensing agent:** selects genuine anatomy assets and records individual licenses; no commercial reuse of NC assets.
8. **Atlas desktop agent:** PyVistaQt QtInteractor + object/picking events, no fabricated anatomy assets.
9. **API/security agent:** verifies authentication and controlled cloud request, source approvals, request limits and logging.
10. **Windows build agent:** tests the packaged native Windows executable and installer, not every small Quest.
11. **Independent reviewer agent:** ensures target output matches the Quest, accepts actual UI artifacts and targeted security checks.

## Live wiring

- The **same server** owns HTTP routes. A second `uvicorn` app is forbidden.
- Desktop Qt pages should be attached to the **existing Portal** by the active owner of `apps/desktop/src/aetherion_desktop/main.py`. Do not overwrite Q-0437 or other active leases.
- Health observations remain in their existing authoritative SQLite store; scientific reference content is not personalized health telemetry.
- Mobile/watch will consume the same versioned API after separate authenticated implementation.
- For real 3D, Server owns model metadata, source and optional preprocessing; native Qt uses GPU for interactive geometry.

## Call examples

```text
GET  /api/v1/knowledge/status
GET  /api/v1/knowledge/articles?query=fracture
GET  /api/v1/knowledge/articles/CLIFF-055
GET  /api/v1/knowledge/symptoms?query=dau%20nguc
GET  /api/v1/knowledge/interview/ai-status
POST /api/v1/knowledge/interview/next
```

Example question payload: `{"symptoms":["đau ngực"],"answers":{},"use_ai":false}`. For cloud AI calls, user must additionally opt in with `"allow_cloud":true` and the server admin must have configured the API provider. Do not record real patient information in this unvalidated prototype.
