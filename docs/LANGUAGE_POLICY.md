# AETHERION language policy — Vietnamese + English

**Effective 2026-11-14.** AETHERION is a bilingual native product, not a Vietnamese-only application. This requirement covers Desktop, Server Admin and planned companion clients. It supersedes earlier "thuần Việt" instructions. See root `AGENTS.md`.

## Three distinct types of text

| Category | Current evidence | Rule |
|---|---|---|
| User interface | Many strings in `apps/desktop/src/aetherion_desktop/main.py` and `portal.py` are Vietnamese literals | All labels/actions/help/warnings need `vi` and `en` catalog entries and a visible persisted switch |
| NASA science | `knowledge/nasa/cliff_119_2023/records/CLIFF-001.json` and `CLIFF-002.json` include English page-anchored original text | Preserve original English; translated text must be a separate derivative with source-language, reviewer and original page/source links |
| Symptom reference | `knowledge/symptoms/ASTRA_819_REFERENCE.json` uses Vietnamese labels and provisional triage explanations | Preserve `name`, `ids`, `tier`, `routes`; add optional independently reviewed `labels.vi`/`labels.en` later; do not claim English translations are medically validated |

Machine JSON identifiers, API status enums, hashes, source URLs, metadata, units and scientific citations are **not** natural-language UI and must never be translated in place. Data provenance and language coverage are separate concerns.

## Agent implementation contract

1. Supported locale codes: `vi` and `en`; preserve a user-selected locale between sessions using Qt `QSettings`. Switching languages may not change API state or clinical data.
2. Maintain matching semantic key catalogs at `apps/desktop/src/aetherion_desktop/i18n/vi.json` and `en.json`; ensure any new user-facing string has both. Keep navigation actions and source/model IDs independent of translated display text.
3. Translate only the UI chrome of a scientific document reader. Show the original NASA document unmodified in either app locale; provide clearly labelled translated versions only when independently produced and reviewed.
4. Medical terminology and medical advice require source/clinical review in **each language**. A missing translation must be surfaced as missing/unreviewed; do not auto-generate a misleading diagnosis or dosage. Draft search-only English aliases may link to an unchanged source ID with a prominent UNREVIEWED label. Any clinical decision, urgency or treatment logic must not rely on a draft translation; it requires separate review.
5. **Implementation progress (14 Nov 2026):** Desktop Portal and top-level shell, Mission Control, Personal Health, NASA Explore, offline CliFF catalog and article reader now have VI/EN code paths using the same catalogs. UI copy is localized while scientific source content is not rewritten. The localization layer covers dynamic status/error labels and provenance warnings, not just static headings. Native Windows visual/interaction verification and independent acceptance are still outstanding; do not mark full bilingual QA PASS yet.
6. Run the focused read-only `python scripts/audit_bilingual.py` for catalog/key/source-language consistency when needed. Do not add 119 test suites for medical translation or translate original PDF-derived JSON. All new screens (including Server Admin, mobile/watch) must adopt the shared locale contract.
7. Do not rewrite a verified English original to comply with a Vietnamese-language instruction, and do not rewrite the original Vietnamese symptom reference to comply with an English-language instruction. Additive, versioned translations only.

## Snapshot of JSON data checked

As observed on `main` on 2026-11-14, repository-owned JSON files include 116 `knowledge/nasa/cliff_119_2023/records/*.json`, 119 `qa/*.json`, 102 image provenance `media/**/*.json`, the Vietnamese 819-symptom reference, English NASA challenge/resource metadata and technical `packages/contracts/*.json`. This is a **language classification**, not certification that all source PDF files are locally downloaded, all clinical translations reviewed, or every document verified. Avoid declaring either "all JSON is Vietnamese" or "all JSON is English".

## English symptom search overlay — limited coverage

AETHERION now carries `knowledge/symptoms/label_aliases_en.json`, with 51 source-ID-checked English display/search translations (93 distinct English terms). The current Desktop and Server symptom search can match these English aliases and show English plus original Vietnamese labels without rewriting the 819-source JSON. **Only 51 of 819 original labels have draft translations; zero have been claimed clinically reviewed.** The remaining source labels remain in original Vietnamese pending terminology work. The original source Git blob, source IDs and original risk metadata are untouched. The focused `scripts/audit_bilingual.py` checks source identity and labels without fabricating medical validation.
