# AETHERION — NASA Real-Data Hackathon Demo / Bản trình diễn dùng số liệu NASA thực

> **Operational state:** implemented Qt component on `main`, source-file readback verified; Windows native execution and independent review **not yet certified**. The interface must never show fake astronaut telemetry.

## 1. What the demo does / Cách trải nghiệm

Launch native AETHERION Desktop. On the five-card Portal, select **DEMO FOR HACKATHON** (a separate banner, not a sixth health dashboard entry). The first page provides source and limitations. Click **Bắt đầu khám phá dữ liệu / Start real-data explorer** to open a read-only timeline. Switch four NASA record groups, click original timepoints, view actual readings, report ranges and sample counts, and follow the published NASA source link.

The entire replay can work **without Server or authentication**: the archive is in `apps/desktop/src/aetherion_desktop/features/demo/ma7_source.json`, packaged into the Windows Python distribution via `apps/desktop/pyproject.toml`. It NEVER writes into `/api/v1/observations`, private crew profiles, emergency alerts, or the patient database. The timed-play button advances through actual historic timepoints. Its interval is a UI playback choice, **not** recorded NASA sample cadence.

## 2. Actual source / Nguồn đo thực tế

**NASA Manned Spacecraft Center** (15 June 1962), *Postlaunch Memorandum Report for Mercury-Atlas No. 7 (MA-7), Part I — Mission Analysis*. [Unclassified NASA archival PDF](https://www.nasa.gov/wp-content/uploads/2026/01/ma07-te2.pdf) (classification change appears at the beginning). The report's historical measurements, not a modern digital sensor feed, provide these four panels:

| Source table, printed page | Collection and types | Actual timepoints | Non-null source-backed readings |
|---|---|---:|---:|
| §7.3.2.3, p. 7-33 | Mean heart rate, respiratory rate, temperature; each with reported range and observation count | 5 | 13 |
| Table 7.3.1.2-1, p. 7-41 | Oral temperature, pulse, BP, respiratory rate, weight at clinical examinations | 4 | 17 |
| Table 7.3.1.2-2, p. 7-42 | Hemoglobin, hematocrit, WBC, RBC, five differential fractions | 4 | 35 |
| Table 7.3.2.3-1, p. 7-44 | Six clearly legible Category-I blood pressures and listed pulse pressure | 6 | 18 |
| **Total** | **18 distinct report metrics** | **19** | **83** |

**Critical analytical differences:**
- The five flight-phase rows are **aggregated mean observations**, with their original ranges and sample counts; they are not 5 instantaneous spacecraft telemetry samples. Respiratory rate was *not obtained* for orbit and reentry.
- The four clinical exam dates and four whole blood draw timepoints are different sampling schedules: no timestamp interpolation or cross-group "same moment" association.
- A historical postflight pulse of `76–80` is a reported **range**. Missing values remain `null`, not zero or normal.
- NASA's MA-7 report explicitly questions calibration/interpretation of inflight blood pressure. The six Category I figures are archival recorded instrument values, **not validated clinical diagnoses**.
- Hemoglobin is given as **g** in the original table; the app preserves the original notation rather than asserting an unsupported g/dL conversion.
- All NASA original wording/source markers remain separate from translated interface labels; the program does not claim that NASA reviewed the Vietnamese wording.

## 3. Related official NASA Space Apps resources are distinct studies

- [2026 astronaut health software challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)
- [NASA Open Science Data Repository](https://osdr.nasa.gov/)
- [OSD-569 — Inspiration4 whole-blood CBC](https://osdr.nasa.gov/bio/repo/data/studies/OSD-569)
- [OSD-575 — Inspiration4 serum CMP/cytokines](https://osdr.nasa.gov/bio/repo/data/studies/OSD-575)
- [NASA OSDR public file API](https://osdr.nasa.gov/osdr/data/osd/files/569)

**OSD-569/575 source files are not the Mercury MA-7 data and are not silently included as values here.** The original study downloads could not be retrieved to the current authoring environment, which has no working external DNS. The NASA Space Apps Navigator's 2026-11-13 answer explicitly says there is no single mandatory publicly downloadable astronaut health dataset with every indicator: see [NASA Space Apps Discussion #2025](https://github.com/nasa/spaceapps/discussions/2025).

## 4. What this demo demonstrably does NOT contain

ECG **waveforms**, SpO₂, sleep, mood, glucose in serum, personal radiation dose and uninterrupted human sensor time series remain `NO_SOURCE_DATA` in this archival data pack. There are valid NASA research portals covering some of those topics, but a source URL is **not** a license to invent a time-series value. The entire application must keep historical research, engineering sensor test fixtures, synthetic streams (if ever explicitly added) and real authenticated observations in separate collections and labels.

## 5. Source and acceptance boundaries

- `features/demo/ma7_source.json` holds transcribed, typed and page-labeled historic measurements.
- `features/demo/nasa_ma7.py` enforces source identity, phase/metric/units and data validity before displaying a point.
- `portal.py` and `main.py` wire one native user path; global VI/EN and visual preferences propagate to it.
- `i18n/vi.json`, `i18n/en.json` localize application chrome; scientific identifiers, values and source timepoints are not reinterpreted.
- Focused inspection can verify the 19-stage/83-value data artifact and exact source link; source PDF binary SHA is not embedded or independently verified.
- **Final native acceptance requires** Windows PySide6 launch at target resolutions, open Portal → Demo → briefing → record groups → source link, confirm all 83 real values render, check VI/EN and reduced motion, and an independent reviewer. Static GitHub checks do not certify the interactive Windows result.

**VI:** Bản này trình diễn dữ liệu NASA thật đã được công bố; không phải hồ sơ y tế sống, không phải mô phỏng sinh hiệu và không phải thiết bị y tế.
