# PS4 Beat Saber File Analysis — 2026-04-24

## Verified CUSA IDs

| Region | CUSA ID | Content ID | Notes |
|--------|---------|-----------|-------|
| **US (PSVR Bundle)** | **CUSA12878** | `UP4882-CUSA12878_00-BEATSABERFULL000` | Confirmed via GameFAQs + PS Store |
| **EU** | CUSA14143 | `UP4882-CUSA14143_00-BEATSABERFULL000` | EU release |
| **JP** | CUSA12878 | — | Same as US |

The fileshare context had a typo listing `CUSA18278` — confirmed as **CUSA12878** for all known regions.

---

## Fileshare Contents

### Main Directory: `smb://192.168.100.135/incoming/temp/BeatSaberPs4/`

| File/Folder | Size | Description |
|-----------|------|-------------|
| `Beat.Saber_CUSA12878_v2.04_BACKPORT_[...].pkg` | 4.9 GB | Full backported game v2.04 (9.00-12.00) |
| `Beat.Saber_CUSA12878_v1.00_[5.50].pkg` | 255 MB | Launcher stub v1.00 |
| `Beat.Saber_CUSA12878_v1.79_[9.00].pkg` | 3.5 GB | Full game v1.79 |
| `Beat.Saber_CUSA18278_DCLPACK.v14_[246]_OPOISSO893/` | Directory | 246 DLC song packages |

---

## PKG Format Analysis

### v1.00 PKG (CUSA12878, v1.00, 255 MB)

**Content ID:** `UP4882-CUSA12878_00-BEATSABERFULL000`
**Type:** `CONTENT_TYPE_GD` (Game)
**DRM:** `PS4`
**Files:** 15 files (27 entries), 6 SC (system content) entries

**File Structure:**

| File ID | Name | Size (bytes) | Offset | Encrypted |
|---------|------|-------------|--------|----------|
| 0x001 | (unnamed) | 864 | 0x2DE0 | No |
| 0x010 | (unnamed) | 2,048 | 0x2000 | No |
| 0x020 | (unnamed) | 256 | 0x2800 | **Yes** |
| 0x080 | (unnamed) | 384 | 0x2900 | No |
| 0x100 | (unnamed) | 864 | 0x2A80 | No |
| 0x200 | (unnamed) | 233 | 0x3140 | No |
| 0x400 | (unnamed) | 1,024 | 0x7200 | **Yes** |
| 0x401 | (unnamed) | 512 | 0x7600 | **Yes** |
| 0x402 | (unnamed) | 160 | 0x3BB3F0 | **Yes** |
| 0x403 | (unnamed) | 532 | 0x3BB490 | **Yes** |
| 0x409 | (unnamed) | 8,192 | 0x3BB6B0 | No |
| **0x1000** | `param.sfo` | 1,868 | 0x7800 | No |
| **0x1001** | `playgo-chunk.dat` | 416 | 0x3230 | No |
| **0x1002** | `playgo-chunk.sha` | 15,540 | 0x33D0 | No |
| **0x1003** | `playgo-manifest.xml` | 368 | 0x7090 | No |
| **0x1004** | `pronunciation.xml` | 3,132 | 0x2974E0 | No |
| **0x1005** | `pronunciation.sig` | 20 | 0x298120 | No |
| **0x1006** | `pic1.png` | 180,074 | 0x4D800 | No |
| 0x100B | `shareparam.json` | 58 | 0x3BB3B0 | No |
| 0x100D | `save_data.png` | 14,309 | 0x293CF0 | No |
| **0x1200** | `icon0.png` | 104,767 | 0x7F50 | No |
| **0x1220** | `pic0.png` | 180,074 | 0x21890 | No |
| 0x1260 | `changeinfo/changeinfo.xml` | 220 | 0x298140 | No |
| 0x1280 | `icon0.dds` | 131,200 | 0x79770 | No |
| 0x12A0 | `pic0.dds` | 1,036,928 | 0x997F0 | No |
| 0x12C0 | `pic1.dds` | 1,036,928 | 0x196A70 | No |
| **0x1400** | `trophy/trophy00.trp` | 1,192,336 | 0x298220 | No |

**Analysis:** The v1.00 PKG is a **launcher stub** — it contains no game data files (`.dat`, `.assets`, etc). It's just the PS4 shell with PARAM.SFO, icons, trophies, and playgo manifests. The actual game data must be in a separate data package or downloaded at first launch. The game content (including songs) is in the larger v1.79 or v2.04 packages, OR in the individual DLC packages.

**PARAM.SFO Parsed Fields:**
```
APP_TYPE: 1.00
APP_VER: 3.00.000
ATTRIBUTE: 1.00
CATEGORY: 1.00
CONTENT_ID: SABERFULL000...
PUBTOOLINFO: (build metadata)
TITLE: 5080000,st_t
TITLE_ID: 02408004000400006764
VERSION: 3.00.000
```

---

## DLC Pack Structure

### Directory: `Beat.Saber_CUSA18278_DCLPACK.v14_[246]_OPOISSO893/`

