---
name: ps4-environment-system
description: "How the PS4 game maps songs to environments - environment is NOT in individual AssetBundles but in the game's song database"
metadata:
  type: reference
---

# PS4 Environment System

The PS4 version of Beat Saber uses **Unity Addressables** for asset management. The environment for each song is determined by the song's album/pack association, NOT by data within the individual song AssetBundle.

## Key findings

1. **Environment is NOT in the bundle** — The `BeatmapLevelData` MonoBehaviour (in each song's AssetBundle) has no `_environment` field. It only stores `_audioClip`, `_audioDataAsset`, and `_difficultyBeatmapSets`.

2. **Environment is tied to the album/pack** — The game determines which environment to load based on which album/pack the song belongs to. This association is stored in the game's Addressable content system.

3. **Addressable bundles** — The game's content is split across ~1000+ Addressable bundles in `StreamingAssets/aa/PS4/`. These include:
   - `monoscripts` bundles (MonoBehaviour script data)
   - `unitybuiltinshaders` bundles (shader data)
   - Other bundles for game content (level data, environments, etc.)

4. **Song database** — The `BeatmapLevelPack` ScriptableObjects that define which songs exist and their environments are stored in the Addressable system. These are NOT directly accessible via UnityPy in the resources.assets files we found.

## Practical implications

- **Current behavior**: Our plugin redirects a specific song (e.g., Start Me Up) to a custom AssetBundle. The game still thinks it's the original song, so it loads the original song's environment (Rolling Stones for Start Me Up).

- **Changing environments**: To use a different environment, we would need to:
  1. Modify the game's song database in resources.assets (requires UABEA and understanding the format)
  2. Add a new song entry pointing to our custom bundle with the desired environment
  3. This is part of Milestone 4: "Add Custom Song to Album"

- **Fallback/Default**: The safest fallback is whatever environment the redirected song uses. For Start Me Up, that's the Rolling Stones environment.

## Available PS4 environments

The PS4 game has environments from:
- OST Volume 1-5 (DefaultEnvironment, Triangle, BigMirror, Nice, etc.)
- DLC packs (Interscope, BTS, Rolling Stones, etc.)

Custom environment names from BeatSaver (e.g., `FHMPlat`, `Kwangya_Portal`) do not exist on PS4 and cannot be used without creating new environment assets.

## Related

- [[toolchain-and-build]] — For UABEA and asset patching tools
- [[assetbundle-structure]] — For how AssetBundles are structured

---

## PS4 Process Signal Handling — CRITICAL (Exp 165–166, 2026-07-31)

**Never install process-wide SIGSEGV/SIGBUS handlers for memory probing while the game is actively rendering/allocating (e.g. the song list). Doing so crashes the game — REGARDLESS of which thread runs the scan.**

### Why

- `sigaction()` signal dispositions are **per-process**, not per-thread.
- Unity's garbage collector (and other subsystems) use page-protection signals (SIGSEGV/SIGBUS via mprotect) internally for write barriers / dirty tracking.
- While our handlers are installed, a GC page-protection fault on the **main game thread** is delivered to *our* handler → it calls `siglongjmp()` to a scan `sigjmp_buf` → the main thread resumes executing in the wrong stack frame → catastrophic corruption → instant crash (CE-34878-0), no error dialog.

### Evidence

| Version | Approach | Result |
|---------|----------|--------|
| v0.74–v0.8008 | Synchronous scan in **song-start redirect hook** (GC quiescent), persistent handlers | ✅ Found 17 candidates, no crash |
| v0.8043 | Scan in detached pthread, per-call sigaction | ❌ Instant crash on entering Solo song list (GC active) |
| v0.8044 | **Synchronous** scan in MoveNext hook (song-list render), persistent handlers | ❌ **Crash again at the same point** — log ends at `[MODE] Starting BeatmapLevelSO memory scan...`. The thread is irrelevant; the handlers during active rendering are the hazard. |
| v0.8045 | Signal-free: `sceKernelQueryMemoryProtection` syscall reads | 🔲 Deployed, awaiting test |

### Rules

1. **Prefer `sceKernelQueryMemoryProtection` for safe reads** — a real libkernel syscall that reports the mapped range `[start,end)` + protection of an address WITHOUT faulting. Self-test it once against a known-good address and fail-closed (disable the scan) if it's a stub — `mincore`/`msync` are stubs on PS4, but query-memory-protection is a real, commonly-used syscall.
2. If a fault-catching read is truly unavoidable, run it ONLY at quiescent moments — the open()/redirect song-start hook, as v0.74–v0.8008 proved safe. **Never during song-list rendering.**
3. `sigsetjmp`/`siglongjmp` must be set up and executed on the **same thread** (a `sigjmp_buf` is thread-stack-scoped).
4. **Background threads created from hooks are unsafe** (v0.8016, `scePthreadCreate`).
5. The v0.8045 plugin removed ALL signal handlers: `mode_try_read()`, `mode_extract_string()`, and `extract_utf16_string()` all go through `sceKernelQueryMemoryProtection`.
