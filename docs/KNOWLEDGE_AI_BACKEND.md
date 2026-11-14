# AETHERION Knowledge Search + Adaptive Interview — backend implementation

This feature is **AETHERION native backend code** in the single existing FastAPI server. It does not create a second backend, fork ASTRA UI, or replace the NASA medical articles.

## Data sources

- `knowledge/nasa/cliff_119_2023/records/CLIFF-???.json`: original article-derived structured content by the existing NASA ingest agents. **No data are rewritten.**
- `knowledge/symptoms/ASTRA_819_REFERENCE.json`: 819 symptom labels copied byte-for-byte from owner's earlier ASTRA repository with matching source SHA. The 41/125/653 legacy tier labels are **NOT clinically validated** and are not activated as diagnosis or triage.
- The content lookup is read-only and searches actual article text, headings, categories, and Vietnamese symptom names + aliases without requiring diacritics.

## HTTP routes

All routes live in **the existing AETHERION server process** at `/api/v1/knowledge/`.

| Route | Behavior |
| --- | --- |
| `GET status` | Count JSON articles, missing slots, vocabulary labels |
| `GET articles?query=...` | Search whole extracted text and return metadata, source, word counts |
| `GET articles/CLIFF-055` | Get full locally available sections, tables, citations, media metadata |
| `GET symptoms?query=...` | Search 819 Vietnamese labels, aliases and route groups |
| `GET interview/ai-status` | Report **configured**, not an unproven running model |
| `POST interview/next` | Stateless adaptive questions, no diagnosis; optionally asks a real LLM to select among approved question IDs |

## Optional *actual* AI inference (not a dummy response)

AI is **off by default**. It can call either local Ollama or a configured OpenAI-compatible chat model. The model selects the next structured question, and the server validates the returned ID against fixed allowed choices. The model cannot create a diagnosis, new safety rules, dosing or clinical orders.

Local:

```powershell
$env:AETHERION_INTERVIEW_AI_PROVIDER="ollama"
$env:AETHERION_INTERVIEW_AI_MODEL="your-installed-model-name"
# Install/run Ollama and pull that model separately; verify /api/v1/knowledge/interview/ai-status
```

Cloud (not default):

```powershell
$env:AETHERION_INTERVIEW_AI_PROVIDER="openai"
$env:AETHERION_INTERVIEW_AI_MODEL="your-supported-model-name"
$env:AETHERION_OPENAI_API_KEY="your-own-key"
```

**Each request** must set `use_ai=true`; for cloud, explicitly `allow_cloud=true`. The cloud path transmits recognized symptom labels and structured answers; **never send real patient information before a privacy/compliance assessment**. If AI is unavailable it reports `MODEL_UNAVAILABLE` and continues deterministic questioning instead of pretending model inference succeeded.

Example:
```json
{"symptoms":["đau ngực"],"answers":{},"use_ai":false}
```

The API returns an explicit next question and accepted answer choices; subsequent calls submit answers keyed by question ID. Critical flags rely on explicit witness/user-reported answers, not inferred physiology or legacy ASTRA tier. **No automated diagnosis or treatment is provided.**

## Important limitations and next integration

1. Existing native PySide6 `MedicalLibraryPage` uses a special full-text SQLite library file that is **not built yet**; the new searchable JSON backend works from article files independently. Wire its search into native Qt without modifying another agent's active `main.py` or `medical_library.py` lease.
2. Medical article images are currently returned as **metadata only**. Approved binary media needs separate audited read endpoint or offline SQLite importer; rights and SHA must be checked.
3. Server currently lists the article source's own verification *claim*, not independent PDF hash validation. Original PDF comparison and clinical review still separate gates.
4. RAG, embeddings, vector stores, tools, model fine-tuning and automated knowledge improvement are **future, versioned, human-reviewed** extensions, not working features. Never allow a self-modifying model to update safety rules or medical evidence without approval.
