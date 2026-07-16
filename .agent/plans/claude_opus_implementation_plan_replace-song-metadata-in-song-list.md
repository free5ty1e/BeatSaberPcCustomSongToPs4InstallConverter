# Next Steps & Strategy for Beat Saber Deluxe — Song Info & Mode Selector

## Situation Assessment

### What Works ✅
- **Per-song bundle redirect**: Replace any song's audio + beatmaps with custom content. Fully operational (12 Rolling Stones slots hijacked).
- **Pack bundle redirect (unmodified)**: Exp 134a proved that redirecting the Addressables pack bundle `therollingstones_pack_assets_all_...` to an AFR copy works — game loads normally.
- **Pipeline**: v0.52 — builds custom bundles with PCM16 audio, 5-difficulty beatmap conversion, all naming conventions handled.
- **Plugin**: v0.65 — dynamic redirect via `redirects.json`, case-insensitive matching.

### What Doesn't Work ❌
- **Any modified pack bundle crashes the game (CE-34878-0)** — Tested exhaustively:
  - Exp 132: `bf.save("original")` with `save_typetree()` → crash
  - Exp 133: `cab.save()` + manual bundle build → crash
  - Exp 134b: Text-only byte patch (same blob size, LZ4 flag=2) → crash
  - Exp 135: Text-only byte patch with LZ4HC (flag=3) → **STILL CRASH**
- **UnityPy `save_typetree()` silently ignores modifications** for BeatmapLevelSO in Unity 2022.3
- **UnityPy `cab.save()` produces incompatible CABs** (+4 bytes vs original)
- **IL2CPP hooks are dead** — all 4 approaches experimentally proven non-viable (constructor never fires, getter inlined, SetData conditional, SetContent crashes)

### The Core Problem

The pack bundle that contains `BeatmapLevelSO` (with song name, artist, mode selector) **cannot be modified by any known method**. Even trivial same-size text patches with correct LZ4HC compression still crash. This means the crash is **NOT from compression flags** — it's from something subtler in the bundle rebuilding process.

> [!IMPORTANT]
> **Exp 135 result is the most critical data point**: LZ4HC (flag=3) + text-only patch (same blob size) + manual bundle build **STILL CRASHED**. This eliminates compression as the root cause and points to a structural difference in how we rebuild the UnityFS wrapper.

---

## Root Cause Hypotheses for Pack Bundle Crashes

Since we've eliminated compression (flag=3 matches), blob content changes (same size), and UnityPy serialization (we bypass it), the remaining suspects are:

| # | Hypothesis | Evidence For | Evidence Against | Test |
|---|-----------|-------------|-----------------|------|
| 1 | **Block boundary alignment differs** — recompression produces different block sizes, shifting block boundaries | Bundle size differs (7,905,246 vs 7,902,803) | Both have 65 blocks with flag=3 | Compare per-block sizes original vs rebuilt |
| 2 | **Blocks info hash / checksum** — PS4 validates the blocks info section | Blocks info size differs (198 vs 199 bytes) | No known Unity checksum mechanism | Binary diff the blocks info sections |
| 3 | **Node path strings differ** — CAB name or resource names slightly different | Not checked | Nodes are copied from original | Hex compare node metadata |
| 4 | **UnityFS header field mismatch** — file_size, engine version string, padding | Different total sizes | We write identical header fields | Binary compare first 64 bytes |
| 5 | **CAB data within bundle is byte-different** — even "same size" text patch changes the decompressed CAB bytes in ways we don't account for | We modify CAB raw bytes | Text-only, same size | Binary diff decompressed CAB bytes vs original |
| 6 | **The game checks bundle file hash/size against catalog** — the Addressables catalog (`catalog.json`) may contain a hash or expected file size for each bundle | Addressables systems commonly hash content | We haven't checked catalog.json | Parse `catalog.json` for hash/size fields |

### Most Likely: Hypothesis 6 — Addressables Catalog Hash

Addressables v1.x+ catalogs (`catalog.json` or `catalog.bin`) often include **content hashes** or **CRC checksums** per bundle. If the PS4 game checks the hash at load time, **any modification** to the bundle file would fail — even a single-byte change. This would explain why:
- Original bundle via redirect: ✅ (hash matches)
- ANY modified bundle: ❌ (hash mismatch → CE-34878-0)

---

## Proposed Experiment Sequence

### Phase 1: Investigate the Addressables Catalog (Priority: HIGHEST)

> [!TIP]
> This is the single most important investigation. If the catalog contains hashes, we need to either patch the catalog too or abandon pack bundle modification entirely.

