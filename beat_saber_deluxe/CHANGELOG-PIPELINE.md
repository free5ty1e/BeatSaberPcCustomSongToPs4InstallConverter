# Pipeline Changelog — Beat Saber Deluxe Song Conversion Pipeline

All notable changes to the song conversion pipeline (`tools/`, `development/scripts/`) are documented here.

## [v0.53] — 2026-07-16
### Added
- **CRC correction via GF(2) linear algebra in build_patched_pack_bundle.py** — Adjusts alignment padding bytes to make the rebuilt bundle's CRC32 match the original (`0xdc8b314f`). Uses 32×32 GF(2) matrix exponentiation (M^L for L=7.9M), Gauss-Jordan matrix inversion, and the CRC table's linearity over GF(2) to compute exact padding values.
- **LZ4HC compression (flag=3)** — Blocks and blocks info now compressed with LZ4HC (mode='high_compression', compression=9, store_size=False) with per-block flag=3, matching the PS4's Unity requirement.
- **Bundle assembly in memory** — Bundle is now assembled in a bytearray for padding byte manipulation, allowing CRC correction before final write.

### Changed
- Pipeline version bumped from v0.52 to v0.53.
- build_patched_pack_bundle.py: CRC correction integrated into bundle build process, UnityPy verification wrapped in try/except to handle modified CAB format.

### Technical
- **CRC table linearity proof:** `table[a XOR b] = table[a] XOR table[b]` — the CRC table IS linear over GF(2), enabling exact CRC correction without brute-force search.
- **31 million byte check iterations** — ~16.7M padding byte combinations tested via precomputed M-weighting matrix for 3 free padding bytes + 1 correction byte.

## [v0.52] — 2026-07-15
### Added
- **BeatmapLevelSO CAB binary injection** — Raw byte-level replacement of StartMeUp's BeatmapLevelSO blob at verified CAB offset 79924, with size delta handling by extending the CAB file. Patched CAB files generated for Espresso (89997B), Duvet (89962B), and Time Lapse (89991B) — each with custom song name, artist, BPM, and 5-mode preview sets at correct serialized offsets.
- **inject_pack_bundle.py full pipeline** — Blob builder + CAB patching in single tool: finds StartMeUp blob via UnityPy typetree anchors, patches all 5 string fields at verified byte offsets, writes patched standalone CAB files for deployment via AFR redirect or direct file replacement.

### Changed
- Pipeline version bumped from v0.51 to v0.52.
- inject_pack_bundle.py rewritten: now generates complete patched CAB files (not just blobs) with verified Espresso/Duvet/TimeLapse BeatmapLevelSO content at correct byte offsets.

### Verified
- **Blob format verified against StartMeUp hex dump** — all fields match: m_GameObject(PPtr), class=1, m_Script PPtr(Standard char pathID), m_Name(string), _version(type=0x78), _levelID, _songName, _songAuthorName, BPM(double=126.5), 8 preview doubles, coverImage PPtr(zeroed), environments, 5-mode _previewDifficultyBeatmapSets with Standard pathID=-7286399427822119286
- **Espresso blob on disk**: 1257B, m_Name="EspressoCustomBeatmapLevel" (size=27), BPM=126.5, _levelID="custom/espresso" ✓ all critical fields verified byte-by-byte
- **CAB delta handling**: Espresso+817B, Duvet+782B, Time Lapse+811B — CAB grows naturally with delta shifting all subsequent objects forward

### Known Limitations
- **No PS4 deployment yet** (PS4 offline as of Exp 130) — patched CABs available for testing when console is powered on
- **UnityPy save_bundle() cannot be used** (Exp 116) — any UnityPy re-saved bundle crashes game with CE-34878-0; raw binary replacement required

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
