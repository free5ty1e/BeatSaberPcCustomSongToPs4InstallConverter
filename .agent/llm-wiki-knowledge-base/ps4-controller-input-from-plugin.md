---
name: ps4-controller-input-from-plugin
description: "How a GoldHEN plugin reads PS4 controller input inside a game: scePadRead hooking, OrbisPadData layout, button bits (L3=0x2, R3=0x4), the NID-obfuscated eboot import methodology, and why Move controllers can never set stick-click bits."
metadata:
  type: reference
---

# PS4 Controller Input From a GoldHEN Plugin

How to observe/intercept PS4 controller input from a plugin running inside a game
process. Verified on Beat Saber PS4 (CUSA12878 patch 2.04) in Exp 278; all facts
dual-checked against the OpenOrbis toolchain headers AND shadPS4Plus's
SDK-accurate implementation. See [[in-game-plugin-toggle]] for the feature built
on this.

## The pad API surface (libScePad)

| Function | Signature | Notes |
|---|---|---|
| `scePadRead` | `int scePadRead(s32 handle, OrbisPadData* pData, s32 num)` | **What Beat Saber actually imports** — buffered read; returns the count of samples written; the most recent state is `pData[n-1]` |
| `scePadReadState` | `int scePadReadState(s32 handle, OrbisPadData* pData)` | simple 2-arg variant; **NOT imported by Beat Saber** — never assume which read function a game uses |
| `scePadOpen` | `int scePadOpen(s32 userID, int32 type, int32 index, void *param)` | open a handle (only needed if you poll your OWN handle) |
| `scePadInit` / `scePadClose` | — | library init / handle close |

## OrbisPadData layout (verified)

```c
struct OrbisPadData {
    uint32_t buttons;       // offset 0x00 — the ONLY field the hotkey needs
    stick leftStick;        // 0x04 (2 bytes)
    stick rightStick;       // 0x06
    analog analogButtons;   // 0x08 (L2/R2 analog — NOT in the buttons mask)
    ...
};
```

Button bit values (OpenOrbis `orbis/_types/pad.h` enum OrbisPadButton; shadPS4Plus
`OrbisPadButtonDataOffset` agrees):

```
L3=0x0002  R3=0x0004  OPTIONS=0x0008  UP=0x0010  RIGHT=0x0020  DOWN=0x0040  LEFT=0x0080
L2=0x0100  R2=0x0200  L1=0x0400  R1=0x0800
TRIANGLE=0x1000  CIRCLE=0x2000  CROSS=0x4000  SQUARE=0x8000  TOUCH_PAD click=0x100000
```

⚠️ These differ from some PS3-era conventions — verify from the headers, don't trust
memory. A plugin reading the hook's output only needs `((uint32_t*)data)[n-1]`.

## Hooking pattern (proven in this project — with the Exp 278b lesson)

```c
void *fn = dlsym(RTLD_DEFAULT, "q1cHNfGycLI");   // ← resolve BY NID
if (!fn) fn = dlsym(RTLD_DEFAULT, "scePadRead"); // readable-name fallback only
Detour_Construct(&Detour_hook_pad_read, DetourMode_x64);
Detour_DetourFunction(&Detour_hook_pad_read, (uint64_t)fn, (void *)pad_read_hook);
```

⚠️ **THE NID RESOLUTION RULE (Exp 278b root cause):** Sony system libraries
(libScePad, libSceMove, …) export functions **under their NIDs, NOT readable
names**. `dlsym(RTLD_DEFAULT, "scePadRead")` finds NOTHING — the game imports
it as NID `q1cHNfGycLI`. Readable-name dlsym only works for symbols the
GAME'S OWN EBOOT exports by name (e.g. `il2cpp_string_new`). **Always resolve
system-library functions by NID** (verified from the game's import table via
the methodology below, or a NID DB like shadPS4's aerolib.inl):

| Function | NID |
|---|---|
| `scePadRead` | `q1cHNfGycLI` |
| `scePadReadState` | `YndgXqQVV7c` |
| `sceMoveReadStateRecent` | `f2bcpK6kJfg` |

- `dlsym(RTLD_DEFAULT, ...)` is the proven pattern (proven for
  [[plugin-architecture]] — il2cpp_string_new). At `module_start` only 3
  modules are visible — install LAZILY from `open_hook()` with retries
  (system libs are loaded before the game's first file open because the
  eboot imports them). Set a **gave-up flag** when retries exhaust (don't
  re-log the error on every open — the v0.8049 spam bug).
- Hook body: call the original first (`HOOK_CONTINUE`), then inspect the
  output. `n <= 0` = no fresh sample — skip, don't reset hold state.
- Time source for hold durations: `uint64_t sceKernelGetProcessTime(void)` —
  µs, monotonic, in `orbis/libkernel.h` (the same lib plugins already link).
- **Signature ambiguity can be resolved safely at runtime**: when a hooked
  function's arity is uncertain (e.g. shadPS4 documents
  `sceMoveReadStateRecent` as 4-arg (handle, timestamp, data, out_count) but
  a 3-arg form would leave the data buffer in RSI instead of RDX), validate
  the candidate registers with `sceKernelQueryMemoryProtection` (the
  v0.8045-proven signal-free technique — an int argument fails RW-pointer
  validation) and pass ALL registers through either way.

