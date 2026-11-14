# NASA OSDR Research Dataset Selection (Q-0109)

**Retrieved:** `2026-11-14T03:48:00Z`  
**Source:** [NASA Open Science Data Repository (OSDR)](https://osdr.nasa.gov/)  
**Critical Boundary:** Every dataset below is a **historical or experimental spaceflight research archive**, **not** live astronaut telemetry and **not** a clinical diagnostic rule.

## Selected Datasets

| OSD ID | Version | Organism | Mission / Platform | Hazard Domains | Assay Types | Key Units | License / Access |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [OSD-575](https://osdr.nasa.gov/bio/repo/data/studies/OSD-575) | v3 (`LSDS-8`, DOI `10.26030/mc5d-p710`) | *Homo sapiens* (`n=28` serum samples, 4 crew) | SpaceX Inspiration4 (3-day LEO, Sep 2021) | Altered gravity, radiation, closed habitat | Quest Diagnostics CMP; Eve Tech HD71 & HDCVD9 multiplex; Alamar NULISAseq | `NPQ` (log2 IPC-normalized), `pg/mL`, CMP units, `day` (`L-92`..`R+194`), `°C` | `CC0-1.0` (open metadata/transformed); DAR/IRB for raw human files |
| [OSD-569](https://osdr.nasa.gov/bio/repo/data/studies/OSD-569) | v4 (`GLDS-561`, `LSDS-7`, DOI `10.26030/e0rx-sh52`) | *Homo sapiens* (`n=81` whole blood samples, 4 crew) | SpaceX Inspiration4 (3-day LEO, Sep 2021) | Radiation, altered gravity, closed habitat | Complete Blood Count (Quest); WGS & Clonal Hematopoiesis; ONT PromethION & Ultima RNA-Seq | Standard CBC units, sequencing read counts / flow-cycles, `day` | `CC0-1.0` (open metadata/summaries); DAR/IRB for raw genomic files |
| [OSD-530](https://osdr.nasa.gov/bio/repo/data/studies/OSD-530) | v3 (`GLDS-530`, DOI `10.26030/r2xr-h714`) | *Homo sapiens* (`n=64` plasma samples, 6 ISS astronauts) | ISS >120 days (JAXA Cell-Free Epigenome Study) | Altered gravity, radiation, isolation, closed habitat | Plasma cfRNA & CD36-exMT RNA-Seq (Illumina NextSeq 500, 2×36 bp) | `base pair` (`UO:0000244`), `day` (`UO:0000033`), `°C` (`UO:0000027`), log2 normalized counts & SEM | NASA OSDR open science (de-identified processed tables) |
| [OSD-258](https://osdr.nasa.gov/bio/repo/data/studies/OSD-258) | v2 (`GLDS-258`, `GSE137081`, DOI `10.26030/gfew-5417`) | *Homo sapiens* (hiPSC-derived cardiomyocytes, `n=18`) | ISS SpaceX CRS-9 (SABL, 5.5 weeks) | Altered gravity | RNA-Seq (Illumina HiSeq 2000, 100 bp PE) & calcium-handling assay | `read`, `percent`, `base pair`, `°C`, DESeq2 normalized counts | NASA OSDR open science |
| [OSD-374](https://osdr.nasa.gov/bio/repo/data/studies/OSD-374) | v1 | *Mus musculus* (hippocampus) | Ground proton irradiation analog (2w & 20w) | Radiation, distance from Earth | DIP-Seq (5mC/5hmC, HiSeq 2000, 75 bp SE) & RNA-Seq (`GL-DPPD-7101-G`) | `base pair`, `week`, DESeq2 normalized counts | NASA OSDR open science |

## Selection Rationale for AETHERION

1. **Human Longitudinal Coverage (`OSD-575`, `OSD-569`, `OSD-530`):** Provides authentic *Homo sapiens* pre-flight, in-flight (`OSD-530`), and post-flight recovery (`L-168` through `R+194`) assay metadata with explicit units (`NPQ`, `pg/mL`, `day`, `°C`, `base pair`).
2. **Cardiovascular & Microgravity Mechanism (`OSD-258`):** Connects microgravity exposure to human cardiomyocyte calcium handling and mitochondrial gene expression without fabricating patient cardiac telemetry.
3. **Deep-Space Radiation Analog (`OSD-374`):** Covers long-term (2-week and 20-week) neuro-epigenetic proton radiation effects in *Mus musculus*, clearly separated by species so animal models are never conflated with human observations.
4. **Machine-Readable Catalog:** Full structured provenance is stored in [osdr_datasets.json](osdr_datasets.json) for downstream ingestion by `apps/server/` and `apps/desktop/` (Q-0110+).
