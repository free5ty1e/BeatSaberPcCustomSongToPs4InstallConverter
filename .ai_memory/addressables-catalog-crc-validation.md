---
name: addressables-catalog-crc-validation
description: "ROOT CAUSE: The Addressables catalog stores per-bundle CRC32 + file size checksums. Modified bundles fail CRC validation, causing CE-34878-0 crash."
metadata: 
  node_type: memory
  type: reference
  originSessionId: bc573f12-ef2e-43e2-9a5a-f79fefc465a0
---

# Addressables Catalog CRC Validation (Root Cause of Pack Bundle Crashes)

## Summary
The game's Addressables catalog (`aa/catalog.json`) stores per-bundle **CRC32**, **MD5 hash**, and **file size** for every asset bundle. When any bundle is loaded, the game validates its CRC against the stored value. This is the root cause of ALL pack bundle modification crashes: any change to the bundle file changes the CRC, causing the game to reject it.

## Evidence
- `m_UseCrcForCachedBundles: true` — explicit CRC check enabled
- `m_Crc: 3700109647` (0xdc8b314f) — stored CRC for rolling stones pack
- `m_BundleSize: 7902803` — stored file size
- `m_Hash: "a99482a8..."` — MD5 content hash (also used as filename component)
- Original bundle (CRC matches): ✅ works via redirect
- Any modified bundle (CRC differs): ❌ CE-34878-0 crash

## Catalog Storage Format
The catalog's `m_ExtraDataString` field contains **UTF-16 LE encoded JSON blocks**, one per bundle:
```json
{"m_Hash":"<MD5-hex>","m_Crc":<uint32>,"m_BundleSize":<file_size>,
 "m_BundleName":"<internal-name>","m_UseCrcForCachedBundles":true,
 "m_UseUWRForLocalBundles":false,"m_AssetLoadMode":0,...}
```

The rolling stones pack entry was found at UTF-16 offset 51087 in the ExtraDataString.

## Why We Can't Fix It (Currently)
The catalog is a **plain JSON file** (`aa/catalog.json`, 793KB). Unity's Addressables system loads it via `ContentCatalogProvider`, NOT via `AssetBundle.LoadFromFile`. The AFR plugin only hooks `AssetBundle::LoadFromFile`, so it **cannot redirect the catalog**.

Without the ability to patch or redirect the catalog:
- **No pack bundle modification is possible** — any change to a bundle file changes its CRC
- The catalog cannot be patched on PS4 (filesystem is read-only)
- GoldHEN AFR cannot intercept JSON file loads

## Options to Overcome This
1. **Match original CRC via collision** — CRC32 is linear; could adjust padding bytes to match original CRC with enough computation
2. **Bypass pack bundle entirely** — modify per-song bundles instead (approach being tested in Exp 138)
3. **Catalog redirect via system-level hook** — requires hooking `sceKernelOpen` or `fopen`, not just `LoadFromFile`

## Related
- [[experiment-log]] — See Experiments 134-136
- [[pack-bundle-patching]] — Pack bundle patching approaches (all currently blocked)
- [[unitypy-serialization-limitations]] — Why UnityPy-based approaches also fail
