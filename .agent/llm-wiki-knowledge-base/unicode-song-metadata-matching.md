---
name: unicode-song-metadata-matching
description: "Why non-ASCII song titles ('…Baby One More Time') missed their metadata replacement — 3-part chain: JSON \\uXXXX escaping, byte-verbatim plugin parsing, and UTF-16 '?' folding. Fixed pipeline v0.5346 / plugin v0.8047."
metadata:
  type: root-cause
---

# Unicode Song Metadata Matching (Exp 228)

The plugin's song-list title replacement compares the game's live UTF-16
song title against `song_metadata.json` keys. Any non-ASCII character in a
slot title — an ellipsis (`…`), an accented letter, an em-dash — breaks the
match through THREE independent bugs that all had to be fixed together.

## The chain (as hit by '…Baby One More Time')

```
song_metadata.json (PS4)      plugin parse            game System.String
"…Baby One More Time"   →   key = …Baby...   vs  U+2026 '…' → extract
     (ensure_ascii=True          (byte-verbatim,          folds non-ASCII
      6 ASCII bytes              no unescape)              code units to '?')
                                                        → "?Baby One More Time"
```

`…Baby One More Time` ≠ `?Baby One More Time` — the lookup can never
succeed. Each fix alone is insufficient:

1. **Unescape alone fails:** after `\uXXXX` → UTF-8 the key is
   `…Baby One More Time` (raw ellipsis) — but the extraction still folds to
   `?Baby...`. Raw UTF-8 key vs folded game string: still no match.
2. **Fixing extraction alone fails:** extracting real UTF-16 → UTF-8 would
   need a UTF-8-aware compare AND a UTF-8→UTF-16-aware replacement-string
   creator (bigger change, and the ASCII-fold is intentional — the PS4
   cannot render the ellipsis in the compared buffer anyway).
3. **The correct minimal design: fold BOTH sides through the SAME
   projection.** `extract_utf16_string` folds every non-ASCII UTF-16 code
   unit to `'?'` (1 BMP char = 1 `?`; 1 astral char = 2 UTF-16 units = 2
   `?`). So the plugin folds loaded KEYS through the mirror function
   `fold_utf8_to_ascii` (1 UTF-8 BMP sequence = 1 `?`, 4-byte astral
   sequence = 2 `?`) at `load_song_metadata` time. Byte-exact match for ANY
   Unicode title. VALUES are never folded — they are the display strings.

## The fixes (pipeline v0.5346 / plugin v0.8047)

| Layer | Fix | Why |
|---|---|---|
| Pipeline writer | `json.dump(..., ensure_ascii=False)` + UTF-8 file, at ALL 3 song_metadata dump sites | raw `…` in the file — human-readable; no escapes to begin with |
| Plugin parser | `json_unescape_inplace()` after `parse_json_pairs` | backward compat: files already deployed with `\uXXXX` still match |
| Plugin compare | `fold_utf8_to_ascii(keys[i])` in both song_names/song_artists loaders | mirrors `extract_utf16_string`'s fold exactly (BMP 1×`?`, astral 2×`?`) |
| Plugin fallback string creator | `create_il2cpp_string` now decodes UTF-8→UTF-16LE | was byte-per-codeunit mojibake (`…` → two code units); `il2cpp_string_new` (primary) already handled UTF-8 |

## Why the log proved it cleanly

`v0.5345_multipack_bomt_metadata_title_miss.txt`: every OTHER Britney slot
replaced — including `Oops!...I Did It Again` (ASCII dots — no Unicode) —
but the BOMT cell fired ONLY the author replacement
(`MoveNext #47: author 'Britney Spears' -> ' '`), never the songName. A slot
whose stock title is pure ASCII working while one Unicode-prefixed title
fails isolates the bug to the title-matching path, not the hook, feature
gate, or file loading.

## Durable rules

- **A byte-level JSON parser must unescape what the writer may escape** — or
  the writer must guarantee no escapes (`ensure_ascii=False`). Both were
  done (defense in depth).
- **Fuzzy/lossy extraction defines the comparison alphabet.** When one side
  of a compare passes through a lossy projection (`?`-folding), the other
  side must be projected through the SAME function, not "fixed" to be
  lossless — mirror the projection.
- **Astral chars (emoji, > U+FFFF) count TWO in UTF-16.** The fold emits two
  `?` per astral char to stay byte-exact with extraction. Any future
  "smarter" fold that emits one would silently re-break emoji-titled maps.
- Python `json.dump` defaults `ensure_ascii=True` — any config consumed by a
  non-stdlib parser must pass `ensure_ascii=False` explicitly.

See also: [[beatmap-format-v3]] (BeatSaver v4 columnar + Info.dat metadata
keys found in the same experiment), [[ps4-file-system-redirects]],
[[feature-flags]] (enable_song_metadata_modification gates this path)
