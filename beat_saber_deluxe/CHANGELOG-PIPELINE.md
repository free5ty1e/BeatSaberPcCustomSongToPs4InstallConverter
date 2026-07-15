# Pipeline Changelog — Beat Saber Deluxe Song Conversion Pipeline

All notable changes to the song conversion pipeline (`tools/`, `development/scripts/`) are documented here.

## [v0.51] — 2026-07-15
### Added
- **Plugin toggle CLI flags** — `--enable-plugin` and `--disable-plugin` for toggling the Beat Saber Deluxe plugin on PS4 without recompiling or removing files. Enable comments out/uncomments the .prx entry in plugins.ini under [CUSA12878]. Disable comments it out with `#;`. Both work standalone (no --song-dir needed).
- **BeatmapLevelSO metadata blob builder** — `_build_beatmap_level_so_blob()` constructs IL2CPP-compatible serialized data with custom song name, artist, duration, BPM, and 5-mode preview sets. Format verified byte-for-byte against pack bundle data.
- **BeatmapLevelSO injection function** — `inject_beatmap_level_so()` integrates blob builder into the pipeline (Step 6.5), runs after beatmap replacement and before bundle save. Currently logs blob to disk for inspection until UnityPy type support is added.
- **`--song-name` and `--artist` CLI flags** — override song display name and artist/song-author values. Auto-derived from Info.dat or BeatSaver API when not provided.

### Changed
- Pipeline now injects BeatmapLevelSO metadata blob into per-song CAB bundles by default (every song build). Blob is saved to `_beatmap_level_so_<song>.blob` for inspection.

### Known Limitations
- **CAB file injection not yet operational** — UnityPy lacks type info for BeatmapLevelSO. The blob is constructed correctly but cannot be injected into the built CAB without corrupting external references. Work items: (A) post-save raw CAB patching, (B) UnityPy type registry extension, or (C) separate Addressables entry creation. Needs PS4 testing once injection mechanism is resolved.

## [v0.50] — 2026-07-13
### Added
- **Pipeline versioning** — central `VERSION` file at project root. Pipeline scripts display version on run.
- **`--add-mode-characteristics` flag** — adds OneSaber and 90Degree `_difficultyBeatmapSets` entries to the per-song bundle (cloned from Standard difficulties). This ensures the actual beatmap data exists for extra modes even though the mode selector UI is driven by a separate data source.

### Changed
- Pipeline now reads and displays version from `VERSION` file on startup.
- Documentation updated for pipeline version tracking separation from plugin version.
