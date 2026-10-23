#!/usr/bin/env python3
"""
make_rights_clean_test_song.py — synthesize a small original song for
Beat Sage live tests (M13).

Everything here is generated math (sine oscillators + envelopes): the
output is unconditionally ours — no samples, no recordings, no MIDI of
existing music — so uploading it to beatsage.com satisfies the rights
assertion in the web app ("I have the rights to process this audio").

The song: a 4-chord loop (Am–F–C–G) at 120 BPM with bass, soft chords, a
pentatonic melody on top, and a simple kick/hat groove — musical enough
for Beat Sage's AI to find beats (their mapper needs tempo), short enough
(48s) to be polite to their free queue.

Usage:
    python3 development/scripts/make_rights_clean_test_song.py out.wav [seconds]
"""

from __future__ import annotations

import math
import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 120.0
BEAT = 60.0 / BPM


def note(freq_hz: float, start_s: float, dur_s: float, amp: float,
         harmonics: tuple[tuple[int, float], ...] = ((1, 1.0), (2, 0.35), (3, 0.12))) -> tuple[np.ndarray, np.ndarray]:
    """One synthesized note → (channel segment, envelope)."""
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    wave_sum = np.zeros(n)
    for mult, weight in harmonics:
        wave_sum += weight * np.sin(2 * np.pi * freq_hz * mult * t)
    # percussive envelope: quick attack, exponential decay, soft release
    env = np.minimum(1.0, t / 0.008) * np.exp(-t / (dur_s * 0.45))
    release = int(0.02 * SR)
    if n > release:
        env[-release:] *= np.linspace(1, 0, release)
    seg = amp * env * wave_sum
    idx = np.arange(int(start_s * SR), int(start_s * SR) + n)
    return seg, idx[:len(seg)]


def add(buf: np.ndarray, seg: np.ndarray, idx: np.ndarray) -> None:
    buf[idx] += seg


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "bsd_original_test_song.wav")
    total_s = float(sys.argv[2]) if len(sys.argv) > 2 else 48.0
    total_n = int(total_s * SR)
    mix = np.zeros(total_n)

    A, C, D, E, F, G = 220.0, 261.63, 293.66, 329.63, 174.61, 196.0
    # Am F C G loop — roots for the bass, triads for the chords
    chords = [
        (A, [A, C, E]),          # Am
        (F / 2 * 2, [F, A, C]),  # F
        (C, [C, E, G]),          # C
        (G / 2 * 2, [G, C, E]),  # G (inverted for voice leading)
    ]
    chord_beats = 4  # one bar (4 beats) per chord
    loop_beats = chord_beats * len(chords)
    melody_notes = [E, G, A, C, D, C, A, G]  # Am pentatonic-ish contour

    beat_i = 0
    while beat_i * BEAT < total_s - 2:
        bar_chord = chords[(beat_i // chord_beats) % len(chords)]
        root, triad = bar_chord
        pos = beat_i * BEAT
        in_bar = beat_i % 4

        # Bass: root on every beat, fifth-of-the-beat accent
        add(mix, *note(root / 2, pos, BEAT * 0.9, 0.32))
        # Kick: on 1 and 3
        if in_bar in (0, 2):
            add(mix, *note(55.0, pos, 0.18, 0.5, harmonics=((1, 1.0),)))
        # Hat: every beat, lighter on offbeats
        add(mix, *note(6000.0 + 400 * in_bar, pos, 0.03, 0.06 if in_bar % 2 else 0.04))
        # Chords: sustained pad each bar start
        if in_bar == 0:
            for f in triad:
                add(mix, *note(f * 2, pos, BEAT * chord_beats * 0.95, 0.06))
        # Melody: one note per beat from the contour
        mel = melody_notes[(beat_i * 3) % len(melody_notes)]
        add(mix, *note(mel * 2, pos + BEAT * 0.25, BEAT * 0.6, 0.16))
        beat_i += 1

    # Normalize to a safe peak + gentle fades
    peak = np.max(np.abs(mix)) or 1.0
    mix = 0.85 * mix / peak
    fade = int(1.0 * SR)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)
    pcm = (mix * 32767).astype(np.int16)

    with wave.open(str(out), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    dur = total_n / SR
    print(f"✅ {out} — {dur:.0f}s, {SR}Hz mono, original synthesis (rights-clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
