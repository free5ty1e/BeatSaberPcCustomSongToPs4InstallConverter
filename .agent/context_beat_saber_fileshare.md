\\192.168.100.135\incoming\temp\

### File Locations

**SMB Share Locations:**

```
SMB share host is 192.168.100.135 and share name is `incoming`
All Beat Saber PS4 files are located here for reference:
smb://192.168.100.135/incoming/temp/BeatSaberPs4  (Game/Update packages)
smb://192.168.100.135/incoming/temp/BeatSaberPs4/Beat.Saber_CUSA18278_DCLPACK.v14_[246]_OPOISSO893  (Official DLC packages - more songs)
smb://192.168.100.135/incoming/temp/BeatSaberPs4/decrypted_ps4_dump (dump of game from ps4 dumper while it was running in memory)
smb://192.168.100.135/incoming/temp/rb4dx (Rock Band 4 Deluxe installer, example hook for custom songs in another game Rock Band 4)

```

For reference, the CUSA ID CUSA12878 is confirmed correct for US PS4. Some of the filenames may have typos in this ID, but they are all for CUSA12878.

**PS4 FTP Access (READ-ONLY):**

```
ftp://192.168.100.117:2121
Login: anonymous
```

- Port: 2121
- Use only for READ operations - do NOT write to PS4
- Is usually powered off, if needed I can power it up and start its FTP server but I do not want to leave it on for long.