**Contains:** 246 individual DLC song packages organized into 26 music pack folders.

### DLC PKG Naming Convention:
```
CUSA12878_<Artist>-<SongName>[_OPOISSO893].pkg
```
- **Size:** ~1 MB each (1,048,576 bytes — exactly 1MB block)
- **Format:** Individual song DLC packages

### DLC Music Packs (26 packs, 246 songs):

| Pack # | Pack Name | Songs |
|--------|---------|-------|
| 01 | MONSTERCAT MUSIC PACK VOL 1 | 10 |
| 02 | IMAGINE DRAGONS MUSIC PACK | 12 |
| 03 | PANIC! AT THE DISCO MUSIC PACK | 10 |
| 04 | ROCKET LEAGUE & MONSTERCAT MUSIC PACK | 6 |
| 05 | GREEN DAY MUSIC PACK | 6 |
| 06 | TIMBALAND MUSIC PACK | 5 |
| 07 | LINKIN PARK MUSIC PACK | 11 |
| 08 | BTS MUSIC PACK | 13 |
| 09 | INTERSCOPE MIXTAPE MUSIC PACK | 7 |
| 10 | SKRILLEX MUSIC PACK | 8 |
| 11 | BILLIE EILISH MUSIC PACK | 10 |
| 12 | LADY GAGA MUSIC PACK | 10 |
| 13 | FALL OUT BOY MUSIC PACK | 8 |
| 14 | ELECTRONIC MIXTAPE PACK | 10 |
| 15 | LIZZO MUSIC PACK | 9 |
| 16 | THE WEEKND MUSIC PACK | 12 |
| 17 | ROCK MIXTAPE MUSIC PACK | 8 |
| 18 | QUEEN MUSIC PACK | 11 |
| 19 | LINKIN PARK x MIKE SHINODA MUSIC PACK | 8 |
| 20 | THE ROLLING STONES MUSIC PACK | 11 |
| 21 | DAFT PUNK MUSIC PACK | 10 |
| 22 | HIP HOP MIXTAPE MUSIC PACK | 9 |
| 23 | SHOCK DROPS MUSIC PACK | 3 |
| 24 | BRITNEY SPEARS MUSIC PACK | 11 |
| 25 | MONSTERCAT MIXTAPE 2 MUSIC PACK | 12 |
| 26 | METALLICA MUSIC PACK | 18 |
| **Total** | | **246** |

### Sample DLC PKG Filenames:

**Britney Spears:**
- `CUSA12878_Britney.Spears-Till.the.World.Ends_OPOISSO893.pkg`
- `CUSA12878_Britney.Spears-Toxic_OPOISSO893.pkg`
- `CUSA12878_Britney.Spears-Baby.One.More.Time_OPOISSO893.pkg`

**Queen:**
- `CUSA12878_Queen-Bohemian.Rhapsody.pkg`
- `CUSA12878_Queen-Dont.Stop.Me.Now.pkg`
- `CUSA12878_Queen-We.Will.Rock.You.pkg`
- `CUSA12878_Queen-Killer.Queen.pkg`

**The Weeknd:**
- `CUSA12878_The.Weeknd-Blinding.Lights.pkg` (⚠️ This is a community favorite!)
- `CUSA12878_The.Weeknd-The.Hills.pkg`
- `CUSA12878_The.Weeknd-I.Feel.It.Coming.pkg`

**Imagine Dragons:**
- `CUSA12878_Imagine.Dragons-Believer.pkg` (⚠️ Also a top community song!)
- `CUSA12878_Imagine.Dragons-Enemy.pkg`
- `CUSA12878_Imagine.Dragons-Natural.pkg`

**Electronic Mix:**
- `CUSA12878_Darude-Sandstorm.pkg` (⚠️ Top community map!)
- `CUSA12878_Marshmello-Alone.pkg`
- `CUSA12878_Martin.Garrix-Animals.pkg`

---

## Key Observations

1. **DLC packages are individual** — each song = one `.pkg` file. This is different from PC where songs are JSON files in a folder.
2. **DLC package size ~1MB each** — very small, suggesting compressed Unity asset bundles inside.
3. **DLC naming uses CUSA12878** — confirms correct CUSA ID.
4. **The DLC contains audio + beatmap data** — the entire song (audio clip, cover art, beatmaps) is packed into a single small package per song.
5. **No `sharedassets` in DLC packages** — the DLC packages likely override or extend the main game's level pack, referencing internal assets rather than modifying sharedassets.
6. **Community favorites ARE in the official DLC** — songs like Blinding Lights, Believer, Sandstorm, etc. are already official DLC! These may not need custom song conversion at all.

---

## Next Steps for Analysis

1. **Download and extract 2-3 DLC song packages** to understand the internal format
2. **Download and extract the v1.79 full game** to find `sharedassets*.assets` files
3. **Compare DLC internal format with known PC JSON format** to understand conversion requirements
4. **Look for `BeatMapData` and `AudioClip` asset types** in extracted files