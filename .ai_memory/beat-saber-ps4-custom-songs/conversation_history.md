# Beat Saber PS4 Custom Songs Pipeline - Complete Conversation History

**Date:** 2026-04-27  
**Project:** Beat Saber PS4 Custom Songs Pipeline  
**Goal:** Build PS4 fPKG for custom songs with GoldHEN

---

## Executive Summary

The user wants to build a pipeline that:
1. Downloads Beat Saber songs from PC version (BeatSaver API)
2. Converts to PS4-compatible format  
3. Creates installable fPKG for GoldHEN jailbroken PS4
4. Includes all difficulty levels (Easy/Normal/Hard from user's request - avoid Expert/Expert+ only)

**Constraints:**
- User plays on "Hard", friends on "Medium/Easy"
- Must have all difficulties available
- Keep scripts outside gitignored folders
- Markdown docs at project root

---

## Test Results Timeline

### CE-36426-1 Error (v5, v6, v7)
- **Date**: 2026-04-27
- **Packages tested**: custom_songs_v5.pkg, custom_songs_v6.pkg, custom_unlocker_v2.pkg, custom_unlocker_v3.pkg
- **Result**: CE-36426-1 error when installing via GoldHEN
- **Analysis**: Header format issue - mixed endianness in PKG header fields

### CE-34707-1 Error (v1-v4)
- **Date**: 2026-04-26
- **Packages tested**: custom_songs_v1-v4.pkg
- **Result**: CE-34707-1 error
- **Analysis**: Different error code - shows changes affect PKG validity differently

### Orbis-Pub-Gen Error
- **Date**: 2026-04-27
- **Error**: "File does not exist: param.sfo"
- **Status**: Still occurring - GP4 has duplicate file entries

---

## PKG Header Comparison (Reference vs Our v6)

The reference DLC uses **32-bit little-endian** for fields at 0x10-0x2c, NOT 64-bit big-endian as we initially used:

| Offset | Reference (LE) | Our v6 (BE) | Issue |
|--------|-----------------|--------------|-------|
| 0x10 | 0x0b000000 | 0x00000000 | entry table off |
| 0x14 | 0x0b000600 | 0x00000000 | entry count |
| 0x18 | 0x802a0000 | 0x00000200 | body offset |
| 0x20 | 0x00000000 | 0x0006ca80 | body size |
| 0x28 | 0x00000000 | 0x00002000 | PFS offset |

Reference uses mixed endianness - key fields at 0x10-0x2c are 32-bit LE!

---

## Working DLC Reference Analysis

### Reference PKG Structure
- **Size**: 1,048,576 bytes (1 MB)
- **Magic**: 7f434e54 ("7fCNT")
- **Entry count**: 0 (PFS mode - no entry table)
- **Body offset**: 0x200
- **Content ID**: UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX

### param.sfo Structure
```yaml
TITLE: "RIOT - Overkill"
TITLE_ID: "CUSA12878"
CONTENT_ID: "UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX"
VERSION: "01.00"
CATEGORY: "ac"
CONTENT_TYPE: 0x1b (27 = AC/DLC)
DRM_TYPE: 0x0f (15 = free)
```

---

## Pipeline Versions

| Version | Method | Status | Notes |
|---------|--------|--------|-------|
| v1-v4 | Various custom builds | CE-34707-1 | Early attempts |
| v5 | Python custom header (64-bit BE) | CE-36426-1 | Wrong endianness |
| v6 | Python custom header (32-bit LE) | CE-36426-1 | Fixed endianness, same error |
| v7 | Template clone from reference | Pending | Copy reference header |
| v1-v2 | Unlocker | CE-36426-1 | |

---

## Songs Data

- **Total downloaded**: 94+ songs from BeatSaver API
- **Location**: `/beat-saber-ps4-custom-songs/songs_repo/`
- **Converted location**: `/beat-saber-ps4-custom-songs/windows_build/CUSA12878-app/songs/`

---

## Current Issues

### Issue 1: CE-36426-1 Error
The v6 header using correct 32-bit LE fields still fails. Likely issues:
- Missing or incorrect core PKG header fields
- Entry table structure required even with entry_count=0
- Digest hashes incorrect
- Content ID format mismatch

**Solution:** Template clone approach (v7) - copy reference header entirely, swap only PFS content

### Issue 2: Orbis-Pub-Gen "File does not exist"
- GP4 has duplicate file entries (param.sfo in two locations)
- Path confusion between windows_build/sce_sys/ and CUSA12878-app/sce_sys/
- Need clean GP4 with single source

**Solution:** Clean up GP4, use only CUSA12878-app/sce_sys/

---

## Execution Plan

### Phase 1: Template-Cloned PKG (v7)
1. Load reference PKG as template
2. Copy entire header
3. Replace PFS with our content
4. Update PFS-referencing fields only
5. Output: custom_songs_v7.pkg

### Phase 2: Dual PKG Generation
- Keep v6 as alternative
- Build both v6 and v7 in pipeline

### Phase 3: Unlocker
- Clone unlocker header similarly

### Phase 4: Documentation
- Create windows_build/README.txt with CLI + GUI instructions

### Phase 5: GP4 Cleanup 
- Remove duplicate sce_sys folder
- Regenerate Project.gp4

### Phase 6: Pipeline Update
- Build both versions
- Show both in output messages

---

## Key Files

```
beat-saber-ps4-custom-songs/
├── PROGRESS.md                    ← This project's progress log
├── pipeline.py                   ← Main wrapper script
├── songs_repo/                  ← Downloaded songs (94+)
├── output/
│   ├── custom_songs_v6.pkg    ← Our custom header
│   ├── custom_songs_v7.pkg    ← Template clone (new)
│   └── custom_unlocker_v3.pkg  ← 
├── windows_build/
│   ├── Project.gp4            ← GP4 project (needs fix)
│   ├── CUSA12878-app/
│   │   ├── sce_sys/
│   │   └── songs/
│   └── sce_sys/               ← Duplicate (remove)
├── scripts/
│   ├── build_pkg_v6.py       ← Our custom header
│   ├── build_pkg_v7.py        ← Template clone (new)
│   └── create_unlocker_v3.py  ← 
└── dlc_reference/
    └── CUSA12878_RIOT-Overkill.pkg  ← Reference template
```

---

## Next Steps

1. Test v7-clone package on PS4
2. Test v6 package on PS4  
3. If v7 works, iterate on it
4. If both fail, need deeper analysis

---

## User Preferences

- Plays on Hard difficulty
- Friends play on Medium/Easy
- Wants all difficulties available
- Scripting outside gitignored folders
- Markdown docs at project root

---

*Exported: 2026-04-27*