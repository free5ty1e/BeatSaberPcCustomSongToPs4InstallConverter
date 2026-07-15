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

### Verified
- **Plugin toggle LIVE on PS4** (Exp 129): `--enable-plugin` and `--disable-plugin` tested and verified on console — both flags correctly update plugins.ini under [CUSA12878]. Enable uncomments the .prx entry; disable comments out release + debug entries with `#;`.
- **BeatmapLevelSO blob format verified byte-for-byte** against StartMeUp pack bundle hex dump (440B). Exact serialization mapped: m_GameObject(PPtr), classID(int32=1), m_Script(PPtr→BeatmapCharacteristicSO, Standard pathID=-7286399427822119286), m_Name(UTF-8), _version, _levelID, _songName, _songSubName, _songAuthorName, _levelAuthorName, 7 preview doubles, coverImage/coverClip PPtrs, environment strings, _previewDifficultyBeatmapSets[5]. Test blobs generated for Espresso (1259B), Duvet (1224B), Time Lapse (1253B).

### Known Limitations
- **CAB file injection not yet operational** — set_raw_data() via UnityPy typetree FAILS with "read_str out of bounds" (IL2CPP PPtr mismatch). Work items: (A) Raw SerializedFile manipulation — modify StartMeUp blob as binary template at known byte offsets; (B) UnityPy type registry extension for BeatmapLevelSO; (C) separate Addressables manifest entry.

## [v0.50] — 2026-07-13
### Added
- **Pipeline versioning** — central `VERSION` file at project root. Pipeline scripts display version on run.
- **`--add-mode-characteristics` flag** — adds OneSaber and 90Degree `_difficultyBeatmapSets` entries to the per-song bundle (cloned from Standard difficulties). This ensures the actual beatmap data exists for extra modes even though the mode selector UI is driven by a separate data source.

### Changed
- Pipeline now reads and displays version from `VERSION` file on startup.
- Documentation updated for pipeline version tracking separation from plugin version.
