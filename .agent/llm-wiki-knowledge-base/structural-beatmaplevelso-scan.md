---
name: structural-beatmaplevelso-scan
description: "How to find and patch BeatmapLevelSO objects in RAM via structural scanning (klass range + version + string pointers + preview array validation) — the revived mode-selector injection (v0.8042+) and its thread-safety rules"
metadata:
  type: reference
---

# Structural BeatmapLevelSO Scan (Mode Selector Injection)

## Overview

The mode selector UI reads `BeatmapLevelSO._previewDifficultyBeatmapSets` (offset `0x98`) from the **pack bundle's** BeatmapLevelSO ScriptableObject — NOT the per-song bundle's `BeatmapLevel._difficultyBeatmapSets` (which Phase 1 of the pipeline injects and which only affects gameplay data). Pack-bundle file patching is blocked by Addressables CRC+size validation, so Phase 2 patches the BeatmapLevelSO objects **in RAM** at runtime.

Unlike the abandoned exact-klass search (v0.66–v0.8015, searched for klass == `0x2012007E0` as first 8 bytes, 0 matches), this approach finds objects **structurally**: it does NOT need the exact klass value in advance.

## Object Layouts (IL2CPP runtime, PS4)

```
BeatmapLevelSO (PersistentScriptableObject):
  0x00 klass (in [0x80000000,0x90000000] or [0x200000000,0x210000000])
  0x18 _version (int, 1-50)
  0x20 _levelID (System_String*)
  0x28 _songName (System_String*)
  0x38 _songAuthorName (System_String*)
  0x98 _previewDifficultyBeatmapSets (Il2CppArray*)  ← TARGET FIELD

PreviewDifficultyBeatmapSet (0x20 bytes):
  0x00 klass
  0x10 BeatmapCharacteristicSO* _beatmapCharacteristic
  0x18 Il2CppArray* _previewDifficultyBeatmaps (List of PreviewDifficultyBeatmap)

PreviewDifficultyBeatmap struct: 36 bytes
Il2CppSZArray header: 0x00 klass, 0x18 max_length, 0x20 data
System_String: 0x10 or 0x14 _stringLength (try both), chars UTF-16LE after

BeatmapCharacteristicSO: 0x30 _serializedName (System_String*)
```

## Structural Signature (for finding the klass without an anchor)

A BeatmapLevelSO candidate passes ALL of:
1. klass pointer in range `[0x80000000, 0x90000000]` (module range) or `[0x200000000, 0x210000000]` (8GB klass range)
2. `_version` (0x18) in `[1, 50]`
3. `_levelID` (0x20), `_songName` (0x28), `_songAuthorName` (0x38) are valid pointers (`>= 0x1000000`)
4. `_previewDifficultyBeatmapSets` (0x98) is structurally valid (`mode_preview_arr_ok`): array klass in range, max_length 1-10, first set klass in range, `_beatmapCharacteristic` valid ptr, `_previewDifficultyBeatmaps` valid ptr

The FIRST matching candidate's klass pointer is the BeatmapLevelSO klass (all instances share it). Then collect ALL objects with that exact klass passing the same validation.

## Scan Ranges & Cost

- `16MB (0x1000000) – 4GB (0x100000000)` — primary; ~65,280 pages of 64KB. v0.77 found **17 candidates** here matching checks 1-3.
- `8GB (0x200000000) – 8.25GB (0x210000000)` — GC heap supplement; ~4,096 pages.
- Page step 64KB, stride 32 bytes (candidates must be 32-aligned).
- Cost dominated by SIGSEGV probing of unmapped pages (~1-2s for the 4GB pass). **Accept the pause.**

## Patching

1. From any BSL's Standard preview set, read the Standard `BeatmapCharacteristicSO*` (first set + 0x10).
2. Scan ±16MB around it for objects with the SAME klass; validate each by extracting `_serializedName` (0x30) and matching `"OneSaber"`, `"NoArrows"`, `"90Degree"`, `"360Degree"`.
3. Build a new `Il2CppSZArray` of 5 `PreviewDifficultyBeatmapSet` objects (malloc'd, klass copied from originals, each referencing the right charSO and a copy of Standard's preview difficulty list).
4. Atomically write the new array pointer into `bsl_addr + 0x98`. 8-byte aligned store = atomic on ARM64/x64.

Note: the pipeline's per-song bundles already contain all 5 mode `_difficultyBeatmapSets` (Phase 1), so once the UI shows the mode buttons, gameplay data for each mode already exists (cloned Standard patterns; unique 360/90 .dat files are not yet compiled into per-mode TextAssets — roadmap M5).

## CRITICAL Thread-Safety Rules (Exp 165 crash)

**Never run the scan from a background/worker thread.** v0.8043 did exactly that and crashed the game instantly on entering the Solo song list:

- `sigaction()` dispositions are **process-wide**, not per-thread.
- Unity's GC uses page-protection signals (SIGSEGV/SIGBUS via mprotect) for write barriers.
- While the worker's handlers were installed, a GC fault on the **main thread** was delivered to our handler → `siglongjmp` to the **worker thread's** jmpbuf → main thread resumed in the worker's stack → instant crash (no error dialog).

Rules:
1. Run the scan **synchronously inside the hook on the game thread** (game paused → its own handlers can't fire).
2. Install handlers ONCE for the whole scan (`mode_install_handlers()`), restore ONCE (`mode_restore_handlers()`) — not per page read.
3. `sigsetjmp`/`siglongjmp` are thread-stack-scoped; never jump across threads.
4. This is consistent with the older lesson: background threads created from hooks are unsafe (v0.8016, `scePthreadCreate`).

## Related

- [[il2cpp-dump-mode-selector-hook]] — Class layouts, method RVAs, hook dead-ends (getter inlined, ctor never fires)
- [[song-metadata-addressables-structure]] — Pack vs per-song bundle hierarchy, CRC blocker
- [[memory-injection-addressables-bypass]] — The abandoned exact-klass/string-search approach (context)
- [[ps4-environment-system]] — Signal-handling platform gotcha
