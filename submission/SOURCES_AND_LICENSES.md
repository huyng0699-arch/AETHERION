# AETHERION — Compiled Sources, Licenses, and Attribution Notice (Q-0264)

This document compiles the verified license, `NOTICE`, third-party dependency, and NASA data attribution inventory for Team **TRUY TINH**'s NASA Space Apps 2026 submission.

## 1. Repository License & Legal Notices

| Artifact | Purpose | SHA-256 |
| --- | --- | --- |
| `LICENSE` | Apache License, Version 2.0 (covers AETHERION original software only) | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| `NOTICE` | Copyright 2026 Nguyen Gia Huy and AETHERION contributors; Team TRUY TINH; non-endorsement disclaimer | `1dbcf1a31ef7de12b02f14f26232ba499f2e9ba5db75332ccfdedde37857f533` |
| `THIRD_PARTY_NOTICES.md` | Third-party runtime/library license inventory (Python PSF, FastAPI MIT, Uvicorn BSD-3-Clause, Pydantic MIT, PySide6 LGPLv3/GPLv3/commercial) | `51340c054a6b870580cbe0521ce8481b208b9826177be5947874ab088c516c30` |

**Non-endorsement & non-relicensing notice:**
- NASA is **not** a sponsor, partner, certifier, or endorser of AETHERION.
- Original NASA documents, datasets, and third-party libraries retain their own licenses/terms and are **not** relicensed under Apache-2.0.

## 2. Verified NASA & Scientific Data Attribution

Machine-verified provenance registry: `knowledge/nasa/source_registry.json` (SHA-256: `2f5d703dfc5c3fd5d97a7a3dd068c8c9f1b60e885a578662ad76dac6dbc0e068`).

1. **NASA Space Apps 2026 Challenge — Create Health Monitoring Software for Astronauts on Space Missions**
   - URL: https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/
   - Artifact: `knowledge/nasa/challenge_2026.json` (`VERIFIED_OFFICIAL_SOURCE`)
2. **NASA Open Science Data Repository (OSDR)**
   - URL: https://osdr.nasa.gov/
   - Selected Studies (`knowledge/nasa/osdr_datasets.json`): `OSD-575` (v3, DOI `10.26030/mc5d-p710`, CC0-1.0 open metadata/tables; controlled raw human files require DAR/IRB), `OSD-569` (v4), `OSD-530` (v3), `OSD-258` (v2), `OSD-374` (v1).
   - Rights & Transformation Policy: `knowledge/nasa/dataset_rights_and_transforms.json`.
3. **NASA Life Sciences Portal (NLSP) & Human Research Program (HRP)**
   - URLs: https://www.nasa.gov/hrp/nlsp/ , https://www.nasa.gov/hrp/
   - Artifact: `knowledge/nasa/official_resources.json` (`VERIFIED_OFFICIAL_SOURCE`; LSAH human surveillance remains restricted).
4. **NASA Integrated Medical Model (IMM) — CliFF 119 (2023)**
   - URL: https://www.nasa.gov/integrated-medical-model-documentation/
   - Status: `NOT_IMPORTED` (`0/119` verified PDFs in repository; audited in `knowledge/nasa/cliff_119_status.json` and `knowledge/medical/cliff_119_audit.json`).
