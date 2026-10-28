"""
testsong.py — the original, rights-clean "BSD Deluxe Theme" test song (M13).

100% mathematical synthesis: sine oscillators + envelopes only — no samples,
no recordings, no MIDI of existing music. The output is unconditionally
ours, which makes it the perfect Beat Sage validation song (uploading it
satisfies the rights assertion) and the perfect web-app demo asset.

The song: a 4-chord loop (Am–F–C–G) at 120 BPM with bass, soft chords, a
pentatonic melody, and a kick/hat groove — musical enough for Beat Sage's
AI to find beats (their mapper needs tempo), short enough (default 48s) to
be polite to their free queue.

Promoted from development/scripts/make_rights_clean_test_song.py (proven in
Exp 283's live Tier-1 verification + the real PS4 deploy of the generated
map). The CLI wrapper remains in development/scripts/ for validation runs;
the web app serves it on demand via GET /api/songs/test-song.
"""

from __future__ import annotations

import wave
from pathlib import Path

SR = 44100
BPM = 120.0
BEAT = 60.0 / BPM


def generate_wav(out: Path | None = None, seconds: float = 48.0) -> bytes:
    """Synthesize the theme song → bytes (and optionally write `out`).
    Deterministic: the same seconds value always yields the same song."""
    import numpy as np  # lazy: numpy is a pipeline requirement, not server-startup

    total_n = max(1, int(seconds * SR))
    mix = np.zeros(total_n)

    A, C, D, E, F, G = 220.0, 261.63, 293.66, 329.63, 174.61, 196.0
    chords = [
        (A, [A, C, E]),          # Am
        (F, [F, A, C]),          # F
        (C, [C, E, G]),          # C
        (G, [G, C, E]),          # G (inverted for voice leading)
    ]
    chord_beats = 4  # one bar per chord
    melody_notes = [E, G, A, C, D, C, A, G]  # Am pentatonic-ish contour

    def add(freq_hz, start_s, dur_s, amp, harmonics):
        n = int(dur_s * SR)
        if n <= 0:
            return
        t = np.arange(n) / SR
        wave_sum = np.zeros(n)
        for mult, weight in harmonics:
            wave_sum += weight * np.sin(2 * np.pi * freq_hz * mult * t)
        env = np.minimum(1.0, t / 0.008) * np.exp(-t / (dur_s * 0.45))
        release = int(0.02 * SR)
        if n > release:
            env[-release:] *= np.linspace(1, 0, release)
        seg = amp * env * wave_sum
        idx0 = int(start_s * SR)
        idx1 = min(idx0 + n, total_n)
        if idx1 > idx0:
            mix[idx0:idx1] += seg[:idx1 - idx0]

    harmonics = ((1, 1.0), (2, 0.35), (3, 0.12))
    beat_i = 0
    while beat_i * BEAT < seconds - 2:
        root, triad = chords[(beat_i // chord_beats) % len(chords)]
        pos = beat_i * BEAT
        in_bar = beat_i % 4
        add(root / 2, pos, BEAT * 0.9, 0.32, harmonics)            # bass
        if in_bar in (0, 2):
            add(55.0, pos, 0.18, 0.5, ((1, 1.0),))                 # kick
        add(6000.0 + 400 * in_bar, pos, 0.03,
            0.06 if in_bar % 2 else 0.04, harmonics)               # hat
        if in_bar == 0:
            for f in triad:
                add(f * 2, pos, BEAT * chord_beats * 0.95, 0.06, harmonics)
        mel = melody_notes[(beat_i * 3) % len(melody_notes)]
        add(mel * 2, pos + BEAT * 0.25, BEAT * 0.6, 0.16, harmonics)
        beat_i += 1

    peak = np.max(np.abs(mix)) or 1.0
    mix = 0.85 * mix / peak
    fade = min(int(1.0 * SR), total_n // 4)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)
    pcm = (mix * 32767).astype(np.int16).tobytes()

    import io
    buf = io.BytesIO()
    with wave.open(buf, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    data = buf.getvalue()
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    return data


# ═════════════════════════════════════════════════════════════════════════════
# M15: the CHIPTUNE test songs — authentic NES-style synthesis (Exp 287).
#
# The NES's five channels distilled to the three that matter for Beat Sage
# test material (the DPCM sample channel is unused):
#   · PULSE (×2): square waves at 12.5/25/50/75% duty — melody + harmony
#   · TRIANGLE (×1): the 16-step, 4-bit triangle — bass (always full volume,
#     exactly like the hardware)
#   · NOISE (×1): the 15-bit LFSR with 16 preset periods — the drum kit
#     (kick = the longest periods' low rumble, snare = mid, hats = the
#     shortest periods' bright hiss), with stepped volume envelopes
#     (the hardware's 16 linear levels)
#
# Why chiptunes for testing: perfectly on-grid rhythms (the exact input the
# descent engine wants), strong on-beat emphasis, and — unlike the synth
# theme — they exercise the grid-inference path the way real music does.
# ═════════════════════════════════════════════════════════════════════════════

NES_VOLUME_MAX = 15          # the hardware's 4-bit volume


def _nes_pulse(t, freq, duty=0.25):
    """A pulse channel waveform: square at the given duty cycle."""
    import numpy as np
    if freq <= 0:
        return np.zeros_like(t)
    return (np.mod(t * freq, 1.0) < duty).astype(np.float64) * 2.0 - 1.0


def _nes_triangle(t, freq):
    """The NES triangle: a 16-step (4-bit) quantized triangle — the
    characteristic chunky bass voice."""
    import numpy as np
    if freq <= 0:
        return np.zeros_like(t)
    phase = np.mod(t * freq, 1.0)
    tri = 1.0 - 2.0 * np.abs(2.0 * phase - 1.0)   # −1..1
    return np.round(tri * 7.0) / 7.0             # the 4-bit quantization


def _lfsr_noise(n_samples, toggle_freq, seed=0x0001):
    """The NES noise channel: a 15-bit LFSR bitstream held at the toggle
    rate (the hardware clocks the shift register every P cycles; P selects
    the drum voice: long P = low rumble, short P = bright hiss)."""
    import numpy as np
    out = np.zeros(n_samples)
    lfsr = seed
    hold = max(1, int(round(SR / max(toggle_freq, 1.0))))
    bit = 1
    for i in range(n_samples):
        if i % hold == 0:
            b0 = lfsr & 1
            b1 = (lfsr >> 1) & 1
            lfsr = (lfsr >> 1) | (((b0 ^ b1) & 1) << 14)
            bit = (~lfsr) & 1
        out[i] = 1.0 if bit else -1.0
    return out


def _nes_env(n_samples, peak=15, decay_steps=10):
    """A stepped volume envelope (the 16 hardware levels): instant attack,
    linear decay in discrete steps — the chiptune signature."""
    import numpy as np
    steps = np.linspace(peak, 0, max(decay_steps, 1))
    idx = np.clip((np.arange(n_samples) * len(steps) / max(n_samples, 1))
                  .astype(int), 0, len(steps) - 1)
    return steps[idx] / NES_VOLUME_MAX


def _place(buf, start_s, length_s, wave, gain=1.0, env=None):
    """Mix one voice segment into the buffer at start_s."""
    n = min(int(length_s * SR), len(wave))
    if n <= 0:
        return
    i0 = int(start_s * SR)
    i1 = min(i0 + n, len(buf))
    if i1 <= i0:
        return
    seg = wave[:i1 - i0] * gain
    if env is not None:
        seg = seg * env[:i1 - i0]
    buf[i0:i1] += seg


# ── Song 1: "BSD NES Groove" — the basic drum-beat rhythm song ───────────────

def generate_nes_groove(seconds: float = 64.0) -> bytes:
    """120 BPM, Am–F–C–G: kick/snare/hat groove (the noise channel),
    triangle bass on eighths, and a duty-cycled pulse riff — the 'basic
    rhythm with drum beats' test song. Deterministic."""
    import numpy as np
    bpm = 120.0
    beat = 60.0 / bpm
    total_n = int(seconds * SR)
    mix = np.zeros(total_n)

    def n(s):
        return int(s * SR)

    A, C, D, E, F, G = 110.0, 130.81, 146.83, 164.81, 87.31, 98.0
    roots = [A, F, C / 2, G / 2]              # Am, F, C, G (bass voicing)
    riff = [A, C, D, E, G, E, D, C]          # Am pentatonic contour

    t_beat = 0
    beat_i = 0
    while (t_beat * beat) < seconds - 0.5:
        t = t_beat * beat
        bar = (beat_i // 4) % 4
        in_bar = beat_i % 4

        # drums: kick 1&3, snare 2&4, hats on every eighth
        if in_bar in (0, 2):
            kick = _lfsr_noise(n(0.10), 1789773 / 4068.0)
            _place(mix, t, 0.10, kick, 0.9, _nes_env(n(0.10), 15, 12))
        if in_bar in (1, 3):
            snare = _lfsr_noise(n(0.16), 1789773 / 508.0)
            _place(mix, t, 0.16, snare, 0.55, _nes_env(n(0.16), 13, 14))
        hat = _lfsr_noise(n(0.03), 1789773 / 32.0)
        _place(mix, t, 0.03, hat, 0.28, _nes_env(n(0.03), 9, 5))
        offbeat = _lfsr_noise(n(0.02), 1789773 / 40.0)
        _place(mix, t + beat / 2, 0.02, offbeat, 0.18, _nes_env(n(0.02), 7, 4))

        # bass: triangle, root eighths (two pulses per beat)
        tt = np.arange(n(beat)) / SR
        _place(mix, t, beat / 2, _nes_triangle(tt, roots[bar] / 2), 0.5)
        _place(mix, t + beat / 2, beat / 2,
               _nes_triangle(tt, roots[bar] / 2), 0.5 if in_bar % 2 else 0.35)

        # melody: a 25%-duty pulse riff — one note per beat from the contour,
        # with a grace 16th into beat 1 of each bar
        duty = 0.25 if bar % 2 == 0 else 0.125
        freq = riff[beat_i % len(riff)] * 2
        _place(mix, t, beat * 0.9, _nes_pulse(tt, freq, duty), 0.30,
               _nes_env(n(beat), 15, 22))
        if in_bar == 0:
            grace = _lfsr_noise(n(0.02), 1789773 / 64.0)
            _place(mix, t - beat / 4 if t > beat / 4 else t, 0.02, grace,
                   0.15, _nes_env(n(0.02), 6, 3))

        t_beat += 1
        beat_i += 1

    return _finish_pcm(mix, seconds)


# ── Song 2: "BSD NES Scale Runner" — the scales-as-melody song ──────────────

def generate_nes_scale_runner(seconds: float = 60.0) -> bytes:
    """140 BPM, C major: running scales (16th-note runs up and down +
    thirds), a steady kick/hat pulse, and triangle bass — the
    scales-as-basic-melody test song. The cleanest descent-engine input:
    strong on-beat emphasis where every run starts. Deterministic."""
    import numpy as np
    bpm = 140.0
    beat = 60.0 / bpm
    total_n = int(seconds * SR)
    mix = np.zeros(total_n)

    def n(s):
        return int(s * SR)

    # C major scale (C4..C6)
    scale = [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25,
             587.33, 659.26, 698.46, 783.99, 880.0, 987.77, 1046.5]
    roots = [65.41, 87.31, 98.0, 110.0]       # C2, F2, G2, A2 bass roots

    t_beat = 0
    beat_i = 0
    run_pos = 0
    direction = 1
    while (t_beat * beat) < seconds - 0.5:
        t = t_beat * beat
        bar = (beat_i // 4) % 4
        in_bar = beat_i % 4

        # drums: kick on the beat, hat on the eighth
        kick = _lfsr_noise(n(0.09), 1789773 / 2034.0)
        _place(mix, t, 0.09, kick, 0.8, _nes_env(n(0.09), 15, 12))
        hat = _lfsr_noise(n(0.03), 1789773 / 32.0)
        _place(mix, t + beat / 2, 0.03, hat, 0.22, _nes_env(n(0.03), 8, 4))

        # bass: triangle, the bar's root on beats 1 & 3, fifth on 2 & 4
        tt = np.arange(n(beat)) / SR
        root = roots[bar] if in_bar in (0, 1) else roots[bar] * 1.5
        _place(mix, t, beat * 0.95, _nes_triangle(tt, root), 0.5)

        # melody: a 16th-note scale run — four notes per beat, changing
        # direction at the scale's edges (up 4, down 4 pattern feels
        # musical; every beat boundary restarts emphasis)
        for sixteenth in range(4):
            if run_pos >= len(scale):
                direction = -1
            elif run_pos <= 0:
                direction = 1
            freq = scale[run_pos]
            t0 = t + sixteenth * beat / 4
            _place(mix, t0, beat / 4 * 0.95,
                   _nes_pulse(tt, freq, 0.5), 0.26,
                   _nes_env(n(beat / 4), 15, 10))
            run_pos += direction
            if direction == 1 and run_pos >= len(scale):
                run_pos = len(scale) - 1
                direction = -1
            elif direction == -1 and run_pos < 0:
                run_pos = 0
                direction = 1

        t_beat += 1
        beat_i += 1

    return _finish_pcm(mix, seconds)


def _finish_pcm(mix, seconds: float) -> bytes:
    """Shared finishing: normalize to a safe peak (the NES mix is quiet by
    nature — bring it up), fades, WAV encode."""
    import io

    import numpy as np
    peak = np.max(np.abs(mix)) or 1.0
    mix = 0.85 * mix / peak
    total_n = len(mix)
    fade = min(int(0.05 * SR), total_n // 4)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)
    # one soft clip for the chiptune square edges
    mix = np.tanh(mix * 1.1)
    pcm = (mix * 32767).astype(np.int16).tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    return buf.getvalue()


# The registry the endpoint + CLI dispatch on
def _generate_theme(seconds: float = 48.0):
    return generate_wav(seconds=seconds)


TEST_SONGS = {
    "theme": {
        "label": "BSD Deluxe Theme (the original synth)",
        "seconds": 48,
        "generate": _generate_theme,
    },
    "nes_groove": {
        "label": "NES Groove — drums + bass + duty-cycled riff (120 BPM)",
        "seconds": 64,
        "generate": generate_nes_groove,
    },
    "nes_scale_runner": {
        "label": "NES Scale Runner — running major scales (140 BPM)",
        "seconds": 60,
        "generate": generate_nes_scale_runner,
    },
}
