# Beat Saber PS4 Custom Songs - Progress Log

## Project Goal
Build a PS4 custom songs pipeline that downloads and converts Beat Saber PC songs to installable fPKG format for Beat Saber on PS4 with GoldHEN.

## Constraints
- User plays on "Hard", friends on "Medium/Easy"
- Must have all difficulties (avoid Expert/Expert+ only)
- Keep scripts outside gitignored folders for source control
- Markdown docs at project root

## Test Results

### PKG Test History

| Version | Method | Status | Error |
|---------|--------|--------|-------|
| v1-v4 | Python custom | CE-34707-1 | Various attempts |
| v5 | Python (64-bit BE) | CE-36426-1 | Wrong endianness |
| v6 | Python (32-bit LE) | CE-36426-1 | Header structure |
| **v7** | Template clone | **TEST PENDING** | - |
| Unlocker v2 | Python | CE-36426-1 | - |
| **Unlocker v3** | Template clone | **TEST PENDING** | - |

### CE-36426-1 Root Cause
Reference PKG uses **32-bit LE** fields at 0x10-0x2c (NOT 64-bit BE as initially used).
Even after fixing endianness, the header still isn't accepted - likely needs:
- Correct entry table structure
- Proper digest hashes
- Specific template cloning approach (v7)

### Orbis-Pub-Gen
- **Issue**: "File does not exist: param.sfo"
- **Fix Applied**: Removed duplicate sce_sys folder, regenerated GP4 with 831 files
- **Status**: Need testing

## Working DLC Reference Analysis
- Magic: 7f434e54 ("7fCNT")
- Content ID: UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX
- Title ID: CUSA12878
- DRM: 0x0f (free), Type: 0x1b (DLC)

## Current Build Outputs

| File | Method | Size |
|------|--------|------|
| custom_songs_v6.pkg | Custom header (LE) | 449,152 |
| custom_songs_v7.pkg | Template clone | 449,152 |
| custom_unlocker_v3.pkg | Template clone | 20,512 |

## Files Structure
```
beat-saber-ps4-custom-songs/
├── README.md                    ← Project index
├── PROGRESS.md                 ← This file
├── pipeline.py                 ← Main wrapper
├── songs_repo/                 ← 94+ downloaded songs
├── output/
│   ├── custom_songs_v6.pkg
│   ├── custom_songs_v7.pkg
│   └── custom_unlocker_v3.pkg
├── windows_build/
│   ├── Project.gp4            ← Regenerated (831 files)
│   ├── README.txt             ← CLI/GUI instructions
│   ├── CUSA12878-app/
│   │   ├── sce_sys/
│   │   └── songs/
│   └── output/
├── scripts/
│   ├── build_pkg_v6.py        ← Custom header
│   ├── build_pkg_v7.py         ← Template clone
│   └── create_unlocker_v3.py   ← Unlocker
└── dlc_reference/
    └── CUSA12878_RIOT-Overkill.pkg  ← Reference template
```

## Next Steps
1. Test v7 + v3 unlocker on PS4 with GoldHEN
2. If v7 works, iterate on it
3. If both fail, debug deeper with reference comparison
4. Test orbis-pub-gen with cleaned GP4

## References
- BeatSaver API: https://beatsaver.com/
- GoldHEN: https://github.com/GoldHEN/GoldHEN/
- OpenOrbis: https://github.com/OpenOrbis/LibOrbisPkg