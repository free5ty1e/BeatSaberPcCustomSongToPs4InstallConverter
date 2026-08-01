---
name: structural-beatmaplevelso-scan
description: "How to find and patch BeatmapLevelSO objects in RAM via structural scanning (klass range + version + string pointers + preview array validation) — the revived mode-selector injection (v0.8045, signal-free via sceKernelQueryMemoryProtection)"
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

- `16MB (0x1000000) – 64GB (0x1000000000)` — primary; **1MB page reads** (~65,536 total reads, same syscall count as the old 4GB@64KB pass → stutter stays brief). v0.77 found **17 candidates** here matching checks 1-3. **(v0.8045 scanned only 16MB–4GB + 8–8.25GB and found 0 — too narrow.)**
- `8GB (0x200000000) – 8.25GB (0x210000000)` — GC heap supplement; 64KB page reads.
- When a page read fails (hole/partial mapping), jump to the next mapping boundary via `sceKernelQueryMemoryProtection` result instead of stepping page-by-page.
- Page step 64KB/1MB, stride 32 bytes (candidates must be 32-aligned).
- Cost dominated by probing pages (~1-2s for the full pass). **Accept the pause.**

## System.String length pitfall (v0.8046 bugfix)

IL2CPP `System.String`: `_stringLength` at 0x10 (or 0x14 on PS4), chars UTF-16LE after. When probing both offsets, `len_14` is the **first two UTF-16 chars combined** (e.g. `"St"` → `0x00740053`), which is huge and NEVER 0 for a non-empty string. Length-selection logic must only use `len_14` when it's a plausible length `(0,256)`:

```c
if (len_10 > 0 && len_10 < 256 && (len_14 == 0 || len_14 >= 256)) { len = len_10; chars = str+0x14; }
else if (len_14 > 0 && len_14 < 256)                             { len = len_14; chars = str+0x18; }
else                                                              { len = len_10; chars = str+0x14; }
```

The v0.8045 one-liner `(len_14 == 0) ? len_10 : len_14` always picked the garbage `len_14`, so every string extraction failed and the klass find returned "not found".

## Safe Reads — USE sceKernelQueryMemoryProtection, NOT SIGNAL HANDLERS (v0.8045)

**Every memory read in the plugin now goes through `mode_try_read()`, backed by the `sceKernelQueryMemoryProtection` syscall** (declared in `libkernel.h`, linked via `-lkernel`). It reports the mapped region `[start, end)` and protection flags of an address WITHOUT triggering a fault:

```c
static int mode_try_read(uint64_t addr, void* buf, size_t size) {
    if (size == 0 || addr < 0x1000000ULL) return 0;
    // one-time self-test against a known-good address; if the syscall is a stub,
    // disable the scan entirely (fail-closed, no crash)
    if (!g_qmp_ok) { /* verify range/prot of &g_qmp_ok; set g_qmp_ok or return 0 */ }
    void *r_start = NULL, *r_end = NULL; int32_t prot = 0;
    if (sceKernelQueryMemoryProtection((void*)addr, &r_start, &r_end, &prot) != 0) return 0;
    if (!(prot & 1)) return 0;                          // SCE_KERNEL_PROT_CPU_READ = 0x1
    if (!r_start || !r_end) return 0;
    if ((uint64_t)r_end - (uint64_t)r_start < size) return 0;
    if (addr + size > (uint64_t)r_end) return 0;        // region must cover [addr, addr+size)
    memcpy(buf, (void*)addr, size);
    return 1;
}
```

**Why (Exp 166 confirmed):** v0.8043 (worker thread) AND v0.8044 (synchronous game-thread scan) BOTH crashed with CE-34878-0 at the same point — the crash log ends at `[MODE] Starting BeatmapLevelSO memory scan...`. Signal handlers are **process-wide**, and Unity's GC throws page-protection SIGSEGV/SIGBUS faults as a **normal part of write-barrier/compaction during song-list rendering**. Any process-wide handler installed while the game is actively rendering hijacks those faults → `siglongjmp` to the scan stack → instant crash. The thread that runs the scan is irrelevant; the handlers themselves are the hazard.

Rules:
1. **Never install SIGSEGV/SIGBUS handlers while the game is actively rendering/allocating** (song list). This includes per-call `sigaction` wrappers like the old `extract_utf16_string`.
2. **Use `sceKernelQueryMemoryProtection` for safe reads** — it cannot be hijacked. Verify once against a known-good address and fail-closed if it behaves like a stub (mincore/msync are stubs on PS4; query-memory-protection is a real, commonly-used syscall).
3. If a fault-catching read is truly unavoidable, do it ONLY at quiescent moments (the open()/redirect song-start hook) — v0.74–v0.8008 proved that timing is safe (17 candidates, no crash).
4. `sigsetjmp`/`siglongjmp` are thread-stack-scoped; never jump across threads.
5. Background threads created from hooks are unsafe (v0.8016, `scePthreadCreate`).

## Patching

1. From any BSL's Standard preview set, read the Standard `BeatmapCharacteristicSO*` (first set + 0x10).
2. Scan ±16MB around it for objects with the SAME klass; validate each by extracting `_serializedName` (0x30) and matching `"OneSaber"`, `"NoArrows"`, `"90Degree"`, `"360Degree"`.
3. Build a new `Il2CppSZArray` of 5 `PreviewDifficultyBeatmapSet` objects (malloc'd, klass copied from originals, each referencing the right charSO and a copy of Standard's preview difficulty list).
4. Atomically write the new array pointer into `bsl_addr + 0x98`. 8-byte aligned store = atomic on ARM64/x64.

Note: the pipeline's per-song bundles already contain all 5 mode `_difficultyBeatmapSets` (Phase 1), so once the UI shows the mode buttons, gameplay data for each mode already exists (cloned Standard patterns; unique 360/90 .dat files are not yet compiled into per-mode TextAssets — roadmap M5).

## Related

- [[il2cpp-dump-mode-selector-hook]] — Class layouts, method RVAs, hook dead-ends (getter inlined, ctor never fires)
- [[song-metadata-addressables-structure]] — Pack vs per-song bundle hierarchy, CRC blocker
- [[memory-injection-addressables-bypass]] — The abandoned exact-klass/string-search approach (context)
- [[ps4-environment-system]] — Signal-handling platform gotcha
