# Beat Saber PS4 Custom Song Support — Roadmap

## 🏆 Milestone 1: Plugin Infrastructure ✅
- [x] GoldHEN plugin loads without crash (AFR path, no jailbreak)
- [x] File logging via sceKernelOpen/Write to AFR directory
- [x] Detour hooks for open() without jailbreak
- [x] AssetBundle internal rename via UnityPy (m_Name + container path)
- [x] Notification fixed (was hardcoded v0.37, now uses PLUGIN_VERSION)

## 🎯 Milestone 2: File Redirect & Asset Loading ✅
- [x] open() hook redirects BeatmapLevelData files to custom bundles
- [x] Cross-song redirect confirmed (Start Me Up → $100 Bills)
- [x] Other songs unaffected (targeted redirect)
- [x] AFR directory auto-creation with permissions fix

## 🔧 Milestone 3: Custom Song Format Conversion 🚧 IN PROGRESS
### Beatmap Data Replacement
- [x] Beatmap gzip replacement via `set_raw_data` + `save_typetree`
- [x] Compressed size fix (m_Script length = compressed size, not decompressed)
- [x] `save_typetree` verified byte-perfect with original (v0.39diag)
- [ ] **V3 note format conversion (CURRENT ISSUE)** — `_notes` → `colorNotes` + `colorNotesData`
  - [x] Note properties deduplication (x, y, c, d) into data arrays
  - [ ] Verify V3 field order matches game expectations
  - [ ] Test: minimal beat change (5.5→5.0) to isolate save_typetree vs content issue
- [ ] **Obstacles conversion** — `_obstacles` → `obstacles` + `obstaclesData` (custom song's data)
- [ ] **Bomb notes conversion** — convert custom song's `_notes` with type=3 → `bombNotes`
- [ ] **Chain conversion** — preserve/convert custom song's chain data
- [ ] **Arc conversion** — preserve/convert custom song's arc data
- [ ] Environment renders correctly with custom beatmaps
- [ ] Beatmap events from song handled (lighting data)

### Audio Replacement
- [ ] Audio format analysis (FSB5 structure on PS4)
- [ ] Install FSB5 creation tools (fsbank or similar)
- [ ] Replace AudioClip with custom song audio
- [ ] Update AudioClip metadata (length, sample rate, etc.)

### Visual Data
- [ ] Cover art injection into bundle
- [ ] Cover art display in song selection menu

## 📋 Milestone 4: Add Custom Song to Album
- [ ] Install UABEA via Wine for resources.assets editing
- [ ] Analyze resources.assets song database structure
- [ ] Add custom song entry to existing pack
- [ ] Add custom song to "My Songs" / custom pack
- [ ] Verify song appears in UI and is playable

## 🎨 Milestone 5: Full Custom Song Pipeline
- [ ] End-to-end script: BeatSaver download → PS4 AssetBundle
- [ ] Devcontainer tools persisted (lz4, UnityPy, fmod_toolkit)
- [ ] Convert ALL beatmap components (notes, obstacles, bombs, chains, arcs)
- [ ] Audio conversion (FSB5 with custom audio)
- [ ] Cover art injection
- [ ] Resources.assets patching for new song entries

## 🔬 Known Issues & Investigations
- [ ] `save_typetree` produces Byte-identical output but game fails to load
- [ ] V2→V3 note conversion may produce wrong field order/format
- [ ] `set_raw_data` serialization bug (workaround: use `save_typetree`)
- [ ] Latin1 vs surrogateescape encoding for binary data
- [ ] FSB5 audio needs FMOD tools (fsbank)
