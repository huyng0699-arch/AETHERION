# AETHERION — 30-second judge demo storyboard

**Quest:** Q-0259 · **Status:** component prepared; recording and independent review pending  
**Audience:** NASA Space Apps Challenge 2026 judges · **Language:** English  
**Product:** AETHERION (independent Team TRUY TINH prototype, not a NASA product or medical device)

This is a **recording plan**, not footage, a public demo link, or proof of successful Windows acceptance. Every captured scene must come from the running AETHERION native Qt app or from an authentic, explicitly labelled repository/source file. Do not insert mock screenshots, synthesized telemetry, invented NASA quotations, clinical advice or claims of sensor integration.

## Precisely 30 seconds

| Time | Camera and click path | Spoken English line / on-screen caption | Evidence and guardrails |
| --- | --- | --- | --- |
| **00:00–00:04 (4 s)** | Start with the real native Windows app on its **five-card Portal**. Show top horizontal menu and click **Mission Control** or its portal monitoring tile. | "AETHERION is a local-first astronaut health information prototype." | Portal must truly be the first page on launch; never substitute a browser mock or a pre-rendered slide. |
| **00:04–00:10 (6 s)** | In Mission Control, show an actual authorized session. For a demo-only account, enter a local subject ID and click **Open subject** / **Refresh recorded data**. Prepare the recording so no password, bearer token, patient identifier or private information appears. | "It separates authorized records from missing information." | If authorization is not genuinely working, show **DENIED** and say so. Do not fake sign-in, hide a 401/403 error or imply anonymous access is a feature. |
| **00:10–00:17 (7 s)** | Show the **real API-backed observation/provenance table**, or its honest **NO_DATA / OFFLINE / UNVERIFIED** state. Zoom for readable columns `Metric`, `Observed at`, `Source`, `Quality` and `Verification`. | "Every reading carries identity, source, time and uncertainty." | Any sample observations must be clearly captioned **ENGINEERING TEST DATA — NOT LIVE ASTRONAUT TELEMETRY**. If no persisted observation is available, deliberately show NO_DATA instead; do not add fabricated readings for the film. |
| **00:17–00:23 (6 s)** | Navigate to **Personal Health** using the real top menu or an actual Mission → Personal action. Show the selected authorized identity or the existing honest unavailable state. | "Crew members can review available information without symptom intake." | Show only functioning screens. If the handoff is not working in the Windows build, use the real Personal view's missing-data state and omit any claim of identity synchronization. |
| **00:23–00:30 (7 s)** | Show the authentic scientific provenance **file view**: `knowledge/nasa/hazards/space_radiation.json` (or another verified hazard source) with an official NASA source URL visibly highlighted. Cut to end title with team/challenge. | "NASA sources provide research context—not live health readings." | **Label this as SOURCE REGISTRY / REPOSITORY FILE**, not a finished native Explore integration. End slate: `AETHERION · Team TRUY TINH · NASA Space Apps 2026 · Independent prototype`. |

Total: **4 + 6 + 7 + 6 + 7 = 30 seconds**. Edit only actual captured interactions. Cuts and text captions are permitted; never overlay an invented interface, completed medical recommendation, simulated ECG, or a NASA logo implying endorsement.

## Capture procedure

1. On a genuine Windows 10/11 installation, check out the latest AETHERION commit and start **server** and **PySide6 desktop** using `scripts/start_server.ps1` and `scripts/start_desktop.ps1`. Confirm Portal is the initial native page; the older `submission/JUDGE_STARTUP.md` currently describes Mission-first startup and must be corrected separately to the V3 design.
2. Use only a **temporary engineering-only local user** and synthetic/consented non-personal test subject. Keep the prototype on loopback. Do not record passwords, tokens, API credentials, personal health information, unlicensed medical media or a misleading flight-safety claim.
3. Check actual authenticated `GET /api/v1/observations?subject_id=...` output before filming. Confirm any visible rows correspond exactly to the real SQLite records with source ID, time and unit; otherwise film the NO_DATA path.
4. Record actual Qt interactions at legible Windows DPI and capture the original NASA citation URL from the repository's local source registry. The hazard JSON contains reference metadata; **it is not downloaded clinical source text, a validated radiation rule or a functioning spacecraft sensor**.
5. Trim to precisely 30 seconds without changing the truth of actions. Export video with intelligible captions/voice-over and no unlicensed music. Record output filename, size, SHA-256, captured commit SHA, Windows version, Qt version and any permissions needed to view it.
6. Open the final public URL **in a fresh private browser with no login**. If it cannot be opened, keep Q-0260 blocked and do not submit an inaccessible link. Official NASA Project-tab submission remains a separate authorized action.

## Deliverables and acceptance still missing

- [x] A 30-second English shot-by-shot plan grounded in available AETHERION components and exact source paths.
- [x] Negative-state path specified without fake medical telemetry or unsupported NASA attribution.
- [ ] Actual native Windows video/screenshot and observed click path.
- [ ] Confirmed working local authentication and observation read on the captured build, or candidly document failure-state only.
- [ ] Artifact hash, public video/slide URL, incognito access test and judge readability.
- [ ] Independent reviewer approval; official team/challenge association still pending Q-0256.

**Current acceptance decision:** **COMPONENT_READY — RECORDING / TEST / REVIEW PENDING**, not DONE. Q-0256 and Q-0106 remain the declared dependencies; the former is blocked pending official team/project confirmation. A storyboard is useful production material but not a substitute for judge-accessible video or NASA submission.

**Scientific references for the source shot:** [official 2026 challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/); [NASA HRP](https://www.nasa.gov/hrp/); AETHERION reference record `knowledge/nasa/hazards/space_radiation.json`. These source links must not be described as live data integrations.
