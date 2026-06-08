# OpenOrbis SDK Setup Guide
**Purpose:** Comprehensive instructions for obtaining, installing, and utilizing the OpenOrbis SDK within the Beat Saber Deluxe development environment.

## 📌 Overview
The OpenOrbis SDK is a free, open-source toolchain used to develop and compile `.sprx` (system plugin) and `.elf` (executable) files for the PlayStation 4. It allows developers to create homebrew without the official Sony SDK.

**Official Repository:** [OpenOrbis-PS4-Toolchain](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain)

## 📥 Installation Methods

### Method A: Automated Script (Recommended)
The project includes a script `/workspace/install_openorbis_complete.sh` designed for Linux/DevContainer environments.

**What the script does:**
1. **Dependencies:** Installs `clang` and `lld` (the required LLVM toolchain) via `apt`.
2. **SDK Retrieval:** Queries the GitHub API for the latest release, identifies the correct Linux archive (e.g., `toolchain-llvm-18.tar.gz`), and downloads it.
3. **Installation:** Extracts the SDK to `/opt/openorbis`.
4. **Environment Config:** Appends `OO_PS4_TOOLCHAIN` and the binary path to `~/.zshrc` for persistence.

**To run the script:**
```bash
sudo /workspace/install_openorbis_complete.sh
source ~/.zshrc
```

### Method B: Manual Host-to-Container Mount
For users who prefer managing the SDK on their host machine:
1. **Download:** Get the Linux SDK from the [Releases Page](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain/releases).
2. **Extract:** Place it in a local folder (e.g., `/home/user/openorbis`).
3. **Mount:** Update `.devcontainer/openorbis.devcontainer.json` to map the host folder to the container:
   ```json
   "mounts": [
     "source=/home/user/openorbis,target=/opt/openorbis,type=bind,consistency=cached"
   ]
   ```

## 🛠️ Verification
To confirm the toolchain is active, run:
```bash
# Check compiler
clang --version

# Check SDK binaries (e.g., readoelf)
ls $OO_PS4_TOOLCHAIN/bin/linux/readoelf
```

## 🚀 Compilation Workflow
The project uses a `Makefile` in `/workspace/beat_saber_deluxe/`.

**Build process:**
1. Navigate to the project: `cd /workspace/beat_saber_deluxe`
2. Run the build: `make`
3. The resulting binary is created at `build/beat_saber_deluxe.sprx`.

**Cross-Compiler Notes:**
The toolchain uses `clang` with the `-fPIC` and `-shared` flags to create a position-independent library compatible with the PS4's dynamic loading system.
