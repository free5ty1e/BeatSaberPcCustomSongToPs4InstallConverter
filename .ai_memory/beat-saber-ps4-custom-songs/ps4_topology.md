# PS4 FTP Topology — Beat Saber PS4 Setup

## PS4 Connection Info

- **FTP Server**: `192.168.100.117:2121`
- **Username**: anonymous
- **Password**: anonymous
- **Status**: Read/write access confirmed
- **Note**: `nlst()` command not implemented, use `LIST` instead

---

## Installed Game: CUSA12878 (Beat Saber US PS4/PSVR)

### Package Paths

| Path                     | File         | Size  | Description                |
| ------------------------ | ------------ | ----- | -------------------------- |
| `/user/app/CUSA12878/`   | `app.pkg`    | 254MB | v1.00 launcher shell       |
| `/user/app/CUSA12878/`   | `app.pbm`    | 774B  | Content info manifest      |
| `/user/app/CUSA12878/`   | `app.json`   | 258B  | Package metadata           |
| `/user/app/CUSA12878/`   | `app.xml`    | 279B  | PlayGo status              |
| `/user/patch/CUSA12878/` | `patch.pkg`  | 4.9GB | v2.04 backport (ENCRYPTED) |
| `/user/patch/CUSA12878/` | `patch.json` | 263B  | Patch metadata             |
| `/user/patch/CUSA12878/` | `patch.xml`  | 279B  | PlayGo status              |

### Package Metadata

**app.json** (v1.00 launcher):

```json
{
  "numberOfSplitFiles": 1,
  "packageDigest": "D8842D6F...",
  "pieces": [
    {
      "fileOffset": 0,
      "fileSize": 254607360,
      "url": "/mnt/usb0/Games/VR/BeatSaber-CUSA12878/Beat.Saber_CUSA12878_v1.00_[5.50]_OPOISSO893.pkg"
    }
  ]
}
```

**patch.json** (v2.04 backport):

```json
{
  "numberOfSplitFiles": 1,
  "packageDigest": "294D4A5D...",
  "pieces": [
    {
      "fileOffset": 0,
      "fileSize": 4943511552,
      "url": "/mnt/usb0/Beat.Saber_CUSA12878_v2.04_BACKPORT_[5.05-6.72-7.xx-9.00-11.00-12.00]_OPOISSO893.pkg"
    }
  ]
}
```

### Encryption Status

- **app.pkg**: Encrypted (PKG magic `7F434E54` at start)
- **patch.pkg**: **ENCRYPTED** — confirmed with random-looking body data at 0x2000
- The PS4 kernel decrypts PKGs transparently when the game runs
- FTP serves raw encrypted file data
- Cannot extract decrypted game files via FTP alone

---

## Save Data

**Path**: `/user/home/1c9d7579/savedata/CUSA12878/`

| File                        | Size | Description                                 |
| --------------------------- | ---- | ------------------------------------------- |
| `sdimg_sce_sdmemory`        | 39MB | Virtual SD card image (profile + game data) |
| `sdimg_Default`             | 3MB  | Default profile                             |
| `sdimg_sce_bu_sce_sdmemory` | 39MB | Backup SD card image                        |
| `*.bin`                     | 96B  | Metadata files                              |

### SD Card Image Format

- **sdimg_sce_sdmemory** (39MB total):
  - Header: `01000000000000000b2a3301...` at offset 0
  - Contains game profile/settings (decrypted)
  - Contains compressed data (gzip/zlib streams found)
  - NO Unity game assets (game data is in encrypted patch.pkg)
  - Format: PS4 virtual SD card (proprietary)

---

## GoldHEN Modding Setup

**Path**: `/user/data/GoldHEN/`

### Plugins Directory

**Path**: `/user/data/GoldHEN/plugins/`

| File                      | Size  | Description                  |
| ------------------------- | ----- | ---------------------------- |
| `RB4DX-Plugin.prx`        | 96KB  | Rock Band 4 modding plugin   |
| `game_patch.prx`          | 132KB | Generic game patching plugin |
| `afr.prx`                 | 72KB  | Audio frame rate patch       |
| `aio_fix_505.prx`         | 57KB  | All-in-one fix               |
| `button_swap.prx`         | 55KB  | Button remapping             |
| `fliprate_remover.prx`    | 72KB  | Flip rate patch              |
| `force_1080p_display.prx` | 72KB  | Display resolution patch     |
| `gamepad_helper.prx`      | 91KB  | Gamepad helper               |
| `no_share_watermark.prx`  | 73KB  | Remove share watermark       |
| `plugins.ini`             | 257B  | Plugin configuration         |
| `md5.txt`                 | 542B  | MD5 checksums                |
| `sha256.txt`              | 833B  | SHA256 checksums             |

### RB4DX Modding Structure

**Path**: `/user/data/GoldHEN/RB4DX/ps4/`

