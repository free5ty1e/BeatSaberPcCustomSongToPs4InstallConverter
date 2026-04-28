# Beat Saber PS4 — Alternative Paths & Tools Analysis

## The Core Problem

We need to understand how Beat Saber loads:
1. Song data (beatmaps, audio)
2. Unity engine asset loading (`AssetBundle.LoadFromFile`, `Resources.Load`)
3. FMOD audio system
4. Level pack / song catalog

Without this knowledge, we can't build a working custom song plugin.

**Key insight from research**: Your PS4 has **every tool needed** already installed — no additional downloads required.

---

## PATH 1: Use ps4debug to Analyze Beat Saber at Runtime (Recommended)

### What It Is
A full debugger that attaches to running PS4 processes. Think of it like a graphical hex editor + memory viewer + debugger for your PS4.

**Supports your PS4 firmware (11.00+)**

### What You Get
- **Memory scanner** — Like Cheat Engine, scan for values in Beat Saber's memory
- **Memory viewer** — Browse any area of the game's RAM
- **Breakpoints** — Pause execution when specific memory is accessed
- **Multi-process support** — Attach to game while it's running
- **Hardware breakpoints** — Trap when code reads/writes specific addresses

### What This Lets Us Do

1. **Find where audio is loaded**:
   - Play a song → scan memory for the audio filename → find the audio loading code → understand format

2. **Find where beatmaps are parsed**:
   - Look for string patterns like "Expert", "Normal", note data → find the parsing code

3. **Find Unity engine hooks**:
   - Search for `AssetBundle`, `sharedassets`, `level` strings → find asset loading functions

4. **Identify function addresses**:
   - Set breakpoints on game file reads → capture which functions load `sharedassets`

### How To Use (Step by Step)

#### On PS4:
1. Load GoldHEN (if not already)
2. Load **ps4debug.bin** payload (via payload loader or `/data/payloads/`)
3. Start Beat Saber and navigate to a song

