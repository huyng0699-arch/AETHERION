# AETHERION — Defects and unfinished integration triage, 14 Nov 2026

This document is an actionable inventory. Refer to each individual new Quest in `quests/INDEX_LIBRARY_AI_BUGFIX_20261114.md` and `quests/INDEX_ATLAS_UX_DATA_FIXES_20261114.md`. These are observed defects and unresolved product gaps, **not 15 distinct GitHub CI runtime errors**.

| Defect/gap | Current finding | Responsible role | Next action |
| --- | --- | --- | --- |
| CI runners | GitHub Actions repeatedly fail in ~1–2 seconds with empty runner_name/steps and 404 redirected logs | ci-debug | Determine Actions permission/billing/runner activation, separate infrastructure failure from tests |
| Request validation 422 | Pydantic ValueError ctx was not JSON serializable | server-debug | New code uses jsonable_encoder; run one invalid-request smoke, no full test suite |
| Engineering observation smoke | GET excluded non-live test data by default | server-debug | Explicit `include_non_live=true` added to smoke script; verify once |
| CI test runner mismatch | Existing unittest discovery includes pytest-dependent modules | ci-maintainer | Change CI dependency/runner only when Actions runner works; limit triggers |
| Quest board | Hardcoded 435 and multiline YAML parsing errors | quest-tooling | Preserve active Q-0241 path claim; update after its owner resolves |
| Native Portal & search | Knowledge/Symptom widgets are modules, not yet mounted | desktop-ux | Q-0440 and Q-0442; coordinate Q-0437 Portal owner |
| NASA source document coverage | 116 structured records at last detailed review, missing 019,021,119; zero verified original PDF archives | nasa-source | Resolve missing records and original source archive without declaring existing JSON invalid |
| Offline medical SQLite | No complete locally verified final file `AETHERION_NASA_CLIFF_119.sqlite` yet | offline-library | Ingest actual JSON and approved media with no content truncation |
| External media rights | Sepsis JPEG end marker failed in last documented audit; image rights must be file-level | media-quality | Verify actual current media and repair only defective bytes |
| 3D Anatomy | PyVistaQt source and optional QtInteractor adapter exist, but no licensed mesh installed | anatomy-assets | Import approved model(s), add server metadata and prove genuine picking |
| UI quality | Multiple placeholder tabs, inconsistent appearance, scope/identity handoffs unfinished | native-ux | Preserve one shell, make controls truly work and visually unify |
| Windows executable | Python module startup ≠ genuine Windows EXE, packaging not yet verified | windows-packaging | One dedicated cold-start acceptance |
| AI inference | Optional model adapters are coded; no local Ollama/OpenAI model verified connected | ai-runtime | Configure model, verify one response, prevent unconsented cloud use |
| Clinical AI rules | Legacy symptom severity labels are not clinically reviewed | clinical-review | Validate evidence, false negative harms, human escalation and versioned review before using risk classes |
| Future RAG/evolution | No embeddings, reviewed feedback-to-release system or autonomous safe training pipeline | ai-governance | Follow `docs/RAG_EVOLUTION.md` phased work; never claim deployed |

**Process:** Direct code first; only focused checks where failures matter. No duplicate tests for each Quest and no invented PASS.
