# Pipeline Changelog — Beat Saber Deluxe Song Conversion Pipeline

All notable changes to the song conversion pipeline (`tools/`, `development/scripts/`) are documented here.

## [v0.50] — 2026-07-13
### Added
- **Pipeline versioning** — central `VERSION` file at project root. Pipeline scripts display version on run.
- **`--add-mode-characteristics` flag** — adds OneSaber and 90Degree `_difficultyBeatmapSets` entries to the per-song bundle (cloned from Standard difficulties). This ensures the actual beatmap data exists for extra modes even though the mode selector UI is driven by a separate data source.

### Changed
- Pipeline now reads and displays version from `VERSION` file on startup.
- Documentation updated for pipeline version tracking separation from plugin version.