```
ps4/
├── track/           # Custom instrument tracks (674KB scene files)
│   ├── drums/
│   ├── guitar/
│   ├── vocals/
│   ├── guitar_unlit_og.scene_ps4      # 674KB
│   ├── guitar_unlit_rb2.scene_ps4     # 674KB
│   └── vocals_drum.scene_ps4          # 437KB
├── fmod_banks/
│   └── PS4/                          # Custom FMOD audio banks
├── char/              # Character models
│   └── musician/
├── config/            # Game configuration patches
├── dx/                # Gameplay patches
├── ui/                # UI textures
│   ├── background/
│   ├── game/
│   ├── locale/
│   ├── overshell/
│   ├── startup/
│   ├── textures/
│   └── voting/
├── patched_songs/    # Custom song data
├── settings/         # Plugin settings
│   ├── controller/
│   ├── gameplay/
│   ├── sfx/
│   ├── theme/
│   ├── venue/
│   └── visuals/
├── shared/           # Shared assets
│   └── scene/
└── system/           # System configuration
```

### RB4DX Plugin Architecture (Reference)

The RB4DX plugin works by:

1. Loading modded assets from `/user/data/GoldHEN/RB4DX/ps4/`
2. **Runtime patching**: Hooks FMOD audio, file I/O, game logic
3. **File redirects**: Overrides game file reads with modded versions
4. **Memory patches**: Patches game functions in memory

Key hooks used:

- FMOD bank loading hooks
- File system `open()` / `read()` / `stat()` hooks
- Game logic function patches (via `game_patch.prx`)

---

## Directory Structure (Full FTP Tree)

```
/
├── adm/
├── app_tmp/
├── data/
├── dev/
├── eap_user/
├── eap_vsh/
├── hdd/
│   └── (user data, etc.)
├── host/
├── hostapp/                # Game app mounts (empty/inactive)
├── mnt/
│   ├── pfs/
│   │   ├── pfs/           # Trophy data only
│   │   └── sandbox/      # GoldHEN/jailbreak sandboxes
│   ├── disc/
│   ├── ext0/              # External storage (USB)
│   └── rnps/
├── preinst/
├── preinst2/
├── system/                # System libraries
│   ├── app/
│   ├── common/
│   ├── priv/
│   ├── sys/
│   ├── vsh/
│   └── vsh_asset/
├── system_ex/             # Extended system
│   └── app/
├── system_tmp/
├── update/
├── usb/
├── user/
│   ├── app/
│   │   └── CUSA12878/    # Beat Saber game directory
│   ├── appmeta/
│   ├── bgft/             # Download manager
│   │   └── task/         # 80+ download tasks
│   ├── common/
│   ├── data/
│   │   ├── GoldHEN/      # MODDING KEY LOCATION
│   │   ├── PS4Xplorer/
│   │   ├── cache0001/
│   │   ├── cachecip0001/
│   │   └── sce_logs/
│   ├── home/
│   │   └── 1c9d7579/
│   │       ├── frined_notification/
│   │       ├── ime/
│   │       ├── np/
│   │       ├── savedata/
│   │       │   ├── CUSA12878/       # Beat Saber save data
│   │       │   └── (other games)/
│   │       ├── topmenu/
│   │       ├── trophy/
│   │       └── webkit/
│   ├── license/
│   ├── patch/
│   │   └── CUSA12878/    # Beat Saber patch directory
│   ├── priv/
│   ├── savedata/
│   ├── sshared/
│   ├── system/
│   └── temp/
└── (PS4 device files via /dev)
```

---

## Device Files (`/dev/`)

Key devices visible via FTP:

| Device            | Type      | Description                             |
| ----------------- | --------- | --------------------------------------- |
| `pfsctldev`       | Character | PFS (PlayStation File System) control   |
| `da0x6.crypt`     | Block     | Main hard drive (encrypted partition 6) |
| `ugen0.*`         | Character | USB devices                             |
| `ugen2.2`         | Character | Fileshare USB?                          |
| `notification0-5` | Character | System notifications                    |
| `mbus`            | Character | Message bus                             |
| `sbl_srv`         | Character | Security bottom layer                   |
| `npdrm`           | Character | NPDRM (DRM) device                      |
| `sflash0*`        | Block     | System flash (firmware)                 |

---

## Notes for Beat Saber Modding

1. **Custom Song Path**: Create `/user/data/GoldHEN/BeatSaber/songs/` following RB4DX pattern
2. **Plugin Needed**: Need a `BeatSaber-Plugin.prx` like `RB4DX-Plugin.prx`
3. **Game Data Access**: Cannot access decrypted game data via FTP — need PS4-side plugin
4. **Unity Hooks**: Plugin needs to hook Unity `AssetBundle.LoadFromFile` and `Resources.Load`
5. **FMOD Hooks**: Plugin needs to hook FMOD bank loading (like RB4DX does)

---

## Useful Commands

### Connect via Python

```python
import ftplib
s = ftplib.FTP()
s.connect('192.168.100.117', 2121, timeout=15)
s.login()
s.cwd('/user/app/CUSA12878')
s.retrlines('LIST', print)  # Use LIST instead of nlst()
```

### Download a file

```python
with open('/path/local', 'wb') as f:
    s.retrbinary('RETR filename', f.write)
```

### Read from offset (REST command)

```python
s.voidcmd('TYPE I')
conn = s.transfercmd('RETR patch.pkg', rest=0x2000)
data = conn.recv(4096)
conn.close()
```

### List directory

```python
s.cwd('/path')
s.retrlines('LIST', print)
```

---

## Last Updated

- **Date**: 2026-04-24
- **PS4 Firmware**: 9.00
- **GoldHEN Version**: Active (timestamp Apr 1 2025, Apr 24 2026)
- **Fileshare**: Connected as USB mass storage device
