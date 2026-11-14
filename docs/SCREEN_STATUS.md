# AETHERION — Native Windows Screen Status / Trạng thái màn hình

**Latest authoring audit:** 2026-11-14T17:46:01Z, Q-0485 Open MCT UI correction on branch; source only.  
**Evidence class:** GitHub branch and source diff inspected. No Qt render, GUI screenshot, desktop launch, or runtime acceptance; visual proof remains **PENDING**.

## Current Open MCT visual checkpoint — branch source only (2026-11-14T17:46:01Z)

**Branch:** `agent/q0485-openmct-visual-20261115` · **source commit:** `880072f98205c0a1dbf26c8b7c4a5ce7bd7bfdaa`  
**Changed screen:** Mission Operations Home, UTC observations, Browse Demo/NASA selection, hosted Monitoring shell.  
**Changed file:** `apps/desktop/src/aetherion_desktop/mission_ops_home.py`

- The bottom UTC Time Conductor was already below the three-pane splitter in current source; no change was needed to its placement.
- Replaced index-based UTC bars with an interactive true-time scatter view: actual UTC timestamps set horizontal positions, no connecting/interpolated line, and point selection selects its source row for Inspect.
- Browse now exposes Demo and keeps Demo/NASA objects selected while their hosted pages are open.
- The outer conductor hides only while Q-0477 Monitoring is displayed, avoiding two independent visible time controls. No shared-time API or synchronization is claimed.
- Independent source review found and the follow-up commits fixed three issues: sample selection after the 32-point display window used a wrong row offset, right-edge tick labels could clip, and the plot heading was not visible/accessible. Final source-only review found no blocker.
- Source change status: **CHANGED ON BRANCH**. GitHub Actions renderer added; artifact **PENDING**. Native visual status: **RENDER PENDING**. No screenshot or GUI PASS yet. No Windows desktop launch was performed; a Qt process could not be launched from the current restricted tool runtime. Independent source review is in progress.

---

## Final source SHA after MA-7 selection consistency patch

