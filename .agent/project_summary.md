# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-05-28
**Current Status:** Plugin Architecture Implemented - Transitioning to SDK Environment

## 🎯 The Goal
Enable the installation and playback of custom songs on a jailbroken PS4 by modifying both the game's global song database and the individual song assets.

## 🛠️ The Technical Landscape
- **Game Engine:** Unity 2022.3 (LZ4HAM Compression).
- **Asset Format:** Unity AssetBundles (`.assets`, `.bundle`, and resource files).
- **Audio Format:** FSB5 (contained within AssetBundles).
- **Environment:** **Strictly Offline.** All data must be stored locally.
- **Loading Mechanism:**
    1. **The ID Table:** A packed list of internal IDs used to locate AssetBundles.
    2. **The Metadata Record:** A length-prefixed string sequence containing Display Names and Artists.

## 📦 Explored Assets & Components

| Asset / File | Location | Description | Role |
| :--- | :--- | :--- | :--- |
| `resources.assets` | `Media/` | Global AssetBundle. | **The Soul.** Contains both the ID Table and Metadata Records. |
| `BeatmapLevelsData/[song]` | `StreamingAssets/` | Individual AssetBundles. | **The Body.** Contains gameplay and audio. |
| `beat_saber_songs.json` | `/workspace/` | Extracted Wikipedia song list. | **The Library.** Reference for all official song metadata. |
| `List of songs in Beat Saber` | [Wiki Link](https://en.wikipedia.org/wiki/List_of_songs_in_Beat_Saber) | Official song list. | **The Source.** |

## 🧪 Breakthrough: The "Manifest" Anatomy
Through raw binary analysis of the memory dump, we have decoded the exact structure of the song database in `resources.assets`.

### 1. The ID Table (The "Lookup")
- **Location:** Around offset `872249`.
- **Structure:** A packed sequence of null-terminated or length-prefixed internal IDs.

### 2. The Metadata Record (The "Identity")
- **Location:** Around offset `961965` (for $100 Bills).
- **Structure:** `[Asset Name String]` $\rightarrow$ `[Length (4 bytes)][Short ID]` $\rightarrow$ `[Length (4 bytes)][Display Name]` $\rightarrow$ `[Length (4 bytes)][Artist Name]`

---

## 🛡️ Safety & Rollback Plan (The "Safety Net")
To ensure the experiment is non-destructive:
1. **The Master Backup:** Create a full backup of the original `resources.assets` and the target AssetBundle.
2. **Versioned Patches:** Every modified `resources.assets` will be named with a version (e.g., `resources_v1_test.assets`).
3. **Restore Process:** Delete the modified file and restore the backup.

---

## 🚀 Implementation: "Beat Saber Deluxe" Plugin
To avoid the risks of permanent file modification and to allow for "Adding" songs in the future, we have implemented a **Plugin-based Redirection System**.

### v1: The "Single-Song Hijack" (Implemented)
The plugin is a `.sprx` system plugin that hooks the PS4's file system calls.

**Technical Implementation:**
- **Hook:** `sceFileUtilsOpen` is intercepted using a symbol-lookup hook.
- **Redirection Table:** A mapping of original game paths to custom file paths.
- **Logic:** If the game requests `resources.assets` or `startmeup`, the plugin redirects the request to `/data/custom/bs_deluxe/` without the game knowing.

**Files Created:**
- `include/bs_deluxe.h`: Plugin definitions.
- `src/main.cpp`: Implementation of the `hooked_sceFileUtilsOpen` logic.
- `build.sh`: Conceptual build script for cross-compiling to `.sprx`.

### v2: The "Dynamic Expansion" (Future)
- Implement a memory-patching system to modify the `m_ArraySize` of the song list in real-time.
- Append new song records to the end of the manifest in memory.

## 🚩 Current Blockers
- **SDK Compilation:** The plugin source is ready, but requires a PS4 SDK environment to compile into a binary `.sprx` file.

## 📓 Recent Findings & Updates
- **Sacrifice Selection:** "Start Me Up" selected as the sacrificial song.
- **FTP Status:** Confirmed read-only access; plugin redirection is the only viable path.
- **Implementation:** "Beat Saber Deluxe" plugin source code has been drafted.
- **DevContainer Evolution:** Created a new devcontainer definition (`openorbis.devcontainer.json`) specifically for the OpenOrbis SDK toolchain. This container preserves the opencode environment and workspace persistence.