#### On PC:
1. Download **Reaper Studio** or **PS4 Cheater** (frontends for ps4debug)
   - Reaper Studio: Debugger + Trainer Creator (https://github.com/SilenSara/Reaper-Studio/releases)
   - PS4 Cheater: Memory scanner/viewer (part of ps4debug ecosystem)
2. Connect to ps4debug server on PS4 (usually `http://PS4_IP:8080` or similar)
3. Attach to `eboot.bin` process
4. Start scanning/analyzing

#### Practical Scan Strategy:

```
STEP 1: Find audio loading
───────────────────────────
1. In Beat Saber, select a known song (e.g. "Believer")
2. In PS4 Cheater, scan for the string "Believer" in memory
3. Find where the song name is stored → this tells us where song data lives
4. Set a breakpoint on that memory region → identify what function reads it
5. That function is likely the audio loader or beatmap parser

STEP 2: Find beatmap data
───────────────────────
1. Look for binary data patterns near the song name (note counts, timing values)
2. Search for pattern: small integers near note count (e.g., searching for 100-200 
   as possible note counts)
3. When you find beatmap data, trace back to find who called it

STEP 3: Identify asset loading
──────────────────────────────
1. Search for "sharedassets" string
2. Look for Unity engine function names near that region
3. These are the AssetBundle loading functions we need to hook
```

### Tools for This Path

| Tool | Purpose | Link |
|------|---------|------|
| **ps4debug.bin** | Debugger server (needs to run on PS4) | https://github.com/GoldHEN/ps4debug/releases |
| **Reaper Studio** | GUI debugger + trainer creator | https://github.com/SilenSara/Reaper-Studio/releases |
| **PS4 Cheater** | Memory scanner/viewer GUI | Part of ps4debug ecosystem |
| **MultiTrainer II** | Cheat/trainer loader | Part of ps4debug ecosystem |

### Difficulty: ⭐⭐⭐ (Moderate)
- Requires learning to use a debugger
- Requires patience to find the right memory patterns
- But: **fully doable from your PS4** with GUI tools

### Time Estimate: 1-3 sessions of investigation

---

## PATH 2: Dump Decrypted Game Files with ps4-dumper-vtx

### What It Is
A payload that **dumps all decrypted game files** from a running PS4 game to USB.

**This is exactly what we need** — dump Beat Saber while it's running, get the raw `sharedassets` files, analyze them on PC.

### How It Works

```
1. Plug USB drive into PS4 (formatted FAT32 or exFAT)
2. Run ps4-dumper-vtx payload on PS4
3. Start Beat Saber game
4. The dumper intercepts decrypted file reads and saves them to USB
5. Unplug USB, analyze files on PC
```

### What You Get Dumped

- `sharedassets0.assets` — Base game assets
- `sharedassets1.assets` — Level pack 1
- `sharedassets2.assets` — Level pack 2
- etc.
- `resources/` folder with raw audio files
- Decrypted `eboot.bin` (main executable)
- Decrypted library files (`libunity.so`, `libfmod.so`, etc.)

### Then On PC:

```
1. Open sharedassets.assets in UABE (Unity Asset Bundle Extractor)
2. See exactly how songs are structured
3. See the audio format
4. See the beatmap binary format
5. Look at level pack database structure
```

### Tools for This Path

| Tool | Purpose | Link |
|------|---------|------|
| **ps4-dumper-vtx** | Dump decrypted game files | https://github.com/xvortex/ps4-dumper-vtx |
| **UABE** | Analyze Unity assets on PC | https://github.com/SeriousCache/UABE |
| **IDA Pro Free** or **Ghidra** | Analyze eboot.bin on PC | IDA: https://hex-rays.com/ida-free/ Ghidra: https://ghidra-sre.org/ |

### Difficulty: ⭐⭐ (Easy)
- Most straightforward approach — no debugging needed
- Just run the dumper, play the game, get files
- Analyze on PC with familiar tools

### Time Estimate: 1-2 hours to dump, 1-2 days to analyze

---

## PATH 3: Dump Decrypted Modules (libunity.so, libfmod.so)

### What It Is
Similar to game dumper, but specifically dumps **system libraries** that Beat Saber uses.

### What You Get
- `libunity.so` — The Unity engine library (contains all asset loading code)
- `libfmod.so` — FMOD audio library (contains audio loading code)
- `libSceUserService.so` — Sony libraries
- Other game-related `.sprx` modules

### Why This Matters

Once you have `libunity.so` and `libfmod.so`:
- **On PC with IDA/Ghidra**: Reverse engineer the functions
- Find `AssetBundle_LoadFromFile` → understand how it works
- Find FMOD bank loading functions → understand audio format
- **You don't even need to run Beat Saber** — just dump from the PS4 with game installed

### Tools for This Path

| Tool | Purpose | Link |
|------|---------|------|
| **module-dumper** (part of EchoStretch SDK) | Dump all system modules | https://github.com/EchoStretch/ps4-payload-sdk |
| **auth-dumper** | Dump auth info from ELF files | https://github.com/obhq/auth-dumper |
| **ps4-re-utilities** | Extract keys from kernel dumps | https://github.com/Al-Azif/ps4-re-utilities |
| **IDA Pro Free / Ghidra** | Reverse engineer .so files | (links above) |

### Difficulty: ⭐⭐⭐ (Moderate)
- Requires some reverse engineering knowledge
- But: standard workflow in PS4 modding community

### Time Estimate: 2-4 hours to dump, days to weeks to fully analyze

---

## PATH 4: Use GoldHEN Cheat Menu + JSON Cheats (Easiest, Most Limited)

### What It Is
Your PS4 already has the **GoldHEN Cheat Menu** built in. You can create JSON cheat files that scan/modify memory.

### How It Works

```
1. Create a JSON file: CUSA12878_xx.xx.json
2. Place it in /user/data/GoldHEN/cheats/json/
3. In-game, press Share button → Cheat Menu appears
4. Enable cheats → GoldHEN writes to memory at specified addresses
```

### JSON Cheat Format
```json
[
  {
    "id": "BeatSaber-CustomSongs",
    "title": "Enable Custom Songs",
    "patch": [
      { "search": "000102030405060708090A0B0C0D0E0F", "replace": "DEADBEEFCAFEBABEEFDEADBEEFCAFEBABE" }
    ],
    "notes": "Test patch for CUSA12878"
  }
]
```

### What This Can Do
- **Memory patches** — Replace bytes at specific addresses
- **Search/replace** — Find pattern in memory and replace it
- **Value patches** — Change specific values (like score multipliers)

### What This CANNOT Do
- Hook functions
- Redirect file reads
- Add new code paths
- Modify asset bundles

### Practical Use
This is useful **AFTER** you discover addresses via ps4debug/analysis:
- Once you find that address `0x12345678` needs to change from `0x01` to `0x00` to bypass signature check
- Create a cheat that patches that byte
- Much faster than manual debugging

### Tools for This Path

| Tool | Purpose | Link |
|------|---------|------|
| **GoldHEN Cheat Menu** | Built into your PS4 GoldHEN | (already installed) |
| **PS4CheatsManager** | PC tool to manage cheat files | https://github.com/bucanero/PS4CheatsManager |
| **GoldHEN Cheat Repository** | Community cheat database | https://github.com/GoldHEN/GoldHEN_Cheat_Repository |

### Difficulty: ⭐ (Very Easy — if you have addresses)

---

## PATH 5: Analyze RB4DX Plugin as Reference

### What It Is
Your PS4 already has the **RB4DX plugin** (Rock Band 4 custom song system). This is a working PS4 custom song plugin.

### How It Works

RB4DX consists of:
1. `RB4DX-Plugin.prx` — The GoldHEN plugin (runs on PS4)
2. `ps4/` folder — Modded assets (audio banks, textures, track data)

**We can analyze the plugin** to understand the approach, then apply it to Beat Saber.

### How To Analyze

#### Step 1: Extract the plugin
Download `RB4DX-Plugin.prx` from your PS4 via FTP:
```bash
# Via PC
python3 -c "import ftplib; s = ftplib.FTP(); s.connect('192.168.100.117', 2121); s.login(); s.cwd('/user/data/GoldHEN/plugins'); f=open('RB4DX-Plugin.prx','wb'); s.retrbinary('RETR RB4DX-Plugin.prx', f.write)"
```

#### Step 2: Analyze on PC
- Open in **IDA Pro Free** or **Ghidra**
- Look for function strings like:
  - "FMOD" / "fmod_bank"
  - "open" / "read" / "file_redirect"
  - "custom_songs" / "custom_track"
- This reveals **how RB4DX hooks the game**

#### Step 3: Apply same patterns to Beat Saber
- If RB4DX hooks `fmod_bank_load`, we need the same for Beat Saber
- If RB4DX hooks `AssetBundle_LoadFromFile`, same for Beat Saber
- Function signatures will be different but approach is identical

### Tools for This Path

| Tool | Purpose | Link |
|------|---------|------|
| **RB4DX-Plugin.prx** | On your PS4 (FTP to download) | `/user/data/GoldHEN/plugins/RB4DX-Plugin.prx` |
| **IDA Pro Free** | Reverse engineer plugin | https://hex-rays.com/ida-free/ |
| **Ghidra** | Free reverse engineering suite | https://ghidra-sre.org/ |

### Difficulty: ⭐⭐⭐⭐ (Advanced)
- Requires reverse engineering knowledge
- But: provides exact working reference implementation

### Time Estimate: 1-2 weeks for full analysis

---

## PATH 6: Create a PS4-Side Plugin (Advanced Development)

### What It Is
Build a **new GoldHEN plugin from scratch** that intercepts Beat Saber's file loading.

### This Is The End Goal — But Requires Path 1, 2, 3, or 5 First

You need:
1. Understanding of where Beat Saber loads assets
2. Function addresses to hook
3. Knowledge of audio/beatmap format

### Development Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Plugin SDK | **ps4-payload-sdk** | Build .prx plugins | https://github.com/Scene-Collective/ps4-payload-sdk |
| Hooking | **GoldHEN Plugin SDK** | Function hooks | https://github.com/SilenSara/GoldHEN_Plugin_SDK |
| Testing | **ps4debug** | Attach/debug plugin | https://github.com/GoldHEN/ps4debug |
| Building | **Linux + PS4 SDK** | Compile plugin | Docker container recommended |

### Plugin Architecture (Based on RB4DX)

```c
// Pseudocode for BeatSaber-Plugin.prx
int main(unsigned int args, void *argp) {
    // 1. Install function hooks
    hook_function("libc", "open",    my_open_hook);   // File access
    hook_function("libc", "read",    my_read_hook);   // File reads
    hook_function("libunity", "AssetBundle_LoadFromFile", my_ab_hook); // Unity assets
    
    // 2. Register custom song directory
    custom_songs_path = "/user/data/GoldHEN/BeatSaber/songs";
    
    // 3. Register with game
    // This varies by game — need to discover via analysis
    
    return 0;
}

// Hook: intercept file open() calls
int my_open_hook(const char *filename, int flags, int mode) {
    // Check if game is trying to open a sharedassets file
    if (strstr(filename, "sharedassets")) {
        // Check our custom directory first
        char custom_path[256];
        snprintf(custom_path, sizeof(custom_path), 
                 "%s/%s", custom_songs_path, extract_filename(filename));
        
        if (file_exists(custom_path)) {
            return open(custom_path, flags, mode); // Redirect to custom file
        }
    }
    return original_open(filename, flags, mode); // Normal behavior
}
```

### Difficulty: ⭐⭐⭐⭐⭐ (Very Advanced)
- Requires C development
- Requires PS4 exploitation knowledge
- Requires game analysis (from Paths 1-5)

### Time Estimate: Months of development

---

## Recommended Path Forward

### Phase 1: Dump and Analyze (Start Here — Easiest)

```
WEEK 1-2: DUMP DECRYPTED GAME FILES
──────────────────────────────────
1. Run ps4-dumper-vtx on PS4 with Beat Saber
2. Get sharedassets files on USB
3. On PC: Open in UABE
4. On PC: Open eboot.bin in IDA Pro Free
5. Document:
   - How songs are stored in sharedassets
   - Audio format (FMOD banks vs raw OGG)
   - Beatmap binary format
   - Level pack index structure
```

**Output**: Full understanding of the game file format, no debugging needed.

### Phase 2: Discover Hook Points (If Phase 1 Not Enough)

```
WEEK 2-3: RUNTIME ANALYSIS
────────────────────────
1. Run ps4debug on PS4
2. Attach with Reaper Studio to Beat Saber
3. Search for "sharedassets", "Believer", function patterns
4. Identify: AssetBundle_LoadFromFile, FMOD_Bank_Load addresses
5. Document: Function signatures and calling conventions
```

**Output**: Function addresses and signatures for hooking.

### Phase 3: Reference Implementation

```
WEEK 3-4: ANALYZE RB4DX
────────────────────────
1. Download RB4DX-Plugin.prx from PS4
2. Analyze in IDA Pro Free
3. Document: How it hooks FMOD, file I/O, game logic
4. Map: Which functions are hooked → same exist in Beat Saber?
```

**Output**: Proven implementation pattern to follow.

### Phase 4: Build Plugin

```
MONTH 2+: DEVELOP BEATSABER-PLUGIN.PRX
──────────────────────────────────────
1. Set up ps4-payload-sdk build environment
2. Create plugin skeleton
3. Implement file redirect hooks
4. Implement asset loading hooks
5. Implement custom song directory loading
6. Test incrementally with ps4debug
7. Release to community
```

---

## Complete Tool Reference

### PS4 Debugging & Analysis Tools

| Tool | What It Does | Link |
|------|-------------|------|
| **ps4debug** | Full debugger + memory tools | https://github.com/GoldHEN/ps4debug |
| **Reaper Studio** | GUI debugger + trainer creator | https://github.com/SilenSara/Reaper-Studio |
| **PS4 Cheater** | Memory scanner + viewer | Part of ps4debug |
| **MultiTrainer II** | Trainers + memory patches | Part of ps4debug |
| **ps4-dumper-vtx** | Dump decrypted game files | https://github.com/xvortex/ps4-dumper |
| **module-dumper** | Dump system modules | https://github.com/EchoStretch/ps4-payload-sdk |
| **auth-dumper** | Dump auth info from ELF | https://github.com/obhq/auth-dumper |

### PC Analysis Tools

| Tool | What It Does | Link |
|------|-------------|------|
| **UABE** | Unity asset bundle editor | https://github.com/SeriousCache/UABE |
| **IDA Pro Free** | Binary reverse engineering | https://hex-rays.com/ida-free/ |
| **Ghidra** | Free reverse engineering | https://ghidra-sre.org/ |
| **dnSpy** | .NET decompiler | https://github.com/dnSpy/dnSpy |

### PS4 Development Tools

| Tool | What It Does | Link |
|------|-------------|------|
| **ps4-payload-sdk** | Build PS4 plugins/payloads | https://github.com/Scene-Collective/ps4-payload-sdk |
| **GoldHEN Plugin SDK** | Plugin development framework | https://github.com/SilenSara/GoldHEN_Plugin_SDK |
| **ps4-re-utilities** | Python RE utilities | https://github.com/Al-Azif/ps4-re-utilities |

### PS4 Homebrew Utilities

| Tool | What It Does | Link |
|------|-------------|------|
| **GoldHEN Cheat Menu** | Built-in memory patcher | (already on your PS4) |
| **Apollo Save Tool** | Save editor + hex editor | https://github.com/bucanero/apollo-ps4 |
| **PS4CheatsManager** | Manage cheat files | https://github.com/bucanero/PS4CheatsManager |
| **Remote PKG Installer** | Install PKGs over network | https://github.com/flatz/ps4_remote_pkg_installer |

---

## Immediate Next Steps (This Session)

### Option A: Dump Game Files (Recommended for You)

1. On your PS4: Load **ps4-dumper-vtx** payload
   - Download from https://github.com/xvortex/ps4-dumper-vtx/releases
   - Put `dumper.bin` on USB or `/data/payloads/`
   - Run via payload loader

2. In Beat Saber: Play a few songs to trigger asset loading

3. USB will have decrypted files after playing

4. Analyze with UABE on PC

### Option B: Use ps4debug for Runtime Discovery

1. On your PS4: Load **ps4debug.bin** payload
   - Download from https://github.com/GoldHEN/ps4debug/releases
   - Run via payload loader

2. On PC: Download **Reaper Studio**
   - Connect to ps4debug server
   - Attach to `eboot.bin`

3. Search for strings, set breakpoints, find function addresses

### Option C: Analyze RB4DX First

1. FTP download `RB4DX-Plugin.prx` from your PS4:
   ```
   /user/data/GoldHEN/plugins/RB4DX-Plugin.prx
   ```

2. Open in IDA Pro Free on PC

3. Look for hooks: FMOD, file I/O, custom paths

4. Document the pattern

---

## What I Can Do From Here

1. **Build the PC-side tools** — Song converter, downloader, installer (already done)
2. **Write analysis scripts** — Help parse sharedassets files once you dump them
3. **Create documentation** — For whatever format you discover
4. **Build plugin skeleton** — Once we have function addresses

**What I CANNOT do**: Debug your PS4 or analyze binary files on your PS4. That step requires you to run the tools on your console.

---

## Key Question for You

**Which path do you want to pursue?**

- **Path 1 (ps4debug)** — Runtime analysis, most informative, moderate skill
- **Path 2 (dumper)** — Easiest, get files and analyze on PC with familiar tools
- **Path 3 (RB4DX analysis)** — Learn from the working reference implementation
- **All of the above** — Sequential approach: dump → analyze → debug → build

Let me know and I'll create specific step-by-step instructions for your chosen path.