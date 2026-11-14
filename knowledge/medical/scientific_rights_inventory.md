# Scientific Rights Inventory for Encyclopedia Articles (Q-0139)

This inventory tracks reuse rights across four explicit dimensions (**abstracts**, **full text**, **figures**, and **modifications**) for medical and NASA scientific sources used or referenced by AETHERION.

## Policy Rules
- AETHERION source code is licensed under `Apache-2.0`; **scientific sources and datasets are never relicensed under `Apache-2.0`**.
- Unimported or unverified sources (`NOT_IMPORTED`, `NO_DATA`, `UNVERIFIED`) must keep `full_text_display_allowed = false` and `figure_display_allowed = false`.
- Even U.S. Government works (17 U.S.C. § 105) can contain third-party copyrighted figures or citations that require separate clearance.

## Current Inventory Summary

| Source ID | Import Status | Abstracts | Full Text | Figures | Modifications |
| --- | --- | --- | --- | --- | --- |
| `nasa-imm-cliff-119-2023` | `NOT_IMPORTED` (0/119) | `UNVERIFIED_PENDING_LICENSE_CHECK` | `UNVERIFIED_PENDING_LICENSE_CHECK` | `UNVERIFIED_PENDING_LICENSE_CHECK` | `UNVERIFIED_PENDING_LICENSE_CHECK` |
| `nasa-osdr-open-metadata` | `VERIFIED_METADATA_ONLY` | `ALLOWED_WITH_ATTRIBUTION` | `LINK_OUT_ONLY` | `UNVERIFIED_PENDING_LICENSE_CHECK` | `ALLOWED_WITH_ATTRIBUTION` |
| `nasa-hrp-evidence-reports` | `LINKED_REFERENCE_ONLY` | `ALLOWED_WITH_ATTRIBUTION` | `LINK_OUT_ONLY` | `RESTRICTED_BY_THIRD_PARTY_COPYRIGHT` | `NO_DERIVATIVES` |
| `third-party-clinical-journals` | `POLICY_TEMPLATE` | `UNVERIFIED_PENDING_LICENSE_CHECK` | `LINK_OUT_ONLY` | `PROHIBITED` | `PROHIBITED` |

## Observed Gaps
- `0/119` CliFF PDFs are present locally; per-document figure and citation rights cannot be cleared until the original NASA PDFs are downloaded and audited.
