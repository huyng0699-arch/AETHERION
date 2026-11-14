# NASA CliFF 119 (2023) Originals Status Audit (Q-0108)

**Audited:** `2026-11-14T03:50:00Z`  
**Official NASA Index:** https://www.nasa.gov/integrated-medical-model-documentation/ (page last updated `2026-08-31`)  
**Verification State:** `PARTIAL_STRUCTURED_JSON_NO_PDF_ARCHIVE` (`0 / 119` locally stored raw PDF originals in `original/`; `118 / 119` verified structured JSON records in `records/`, missing only `CLIFF-119`)

## Findings

1. **Official NASA Index Verified Online:** The NASA Integrated Medical Model (IMM) Documentation page is live and documents the 100-condition LEO baseline (`CliFF 100`) versus the expanded 119-condition deep-space list (`CliFF 119 (2023)`).
2. **Local Repository State (`0 / 119`):**
   - `knowledge/nasa/cliff_119_2023/original/` does **not** exist (`0` PDF/DOCX/DOC files present).
   - `knowledge/nasa/cliff_119_2023/manifest.json` does **not** exist (`0` SHA-256 digests verified).
   - `scripts/fetch_nasa_cliff_119.py` is present and configured to require `119` unique NASA-hosted documents before writing `manifest.json`, but `.github/workflows/import-nasa-cliff-119.yml` has not completed an import run.
3. **Honesty & Safety Rule:** AETHERION **must not** claim 119 complete medical condition files or serve placeholder clinical text as NASA CliFF originals. Until a verified Windows/CI run of `scripts/fetch_nasa_cliff_119.py` populates `original/` and `manifest.json`, any feature depending on CliFF 119 originals must report `NO_DATA`.