#### Experiment 136: Parse Addressables Catalog for Bundle Hashes
1. Locate `catalog.json` or `catalog.bin` in `ps4_dump/CUSA12878-patch/Media/StreamingAssets/aa/PS4/`
2. Parse it (it's a Unity Addressables ContentCatalog — JSON with base64-encoded sections)
3. Search for:
   - Bundle file hashes (usually SHA-256 or CRC32)
   - Expected file sizes per bundle
   - Content version strings
4. Specifically find the entry for `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle`
5. Check if there's a hash field — if yes, this is almost certainly the crash cause

**If catalog has hashes → Phase 1b: Catalog Patching**
- The catalog is itself loaded as an Addressables asset. We may be able to:
  - Redirect the catalog file via AFR (same as pack bundle redirect)
  - Patch the hash for our modified bundle
  - This would require understanding the catalog binary format

**If catalog has NO hashes → Phase 2: Binary Diff**

### Phase 2: Binary Diff Original vs Rebuilt Bundle (if no catalog hash)

#### Experiment 137: Bit-Level Bundle Comparison
1. Decompress both original and LZ4HC-rebuilt bundles fully
2. Compare:
   - UnityFS header (bytes 0-63)
   - Blocks info section (compressed + decompressed)
   - Per-block boundaries and sizes
   - CAB raw bytes (should differ only at patched text offsets)
3. Find the exact byte(s) that differ unexpectedly
4. Fix the builder to match the original structure exactly

### Phase 3: Alternative Approach — Bypass Pack Bundle Entirely

If pack bundle modification proves impossible (catalog hash + can't patch catalog), pivot to approaches that don't require modifying the pack bundle:

#### Approach A: Per-Song Bundle Metadata (Display Info)

Even though `BeatmapLevelSO` isn't in per-song bundles, we can try:
1. **Add a BeatmapLevelSO to the per-song bundle** — the game might read metadata from the loaded bundle if it finds a matching object
2. This would require raw CAB manipulation (not UnityPy serialization) to add a new object entry to the per-song bundle's SerializedFile

#### Approach B: Plugin-Based String Interception (NEW)

Instead of hooking IL2CPP methods (proven dead), hook **lower-level string operations**:
1. Hook `il2cpp_string_new` or the game's internal string allocation
2. When the game creates a string matching "Start Me Up", replace it with "Espresso"
3. This is a shotgun approach but might work for display names without needing function-specific hooks
4. Risk: may change strings in unintended places

#### Approach C: resources.assets Patching (Base Game Songs Only)

For the 22 base game songs (not DLC), metadata is in `resources.assets`:
1. We already know the binary format (documented in [song-metadata-storage.md](file:///mnt/c/Users/test/Documents/code/BeatSaberPs4CustomSongSupport/.agent/llm-wiki-knowledge-base/song-metadata-storage.md))
2. Patch song names/artists in `resources.assets`
3. Redirect `resources.assets` via the plugin
4. **Limitation**: Only works for the 22 base songs in the "Extras" pack, not Rolling Stones DLC

#### Approach D: Mode Selector via Per-Song Bundle (Already Partially Working)

Exp 129 showed that `add_mode_characteristics()` successfully adds mode entries to per-song bundles. The pipeline flag `--enable-modes` works. But we need to verify on PS4:
1. Build a per-song bundle with `--enable-modes OneSaber,90Degree`
2. Deploy and test — does the mode selector show the extra modes?
3. If yes, this goal is achieved WITHOUT needing pack bundle modification

---

## Recommended Execution Order

```
1. Experiment 136: Parse Addressables catalog for hashes
   ├── If hashes found → Experiment 136b: Can we redirect + patch the catalog?
   │   ├── If yes → Rebuild pack bundle + patched catalog → test
   │   └── If no → Pivot to Approaches A-D
   └── If no hashes → Experiment 137: Binary diff
       └── Fix builder → test

2. IN PARALLEL with above:
   Experiment 138: Test --enable-modes on PS4
   - Build per-song bundle with OneSaber + 90Degree modes
   - Deploy and test mode selector visibility
   - This doesn't require pack bundle modification

3. Experiment 139: Try resources.assets patching for display info
   - Lower risk, well-understood binary format
   - Test with one of the 22 base songs if we expand beyond Rolling Stones
   - Or try Approach B (string interception) for DLC songs

4. If all else fails for display info:
   Experiment 140: Build custom BeatmapLevelSO in per-song bundle
   - Raw CAB manipulation to add object entry
   - Most complex but doesn't depend on pack bundle modification
```

---

## Key Knowledge Gaps to Fill

| Gap | Why It Matters | How to Fill |
|-----|---------------|------------|
| Addressables catalog format/hashing | Determines if pack bundle modification is viable AT ALL | Parse `catalog.json` from ps4_dump |
| Per-song bundle mode selector behavior on PS4 | Determines if we need pack bundle for modes | Deploy `--enable-modes` bundle and test |
| `resources.assets` redirect viability | Alternative path for song name display | Test redirect of resources.assets via plugin |
| String allocation interception | Backup approach for display name | Research `il2cpp_string_new` hooking |

---

## Files to Examine Next

1. `ps4_dump/CUSA12878-patch/Media/StreamingAssets/aa/PS4/catalog.json` — **THE critical file**
2. `ps4_dump/CUSA12878-patch/Media/StreamingAssets/aa/PS4/settings.json` — Addressables settings
3. `beat_saber_deluxe/tools/build_patched_pack_bundle.py` — current builder (has LZ4 bug, not LZ4HC)
4. `beat_saber_deluxe/tools/full_custom_song_pipeline.py` — `add_mode_characteristics()` for mode testing
