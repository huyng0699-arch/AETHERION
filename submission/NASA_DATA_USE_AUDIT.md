# AETHERION — Actual NASA data and resource use audit (Q-0258)

**Status:** COMPONENT READY — native Explore integration, independent review and official submission pending.  
**Checked:** 14 November 2026 UTC · **Project:** Independent Team TRUY TINH AETHERION / NASA Space Apps 2026 health-monitoring challenge.

This is an **implementation evidence map**, not a claim that OSDR biomedical raw data have been imported, that astronaut physiology is streamed live, or that NASA has endorsed AETHERION. It names a publisher, resource identifier, source URI, processing step and **actual consumer** where one exists. The absence of a native UI consumer is explicitly recorded.

## Resources and actual code paths

| Source / version | Official publisher and URL | Local processing and evidence | Actual AETHERION consumer / observable limitation |
| --- | --- | --- | --- |
| **2026 health-monitoring challenge** | NASA Space Apps Challenge: [official challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/) | `knowledge/nasa/challenge_2026.json` records the prompt, five hazards, retrieved time and verification state; `Q-0106` records a source audit | `submission/CHALLENGE_RESPONSE.md` and the hazard reference JSON cite it. This is **challenge specification**, not astronaut measurements or scientific patient data. |
| **OSD-575, version 3** | NASA Open Science Data Repository (OSDR): [OSD-575](https://osdr.nasa.gov/bio/repo/data/studies/OSD-575), DOI [10.26030/mc5d-p710](https://doi.org/10.26030/mc5d-p710). Official study page lists CC0-1.0 for this study's accessible data/metadata | `knowledge/nasa/osdr_datasets.json` stores source title, DOI, organism, assay/unit metadata, caveats and source URL. Metadata is curated locally; no protected raw human samples or numerical time series are ingested by this AETHERION artifact | `knowledge/nasa/hazards/space_radiation.json` links the study as a research citation; `knowledge/nasa/hazards/altered_gravity.json` uses other study references. No native Qt Mission/Personal observation comes from OSD-575. |
| **OSD-569 v4; OSD-530 v3** | NASA OSDR: [OSD-569](https://osdr.nasa.gov/bio/repo/data/studies/OSD-569), [OSD-530](https://osdr.nasa.gov/bio/repo/data/studies/OSD-530) | Both appear as **metadata records** in `knowledge/nasa/osdr_datasets.json`, with self-reported versions/terms and interpretation limits. No participant-level data redistribution is asserted | At present the records are a reference catalog; no code-backed scientific trend chart or clinical finding is generated from these sources. |
| **OSD-258 v2; OSD-374 v1** | NASA OSDR: [OSD-258](https://osdr.nasa.gov/bio/repo/data/studies/OSD-258), [OSD-374](https://osdr.nasa.gov/bio/repo/data/studies/OSD-374) | Local metadata distinguishes an *in-vitro cell model* (OSD-258) and a *mouse proton-irradiation model* (OSD-374) in `knowledge/nasa/osdr_datasets.json` | These entries inform source-linked hazard descriptions only. They **do not establish human thresholds**, diagnoses or actual astronaut-specific predictions. |
| **Five NASA spaceflight hazard topics** | NASA Human Research Program: [HRP](https://www.nasa.gov/hrp/); official challenge above; individual OSDR links inside the hazard files | `knowledge/nasa/hazards/{space_radiation,isolation_confinement,distance_from_earth,altered_gravity,hostile_closed_environment}.json` maps hazard IDs, organ systems, research references and limits | `knowledge/nasa/offline_literature.py` loads the local scientific reference files; `knowledge/nasa/hazard_to_body_link.py::resolve_hazard_route` consumes them and returns a hazard's source URLs, matched metric names and an honest `NO_DATA` when no eligible observation is present. This **headless library** is implemented; it is **not yet a native Explore page**. |
| **NASA IMM CliFF 119 (2023)** | NASA Integrated Medical Model: [original NASA index](https://www.nasa.gov/integrated-medical-model-documentation/) | `knowledge/nasa/cliff_119_2023/README.md` and the 119 source Quests distinguish the intended collection from successfully imported PDFs and images | **NOT VERIFIED AS 119 COMPLETE.** Do not count an index, SQLite schema, file names or an importer alone as a full offline medical library. Source bytes, license clearance, page anchors and Windows reader proof remain separate gates. |

**Provenance and license caveat:** The official [OSD-575](https://osdr.nasa.gov/bio/repo/data/studies/OSD-575) page was checked for its title/DOI/version/CC0 marker. Other OSDR IDs and metadata are **as recorded in the current repository catalog**; their versions/terms must be separately rechecked against source pages before any redistribution or derived scientific claim. The repository code uses its own Apache-2.0 license; NASA scientific materials do **not** automatically inherit that license. The repo's dataset policy is documented at `knowledge/nasa/dataset_rights_and_transforms.md`.

## End-to-end trace: what works, what does not

```text
NASA public challenge + OSDR source pages
          │ [verified / recorded reference metadata, no patient stream]
          ▼
knowledge/nasa/osdr_datasets.json + hazards/*.json
          │ [offline source catalog, citations and limitation strings]
          ▼
knowledge/nasa/offline_literature.py
          │ [source-linked deterministic hazard routing]
          ▼
knowledge/nasa/hazard_to_body_link.py::resolve_hazard_route
          ├── hazard / organ-system IDs + source URLs
          └── matched locally supplied observation names or NO_DATA
                    │
                    X  NOT WIRED TO NATIVE EXPLORE SCREEN
                    ▼
apps/desktop/src/aetherion_desktop/main.py
     └── Explore menu is presently a labelled placeholder;
         Portal "science" currently routes to Medical Library, not to this hazard catalog.
```

The actual crew observation API (`apps/server/src/aetherion_server/main.py`) is **separate**: it receives source-aware engineering measurements via authenticated endpoints. Nothing in the above NASA research catalog is automatically ingested as a crew member's pulse, oxygen level, ECG, dosimetry, sleep observation or clinical measurement.

The previous citation chain **does not satisfy** a claim that a judge already sees NASA evidence inside the native Explorer view. `Q-0117` must connect the five reference records to a functioning native screen with real clickable source URLs before that UI claim can PASS; a separate Windows verification is needed. **No native view may silently promote research model data into live telemetry.**

## Reproducible focused review — no fabricated test result

1. Read `knowledge/nasa/osdr_datasets.json` and find `osd_id: OSD-575`, `url`, `doi`, `version`, `is_live_telemetry: false` and `limitations`. Compare the public official [OSD-575 study page](https://osdr.nasa.gov/bio/repo/data/studies/OSD-575).
2. Read `knowledge/nasa/hazards/space_radiation.json`; the `primary_sources` include OSD-575 and a live NASA source URL, but the JSON is only a *reference file*, not a database of sensor samples.
3. Inspect `knowledge/nasa/hazard_to_body_link.py`, which loads the offline source registry and produces a `NO_DATA` status for an empty observation list. This documents what the code **does**, without claiming the Qt UI invokes it.
4. Inspect `apps/desktop/src/aetherion_desktop/main.py`: currently `Explore` is a placeholder page and Portal science routes to the separate offline Medical Library. The desired NASA Explore journey has not been demonstrated here.
5. A different reviewer should inspect Q-0258's source-file claims against the latest main HEAD and record `COMPONENT_APPROVED` or `REWORK_REQUIRED` as appropriate. This document alone does not independently approve the Quest.

## Unfinished acceptance steps

- [x] Name publisher, exact NASA OSDR source IDs, URLs, original metadata and processing artifacts.
- [x] Identify exact consuming *Python library* and disclose that no native NASA Explore view currently consumes those references.
- [x] Explicitly distinguish imported metadata from research measurements, raw protected files and live astronaut observations.
- [ ] Build and run a functioning native Explore integration (Q-0117) and document the exact UI output/source click behavior.
- [ ] Verify actual Windows interaction, source-destination link handling and meaningful missing-data state.
- [ ] Verify Q-0256 official team/project association and Q-0260 judge-accessible artifact; finish official Project-tab workflow only through an authorized participant.
- [ ] Obtain independent reviewer approval.

**Result:** **IMPLEMENTED — INTEGRATION / TEST / REVIEW PENDING**, not DONE. The science-linked code and research metadata are genuine references, but current UI consumption and submission gates remain outstanding.
