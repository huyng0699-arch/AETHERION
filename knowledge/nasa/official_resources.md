# NASA Official Data Resources — Provenance Inspection (Q-0107)

- **Retrieved (UTC):** `2026-11-14T03:48:00Z`
- **Machine-Readable Artifact:** `knowledge/nasa/official_resources.json` (SHA-256: `f3590c5c16d4e248680bce12d4beb84591f6e08e90e914042ce7a4b496f0df0e`)
- **Safety Boundary:** Every resource below is historical, experimental, or reference research data — **never** live crew telemetry or clinical diagnosis.

## Verified NASA Resources

| Resource ID | Name | Source URL | Access Model | Verification Status |
| --- | --- | --- | --- | --- |
| `nasa-osdr` | NASA Open Science Data Repository (OSDR) | https://osdr.nasa.gov/ | `PUBLIC_OPEN_ACCESS` | `VERIFIED_OFFICIAL_SOURCE` |
| `nasa-nlsp` | NASA Life Sciences Portal (NLSP) | https://www.nasa.gov/hrp/nlsp/ | `PARTIAL_RESTRICTED_LSAH` | `VERIFIED_OFFICIAL_SOURCE` |
| `nasa-hrp-hazards` | NASA HRP — Five Hazards of Human Spaceflight | https://www.nasa.gov/hrp/ | `PUBLIC_OPEN_ACCESS` | `VERIFIED_OFFICIAL_SOURCE` |
| `nasa-imm-cliff-119` | NASA IMM — CliFF 119 (2023) | https://www.nasa.gov/integrated-medical-model-documentation/ | `LINKED_NOT_IMPORTED` | `LINKED_ONLY_UNIMPORTED` |

## Key Provenance Notes

1. **OSDR (`nasa-osdr`)** unifies GeneLab (omics), Ames Life Sciences Data Archive (ALSDA: physiological, phenotypic, bioimaging, behavioral, hardware, and environmental telemetry), NBISC, and radiation tools (Environmental Data Application, RadLab). Example verified studies: `OSD-599`, `OSD-635`, `OSD-431`, `OSD-919`. Detailed dataset/unit selection is tracked in `Q-0109`.
2. **NLSP (`nasa-nlsp`)** provides access to human research investigations dating back to 1961 (LSDA) and references the Lifetime Surveillance of Astronaut Health (LSAH) program, which is restricted to authorized NASA affiliates.
3. **IMM CliFF 119 (`nasa-imm-cliff-119`)** remains `LINKED_ONLY_UNIMPORTED` until the direct NASA PDF importer (`scripts/fetch_nasa_cliff_119.py`) completes and verifies all 119 SHA-256 hashes.
