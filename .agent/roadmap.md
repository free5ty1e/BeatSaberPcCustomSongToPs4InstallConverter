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

## 🔧 Milestone 3: Custom Song Format Conversion ✅ COMPLETE
### Beatmap Data Replacement ⬅️ VERIFIED WORKING
- [x] Beatmap gzip replacement via `save_typetree` (not `set_raw_data` — had serialization bugs)
- [x] **ROOT CAUSE FIXED:** m_Script is JUST gzip data — no decompressed_size prefix!
- [x] `save_typetree` verified byte-perfect with original (v0.39diag)
- [x] **V3 note format conversion** — `_notes` → `colorNotes` + `colorNotesData` ✅
  - [x] Note properties deduplication (x, y, c, d) into data arrays
  - [x] V3 field order matches game expectations (verified with working bundle)
- [x] **Obstacles conversion** — `_obstacles` → `obstacles` + `obstaclesData` ✅
- [x] Environment renders correctly with custom beatmaps ✅
- [ ] **Bomb notes conversion** — `_notes` type=3 → `bombNotes` + `bombNotesData`
- [ ] **Chain conversion** — preserve/convert custom song's chain data
- [ ] **Arc conversion** — preserve/convert custom song's arc data
- [ ] Beatmap events from song handled (lighting data — separate from lightshow)

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
- [x] ~~m_Script content corrupted by extra decompressed_size prefix~~ **FIXED!** Just gzip data, no prefix.
- [x] ~~`save_typetree` serialization inconsistency~~ **FIXED!** Works byte-perfect.
- [x] ~~Latin1 vs surrogateescape encoding for binary data~~ **FIXED!** Use surrogateescape.
- [x] ~~V3 format conversion needed for PS4 compatibility~~ **FIXED!** V2→V3 working.
- [ ] FSB5 audio needs FMOD tools (fsbank) to convert custom audio tracks
- [ ] BombNotes from custom songs not yet converted (type=3 in V2 `_notes`)
- [ ] Chains from custom songs not yet converted
- [ ] Arcs from custom songs not yet converted
- [ ] Cover art not injected into bundle
- [ ] Converting non-Standard characteristics (NoArrows, OneSaber, 360, 90)
- [ ] Multi-bundle songs (audio longer than single AssetBundle capacity)e-identical output but game fails to load
- [ ] V2→V3 note conversion may produce wrong field order/format
- [ ] `set_raw_data` serialization bug (workaround: use `save_typetree`)
- [ ] Latin1 vs surrogateescape encoding for binary data
- [ ] FSB5 audio needs FMOD tools (fsbank)
