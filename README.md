# AETHERION
### One Health. One Humanity. Beyond Earth.

**AETHERION** is an open-source, offline-oriented health intelligence platform envisioned for people on Earth and future crews operating far from Earth. It begins as **Team TRUY TINH's independent entry** for **NASA Space Apps Challenge 2026**, addressing **[Create Health Monitoring Software for Astronauts on Space Missions](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)**.

> **Mission:** Make understandable, responsible, evidence-based health information accessible to individuals and crews, even when connectivity is unreliable.
>
> **Vision 2050:** Explore how the same foundations could evolve from a public-facing health companion on Earth into an autonomous crew-health platform for future deep-space and Mars expeditions. **2050 is our design horizon, not a confirmed NASA mission date.**

This is **an independent participant project**, not a NASA product, endorsement, flight-ready system, certified medical device, or validated diagnostic system.

## The problem

Long-duration missions combine altered gravity, radiation, isolation, distance from Earth and constrained living environments. Crew members need to see what has been measured, understand changes over time, review trustworthy contextual knowledge, decide when to seek help and document follow-up. On Earth, people face related challenges: fragmented health data, unequal access to intelligible information and weak continuity between self-monitoring and professional care.

## The proposed approach: GATHER → EVALUATE → ACT → RECHECK

1. **GATHER:** Collect health observations with explicit subject, source, timestamp, unit and quality.
2. **EVALUATE:** Show trends and uncertainty; contextualize data against evidence; do not infer health from missing measurements.
3. **ACT:** Present source-linked educational recommendations, care workflows and routes to human assistance. Never substitute an unvalidated rule or AI output for professional judgment.
4. **RECHECK:** Record actions and follow-up measurements to support continuity.

## System architecture

```text
                  AETHERION SERVER
        Local HTTP API | health records | future AI adapters
                  /        |        \
         Windows Desktop   Mobile   Wearable
             (starter)   (planned) (planned)
                   |
     Scientific reference library and provenance
```

The server is the single authority for observation data. Clients are separate applications; an optional local AI module and a cloud AI interface are future extensions, not claims of functioning AI. Offline capability applies only where components and licensed knowledge have actually been installed and tested.

## Current implementation status (14 November 2026)

| Component | Current state |
| --- | --- |
| Repository structure, architecture and installation documentation | Initial scaffold |
| Local Python HTTP service, API health endpoint | Initial runnable implementation; Windows operation not yet independently verified |
| SQLite observation storage and API routes | Initial local-only implementation; not clinically validated |
| Native Windows desktop (PySide6) | Initial interface shell with navigation and API connectivity check |
| Medical response engine, actionable clinical guidance | Planned; **not implemented** |
| NASA datasets and 119-condition medical encyclopedia | Source registry started; **no verified complete dataset is bundled** |
| Mobile application, Wear OS, physical sensors, true 3D anatomy, local/cloud AI | Planned; **not implemented** |
| Windows installer or packaged EXE | Planned; **not available yet** |

**Do not use this prototype with real patient information.** The development API currently has no authentication or production-grade data protection. It binds to localhost by default. No invented sensor readings, fake live telemetry or unsupported health verdicts are displayed.

## Install and launch on Windows

**Requirements:** Windows 10/11, Git and Python 3.11 (including the `py` launcher).

```powershell
git clone https://github.com/huyng0699-arch/AETHERION.git
cd AETHERION
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Then open **two PowerShell windows**, both inside the repository:

```powershell
.\scripts\start_server.ps1
```

```powershell
.\scripts\start_desktop.ps1
```

The local API runs at `http://127.0.0.1:8765`; interactive API documentation is at `http://127.0.0.1:8765/docs`. The desktop is a native Qt window, **not a browser wrapper**. The interface opens to its main dashboard.

See **[full Windows installation and troubleshooting](docs/INSTALL_WINDOWS.md)**, [architecture](docs/ARCHITECTURE.md), [product definition](docs/PRODUCT_SPEC.md), [scientific and safety boundaries](docs/SCIENCE_AND_SAFETY.md), [roadmap](docs/ROADMAP_2050.md) and [2026 submission plan](submission/README.md).

## Repository map

| Path | Responsibility |
| --- | --- |
| `apps/server/` | One local-first HTTP backend, data ingestion and persistence |
| `apps/desktop/` | Independent native Windows client |
| `apps/mobile/`, `apps/watch/` | Planned separate companion applications |
| `packages/contracts/` | Shared API conventions and planned machine-readable schemas |
| `knowledge/nasa/`, `knowledge/medical/` | Curated scientific references, provenance, licensed imports |
| `docs/` | Architecture, installation, validation and long-term vision |
| `submission/` | Submission narrative, citations, demo evidence and outstanding requirements |
| `scripts/`, `tests/` | Local setup, launches and verification |

## Long-term direction: Earth to Mars 2050

**Earth first:** a multilingual, accessible personal health companion supporting preventive learning, device interoperability and ethical privacy safeguards. **Remote care settings:** resilient local deployments for isolated communities, expeditions and disaster response. **Beyond Earth:** a crew-oriented system built for weak connectivity, resource constraints, behavioral health support and evidence traceability. Flight integration would require extensive clinical, security, human-factors and spaceflight qualification that does not yet exist.

Read [ROADMAP_2050](docs/ROADMAP_2050.md) for explicit maturity gates rather than promises of completed capability.

## Open-source reference source trees (from ASTRA's design review)

The directory **[Các mã nguồn mở tham khảo](Các%20m%C3%A3%20ngu%E1%BB%93n%20m%E1%BB%9F%20tham%20kh%E1%BA%A3o/README.md)** contains immutable third-party research snapshots, not code currently loaded into the AETHERION runtime. **PyVistaQt is already present in full (51/51 original Git blobs verified).** VisPy, PyQtGraph, NASA Open MCT, napari and 3D Slicer are pinned for full source import, **not yet confirmed as copied** because the GitHub Actions import run failed. See [source lock](Các%20m%C3%A3%20ngu%E1%BB%93n%20m%E1%BB%9F%20tham%20kh%E1%BA%A3o/SOURCES.lock.json) and [import workflow](.github/workflows/vendor_reference_sources.yml). Source presence is not evidence of a working Qt integration.

## Scientific integrity, licensing and credits

- This project is not affiliated with or endorsed by NASA.
- NASA references are credited and linked; NASA content is not automatically covered by this repository's software license.
- Project-authored code is under [Apache License 2.0](LICENSE); third-party materials retain their own licenses and attribution requirements.
- Inspect [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [submission/REFERENCES.md](submission/REFERENCES.md) before redistribution or judging.
- To meet NASA Space Apps submission requirements, complete the official **Project tab** on the team page; GitHub alone is not a submission.

**Team:** TRUY TINH · **Event:** NASA Space Apps Challenge 2026 · **Category:** Human Exploration / Software.

© 2026 Nguyen Gia Huy and AETHERION contributors. See [NOTICE](NOTICE).