## The Move controller path (Exp 278c — the real input path on Beat Saber)

- **Beat Saber reads both Moves every frame via `sceMoveReadStateRecent`** —
  the ONLY Move state read in the eboot's imports (`sceMoveReadStateLatest`
  is NOT imported). The DS4 is ignored in VR mode (user-verified hardware
  test: L3+R3 on a connected DS4 never fired, and pad polling never appeared).
- **SceMoveData layout** (per shadPS4Plus's SDK-derived OrbisMoveData):
  `float accelerometer[3]` (12B) + `float gyro[3]` (12B) + **`button_data`
  u16 @ +0x18** + **trigger u16 @ +0x1A** + extension data + timestamp +
  count + temperature (~60B total).
- **Move button bits, reconstructed from the game's OWN enum** (dump.cs
  `PSVRDeviceManager.PSMoveButton`: Select=1, **[2 = trigger — skipped by
  the game's enum because it reads the trigger via GetPSMoveAnalog]**,
  Move=4, Start=8, Triangle=16, Circle=32, Cross=64, Square=128):
  **trigger digital bit = 0x2, Move button = 0x4**. The game's button reads:
  `GetPSMoveButtonDown(idx, PSMoveButton)` + `GetPSMoveAnalog(idx)` for the
  trigger (analog).
- **Empirical confirmation built into the hook:** log the first N calls raw
  plus every data-word change (capped) — a button press lights up the boot
  log, confirming or correcting the offset/bits from the first hardware boot.
- A 2-second hold spans 100+ frames, so reading **entry 0** of the data
  buffer is sufficient for held-button detection regardless of which
  returned entry is "most recent".

## DS4 vs Move separation (updated by the Exp 278b hardware test)

Beat Saber imports both libScePad and libSceMove, but in VR mode the **DS4 is
ignored** — the user's hardware test (DS4 connected to the same profile as
the headset + Moves) never fired the L3+R3 pad hook. Move tracking + buttons
flow through libSceMove (`sceMoveReadStateRecent`). The pad path remains a
secondary hook (NID-resolved) for any session where the game polls pads.

## How to verify which pad/move functions a game imports (methodology)

`readelf` cannot parse PS4 ELFs (no section headers: `e_shoff=0`, `e_shnum=0`;
type `ET_SCE_DYNEXEC` 0xfe10). Use
`beat_saber_deluxe/development/scripts/ps4_elf_imports.py`:

1. Walk program headers → find `PT_DYNAMIC`.
2. PS4 dynamic tags are SCE-specific: `DT_SCE_STRTAB` 0x61000035,
   `DT_SCE_SYMTAB` 0x61000039, `DT_SCE_SYMENT` 0x6100003B,
   `DT_SCE_SYMTABSZ` 0x6100003F, `DT_SCE_HASH` 0x61000025 — and their values are
   **offsets relative to the `PT_SCE_DYNLIBDATA` program segment (p_type
   0x61000000)**, NOT file offsets and NOT vaddrs. Self-consistency check that
   proves it: `strtab + strsz == symtab` and `symtab + symtabsz == jmprel`.
3. Game dynsym entries are **NID-obfuscated** (11-char base64-ish hashes +
   `#lib#mod` suffixes). Decode by joining against a NID database —
   shadPS4's `src/core/aerolib/aerolib.inl` (`STUB("NID", name)`) decodes
   846/849 of Beat Saber's imports.

Beat Saber's decoded libScePad imports: `scePadInit`, `scePadOpen`, `scePadClose`,
**`scePadRead`** (NID `q1cHNfGycLI`), `scePadGetControllerInformation`,
`scePadResetLightBar`, `scePadSetLightBar`, `scePadSetVibration`,
`scePadSetMotionSensorState`, `scePadSetAngularVelocityDeadbandState`,
`scePadSetTiltCorrectionState`, `scePadResetOrientation`,
`scePadDeviceClassGetExtendedInformation`, `scePadDeviceClassParseData`.

## Related
- [[in-game-plugin-toggle]] — the feature built on this research
- [[plugin-architecture]] — Detour/dlsym/hook-install patterns
- [[feature-flags]] — the flag gating the hotkey
