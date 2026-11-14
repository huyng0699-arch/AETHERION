# AETHERION — Future retrieval, RAG and governed AI evolution

**Status:** Architecture and research roadmap. **Not implemented, not clinically approved.** The current implementation is searchable read-only JSON, an 819-label symptom vocabulary, structured interview questions and optional real local/cloud LLM selection. Those are distinct from RAG.

## Layer 0 — Source-of-truth library (existing/in progress)

- Original NASA CliFF-derived JSON files under `knowledge/nasa/cliff_119_2023/records/`.
- Proprietor-authorized ASTRA `knowledge/symptoms/ASTRA_819_REFERENCE.json` vocabulary, immutable Git SHA with clinically **unreviewed legacy tiers**.
- Local scientific metadata (original URL, edition, original-page anchor, hash, author, rights) and approved media only.
- Search API: `apps/server/src/aetherion_server/knowledge_catalog.py`.
- One separate AETHERION server, one native Qt desktop. No second standalone AI application.

## Layer 1 — Hybrid information retrieval (future, P2)

Create reusable internal data contracts:

```text
knowledge_document
  document_id · publisher · original_url · source_sha256 · license · review_state
  └── revision_id (immutable)
       └── chunk_id · page_start · page_end · source_anchor · text_sha256
            ├── SQLite FTS5 lexical index
            └── optional licensed embedding/vector index
                 └── hybrid re-ranking with citation and uncertainty
```

Do NOT use RAG to write over the source text. Retrieval generates only source-backed answer context, with page-level links. Missing sources yield `NO_EVIDENCE`, not a hallucinated conclusion. Permission-aware retrieval keeps user-specific notes isolated from public NASA documents.

### Proposed files

| File/folder | Role | Maturity |
|---|---|---|
| `packages/medical_library/retrieval/document_contract.py` | Immutable document and chunk schema | Planned |
| `packages/medical_library/retrieval/chunker.py` | Source-page boundaries, tables, captions | Planned |
| `packages/medical_library/retrieval/fts.py` | SQLite FTS5 lexical baseline | Planned |
| `packages/medical_library/retrieval/embeddings.py` | Optional locally served embeddings with version | Planned |
| `packages/medical_library/retrieval/hybrid.py` | Query blend, citation verification and fail-closed | Planned |
| `apps/server/src/aetherion_server/ai/provider_registry.py` | Explicit local/cloud API, model provenance and readiness | Planned |
| `apps/server/src/aetherion_server/ai/clinical_guard.py` | Approved rule gate, cannot be overridden by AI text | Planned |
| `apps/server/src/aetherion_server/ai/evaluation.py` | Dataset of benign/adversarial tasks and traced outcomes | Planned |

## Layer 2 — Adaptive dialogue (initial code now, further work planned)

The interview should: identify the user's own symptom wording, ask timing/progression/context questions, check explicit red flags, distinguish unknown from no, collect source-backed available measurements when consented and end with a **non-diagnostic** visit summary or hand-off. The optional LLM may choose an allowed question ID; it does **not** supply new medication, a disease probability or a final triage class from unreviewed legacy labels.

Long-term: evaluate multiple model choices behind a stable adapter, track actual accuracy for question-selection, unsupported citations, privacy leaks and false negative red flags. Model calls may be disabled without breaking deterministic care or emergency escalation.

## Layer 3 — Feedback-guided AI improvement (P3, NEVER autonomous clinical self-modification)

The phrase “AI tự tiến hóa” means a **controlled development cycle**, not unsupervised self-updating diagnosis:

1. Acquire voluntary feedback and permission; remove personal identifiers.
2. Review factual corrections with clinicians and original scientific sources; record disagreements.
3. Version training/retrieval datasets, licenses, prompts and model weights.
4. Train or fine-tune offline in a sandbox; maintain a holdout set and evaluation audit.
5. Assess bias, calibration, false negative/positive risk, hallucinations and security.
6. A **different authorized reviewer** approves the version; produce a signed build.
7. Shadow-run, monitor, then deploy with rollback and audit logs.

**Hard prohibition:** No autonomous rewriting of clinical emergency rules, medications, diagnosis thresholds, evidence grades, permissions, or treatment pathways; no training on real personal health data without valid consent/legal basis. The server must support human veto, update history and immediate disable/rollback.

## Acceptance

Only advertise RAG when actual chunk retrieval, citation coverage and offline reproducibility work. Only advertise “self-learning” when a consented feedback-to-reviewed-deployment loop is functioning and independently validated. The 2026 submission should not claim either.
