# Changelog

All notable changes to AETHERION are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-14

### Added
- Five-card AETHERION Portal startup shell with top horizontal menu (`vi` / `en` bilingual UI, theme & reduced-motion support).
- Offline NASA CliFF SQLite medical library (`knowledge/nasa/cliff_119_2023/AETHERION_NASA_CLIFF_119.sqlite`) with 116 verified structured records and 819 bilingual-ready symptom labels (`knowledge/symptoms/ASTRA_819_REFERENCE.json`).
- Server-controlled anatomical mesh catalog (`CC BY 4.0` STL models) and non-diagnostic anatomy-to-CliFF knowledge mapping.
- Care episode persistence (`GATHER -> EVALUATE -> ACT -> RECHECK`), safety witness logging, and privacy-safe JSON operational logging.
- Local-only Ollama AI interview integration (cloud AI disabled by default behind explicit opt-in).

### Changed
- Aligned `aetherion-server`, `aetherion-desktop`, FastAPI `/health` & safety router version, and `CHANGELOG.md` on `0.2.0`.
