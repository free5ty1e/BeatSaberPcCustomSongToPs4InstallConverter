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

## PS4 Process Signal Handling — CRITICAL (Exp 165, 2026-07-31)

**Never install process-wide SIGSEGV/SIGBUS handlers (for memory probing) from a background/worker thread in a game hook. Doing so crashes the game instantly.**

### Why

- `sigaction()` signal dispositions are **per-process**, not per-thread.
- Unity's garbage collector (and other subsystems) use page-protection signals (SIGSEGV/SIGBUS via mprotect) internally for write barriers / dirty tracking.
- While our handlers are installed, a GC page-protection fault on the **main game thread** is delivered to *our* handler → it calls `siglongjmp()` to the **worker thread's** `sigjmp_buf` → the main thread resumes executing in the worker's stack frame → catastrophic corruption → instant crash back to the PS4 menu, no error.

### Evidence

| Version | Approach | Result |
|---------|----------|--------|
| v0.74–v0.8008 | Synchronous scan in hook, persistent handlers | ✅ Found 17 candidates, no crash |
| v0.8043 | Scan in detached pthread, per-call sigaction | ❌ Instant crash on entering Solo song list (GC active) |
| v0.8044 | Synchronous scan in hook, persistent handlers | 🔲 Reverted to proven pattern, awaiting test |

### Rules

1. **Probing must run on the game thread**, synchronously inside the hook (game is paused, so its own handlers can't be hijacked).
2. Install the SIGSEGV/SIGBUS handlers **once** for the whole scan (`mode_install_handlers()`), restore **once** (`mode_restore_handlers()`) before returning to the game — per-call sigaction is slow and widens the window.
3. `sigsetjmp`/`siglongjmp` must be set up and executed on the **same thread** (a `sigjmp_buf` is thread-stack-scoped).
4. Accept a brief UI pause (~1-2s) while the scan runs; it beats a crash. (A 4GB scan at 64KB pages with signal-based fault probing ≈ 1-2s.)
5. This complements the older lesson: **background threads created from hooks are unsafe** (v0.8016, `scePthreadCreate`).
