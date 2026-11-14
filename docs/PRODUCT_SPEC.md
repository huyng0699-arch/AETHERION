# AETHERION — product specification

**Project:** Independent Team TRUY TINH entry, NASA Space Apps Challenge 2026  
**Challenge:** [Create Health Monitoring Software for Astronauts on Space Missions](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)  
**Design horizon:** Earth-first public-health usability; eventual Mars mission support around 2050 as a long-range ambition.

## Owner-corrected UX and architecture

[**Canonical detailed product design**](DESIGN_2026_11_14.md) supersedes older Mission-first entry. **Desktop and Mobile first show a five-card Portal**: Sức khỏe của tôi; Theo dõi & ECG; Hỏi AI về sức khỏe; Khám phá khoa học; Phi hành đoàn for authorized operators or Hành trình của tôi for crew. Windows keeps a top horizontal menu; no permanent left/right sidebars. Aetherion Server has **a separate admin GUI** including local AI selection and pasted Cloud API key with test/secure storage, network/relay, people/permissions, library, device, backup. Ambient galaxy/orbit/rain/water animations are layered backgrounds blended beneath the theme, customizable by font/color/motion; not floating media panels. Local-first LAN/hotspot; optional Telegram Earth relay only, onboard vessel server is a research target. AI symptom vocab serves AI, not the human homepage; NASA originals must be distinguished from clinical AI library and human encyclopedia. This paragraph specifies the **target**, not current implementation.

## Core user journeys

### 0. Portal / First launch
On startup render Portal and five functioning routes, **not Mission Control or a metrics table**. Server connection/login needed for protected data may be requested after showing the Portal. Top navigation remains visible above selected subviews. No phantom data or decorative dead controls.


### 1. Mission Control
After choosing Mission Control from Portal/menu, a crew operator sees authorized people, availability of data, data timestamps, trends, reported issues and source status. A click opens the relevant person. The main application content appears immediately beneath a persistent top menu.

### 2. Personal Health
A healthy user can open the app without entering symptoms. They see available measurements and missing-data states, sleep/activity/wellbeing context where actually collected, and a transparent longitudinal record.

### 3. Explore Space Health
Explain radiation, isolation/confinement, distance from Earth, changed gravity and hostile/closed environments. Every scientific claim must link to its source; learning content is not a fabricated clinical prediction.

### 4. Body Atlas
Long-term interactive true-3D anatomy with selectable organ systems, camera/depth/picking and evidence links. Until a real renderer exists, **do not display a static image as a working 3D feature**.

### 5. Health Knowledge and Guide
Curated, versioned knowledge sources; symptoms and medical conditions have provenance and clinician review states. Local/cloud AI may summarize knowledge but cannot claim diagnosis or treatment authority.

### 6. Care journey
User-initiated or device-supported GATHER → EVALUATE → ACT → RECHECK with documented uncertainty, a care journal, and a clear path to human support.

### 7. Companion ecosystem
Separate mobile and wearable clients share the server's contracts, subject identities and event stream. Real sensors require real integration validation.

## Hackathon acceptance targets

1. A Windows-native client opens into the five-card **Portal**, with a working top menu, then enters Personal/Mission/Monitor/AI/Science on explicit selection.
2. A server process responds over localhost and persists an engineering observation in SQLite.
3. UI distinguishes no readings from a normal reading; does not manufacture measurements.
4. At least one complete GATHER → EVALUATE → ACT → RECHECK journey should be built before claiming the challenge is fully addressed.
5. NASA data must be demonstrably authentic, correctly cited and relevant to the selected challenge before calling the solution data-grounded.
6. Submission materials include a live demo, source citations, visible limitations and setup instructions.

## Status honesty

The **initial scaffold** implements a server health endpoint, initial engineering observation storage and a native shell/connection check. Clinical decision logic, complete journeys, NASA data integration and companion devices are future milestones. This distinction is part of scientific integrity.
