# PS4 Debugging Guide: Finding Function Addresses

## Overview

This guide explains how to find function addresses in the PS4 eboot.bin for building the Beat Saber Deluxe plugin. These addresses are needed to hook into the game's level loading system.

**When needed:** After we exhaust the simplified song replacement approach.

---

## Prerequisites

### Hardware
- PS4 with GoldHEN v2.0+ installed
- USB drive for file transfer
- PC with IDA Pro or Ghidra (free)

### Software
- GoldHEN Debugger or PS4 Debugger
- FTP server (part of GoldHEN)
- Decrypted eboot.bin (from your dump)

---

## Step 1: Set Up PS4 Debug Environment

### Enable FTP Server
1. On PS4, launch GoldHEN
2. Go to **Settings** → **GoldHEN** → **FTP Server**
3. Enable FTP and note the IP address

### Connect via FTP
1. On PC, open browser or FTP client
2. Connect to: `ftp://PS4-IP:2121`
3. Navigate to: `/system_dim/`

### Backup Original eboot.bin
```
/system_dim/common/lib/SceLibc/libSceLibc.sprx
/system_dim/CUSA12878-app/eboot.bin
```

---

## Step 2: Install Debugger Tools

### Option A: PS4 Debugger (Recommended)
1. Download PS4 Debugger pkg from GoldHEN repository
2. Install on PS4
3. Launch from home screen

### Option B: Use IDA Pro Remote Debugging
1. Install IDA Pro 7.x+ on PC
2. Copy `dbgsrv/lin64dbgsrv` to PS4 via FTP
3. Run `lin64dbgsrv` on PS4

---

## Step 3: Find AssetBundle.LoadFromFile

### Method A: String Search in IDA

1. Open eboot.bin in IDA Pro
2. Wait for analysis to complete
3. Press **Shift+F12** to open Strings window
4. Search for: `AssetBundle`
5. Find strings like:
   - `AssetBundle.LoadFromFile`
   - `LoadFromFile_Internal`
   - `StreamingAssets`

### Method B: Cross-Reference Search

1. In IDA, press **Alt+1** to open Classes window
2. Search for: `AssetBundle`
3. Double-click to open class
4. Look for: `LoadFromFile` method
5. Note the RVA (Relative Virtual Address)

### Method C: Pattern Scanning

Search for Unity's AssetBundle loading code:
```
Unity 2022.3 pattern:
55 8B EC 83 EC ?? 53 56 57 8B 7D 08
```

---

## Step 4: Confirm Function Address

### On PS4 with Debugger

1. Launch Beat Saber on PS4
2. Attach debugger to process
3. Set breakpoint on suspected function
4. Play a level
5. If breakpoint hits → correct address!

### Verify with GoldHEN

1. Use GoldHEN's function hook system
2. Add hook for `AssetBundle.LoadFromFile`
3. Check logs for file paths being loaded

---

## Step 5: Document Findings

### Required Information

For each function, document:
```
Function Name: AssetBundle.LoadFromFile
Module: eboot.bin
RVA: 0x12345678
PC Offset: 0x12345678
PS4 Virtual Address: 0x40000000 + RVA
Arguments: path (char*), flags (int)
Return: AssetBundle*
```

### Example Documentation

```
=== Beat Saber PS4 Function Addresses ===

AssetBundle Loading:
- AssetBundle.LoadFromFile: 0x40012340
- AssetBundle.LoadFromMemory: 0x40012450

Level Loading:
- BeatmapLevelsModel.GetLevel: 0x40020100
- BeatmapLevelsModel.ReloadAllLevels: 0x40020180

File System:
- sceKernelOpen: 0x40001000 (libSceLibc)
- sceKernelRead: 0x40001020
```

---

## Step 6: Build Plugin Hooks

Once addresses are known, update plugin:

```c
// In beat_saber_dx/hooks.c

// AssetBundle.LoadFromFile hook
HOOK_FUNCTION(
    "AssetBundle.LoadFromFile",
    0x40012340,  // Your found address
    AssetBundle_LoadFromFile_Hook,
    &AssetBundle_LoadFromFile_Original
);

// Check for custom song paths
static AssetBundle* AssetBundle_LoadFromFile_Hook(const char* path, int flags) {
    // Redirect to custom songs folder
    if (strstr(path, "BeatmapLevelsData")) {
        char newPath[512];
        snprintf(newPath, sizeof(newPath), 
            "/data/GoldHEN/BeatSaberDX/songs/%s", 
            get_filename_from_path(path));
        
        if (file_exists(newPath)) {
            return AssetBundle_LoadFromFile_Original(newPath, flags);
        }
    }
    
    return AssetBundle_LoadFromFile_Original(path, flags);
}
```

---

## Alternative: No-Debugging Approach

**You don't actually need to find these addresses!**

The simplified approach (replacing existing levels) doesn't require any function addresses or plugin development. Simply:

1. Copy existing level AssetBundles
2. Modify audio and metadata in UABEA
3. Add to PKG

The game auto-loads ALL files from `BeatmapLevelsData/` - no hooks needed!

---

## When to Use Debugging

Use the debugging approach if:
- You want to add songs WITHOUT replacing existing ones
- You need dynamic song loading
- You want users to add songs while game is running

For a first implementation, stick with song replacement!

---

## Tools Reference

| Tool | Purpose | Download |
|------|---------|----------|
| IDA Pro | Disassembler + Debugger | hex-rays.com |
| Ghidra | Free disassembler | nsa.gov |
| GoldHEN | PS4 jailbreak + debug | github.com/GoldHEN |
| PS4 Debugger | PS4 debugging app | GoldHEN pkg |

---

## Questions to Answer

After debugging, report:
1. AssetBundle.LoadFromFile address
2. Any file path strings found
3. How BeatmapLevelsData is referenced

But remember: **we likely don't need this for the first version!**