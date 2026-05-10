# Uninstalling Custom PKGs from PS4

## Method 1: Through GoldHEN Settings (Recommended)

### Steps

1. **Launch GoldHEN on PS4**
   - If GoldHEN isn't installed, see other methods below

2. **Navigate to Settings**
   - From the PS4 home screen, go to **Settings**

3. **Find GoldHEN Options**
   - Scroll down to find **GoldHen** (may be near the bottom)
   - Or: Settings → Debug Settings → Game → Package Installer

4. **Use Package Installer**
   - Look for **Package Installer** or **Install Package**
   - This shows all installed PKGs

5. **Find Custom Songs PKG**
   - Look for entries like:
     - "Beat Saber Custom Songs"
     - "BeatSaberDeluxe"
     - Or entries with your Content ID: `UP4882-CUSA12878`

6. **Delete It**
   - Select the PKG
   - Press the **Options** button on your controller
   - Select **Delete** or **Remove**
   - Confirm the deletion

7. **Launch Original Beat Saber**
   - After deletion, the original game should work normally
   - You may need to reinstall the game from disk/PSN if fully removed

---

## Method 2: Through PS4 Settings

### Steps

1. **Go to Settings**

2. **Navigate to Storage**
   - Settings → Storage → System Storage

3. **View Applications**
   - Or: Settings → Application Saved Data Management → Saved Data in System Storage

4. **Find Beat Saber**
   - Look for "Beat Saber" in the list

5. **Delete Custom Content**
   - You may see separate entries for the base game and DLC/custom content
   - Delete only the custom content (CUSA12878 entries)

---

## Method 3: Rebuild Database (If Issues Persist)

If you can't find or delete the PKG:

### Steps

1. **Boot into Safe Mode**
   - Power off PS4 completely
   - Hold the **power button** until you hear a second beep
   - (First beep = power on, Second beep = safe mode)

2. **Connect Controller**
   - Connect via USB and press PS button

3. **Select Options**
   - Choose **Rebuild Database**

4. **Wait**
   - This may take a while but won't delete your games

5. **Try Method 1 Again**
   - After rebuild, the PKG should be easier to find

---

## Method 4: Fresh Reinstall (Nuclear Option)

If all else fails:

1. **Delete ALL Beat Saber Content**
   - Settings → Storage → System Storage → Beat Saber → Delete
   - Delete everything related

2. **Reinstall from Disk/PSN**
   - Reinstall the original game
   - DO NOT install the custom songs PKG

3. **Start Fresh**
   - Now you have a clean slate for testing

---

## Verification

To verify removal:

1. Launch Beat Saber (original version)
2. Check that custom songs are gone
3. Verify original songs still work
4. Check that all difficulties (Easy through ExpertPlus) are available

---

## Important Notes

- **Deleting custom PKG does NOT delete original game**
- Custom songs are installed as ADD-ONS, not replacing the base game
- Your game progress and settings should be preserved
- Original DLC should still work after custom songs are removed

---

## After Uninstall

When you're ready to test again:

1. Build a NEW PKG with only `testlevel`
2. Install the new PKG
3. Launch Beat Saber
4. You should see BOTH original songs AND `testlevel`

The game will show `testlevel` with the SAME content as "Beat Saber" tutorial initially - that's expected for this basic test!

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't find custom PKG | Try Method 3 (Rebuild Database) |
| PKG reinstalls itself | Check GoldHEN isn't auto-installing |
| Game won't launch | Reinstall original game |
| Songs still appear | Delete game cache (Method 4) |

---

## Quick Reference

**GoldHEN Location:** Usually in Settings or as a separate app
**Content ID to look for:** `UP4882-CUSA12878`
**Package Size (previous build):** ~1GB