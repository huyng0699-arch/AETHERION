# ASTRA symptom vocabulary — provenance and use restrictions

The user explicitly authorized importing this **self-authored legacy symptom vocabulary** from `huyng0699-arch/Nasa-/v2/data/phan-tang-hien-tai.json` to AETHERION on 14 November 2026. Source Git blob: `f76580a14166499433cea7f93cbb89f7db62ec17`. Destination SHA matches source exactly; the 819 entries have not been rewritten or silently reclassified.

- **819 Vietnamese symptom labels**, 826 original ID-to-label links; existing baseline group counts: emergency 41, urgent 125, routine 653. Those tiers are **unreviewed original metadata, NOT clinically validated triage**.
- Each entry preserves its exact name, aliases, routes, original IDs, tier and review state.
- The source metadata contains `clinical_validation_completed=false`; this is a searchable terminology index, not automatic diagnostic or treatment authority.
- AETHERION may reuse the vocabulary for search and adaptive questioning but never automatically use its legacy tier as a final clinical severity decision.
- Source is explicitly user-authorized symptom data. This exception **does not authorize importing legacy ASTRA backend code, disease articles, medical treatments or application UI**.
- Use `apps/server/src/aetherion_server/knowledge_catalog.py` and the AETHERION HTTP API rather than reactivating the former ASTRA application.

**License/credit:** owned content transferred with owner's explicit consent. Do not attribute it to NASA; NASA original CliFF content remains a separate scientific library.


## Additive English lookup overlay (2026-11-14)

- `label_aliases_en.json` provides **51 initial English search/display drafts** linked to the exact original Vietnamese labels and stable IDs. These represent **93 distinct English search terms** including synonyms. The original 819-entry `ASTRA_819_REFERENCE.json` was not edited.
- The translation layer declares `translation_status=UNREVIEWED_TERMINOLOGY`. It is **not** a clinical terminology approval, diagnostic code mapping, or triage escalation rule. The remaining 768 source labels have **no English translations in this overlay**; do not invent missing entries or mark 819/819 bilingual.
- The server `knowledge_catalog.py` checks the original Git blob SHA and each original ID/name before serving the supplemental labels. Unmatched/outdated translations are ignored; source names remain authoritative.
- In the native English interview, a translated display label appears **alongside** its original Vietnamese term. The selected clinical vocabulary sent to the API remains the canonical original term and ID association. Optional structured questions are not diagnoses; escalation requires explicitly reported warning signs, never legacy tiers.
- Run `python scripts/audit_bilingual.py --json` to audit matching IDs, alias collisions, catalog keys and provenance. Real Windows interaction verification and independent clinical terminology review are still required.
