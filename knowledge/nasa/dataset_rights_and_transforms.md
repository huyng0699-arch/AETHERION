# NASA Dataset Rights & Transformation Policy (Q-0110)

- **Recorded (UTC):** `2026-11-14T03:51:00Z`
- **Machine-Readable Artifact:** `knowledge/nasa/dataset_rights_and_transforms.json` (SHA-256: `fdbf14592cf9b0bc5a0d79cbed55cc7a514718649d13ba89f6c1538b2e83cc50`)

## Core Licensing & Transformation Rules

1. **No Automatic Relicensing:** AETHERION software code is licensed under `Apache-2.0`. Original NASA datasets and documents retain their own publisher terms (`relicensed_under_apache_2_0: false`).
2. **Provenance & Unit Preservation:** Every transformed record keeps `source_url`, `dataset_id`, `version`, original measurement units, and `is_live_telemetry=false`.
3. **Access Control Respect:** Controlled human files requiring OSDR Data Access Request (DAR) / IRB approval (e.g., `OSD-575`, `OSD-569` raw files) are never fetched or redistributed.
4. **Honest Unimported Status:** `NASA-IMM-CLIFF-119` remains `NOT_IMPORTED` until direct NASA PDFs and SHA-256 digests are verified.

## Dataset Summary

| Dataset ID | Version | License / Terms | Transform ID |
| --- | --- | --- | --- |
| `OSD-575` | `3` | CC0-1.0 (open tables); DAR/IRB for raw human files | `osdr-metadata-to-reference-v1` |
| `OSD-569` | `4` | CC0-1.0 (open summaries); DAR/IRB for raw genomics | `osdr-metadata-to-reference-v1` |
| `OSD-530` | `3` | NASA OSDR open science terms (de-identified) | `osdr-metadata-to-reference-v1` |
| `OSD-258` | `2` | NASA OSDR open science data | `osdr-metadata-to-reference-v1` |
| `OSD-374` | `1` | NASA OSDR open science data | `osdr-metadata-to-reference-v1` |
| `NASA-IMM-CLIFF-119` | `2023` | Original NASA documents (`NOT_IMPORTED`) | `cliff-119-direct-pdf-audit-v1` |
