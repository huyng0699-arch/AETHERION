# AETHERION — Native Windows Screen Status / Trạng thái màn hình

**Latest authoring audit:** 2026-11-14, Q-0485 source-level integration.  
**Evidence class:** GitHub file SHA and route inspection only. **No new Windows screenshot or runtime acceptance** since the owner's rejected five-card baseline.

## Owner-approved first-view architecture

The native Windows app opens **Mission Operations**, a native PySide6 workspace informed by mission-operations information architecture. The old Portal with five oversized cards and orange bottom Demo banner is **not the accepted main visual**.

The historical screenshot at:
`C:\Users\Admin\Documents\Codex\2026-11-09\m-repository-huyng0699-arch-nasa-v\AETHERION\outputs\ui-review\pending\portal-user-provided-20261114.png`
is **before-fix evidence**. A new actual Windows after-fix screenshot **does not yet exist in this evidence record**.

| Screen / route | Source implementation | GitHub status | Native Windows render |
| --- | --- | --- | --- |
| Cold-start Mission Operations | `mission_ops_home.py`; mounted first in `main.py` | Wired in `dc49fe906a2b1669edd4fcfa038ea8c9c3efa478` | **PENDING** |
| Prominent DEMO FOR HACKATHON CTA | `MissionOperationsHome.primary_demo` and independent SIMULATED signal | Wired to briefing | **PENDING** |
| SIMULATED source briefing | `features/demo/synthetic_briefing.py` | Dedicated bilingual native page; explicit Start required | **PENDING** |
| Fully navigable fictional scenario | `synthetic_patient_ui.py` and `synthetic_patients.py`, Q-0484-owned | Q-0485 wires Start to `PatientDemo.start()` / Back to briefing | **PENDING** |
| Fictional SQLite 540 days × 5 IDs × 12 metric types | `Path.home()/.aetherion/demo/synthetic_patients_v1.sqlite3` | Q-0484 source has deterministic generator; **SQLite readback not performed here** | **PENDING** |
| Genuine NASA Mercury MA-7 archive | `nasa_ma7.py` + `ma7_source.json`, Q-0478 | Separate archive signal, NASA briefing and 83 sourced historical values preserved | **PENDING** |
| Scientific NASA CliFF / hazard / glossary archive | `demo_catalog.py`, `demo_library.py`, `demo_hub.py` | Source-backed local catalog; actual available file count must be shown | **PENDING** |
| Legacy five-card Portal | `portal.py` | Retained only under `Alt+Shift+Home`; no longer cold-start Home | Existing screenshot is **REJECTED** |
| Authenticated mission, personal, monitoring, ECG, AI, interview, care | Existing source widgets / real Server | Mission Operations routes bind existing safe handlers, no demo import | **PENDING** |
| NASA Explore, science browser, medical library, atlas, settings | Existing app widgets | Mission Operations routes bind existing handlers | **PENDING** |

### Click journey / Hành trình bắt buộc

```
App launch → Mission Operations (first screen)
  DEMO FOR HACKATHON → SIMULATED briefing → Start
    → Q-0484 PatientDemo: Crew | Personal | Monitoring | History | Data source
       → isolated synthetic SQLite only; Back → briefing
  NASA · MA-7 → original NASA source briefing → historical measured-value explorer
  Navigator → 13 existing real/sourced feature handlers, retaining authorization
```

**Boundary:** the 83 reported NASA MA-7 observations are authentic *historical* values, **not simulated**; fictional patient scenario data are synthetic, **not NASA or live patient telemetry**. Neither collection should be uploaded to authenticated observations. The simulated values do not constitute medical advice, risk classification or original ECG.

## Ownership and QA gates

- GitHub Issue [#8](https://github.com/huyng0699-arch/AETHERION/issues/8), comment [#6876351829](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6876351829), grants only Home/Demo `main.py` integration by Q-0477/Q-0480/Q-0481 owners. Comment [#6876297980](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6876297980) approves routing to Q-0484 without writing its modules. Q-0478 previously released shared Home paths.
- **No modifications to shared VI/EN catalog JSON**, Q-0484 synthetic modules, original NASA values, API permissions, or old Portal internals by Q-0485.
- Q-0485 remains **COMPONENT_READY / review PENDING**, not `DONE`. This document reports code integration, not accepted screen quality.
- **Windows acceptance outstanding:** start an actual Windows PySide6 build at 1040×650 and 150% DPI; capture the first screen after-fix; click Demo → briefing → Start; confirm 5 tabs, five fictional subjects, 540-day range and seeded SQLite readback; navigate Back and real NASA archive; verify all 13 routes plus VI/EN, visual themes, reduced motion, keyboard access, and no accidental patient-store writes.
- An independent reviewer must validate the fresh screenshot and interaction evidence before final DONE. No screenshot has been generated or fabricated in this commit.

## Focused NASA source-link defect requiring owning-agent fix

Source readback found `nasa_ma7.py` uses `QDesktopServices.openUrl(QUrl(...))` without an available `QUrl` import in `build_hackathon_demo()` or module globals. **Until the Q-0478/Q-0484 file owner imports `QUrl` with an ACK and SHA/CAS, original PDF/OSDR/official resource link clicks are a suspected `NameError` failure.** This is not proof of a Windows crash; no native click was attempted. See [Issue #8 comment 6876928259](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6876928259). Q-0485 must not edit this multiply-owned source file without narrow authorization.