- `mission_ops_home.py` latest committed blob: `9e338397d9f61d63ac2ad4b420e31af8a67c80c2` — [`b14978623ee530cc292048a412d4f02a927cff59`](https://github.com/huyng0699-arch/AETHERION/commit/b14978623ee530cc292048a412d4f02a927cff59). The original NASA phase-comparison table now retains the selected metric in the source measurement table and Inspect when switching report phases, and measurement selection drives the same comparison metric. Values and source labels remain read-only.
- [Q-0486 PR #9](https://github.com/huyng0699-arch/AETHERION/pull/9) was inspected but **not imported or edited**: its telemetry widget has UTC time-axis semantics, unsuitable for MA-7's categorical phase/timepoint records without verified UTC timestamps.
- `main.py` blob remains `9889e109c52943064bf27dfb8a4f8e2284db18de` for the persistent-shell integration. Existing Q-0477 internal Monitoring controls remain independent. **Offscreen Qt and Windows visual acceptance still PENDING.**

---

## P0 source checkpoint — persistent Mission Operations (2026-11-14)

**Owner override:** Browse/Workspace/Inspect and bottom UTC conductor must persist throughout normal native routes, not just cold-start Home; the five-card Portal and duplicate horizontal top navigation are explicitly rejected. This is the user's **actual app visual**, not the Server Admin page.

| P0 issue | Code integration on `main` | What is *not* proven |
| --- | --- | --- |
| Browse route previously left Mission Operations | `mission_ops_home.py` [`907a8bff`](https://github.com/huyng0699-arch/AETHERION/commit/907a8bff925c5c5754ab2f2cbcf2dfc705cd441b) adds `attach_feature` / `show_hosted`; `main.py` [`ec0a4399`](https://github.com/huyng0699-arch/AETHERION/commit/ec0a4399995d37cbcfe009987ebbd2b010dc7216) reparents already-constructed native QWidget instances into persistent center Workspace | Qt windowing, reparenting visual behavior, 1040×650 and 150% DPI still **PENDING** |
| Monitoring / Health / ECG / Chat / other routes | All **13 existing routes** point to their original widgets inside central stack, with native signals and authorized identity/access pathways intact in source; Monitoring still calls its existing `refresh()` | Actual HTTP permission and clickthrough not performed |
| Briefing and NASA left the shell | Both `SIMULATED briefing → Start → PatientDemo` and distinct real NASA MA-7 archival widget now mount inside center Workspace, preserving Browse and Inspect | No tested synthetic SQLite COUNT(*), five-tab GUI, original NASA QUrl link fix, or visual acceptance |
| Cluttered duplicate global navigation and status | The old topBar's horizontal route buttons, AETHERION brand and connection pill are hidden, including on resize; global appearance/language/settings/help stay visible. The one displayed status pill in Operations is derived from actual HTTP `/health` reply | Actual post-fix screenshot **PENDING** |
| Unreadable NASA QPainter bars (no phase, value, unit, axis) | **Removed** unlabelled bars from authentic MA-7 report view. Categorical phase-comparison **table** now displays exact original report timepoint, numeric/string value or missing state, unit and qualifier; click a phase to update original measurement table and right Inspect | Source-level view only; table legibility at minimum window and native clickthrough **PENDING** |
| Monitor and Home time ranges | Home Time Conductor has explicit UTC bounds and controls its own validated UTC workspace. Q-0477 Monitoring widget's time controls remain independent. Requested narrow API ACK in [Issue #8 comment #6877383276](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6877383276). | **Not synced** until Q-0477 owner explicitly approves a safe public API, then integration and tests |

**Current source SHAs:** `main.py` blob `9889e109c52943064bf27dfb8a4f8e2284db18de` (commit `ec0a4399`); `mission_ops_home.py` blob `c6c874e0becdd3015a33facfacc53656918fbe68` (commit `907a8bff`). Q-0485 remains RUNNING/IN_PROGRESS/review PENDING.

**Verification boundary:** focused **13/13 GitHub static contract checks** passed for presence of centralized host mappings, existing refresh/subject handoff, new QStackedWidget usage, source-readable NASA categorical table, and absence of topBar duplicate navigation reappearing on resize. No PySide6 Qt/offscreen screenshot, Windows screen, QA clickthrough or independent visual acceptance was obtained; **do not claim visual PASS or DONE.** Previous install attempts were unsuccessful in this runtime. External reviewer must verify rendering, all route switches, source boundaries, VI/EN, theme/reduced motion and minimum window ergonomics.

---

## Latest corrected native Home layout (GitHub source only; 2026-11-14)

**Commit:** [`b92e1a9daac3c8ba036774e6b27aeef7b32633ae`](https://github.com/huyng0699-arch/AETHERION/commit/b92e1a9daac3c8ba036774e6b27aeef7b32633ae) · `mission_ops_home.py` blob `d39354c4b7571847cf6ffc3eb79572573e9533d2`.

The owner’s updated NASA Open MCT direction supersedes five-card Portal / horizontal-menu-only presentation **for the first native app screen**; no implication for Admin HTML, legacy routes or medical access rules.

| Owner correction | Implemented source behavior | Runtime evidence |
| --- | --- | --- |
| Correct cold start | `_choose("home")`; Mission Workspace overview, NASA MA-7 remains separate Browse object | GitHub inspected; Qt/Windows visual **PENDING** |
| Fixed bottom Time Conductor | Controls and UTC status placed *below* the three-pane splitter, above footer; explicit UTC bounds retained for table, discrete plot and Inspect | Source inspection only; no Q-0477 Monitoring filter sync |
| Inspect at 1040 px | Non-collapsible three-pane splitter; left min 177 logical px, center min 405 px, right Inspect min 205 px; horizontal pixel scroll for long properties | Geometry source constraints present; real 1040px / 150% DPI render **PENDING** |
| Correct Home Inspect | Mission properties show unselected subject/source, UTC scope and authorization requirement, not NASA MA-7 claimed as active source | GitHub inspected; interaction **PENDING** |
| Route and data separation | 13 real feature routes intact; prominent Demo → SIMULATED briefing → Q-0484; authentic NASA MA-7 independent | Wiring unchanged; Windows clickthrough **PENDING** |

**Focused structural checks: 15/15 passed** against current source and unchanged `main.py` blob `15274eef60ff1a69a920d10fd32d4763264ed67b`. These are source assertions, not a test of final appearance. PySide6/PyQt6 are not installed in this runtime and a temporary-venv PySide6 installation returned no matching distribution; **no valid Qt offscreen screenshot or Windows after-fix screenshot exists from this run**. The owner-supplied original Windows screenshot remains an explicitly rejected baseline.

**Next acceptance:** fresh Windows GUI capture after fix, browse/Inspect selection, verify conductor does not obscure data at min 1040×650 and 150% DPI, full simulated 5-patient / 540-day SQLite test, source NASA archive and link, VI/EN/themes, actual permissions, independent reviewer. Q-0485 remains `RUNNING / IN_PROGRESS / review PENDING` — do not mark PASS.

---

## Latest Q-0485 source-only workspace review — 2026-11-14

**Owner visual override:** The old SPEC/AGENTS five-card and horizontal-menu-only design language is superseded **only for the first native app screen**. The target is the actual Browse → Workspace → Inspect layout from the NASA Open MCT user-facing information architecture, with one time conductor. This is an implementation requirement, **not** a claim that AETHERION itself is NASA Open MCT or that its appearance has passed.

**Code on `main` (not Windows visual evidence):**
- `57a4d17ceab9862a7a7365c5412ff1629c151e0b`: removed the ornamental `OrbitPanel`; added interactive left Browse object tree, center historical NASA MA-7 report tables/source-derived bars and empty authorized UTC panel, right selected-source properties/Inspect, one shared UTC window, and the pinned **DEMO FOR HACKATHON** action.
- `c66cb536bbd7648eda0e15ab95e675609fe8bd30`: focused source-level fixes for missing Qt `QRectF` import, explicit UTC editor time specification, searchable Browse tree, and metric/source controls. No original NASA values were altered.
- `9517e5dfabd0fe07e21fc42a9e7d9ee3f6b7e6b3`: UTC chart uses only one metric/unit/source family; table, chart and Inspect share the selected UTC bounds and filters. **This optional host-supplied UTC adapter is not yet bound to authenticated Monitoring**; Q-0477 owns that integration, and no claim of live records is made.
- **MA-7 source boundaries:** the 19 historical report timepoints and 83 published numeric/non-null observations have no universally verifiable absolute UTC timestamps. Their original stage labels/mean/qualifier/source-page metadata remain visible, and the UTC Time Conductor does **not** assign invented dates to report phases. The authorized UTC panel shows an honest empty state unless a trusted controller provides actual UTC-stamped observations.
- All 13 existing feature-route keys remain bound through unchanged `main.py` (`dc49fe9` + readiness refinement `83355ec`). The pinned Demo opens SIMULATED briefing → explicit Start → Q-0484 isolated five-patient, 540-day SQLite experience. NASA MA-7 is a separate archival action, never a synthetic stream.
- **Visual proof: PENDING.** An offscreen Qt render was attempted in this runtime, but PySide6 is absent and installing it into a temporary Python virtual environment failed (`No matching distribution found for PySide6` in this environment); therefore **no valid Linux offscreen screenshot was produced**, and **no Windows desktop was launched**. The owner's previously supplied five-card Windows screenshot remains *before-fix rejected evidence*. A fresh Windows after-fix screenshot and independent clickthrough are still required.

### Workspace-specific QA still open

- Render at 1040×650 and 150% DPI: verify tree, UTC conductor, table and Inspector stay usable without clipping; compare actual native visual to owner's Open MCT requirement.
- Confirm Browse selection changes center view/Inspect, report-group and metric selection update real source values, UTC search/presets/filter boundaries do not invent samples, and time controls are explicitly UTC.
- Verify Demo enters briefing before any synthetic SQLite seed; read back seeded patient data from the dedicated database and test all five tabs. Verify the NASA archival path and all 13 existing routes separately, including VI/EN and theme/reduced-motion behavior.
- Independent reviewer signs off actual native interactions. **Q-0485 remains RUNNING/COMPONENT IN PROGRESS (or COMPONENT_READY once current owner releases), review PENDING; never infer DONE from source inspection.**

---

## Owner-approved first-view architecture

The native Windows app opens **Mission Operations**, a native PySide6 workspace informed by mission-operations information architecture. The old Portal with five oversized cards and orange bottom Demo banner is **not the accepted main visual**.

The historical screenshot at:
`C:\Users\Admin\Documents\Codex\2026-11-09\m-repository-huyng0699-arch-nasa-v\AETHERION\outputs\ui-review\pending\portal-user-provided-20261114.png`
is **before-fix evidence**. A new actual Windows after-fix screenshot **does not yet exist in this evidence record**.

| Screen / route | Source implementation | GitHub status | Native Windows render |
| --- | --- | --- | --- |
| Cold-start Mission Operations | `mission_ops_home.py`; mounted first in `main.py` | Wired in `dc49fe906a2b1669edd4fcfa038ea8c9c3efa478` | **PENDING** |
| Prominent DEMO FOR HACKATHON CTA | `MissionOperationsHome.demo` and independent SIMULATED signal | Wired to briefing | **PENDING** |
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
