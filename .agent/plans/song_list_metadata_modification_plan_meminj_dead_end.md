# Song List Metadata Modification — Analysis After Memory Injection Dead End

**Date:** 2026-07-23
**Status:** Planning — Need new approach after memory injection conclusively failed

## Problem Statement

We need to modify song list metadata (song names, artist names, sub-names) displayed in the Beat Saber PS4 song selection UI. 13 Rolling Stones DLC slots are replaced with custom songs, but the UI still shows original names/artists.

## Feature Flag: `enable_song_metadata_modification`

**This feature flag is PRESERVED for future use.** When a new approach is implemented, it will be gated behind this same flag. The flag defaults to `false` (disabled) and must be explicitly enabled in `features.json` to activate song metadata modification.

- **Flag name:** `enable_song_metadata_modification`
- **Default:** `false` (disabled)
- **Location:** `/data/GoldHEN/AFR/CUSA12878/features.json`
- **Pipeline:** `--set-feature enable_song_metadata_modification=true`
- **Plugin global:** `g_feature_song_metadata_modification`

When implementing a new approach, wire it behind this flag in `main.cpp`:
```c
if (g_feature_song_metadata_modification) {
    // new approach code here
}
```

## What We've Tried (All Failed)

### 1. Memory Injection (v0.66–v0.8024) — DEAD
- **Approach:** Scan process memory for BeatmapLevelSO objects or their string fields, patch in-place
- **Why it failed:** Strings not found in any scannable memory region after 15,000+ pages scanned
- **Root cause:** BeatmapLevelSO objects are lazily instantiated; strings don't exist in memory during startup

### 2. Pack Bundle Modification — DEAD
- **Approach:** Modify BeatmapLevelSO objects inside pack bundles before Addressables loads them
- **Why it failed:** Addressables catalog has CRC32 + file_size validation. Any single-byte change fails validation → CE-34878-0 crash

### 3. IL2CPP Method Hooks — DEAD
- **Approach:** Hook `get_songName()`, `get_DisplayName()`, constructors, `SetData()`, `SetContent()`
- **Why it failed:** IL2CPP AOT compiler inlines all getters; constructors never fire for Addressables-deserialized objects; `SetData`/`SetContent` never reached

### 4. UnityPy Bundle Modification — DEAD
- **Approach:** Use UnityPy to modify bundles with `save_typetree()`, `cab.save()`
- **Why it failed:** `save_typetree()` silently ignores BeatmapLevelSO; `cab.save()` produces incompatible format (+4 bytes)

## Alternative Approaches to Investigate

### A. Redirect Pack Bundle AND Catalog Together

**Concept:** If we redirect both the pack bundle AND the Addressables catalog JSON to a patched version with updated CRC/size, the validation would pass.

**Investigation needed:**
- Does `catalog.json` appear in the file-open log? (check v0.8020 log)
- Is it loaded via `open()` → hookable, or via a different path?
- Can we build a patched catalog with correct CRC/size for our modified bundles?

**Risk:** High — catalog format is complex, CRC must match exactly

### B. Hook Unity Rendering/UI Text

**Concept:** Instead of modifying data, intercept the text rendering pipeline. Hook TextMeshPro or Unity UI text functions to substitute displayed text.

**Investigation needed:**
- What UI framework does Beat Saber use? (TextMeshPro? uGUI?)
- Can we find the text-setting function via dlsym or module enumeration?
- Are Unity native runtime functions (not IL2CPP) hookable without inlining issues?

**Risk:** Medium — Unity native functions may not be inlined, but finding the right hook point is non-trivial

### C. mmap Hook to Intercept Bundle Data

**Concept:** Hook `mmap` or `read` at kernel level to intercept raw bundle data as it's being loaded, before the game parses it. Modify BeatmapLevelSO objects at byte level before deserialization.

**Investigation needed:**
- Does the game use `mmap()` or `read()` for bundle loading?
- Can we intercept at the right granularity?
- What's the performance impact of hooking mmap for every file?

**Risk:** Medium-High — mmap hook is very broad, may have performance issues

### D. Delayed Hook / UI Event Trigger

**Concept:** The core timing problem is that memory injection fires during startup, but strings don't exist yet. Hook a function that fires when the song list UI actually renders, then scan at that point.

**Investigation needed:**
- What function fires when the song list populates?
- Can we find `HandleDidSelectAnnotatedBeatmapLevelCollection` or similar?
- Is there a UI scroll event or list adapter callback?

**Risk:** Medium — requires finding the right UI event, but strings SHOULD exist when UI renders

### E. dlsym + Detour on IL2CPP Runtime API

**Concept:** Use `dlsym(RTLD_DEFAULT, "il2cpp_string_new")` to find IL2CPP string allocation, hook it to intercept string creation.

**Investigation needed:**
- Are IL2CPP runtime functions exported on PS4?
- Can we use module base + known offsets from IL2CPP dump to compute addresses?
- Would hooking `il2cpp_string_new` be too broad (fires for every string)?

**Risk:** High — functions may not be exported, hooking too broad

### F. resources.assets Redirect (Limited Scope)

**Concept:** For the 22 base game songs (not DLC), metadata is in `resources.assets`. This can be redirected via existing `open()` hook.

**Investigation needed:**
- Can we build a modified `resources.assets` with updated song names?
- Does the existing redirect system handle this file type?
- Only works for base game songs, not DLC (limitation)

**Risk:** Low — limited scope but potentially viable for base game songs

## Recommended Next Steps

1. **Check the v0.8020 file-open log** — Does `catalog.json` appear? If so, approach A becomes viable
2. **Research Unity UI hooking** — What framework does Beat Saber use? Can we hook text rendering?
3. **Test approach F** — Can we redirect `resources.assets` for base game songs?
4. **Investigate delayed trigger** — When does the song list UI actually render? Can we hook that event?

## Key Constraints

- PS4 FW 9.00 with GoldHEN
- GoldHEN Hook SDK available (Detour_DetourFunction with DetourMode_x64)
- Can hook: `fopen`, `open`, `close`, `mmap`, `read`, `write` (libc/syscall level)
- Cannot: modify files on PS4 filesystem directly (AFR only redirects reads, not writes)
- Memory injection approach abandoned — do not revisit
