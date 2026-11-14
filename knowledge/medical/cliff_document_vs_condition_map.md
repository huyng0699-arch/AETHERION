# CliFF Source Documents vs. Condition Catalog Mapping (Q-0137)

**Updated (UTC):** `2026-11-14T03:57:30Z`  
**Source Documents State:** `NO_DATA` (`0 / 119` verified local NASA CliFF PDFs)  
**Condition Catalog State:** `NO_DATA` (`0` populated encyclopedia entries)

## Why Documents and Conditions Are Separated

1. **NASA CliFF 119 Documents** (`knowledge/nasa/cliff_119_2023/`) are primary NASA Integrated Medical Model (IMM) clinical flight findings and risk-planning PDFs (`2023` exploration list vs. `100`-condition LEO baseline).
2. **AETHERION Condition Catalog** (`knowledge/medical/`) is the structured, searchable encyclopedia schema. A raw PDF index entry is **not** an encyclopedia article, and an unverified legacy count from ASTRA is **never** accepted.
3. **Strict Gating Rule:** No condition entry in `entries` may be marked `READY` unless its underlying source document is locally present, SHA-256 verified in `manifest.json`, and cleared for reuse (`require_verified_source_sha256_for_ready: true`).
