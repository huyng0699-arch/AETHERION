# AETHERION — Scientific Limitations & Absent Integration Disclosures (Q-0262)

This document states the exact scientific, clinical, and hardware boundaries of **AETHERION** for the 2026 NASA Space Apps Challenge.

## 1. Non-Clinical & Non-Flight Status

- **Not Clinically Validated:** AETHERION is a hackathon software prototype, **not** an FDA-cleared medical device, clinical decision support system, or NASA flight-certified software.
- **No Autonomous Diagnosis or Treatment:** Health indicators, provenance labels, and `GATHER -> EVALUATE -> ACT -> RECHECK` workflows support structured human tracking only; they do not replace flight surgeons or clinical protocols.

## 2. Absent Device & Live Telemetry Integrations

- **No Live Flight / Biomedical Hardware Connected:** No real-time spacecraft telemetry bus, ISS/Artemis downlink, Wear OS watch client, or Android companion is connected in the current prototype.
- **Scenario F (Wearable) Blocked/Future:** Watch integration remains future/blocked until an independent Wear OS client exists and delivers signed, source-aware device events.
- **Explicit Missing-Data Semantics:** AETHERION distinguishes `READY`, `NO_DATA`, `STALE`, `OFFLINE`, `DENIED`, `ERROR`, and `UNVERIFIED`. Missing sensor data or user silence **never** implies unconsciousness or healthy status.

## 3. Dataset & Reference Library Limitations

- **NASA OSDR / NLSP Are Historical Research, Not Live Vitals:** Selected OSDR datasets (`OSD-575`, `OSD-569`, `OSD-530`, `OSD-258`, `OSD-374`) are historical human/model-organism studies; controlled raw human files requiring DAR/IRB are excluded.
- **NASA IMM CliFF 119 (2023) Not Imported:** `0/119` original NASA CliFF PDFs are currently present in the repository (`NOT_IMPORTED`, audited in `knowledge/nasa/cliff_119_status.json`).
- **2050 Roadmap Is Aspirational:** Long-term Earth/Mars 2050 tracks (`P3`) are design aspirations, not a NASA-confirmed mission schedule or current hackathon deliverables.
