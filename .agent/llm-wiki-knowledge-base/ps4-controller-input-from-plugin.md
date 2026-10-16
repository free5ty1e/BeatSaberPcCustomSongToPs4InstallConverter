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

## Hooking pattern (proven in this project)

```c
void *fn = dlsym(RTLD_DEFAULT, "scePadRead");   // libScePad loads WITH the game
Detour_Construct(&Detour_hook_pad_read, DetourMode_x64);
Detour_DetourFunction(&Detour_hook_pad_read, (uint64_t)fn, (void *)pad_read_hook);
```

- `dlsym(RTLD_DEFAULT, ...)` is the pattern already proven for `il2cpp_string_new`
  ([[plugin-architecture]]). At `module_start` only 3 modules are visible — install
  LAZILY from `open_hook()` with retries (libScePad is loaded before the game's
  first file open because the eboot imports it).
- Hook body: call the original first (`HOOK_CONTINUE`), then inspect
  `pData[n-1]`. `n <= 0` = no fresh sample — skip, don't reset hold state.
- Time source for hold durations: `uint64_t sceKernelGetProcessTime(void)` —
  µs, monotonic, in `orbis/libkernel.h` (the same lib plugins already link).

## DS4 vs Move separation (the critical fact)

Beat Saber PS4 reads **Move controllers via the separate `libSceMove`**
(`sceMoveInit`/`sceMoveOpen`/`sceMoveReadStateRecent`/…) — visible in the eboot's
imports. `scePadRead` polls therefore carry **DS4-class pads only**, and Move
controllers have no stick-click buttons at all: **a Move physically cannot set the
L3/R3 bits**. A clean-combo hotkey (`buttons == L3|R3` exactly) is Move-proof by
construction.

## How to verify which pad functions a game imports (methodology)

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
