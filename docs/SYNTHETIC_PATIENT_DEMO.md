# AETHERION — Synthetic Patient Demo / Demo hồ sơ bệnh nhân hư cấu

## User journey — Q-0485 target, not yet visually accepted

**Current five-card Portal is a rejected baseline.** The owner wants the appearance of the AETHERION *native application itself* changed to an operations-style Home with an immediately visible **DEMO FOR HACKATHON** action; this is **not** a Server Admin UI technology decision. Q-0485 is responsible for integrating the replacement Home after shared-path owner ACKs.

1. Open the compact **Mission Operations Home** (new Q-0485 target; no verified Windows runtime yet).
2. Select the prominently placed **DEMO FOR HACKATHON** control.
3. Read the short **SIMULATED / TEST DATA ONLY** introduction: five fictional patients, 540 days, twelve metric types and a dedicated SQLite database.
4. Select **Start Patient Demo**. The existing Q-0484 `build_synthetic_patient_demo(...)` widget is shown; `start()` initiates the loader. Only actual SQLite readback confirms whether seeding succeeded.
5. **Crew / Patients** supports selection; **Personal** shows the selected day; **Monitoring** offers 30/90/180/365/540 days; **History** and **Data source** expose row history, provenance and reset.
6. **Back to guide** returns to the synthetic introduction. **NASA REAL ARCHIVE — MA-7 (1962)** is another independent source-labelled choice and contains 83 genuinely published historical data values, not simulated ones.

Q-0484's owner gave Q-0485 *routing consent only* in [GitHub Issue #8 ACK](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6876297980). This is **not permission** to rewrite Q-0484 modules or shared `main.py`, `portal.py` or VI/EN catalogs without other owners' ACK and fresh SHA/CAS.

## Dataset contract

| Field | Exact property |
|---|---|
| Identity | Five obviously fictional IDs `DEMO-P001`–`DEMO-P005`; `Sample Patient 01`–`05` |
| Length | 540 calendar days ending at the UTC seed date; at 2026-11-14, dates are 2025-05-24 through 2026-11-14 |
| Signals | 12 metrics: heart rate, SpO₂, temperature, body mass, sleep, fatigue, steps, respiratory rate, systolic/diastolic blood pressure, glucose, water intake |
| Count | 32,400 possible samples before intentional sparse missing entries (~2.4% per metric) |
| Source | `AETHERION_SYNTHETIC_GENERATOR_V1` |
| Verification | `TEST_FIXTURE`, `UNVERIFIED`, `synthetic=1`, `engineering_test` |
| Generation | Deterministic seeded pseudorandom noise + periodic trends; not derived from NASA, actual patients, sensors, biological studies, diagnoses or treatments |
| Storage | `~/.aetherion/demo/synthetic_patients_v1.sqlite3` (local filesystem, separate from canonical Server database) |
| Availability | Offline, no login; no data is sent to cloud, to canonical `/api/v1/observations`, or to NASA |
| Idempotence | Open again on the same UTC day = reuse existing marked demo store; reset only replaces the isolated marked demo tables |
| Safety | If a foreign database is supplied, refuse modification; never treat blank gaps as normal findings |

### Scientific and application boundary

The **historical NASA MA-7** record viewer displays authentic reported archival values and source pages. **This synthetic patient demo** is an independently generated usability-testing fixture. They must not be blended, mapped to a real person, or submitted to judges as actual NASA observations. The standard Personal/Monitoring/ECG/mission APIs remain authenticated and do **not** receive synthetic rows from this demo.

This demo tests longitudinal navigation, UI rendering, filtering, state handling and relative trends. It does **not** certify medical accuracy, patient-data integrations, an ECG device, spaceflight readiness or clinical safety.

## Implementation files

- `apps/desktop/src/aetherion_desktop/features/demo/synthetic_patients.py`: deterministic SQLite schema, initialization, read-only queries, marker checks and reset
- `apps/desktop/src/aetherion_desktop/features/demo/synthetic_patient_ui.py`: native multi-tab Qt patient explorer, scrollable cards, selected-day profile, chart, history, provenance
- `apps/desktop/src/aetherion_desktop/features/demo/nasa_ma7.py`: narrow hook for full briefing → synthetic demo → return; NASA replay code retained
- `apps/desktop/src/aetherion_desktop/i18n/{vi,en}.json`: bilingual semantic labels
- `tests/test_synthetic_patient_demo.py`: one focused SQLite identity/volume/provenance safety check
- `.github/workflows/synthetic-patient-demo.yml`: targeted Python syntax/SQLite/translation smoke

## Acceptance status

Source implementation and GitHub readback are not equivalent to an actual Windows/PySide6 clickthrough. A targeted GitHub Actions run `43587292152` reported **FAILURE** but **no runner was assigned and the job steps list is empty**; the log endpoint returned `BlobNotFound`. This does not establish a passing or failing Python testcase. The pending acceptance must still confirm a local native launch, transition from Portal to guide to Demo, the actual SQLite row count, 540-day historical navigation, VI/EN, reset, small-window scrolling, and a separate reviewer.

## Calendar-accurate gap behavior (Q-0484 refinement)

Commit [15892ec](https://github.com/huyng0699-arch/AETHERION/commit/15892ec96377b99d925bb01c43d544c8e35f7692) makes the selected **30 / 90 / 180 / 365 / 540** period a window of actual calendar dates, ending on the user's selected `Personal` date (not an arbitrary count of the most recent observed values).

The SQLite store saves **only observations that exist**. Reader `series(..., limit=30, end_day="YYYY-MM-DD")` materializes one **display-only daily slot** per date in that window; if no measured row exists, the slot is marked `NO_DATA` with `value=None` and `source_id=None`. The trend chart splits at that date and never interpolates across missing data. Historical table renders `NO_DATA`, and the trend summary counts observed values rather than total slots. `NO_DATA` is neither zero nor evidence of normality, and no placeholder is persisted in SQLite.

The revised focused test checks chronological windows, explicit missing states, old-date endpoint, and Windows-safe closed SQLite handles. **The test source exists; it has not been shown passing in a real Windows/CI run in this invocation.** The 31,610 computed value count is only the deterministic seed expectation, still awaiting actual SQLite readback on the target environment. Native Windows Mission Operations Home and the short SIMULATED pre-demo guide have been integrated in source by Q-0485, but no after-fix screenshot or real clickthrough has been verified here. Do not accept a visual pass from source inspection.
