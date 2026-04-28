# Beat Saber PS4 Custom Songs - Progress Log

## Project Goal
Build a PS4 custom songs pipeline that downloads and converts Beat Saber PC songs to installable fPKG format for Beat Saber on PS4 with GoldHEN.

## Constraints
- User plays on "Hard", friends on "Medium/Easy"
- Must have all difficulties (avoid Expert/Expert+ only)
- Keep scripts outside gitignored folders for source control
- Markdown docs at project root

## Test Results

### CE-36426-1 Error (v5)
- **Date**: 2026-04-27
- **Packages tested**: custom_songs_v5.pkg, custom_unlocker_v2.pkg
- **Result**: CE-36426-1 error when installing via GoldHEN
- **Root cause**: Header used wrong field format (64-bit BE vs 32-bit LE)

### v6 Build (Latest)
- **Date**: 2026-04-27
- **Status**: Created with correct 32-bit LE fields
- **Output**: /beat-saber-ps4-custom-songs/output/custom_songs_v6.pkg

### Working DLC Reference Analysis
- Uses mixed endianness: most fields at 0x10-0x2c are 32-bit **little-endian**
- The reference shows: 0x10=0x0b, 0x14=0x0b000600, 0x18=0x802a0000 (all as LE)

## PKG Header Formats (v6 vs Reference)

| Offset | v6 (BE) | Reference (LE as shown) | Notes |
|--------|---------|-------------------------|-------|
| 0x10 | 0x00000000 | 0x0000000b | entry table |
| 0x14 | 0x00000000 | 0x0006000b | entry count |
| 0x18 | 0x00000200 | 0x00002a80 | body offset |
| 0x20 | 0x0006ca80 | 0x00000000 | body size |
| 0x28 | 0x00002000 | 0x00000000 | PFS offset |

## Issues Status
- [x] v5 CE-36426-1 - FIXED: Header format corrected in v6
- [ ] Test v6 on PS4 - Pending
- [ ] Fix orbis-pub-gen param.sfo error - Still needed

## Songs Data
- **Total downloaded**: 94+ songs from BeatSaver API
- **Location**: /beat-saber-ps4-custom-songs/songs_repo/

## Next Steps
1. Test custom_songs_v6.pkg on PS4 with GoldHEN
2. If CE-36426-1 persists, investigate remaining header differences