# AETHERION — Synthetic Patient Demo / Demo hồ sơ bệnh nhân hư cấu

## Direct desktop user journey
1. Open the **five-card AETHERION Portal**.
2. Select **DEMO FOR HACKATHON**. The existing NASA source/limitations briefing still opens first.
3. Read the **540-day patient demo walkthrough** at the top: scope, how to navigate, and the explicit synthetic-data notice.
4. Select **Start patient data demo / Bắt đầu Demo bệnh nhân**. A separate offline SQLite database is seeded (or validated and reused), and the real native Qt demo patient workspace opens.
5. In **Crew / Patients**, double-click a fictional profile; **Personal** shows 12 measurement types for the selected day; **Monitoring** plots 30, 90, 180, 365 or 540 days; **History** displays the readings and source IDs; **Data source** exposes the generator flags and a reset control.
6. **Back to guide** returns to the full NASA/Demo introduction. The original NASA research replay and science catalog remain available through their original actions.

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
