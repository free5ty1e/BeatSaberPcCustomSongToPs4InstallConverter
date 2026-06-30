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
- [x] Beatmap gzip replacement via `set_raw_data` + `save_typetree`
- [x] Compressed size fix (m_Script length = compressed size, not decompressed)
- [x] V2→V3 format conversion (`_notes` → `colorNotes` + `colorNotesData`)
- [x] V3 structure preservation (keep template's bombNotes, chains, arcs)
- [x] Custom obstacles from song (`_obstacles` → `obstacles` + `obstaclesData`)
- [ ] ⬅️ THIS IS THE NEXT TEST - v0.43 deployed with template-structure V3
- [ ] Audio replacement (FSB5 format)
- [ ] Cover art replacement

## 📋 Milestone 4: Add Custom Song to Album
- [ ] Install UABEA via Wine for resources.assets editing
- [ ] Modify resources.assets song database to add new song entries
- [ ] Assign custom songs to existing packs
- [ ] Create new custom packs

## 🎨 Milestone 5: Full Custom Song Pipeline
- [ ] End-to-end script: BeatSaver download → PS4 AssetBundle
- [ ] Devcontainer tools persisted (lz4, UnityPy, fmod_toolkit)
- [ ] Beatmap data conversion (notes + obstacles + events)
- [ ] Audio conversion (FSB5 with custom audio)
- [ ] Cover art injection
- [ ] Resources.assets patching for new song entries

## 🔬 Known Issues & Investigations
- [ ] Blank background with custom beatmaps (V3 format fix in progress)
- [ ] `set_raw_data` serialization bug (workaround: use `save_typetree`)
- [ ] Latin1 vs surrogateescape encoding for binary data
- [ ] FSB5 audio needs FMOD tools (fsbank)
