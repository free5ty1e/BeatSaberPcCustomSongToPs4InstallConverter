# Plan: Song Metadata Replacement Pipeline Integration

## Context

The TMP_Text.set_text hook (v0.8035) successfully intercepts and replaces song names/artists in the Beat Saber PS4 UI. The replacement table is currently **hardcoded in C source** (`SONG_REPLACEMENTS[]` in `main.cpp`). We need to:

1. **Externalize** the replacement table to a JSON config file (like `redirects.json`)
2. **Generate** that JSON from the pipeline during song conversion
3. **Deploy** it to PS4 alongside bundles and redirects
4. **Keep the existing pipeline working** — no breaking changes

## Current State

| Component | Status |
|-----------|--------|
| Plugin hook | ✅ Working — replaces text in pause menu, song details, song artist |
| Replacement table | ⚠️ Hardcoded 13-entry C array in `main.cpp` |
| Pipeline | ✅ Working — converts songs, builds bundles, deploys via FTP |
| External config pattern | ✅ Proven — `redirects.json` and `features.json` already loaded from PS4 |

## Design Decisions

### Decision 1: JSON Format

**Chosen: Option C — Two separate flat tables** (no parser changes needed)

```json
{
  "song_names": {
    "Start Me Up": "Espresso",
    "Angry": "Rhythm Is A Dancer",
    ...
  },
  "song_artists": {
    "The Rolling Stones": "Sabrina Carpenter",
    ...
  }
}
```

**Rationale:**
- The plugin's hand-rolled JSON parser (`parse_json_pairs()`) already handles `{"key": "value"}` objects
- Just call `parse_json_pairs()` twice — once for `"song_names"`, once for `"song_artists"`
- No parser extension needed
- Clean semantic separation: song name vs artist replacement
- Flat lookup is O(n) per call, but n ≤ 64 entries and hook fires ~500×/session — fast enough

### Decision 2: File Location

- **PS4 path:** `/data/GoldHEN/AFR/CUSA12878/song_metadata.json`
- **Local path:** `/workspace/beat_saber_deluxe/song_metadata.json`
- Follows same pattern as `redirects.json` and `features.json`

### Decision 3: Plugin Loading

- Load `song_metadata.json` in `module_start()` via `load_song_metadata()`
- Replace hardcoded `SONG_REPLACEMENTS[]` with two external arrays:
  - `METADATA_NAME_KEYS[]` / `METADATA_NAME_VALS[]` (from `"song_names"`)
  - `METADATA_ARTIST_KEYS[]` / `METADATA_ARTIST_VALS[]` (from `"song_artists"`)
- `find_replacement()` searches both arrays, returns replacement + type (name or artist)
- Gated behind `enable_song_metadata_modification` feature flag (already exists)

### Decision 4: Pipeline Generation

The pipeline will generate `song_metadata.json` as part of its normal flow:
- `--generate-metadata` flag (or automatic when `--deploy` is used)
- Reads from `Info.dat` / BeatSaver API (same sources as bundle metadata)
- Merges with any existing `song_metadata.json` (don't overwrite entries for other songs)
- Deploys alongside `redirects.json` and `features.json`

## Implementation Steps

### Step 1: Plugin — Externalize Replacement Table
**Files:** `beat_saber_deluxe/src/main.cpp`

1. Add `#define METADATA_PATH "/data/GoldHEN/AFR/CUSA12878/song_metadata.json"`
2. Add `load_song_metadata()` function:
   - Read file with same pattern as `load_redirects()` (16KB buffer, `parse_json_pairs()`)
   - Parse `"song_names"` section → `METADATA_NAME_KEYS[]` / `METADATA_NAME_VALS[]`
   - Parse `"song_artists"` section → `METADATA_ARTIST_KEYS[]` / `METADATA_ARTIST_VALS[]`
3. Update `find_replacement()` → `find_metadata_replacement()`:
   - Search `METADATA_NAME_KEYS[]` first (exact match)
   - Then search `METADATA_ARTIST_KEYS[]` (exact match)
   - Return replacement string + type flag (name=0, artist=1)
4. Update `tmp_text_set_text_hook()`:
   - Use `find_metadata_replacement()` instead of `find_replacement()`
   - Log replacement type for diagnostics
5. Call `load_song_metadata()` in `module_start()` after `load_features()`
6. Remove hardcoded `SONG_REPLACEMENTS[]` array
7. Add `free_metadata()` in `module_stop()`
8. Bump version

### Step 2: Pipeline — Generate `song_metadata.json`
**Files:** `beat_saber_deluxe/tools/full_custom_song_pipeline.py`

1. Add `--generate-metadata` flag (default: true when `--deploy` is used)
2. Add `generate_song_metadata(target, song_name, artist, output_path)` function:
   - Read existing `song_metadata.json` if present
   - Add/update entry in `"song_names"` and `"song_artists"` sections
   - Write back to local path
3. Call after Step 9 (redirects.json generation) in the main flow
4. Deploy `song_metadata.json` to PS4 in Step 9 (alongside redirects.json)

### Step 3: Deploy Script — Include Metadata
**Files:** `beat_saber_deluxe/deploy_all.sh`

1. Add Step 4.5: Deploy `song_metadata.json` to PS4
2. Upload `/workspace/beat_saber_deluxe/song_metadata.json` → `/data/GoldHEN/AFR/CUSA12878/song_metadata.json`
3. Log the deployment

### Step 4: Seed Initial `song_metadata.json`
**Files:** `beat_saber_deluxe/song_metadata.json` (new)

Generate from `current-song-replacements-on-chris-ps4.md`:
- 32 songs × 2 entries (name + artist) = 64 entries
- Rolling Stones: 13 songs, all share "The Rolling Stones" → "Sabrina Carpenter" artist
- Billie Eilish: 10 songs, each with different original artist
- Lizzo: 9 songs, each with different original artist

### Step 5: Test Deployment
1. Build plugin with external metadata loading
2. Deploy plugin + `song_metadata.json` + `redirects.json` + `features.json`
3. Test Start Me Up → verify song name + artist replace correctly
4. Test Billie Eilish song → verify those replacements work too
5. Test Lizzo song → verify those replacements work too

## What We're NOT Changing

- `full_custom_song_pipeline.py` main flow (Steps 0-8 stay the same)
- `redirects.json` format or generation
- `features.json` format or generation
- Bundle building or audio conversion
- `deploy_all.sh` Steps 1-3 (plugin, bundles, redirects)
- Any existing tools in `tools/`

## File Impact Summary

| File | Change | Risk |
|------|--------|------|
| `main.cpp` | Add `load_song_metadata()`, replace hardcoded table | Medium — core plugin logic |
| `song_metadata.json` | New config file | Low — additive |
| `full_custom_song_pipeline.py` | Add metadata generation + deployment | Low — append to existing flow |
| `deploy_all.sh` | Add metadata deployment step | Low — additive |
| `CHANGELOG-PLUGIN.md` | Version bump entry | None |
| `CHANGELOG-PIPELINE.md` | Version bump entry | None |
