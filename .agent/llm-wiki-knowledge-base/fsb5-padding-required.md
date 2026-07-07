---
name: fsb5-padding-required
description: "⚠️ HISTORICAL — Padding is NOT required with PCM16. This page documents a resolved HEVAG-era issue."
metadata:
  type: reference
  status: historical
---

# ⚠️ HISTORICAL: FSB5 12MB Padding Fix

## This page is OBSOLETE

The 12MB padding "requirement" was a symptom of the HEVAG codec experiments, NOT a real constraint. With **PCM16 (codec=2)** audio, the FSB5 file can be **any size** — no padding needed.

## Working Approach

Use `--no-pad` in the pipeline for full-length songs:

```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./song --target startmeup \
  --pcm16 --no-pad --deploy
```

See [[ps4-fsb5-pcm16-format]] for the working audio format.

## What This Page Used To Say (for historical reference)

The original claim was that FSB5 files must be padded to 12,305,632 bytes (the original Start Me Up `.resource` size) to avoid an audio decoder freeze. This was observed during HEVAG experiments where:

- A 152KB silence FSB5 with padding → notes moved ~1s then froze (Experiment 80)
- Padding alone was NOT sufficient — HEVAG content also needed 5+ predictors

**The actual root cause was HEVAG encoding quality, not file size.** Once we switched to PCM16, the PS4 FMOD decoder accepted files of any size without padding.
