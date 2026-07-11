---
name: toolchain-and-build
description: "PS4 development toolchain: OpenOrbis, clang++, linker flags, create-fself, GoldHEN SDK"
metadata:
  type: reference
---

# PS4 Toolchain & Build System

## OpenOrbis PS4 Toolchain

The OpenOrbis PS4 Toolchain provides the compiler, assembler, and linker for PS4 PRX plugins.

**Environment variable:**
```
OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain
```

**Key binaries:**
- `clang++ --target=x86_64-pc-freebsd12-elf` — cross-compiler (NOT x86_64-pc-linux-gnu!)
- `ld.lld` — LLVM linker with PS4 support
- `create-fself` — FSELF generation tool

## Build Process

### Compilation
```makefile
clang++ --target=x86_64-pc-freebsd12-elf \
  -fPIC -funwind-tables \
  -c -isysroot $(OO_PS4_TOOLCHAIN) \
  -isystem $(OO_PS4_TOOLCHAIN)/include \
  -I./include \
  -o obj/main.o src/main.cpp
```

Critical flags:
- `--target=x86_64-pc-freebsd12-elf` — MUST match PS4's FreeBSD kernel
- `-fPIC` — Position-independent code (required for shared libraries/plugins)
- `-funwind-tables` — Exception handling tables

### Linking
```makefile
ld.lld $(TOOLCHAIN)/lib/crtprx.o obj/*.o \
  -o obj/beat_saber_deluxe.elf \
  -m elf_x86_64 -pie -e _init \
  --script link.x --eh-frame-hdr \
  -L$(TOOLCHAIN)/lib \
  -lGoldHEN_Hook -lSceLibcInternal -lkernel
```

Critical flags:
- `crtprx.o` — PS4 PRX CRT (NOT crtlib.o!)
- `-e _init` — Entry point (NOT module_start!)
- `-pie` — Position-independent executable
- `--no-tls-optimize` — Required to avoid musl TLS conflicts
- `-lGoldHEN_Hook` — GoldHEN hook API
- `-lSceLibcInternal` — PS4 libc
- `-lkernel` — PS4 kernel syscalls

### FSELF Generation
```bash
$(OO_PS4_TOOLCHAIN)/bin/linux/create-fself \
  -in=obj/beat_saber_deluxe.elf \
  -out=obj/beat_saber_deluxe.oelf \
  --lib=beat_saber_deluxe.prx \
  --paid 0x3800000000000011
```

The `--lib` flag produces FSELF format (SCE magic `4f 15 3d 1d`), which GoldHEN expects. Without `--lib`, create-fself produces bare OELF (`7f 45 4c 46`), which GoldHEN rejects.

## Makefile Clean Build
```bash
export OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain
make clean && rm -rf obj && make -B
```
Full rebuild avoids stale object files.

## Python Dependencies (for bundle conversion)
```
UnityPy>=1.9.0  — Unity AssetBundle manipulation
gzip            — Standard library (gzip.compress/gzip.decompress)
json            — Standard library
struct          — Standard library (binary data packing)
```

See also: [[plugin-architecture]], [[development-workflow]], [[ps4-file-system-redirects]]
