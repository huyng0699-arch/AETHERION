# ASTRA symptom vocabulary — provenance and use restrictions

The user explicitly authorized importing this **self-authored legacy symptom vocabulary** from `huyng0699-arch/Nasa-/v2/data/phan-tang-hien-tai.json` to AETHERION on 14 November 2026. Source Git blob: `f76580a14166499433cea7f93cbb89f7db62ec17`. Destination SHA matches source exactly; the 819 entries have not been rewritten or silently reclassified.

- **819 Vietnamese symptom labels**, 826 original ID-to-label links; existing baseline group counts: emergency 41, urgent 125, routine 653. Those tiers are **unreviewed original metadata, NOT clinically validated triage**.
- Each entry preserves its exact name, aliases, routes, original IDs, tier and review state.
- The source metadata contains `clinical_validation_completed=false`; this is a searchable terminology index, not automatic diagnostic or treatment authority.
- AETHERION may reuse the vocabulary for search and adaptive questioning but never automatically use its legacy tier as a final clinical severity decision.
- Source is explicitly user-authorized symptom data. This exception **does not authorize importing legacy ASTRA backend code, disease articles, medical treatments or application UI**.
- Use `apps/server/src/aetherion_server/knowledge_catalog.py` and the AETHERION HTTP API rather than reactivating the former ASTRA application.

**License/credit:** owned content transferred with owner's explicit consent. Do not attribute it to NASA; NASA original CliFF content remains a separate scientific library.

