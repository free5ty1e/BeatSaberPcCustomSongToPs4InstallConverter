╔═══════════════════════════════════════════════════════════════════╗
║          ORBIS-PUB-GEN BUILD INSTRUCTIONS                       ║
║               For Beat Saber Custom Songs                     ║
╚═══════════════════════════════════════════════════════════════════╝

OVERVIEW
═══════
This folder contains the GP4 project file for building a PS4 fPKG
using orbis-pub-gen. Two build methods are available:
1. This orbis-pub-gen tool (needs fixing - see issues below)
2. Python pipeline (output/custom_songs_v*.pkg)


FILE STRUCTURE
════════════
windows_build/
├── Project.gp4                  ← Open this in GUI
├── CUSA12878-app/               ← Main app folder
│   ├── sce_sys/
│   │   ├── param.sfo          ← Must exist here
│   │   └── icon0.png
│   └── songs/
│       ├── [hash1]/
│       │   ├── Info.dat
│       │   ├── EasyStandard.dat
│       │   ├── NormalStandard.dat
│       │   ├── HardStandard.dat
│       │   └── ...
│       └── [hash2]/
│           └── ...
└── output/                     ← PKG output goes here


GUI USAGE (Recommended for beginners)
════════════════════════════════
1. Locate orbis-pub-gen.exe on your system
   - Often in PS4 tools folder or Downloads
   
2. Launch the GUI:
   - Double-click orbis-pub-gen.exe, OR
   - Right-click Project.gp4 → Open with → orbis-pub-gen

3. In the GUI:
   - File → Open Project
   - Navigate to: windows_build/Project.gp4
   - Click "Build PKG" button or press F5

4. Wait for build to complete
   - Output: windows_build/output/*.pkg

5. Transfer the .pkg to your PS4 via FTP/USB


CLI USAGE (Command Line - Better for debugging)
═══════════════════════════════════════════
1. Open Command Prompt or PowerShell

2. Navigate to this folder:
   cd C:\path\to\windows_build

3. Run orbis-pub-gen:
   orbis-pub-gen.exe image Project.gp4

4. For verbose output:
   orbis-pub-gen.exe image Project.gp4 --verbose

5. To specify output folder:
   orbis-pub-gen.exe image Project.gp4 --output my_output


TROUBLESHOOTING
═════════════
Issue: "File does not exist: param.sfo"
─────────────────────────────────────────
Cause: Path mismatch or missing file

Fixes:
1. Verify files exist:
   - Check CUSA12878-app/sce_sys/param.sfo exists
   - Check CUSA12878-app/sce_sys/icon0.png exists
   
2. Run from correct folder:
   - Ensure you're in windows_build/ folder
   - NOT in a subfolder like CUSA12878-app/

3. Check GP4 paths match reality:
   - The GP4 uses relative paths from windows_build/
   - Example: orig_path="CUSA12878-app/sce_sys/param.sfo"


Issue: "Duplicate entry" warning
─────────────────────────────────────────
Cause: GP4 lists same file twice

Fix:
1. Open Project.gp4 in text editor
2. Search for duplicate <file> entries
3. Remove duplicates


Issue: GUI crashes or freezes
─────────────────────────────────────────
Fixes:
1. Try CLI instead for detailed errors
2. Verify no spaces in folder paths
3. Run as Administrator


ISSUE: PKG installs with error on PS4
═══════════════════════════════════════
If your PKG builds but fails to install on PS4:

1. Try Python-generated packages instead:
   - output/custom_songs_v6.pkg
   - output/custom_songs_v7.pkg

2. Check Content ID format:
   - Must match: UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX


WORKING DIRECTORY
══════════════
IMPORTANT: The working directory matters!

✓ CORRECT: Running from windows_build/ folder
   cd C:\PS4Tools\windows_build
   orbis-pub-gen image Project.gp4

✗ WRONG: Running from subfolder
   cd C:\PS4Tools\windows_build\CUSA12878-app
   orbis-pub-gen image ../Project.gp4


ALTERNATIVE: Python Pipeline
═════════════════════════
If orbis-pub-gen fails, use Python:

cd /workspace/beat-saber-ps4-custom-songs
python3 pipeline.py

Output files:
- output/custom_songs_v6.pkg
- output/custom_songs_v7.pkg
- output/custom_unlocker_v3.pkg


CONTENT IDs
═════════
The custom DLC uses:
- Content ID: UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX
- Title ID: CUSA12878
- Category: ac (add-on content)


TESTING ON PS4
═════════════
1. Install custom_unlocker_v3.pkg first (unlocks DLC)
2. Install custom_songs_v*.pkg
3. Launch Beat Saber
4. Check for new songs in custom music pack


MORE HELP
═════════
- LibOrbisPkg: https://github.com/OpenOrbis/LibOrbisPkg
- GoldHEN: https://github.com/GoldHEN/GoldHEN/
- BeatSaver: https://beatsaver.com/

═══════════════════════════════════════════════════════════════════
Updated: 2026-04-27