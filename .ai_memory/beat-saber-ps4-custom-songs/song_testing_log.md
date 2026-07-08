# Song Testing Log

Records which custom songs have been tested on PS4, their sync status, and any issues.

## Status Legend
- ✅ **Perfect** — Sync is correct, full song plays without issues, score saves
- ⚠️ **Minor Issues** — Sync slightly off, but playable
- ❌ **Broken** — Major desync, crashes, or doesn't load

## Next Test Candidate

| Song | Artist | BPM | Duration | Beatmap Format | Modes | Notes |
|------|--------|-----|----------|---------------|-------|-------|
| TBD | TBD | TBD | TBD | TBD | Rollin' Stones replacements | All 12 Rolling Stones songs to be replaced with custom songs. Need a song with dot/bloopy notes (no arrows) to test. |

## Test Results

| Date | Song | Artist | BPM | Duration | Audio Format | Sync | Score Saves | Notes |
|------|------|--------|-----|----------|-------------|------|-------------|-------|
| 2026-07-08 | Espresso | Sabrina Carpenter | 104 | 177.5s | PCM16 FSB5 | ✅ Perfect | ✅ | **bpmData sync fixed!** All note types visible: arrows, chains, arcs, walls. No bombs in this map but confirmed working in prior tests. Standard E/N/H/Ex/Ex+. |
| 2026-06-28 | Drop Pop Candy | Reol | 130 | 224s | PCM16 FSB5 | ✅ | ✅ | v0.50 alpha — first working custom song. 8 beatmaps including 360-degree. |
| 2026-06-28 | Bruises | Fox Stevenson | 174 | 224.8s | PCM16 FSB5 | ❌ | N/A | Desynced — beatmap appears poorly authored. 645 beats at 174 BPM = 222.7s, audio = 224.8s. Not a lapping issue. |
| 2026-06-28 | Bruises (lapped) | Fox Stevenson | 174 | 678.6s | PCM16 FSB5 | ❌ | N/A | Lapped version — wrongfully extended audio due to bug: `_time` in beats was compared to `audio_duration` in seconds. Fixed in lapped_audio.py. |

## Pipeline Notes
- Use `--pcm16` flag for lossless audio (PCM16 FSB5, codec=2)
- V2 beatmaps use `_time` in BEATS — pipeline converts to seconds using BPM from `info.dat`
- Lapped detection: triggers when `max_note_time_in_seconds > audio_duration * 1.3`
- BEATS→seconds conversion: `time_seconds = time_beats * (60.0 / bpm)`
