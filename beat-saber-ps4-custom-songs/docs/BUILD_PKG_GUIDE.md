# Building PS4 PKG with Modified Levels

## After Copying the File (Test 2B)

Once you've copied `beatsaber` to a new name (e.g., `mysong`), follow these steps to build a PKG:

---

## Option A: Using PS4 Fake PKG Tools (Windows)

The tools are in your `windows_build/` folder.

### Steps

1. **Copy your modified levels** to the build folder:
   - Copy entire `BeatmapLevelsData/` folder
   - To: `windows_build/CUSA12878-patch/Media/StreamingAssets/`

2. **Open orbis-pub-gen.exe:**
   - Location: Where you have PS4 Fake PKG Tools installed
   - Usually: `orbis-pub-gen.exe` from v3.87+

3. **Open the Project File:**
   - File → Open → Select `Project.gp4` from `windows_build/`

4. **Build the PKG:**
   - Press **F5** or click Build button
   - Output: `custom_songs.pkg`

5. **Location of output:**
   - Check the build output path in settings

---

## Option B: Using Command Line (If Available)

If you have orbis-pub-gen in your PATH:

```bash
orbis-pub-gen.exe -project windows_build/Project.gp4 -output CUSA12878.pkg
```

---

## File Structure Needed

Your `BeatmapLevelsData/` should look like:

```
BeatmapLevelsData/
├── beatsaber          (original - unchanged)
├── mysong           (your copy)
├── another_copy     (another copy if you made more)
└── ...            (all levels the game will load)
```

---

## What to Check Before Building

1. **Verify files exist:**
   ```
   ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/
   ```
   - Should contain: `beatsaber` + your new copy(s)

2. **Reference files:**
   - `CUSA12878-app/sce_sys/` - Required system files
   - `Project.gp4` - Build configuration

---

## After Building

Transfer to PS4:
- **USB:** Copy PKG to USB → GoldHEN → Install
- **FTP:** Upload to `/data/` → GoldHEN → Install

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Invalid file" error | Check BeatmapLevelsData path is correct |
| "Missing files" error | Ensure sce_sys folder is included |
| "Wrong Content ID" | Use provided Content ID: `UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX` |

---

## Notes

- The game auto-loads ALL files in `BeatmapLevelsData/`
- No additional configuration needed
- Just copy existing level files → they appear as new songs!

This is why Test 2B was the key - we don't need to modify anything, just copy the existing level files!