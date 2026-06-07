# OpenOrbis SDK Setup Guide
**Purpose:** Instructions for obtaining and integrating the OpenOrbis SDK into the Beat Saber Deluxe development environment.

## 📌 Overview
The OpenOrbis SDK is a free, open-source toolchain used to develop and compile `.sprx` (system plugin) and `.elf` (executable) files for the PlayStation 4. 

**Repository:** [OpenOrbis-PS4-Toolchain](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain)

## 📥 Installation Methods

### Method A: Automated Script (Recommended for Linux/DevContainers)
I have provided a comprehensive script `/workspace/install_openorbis_complete.sh` that handles everything.

**What the script does:**
1. Installs the required system compiler (`clang`) and linker (`lld`) via `apt`.
2. Downloads the latest OpenOrbis SDK from GitHub.
3. Installs the SDK to `/opt/openorbis`.
4. Configures the necessary environment variables (`OO_PS4_TOOLCHAIN` and `PATH`) in your `~/.zshrc`.

**To run the script:**
```bash
sudo /workspace/install_openorbis_complete.sh
source ~/.zshrc
```

### Method B: Manual Integration (Host-to-Container Mount)
If you prefer to manage the SDK on your host machine:
1. **Download:** Visit the [Releases Page](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain/releases) and download the Linux version.
2. **Extract:** Extract the archive to a folder on your host (e.g., `/home/user/openorbis`).
3. **Mount:** Add a bind mount to your `.devcontainer/openorbis.devcontainer.json`:
   ```json
   "mounts": [
     "source=/path/to/your/openorbis,target=/opt/openorbis,type=bind,consistency=cached"
   ]
   ```

## 🛠️ Verification
After installation, verify the toolchain is functioning by checking the compiler and the SDK path:

```bash
# Check for Clang
clang --version

# Check for OpenOrbis Binaries
ls $OO_PS4_TOOLCHAIN/bin/linux/readoelf
```

## 🚀 Compilation Workflow
Once the SDK is installed:
1. Navigate to the plugin project: `cd /workspace/beat_saber_Luxe`
2. Run the build command: `make`
3. The output will be located at `build/beat_saber_deluxe.sprx`.
