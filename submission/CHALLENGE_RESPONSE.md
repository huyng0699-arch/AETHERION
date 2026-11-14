# AETHERION — NASA Space Apps 2026 Challenge Response (English)

**Team:** TRUY TINH  
**Project:** AETHERION  
**Challenge:** [Create Health Monitoring Software for Astronauts on Space Missions](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)  
**Repository Architecture:** Local-first Python FastAPI + SQLite server (`apps/server/src/aetherion_server/main.py`) paired with a native PySide6/Qt Windows desktop application (`apps/desktop/src/aetherion_desktop/main.py`).

---

## 1. Challenge Alignment: GATHER → EVALUATE → ACT → RECHECK

On long-duration missions beyond low Earth orbit, astronauts face five NASA Human Research Program (HRP) hazards—**space radiation, isolation and confinement, distance from Earth, altered gravity fields, and hostile closed environments**—while communication delays limit real-time ground flight-surgeon support. AETHERION structures astronaut health monitoring around a transparent, source-tracked four-stage loop:

1. **GATHER (Provenance-First Indicator Collection)**
   - Every observation in AETHERION is typed and bound to `subject_id`, `scope`, `metric`, `value`, `unit`, `observed_at`, `received_at`, `source_id`, `quality`, and `verification_state`.
   - Missing, stale, offline, denied, and unverified states (`NO_DATA`, `STALE`, `OFFLINE`, `DENIED`, `ERROR`, `UNVERIFIED`) are explicitly distinguished from healthy (`READY`) measurements. Silence or a missing sensor reading is **never** interpreted as unconsciousness or normal health.
   - **Implemented evidence:** SQLite observation persistence in `apps/server/src/aetherion_server/store.py` and server entrypoint in `apps/server/src/aetherion_server/main.py`.

2. **EVALUATE (Healthy-First Context & Scientific Traceability)**
   - A healthy crew member can inspect their `Today` / `Personal` status and `Mission Control` overview without being forced through a symptom-intake wizard.
   - Spaceflight hazard context is anchored to **verified NASA Open Science Data Repository (OSDR)** studies rather than fabricated vital signs. Our verified OSDR selection (`knowledge/nasa/osdr_datasets.json`) spans human longitudinal blood/serum/plasma cohorts (`OSD-575`, `OSD-569`, `OSD-530`), human iPSC-derived cardiomyocyte microgravity assays (`OSD-258`), and proton-irradiation neuro-epigenetic models (`OSD-374`), each carrying exact species, assay types, measurement units, DOIs, and license terms.
   - **Implemented evidence:** Official challenge capture (`knowledge/nasa/challenge_2026.json`) and verified OSDR catalog (`knowledge/nasa/osdr_datasets.json`).

3. **ACT (Human-in-the-Loop Agency & Offline Resilience)**
   - Deterministic safety rules and documented offline guidance operate independently of any optional AI gateway; if cloud or local AI is unavailable, core monitoring and human escalation workflows continue without degradation.
   - When an observation or user/witness report warrants attention, AETHERION supports structured incident logging and explicit human acknowledgement (`ACK`) rather than automated diagnosis or fictional emergency dispatch.

4. **RECHECK (Persisted Longitudinal Follow-Up)**
   - All observations, care events, and acknowledgements are persisted in SQLite across application restarts so crew members and flight surgeons (when telemetry syncs) can verify whether a trend resolved, persisted, or requires follow-up.

---

## 2. Scientific Honesty & Current Limitations

AETHERION strictly separates **verified implemented artifacts** from **in-progress or future work**:

- **Not NASA-Affiliated or Clinically Certified:** AETHERION is a hackathon software prototype. It is not flight-ready, not FDA/clinically cleared, and does not provide automated medical diagnosis or treatment.
- **Historical Research ≠ Live Telemetry:** NASA OSDR datasets (`OSD-575`, `OSD-569`, `OSD-530`, `OSD-258`, `OSD-374`) are historical/experimental research records used for scientific context and unit/assay grounding—never passed off as live astronaut vital signs.
- **CliFF 119 Originals Audit:** As recorded in `knowledge/nasa/cliff_119_2023/audit_status.json`, `0 / 119` NASA Integrated Medical Model CliFF PDFs are currently downloaded into this repository (`verification_state: NO_DATA`). AETHERION refuses to fabricate or substitute missing clinical documents.
- **Roadmap Separation:** Mobile (`apps/mobile/`), wearable (`apps/watch/`), and 2050 Earth/Mars expansion tracks are future architectural horizons, not current hackathon completion claims.
