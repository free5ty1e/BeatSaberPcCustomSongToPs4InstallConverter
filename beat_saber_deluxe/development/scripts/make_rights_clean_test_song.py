#!/usr/bin/env python3
"""
make_rights_clean_test_song.py — CLI wrapper: synthesize a rights-clean test
song on demand (M13's theme + M15's NES-authentic chiptunes).

Everything is generated math (sine oscillators for the theme; the NES's
pulse/triangle/LFSR-noise channels for the chiptunes — see
webapp/adapters/testsong.py, the production home of the synth core): the
output is unconditionally ours — no samples, no recordings, no MIDI of
existing music — so uploading it to beatsage.com satisfies the rights
assertion in the web app.

Usage:
    python3 development/scripts/make_rights_clean_test_song.py out.wav [type] [seconds]
    type: theme (default) | nes_groove | nes_scale_runner
"""

from __future__ import annotations

import sys
from pathlib import Path

WEBAPP = Path(__file__).resolve().parents[2] / "webapp"
sys.path.insert(0, str(WEBAPP))

from adapters import testsong  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    out = Path(args[0] if args else "bsd_test_song.wav")
    song_type = args[1] if len(args) > 1 else "theme"
    song = testsong.TEST_SONGS.get(song_type)
    if song is None:
        print(f"❌ Unknown type {song_type!r}. To fix: choose one of: " +
              ", ".join(testsong.TEST_SONGS))
        return 2
    seconds = float(args[2]) if len(args) > 2 else song["seconds"]
    data = song["generate"](seconds)
    out.write_bytes(data)
    print(f"\u2705 {out} \u2014 {seconds:.0f}s, {testsong.SR}Hz mono, type={song_type} "
          f"({song['label']}), original synthesis (rights-clean; deterministic)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
