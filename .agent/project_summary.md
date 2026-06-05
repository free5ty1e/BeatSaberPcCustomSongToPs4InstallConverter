# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-05-28
**Current Status:** Manifest Structure Cracked - Preparing "Start Me Up" Patch

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
- **Purpose:** The game reads this list to determine which AssetBundles to look for in the file system.

### 2. The Metadata Record (The "Identity")
- **Location:** Around offset `961965` (for $100 Bills).
- **Structure:** `[Asset Name String]` $\rightarrow$ `[Length (4 bytes)][Short ID]` $\rightarrow$ `[Length (4 bytes)][Display Name]` $\rightarrow$ `[Length (4 bytes)][Artist Name]`

---

## 🛡️ Safety & Rollback Plan (The "Safety Net")
To ensure the experiment is non-destructive:
1. **The Master Backup:** Before any modification, create a full backup of the original `resources.assets` and the target AssetBundle from the PS4.
2. **Versioned Patches:** Every modified `resources.assets` will be named with a version (e.g., `resources_v1_test.assets`).
3. **Restore Process:** Delete the modified file and restore the backup.

---

## 🧪 Implementation Workflow (The "Surgical Strike")
**Target Sacrifice Song:** "Start Me Up" - The Rolling Stones.

1. **Search:** Locate "Start Me Up" in `resources.assets` to find its exact ID and Metadata offsets.
2. **Modify:** Create a patched `resources.assets` by overwriting:
    - The internal ID in the ID Table.
    - The Display Name and Artist in the Metadata Record.
3. **Package:** Provide the patched `resources.assets` and the required naming for the custom AssetBundle.
4. **Deploy:** Upload via FTP and test.

---

## 📈 Future Goal: The "Expansion" Theory (Adding Songs)
To add songs rather than replace them, we must transition from "Overwriting" to "Expanding".
1. **Increment Size:** Find the `m_ArraySize` header and increase it.
2. **Append Data:** Add the new ID and Metadata record to the end of the arrays.
3. **Offset Management:** Update pointers to avoid breaking other assets.

## 📓 Recent Findings & Updates
- **Discovery:** Attempted to locate "Sympathy For The Devil" in the memory dump but found it was absent.
- **Pivot:** User approved switching the sacrificial song to "Start Me Up" from The Rolling Stones pack.
- **Verification:** Confirmed the existence of the internal ID `StartMeUp` in the `resources.assets` ID table at offset `0x000d4b08` (approx. 864,520).
- **Challenge:** The user-facing display name "Start Me Up" is not appearing in simple string searches, confirming that metadata is stored in serialized Unity objects or a specific binary format that requires offset-based analysis rather than keyword searching.
