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


def _finish_pcm(mix, seconds: float) -> bytes:
    """Shared finishing: normalize to a safe peak, fades, soft clip for the
    chiptune square edges, WAV encode."""
    import io

    import numpy as np
    peak = np.max(np.abs(mix)) or 1.0
    mix = 0.85 * mix / peak
    total_n = len(mix)
    fade = min(int(0.05 * SR), total_n // 4)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.1)
    pcm = (mix * 32767).astype(np.int16).tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    return buf.getvalue()


def _nes_render(events: list, seconds: float) -> bytes:
    """Render the NES mix from a SCORE (the event list built by the score
    functions — the single source of truth for both the audio AND the
    oracle). Each event: {t (seconds), dur (seconds), ch ('pulse'|'tri'|'noise'),
    freq, duty?, gain, env (peak, steps), emphasis (bool — on a musical
    strong beat)."""
    import numpy as np
    total_n = int(seconds * SR)
    mix = np.zeros(total_n)
    n = lambda s: max(1, int(s * SR))
    for ev in events:
        t0 = ev["t"]
        dur = ev["dur"]
        if t0 < 0 or t0 + dur >= seconds:
            continue
        ch = ev["ch"]
        seg_n = n(dur)
        tt = np.arange(seg_n) / SR
        if ch == "pulse":
            wave = _nes_pulse(tt, ev["freq"], ev.get("duty", 0.25))
        elif ch == "tri":
            wave = _nes_triangle(tt, ev["freq"])
        else:
            wave = _lfsr_noise(seg_n, ev["freq"])
        peak, steps = ev.get("env", (15, 10))
        _place(mix, t0, dur, wave, ev.get("gain", 1.0), _nes_env(seg_n, peak, steps))
    return _finish_pcm(mix, seconds)


# ── Song 1: "BSD NES Groove" — the basic drum-beat rhythm song ───────────────

def nes_groove_score(seconds: float = 64.0) -> list:
    """The GROUND-TRUTH score for 'BSD NES Groove' (120 BPM, Am–F–C–G):
    every drum hit, bass note, and melody note with its exact time, voice,
    and emphasis flag. The audio renders FROM this (single source of truth);
    the oracle measures generated charts AGAINST it."""
    bpm = 120.0
    beat = 60.0 / bpm
    events = []
    A, C, D, E, F, G = 110.0, 130.81, 146.83, 164.81, 87.31, 98.0
    roots = [A, F, C / 2, G / 2]
    riff = [A, C, D, E, G, E, D, C]
    t_beat = 0
    beat_i = 0
    while (t_beat * beat) < seconds - 0.5:
        t = t_beat * beat
        bar = (beat_i // 4) % 4
        in_bar = beat_i % 4
        emph = in_bar == 0
        if in_bar in (0, 2):
            events.append({"t": t, "dur": 0.10, "ch": "noise",
                           "freq": 1789773 / 4068.0, "gain": 0.9,
                           "env": (15, 12), "kind": "kick", "emphasis": emph})
        if in_bar in (1, 3):
            events.append({"t": t, "dur": 0.16, "ch": "noise",
                           "freq": 1789773 / 508.0, "gain": 0.55,
                           "env": (13, 14), "kind": "snare", "emphasis": emph})
        events.append({"t": t, "dur": 0.03, "ch": "noise",
                       "freq": 1789773 / 32.0, "gain": 0.28,
                       "env": (9, 5), "kind": "hat", "emphasis": emph})
        events.append({"t": t + beat / 2, "dur": 0.02, "ch": "noise",
                       "freq": 1789773 / 40.0, "gain": 0.18,
                       "env": (7, 4), "kind": "hat", "emphasis": False})
        events.append({"t": t, "dur": beat / 2, "ch": "tri",
                       "freq": roots[bar] / 2, "gain": 0.5,
                       "env": (15, 16), "kind": "bass", "emphasis": emph})
        events.append({"t": t + beat / 2, "dur": beat / 2, "ch": "tri",
                       "freq": roots[bar] / 2, "gain": 0.5 if in_bar % 2 else 0.35,
                       "env": (15, 16), "kind": "bass", "emphasis": False})
        duty = 0.25 if bar % 2 == 0 else 0.125
        events.append({"t": t, "dur": beat * 0.9, "ch": "pulse",
                       "freq": riff[beat_i % len(riff)] * 2, "duty": duty,
                       "gain": 0.30, "env": (15, 22), "kind": "melody",
                       "emphasis": emph})
        t_beat += 1
        beat_i += 1
    return events


def generate_nes_groove(seconds: float = 64.0) -> bytes:
    """120 BPM, Am–F–C–G (see nes_groove_score — the score IS the song)."""
    return _nes_render(nes_groove_score(seconds), seconds)


def nes_scale_runner_score(seconds: float = 60.0) -> list:
    """The GROUND-TRUTH score for 'BSD NES Scale Runner' (140 BPM, C major):
    every kick, hat, bass root, and 16th-note scale note — the oracle's truth."""
    bpm = 140.0
    beat = 60.0 / bpm
    events = []
    scale = [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25,
             587.33, 659.26, 698.46, 783.99, 880.0, 987.77, 1046.5]
    roots = [65.41, 87.31, 98.0, 110.0]
    t_beat = 0
    beat_i = 0
    run_pos = 0
    direction = 1
    while (t_beat * beat) < seconds - 0.5:
        t = t_beat * beat
        bar = (beat_i // 4) % 4
        in_bar = beat_i % 4
        emph = in_bar == 0
        events.append({"t": t, "dur": 0.09, "ch": "noise",
                       "freq": 1789773 / 2034.0, "gain": 0.8,
                       "env": (15, 12), "kind": "kick", "emphasis": emph})
        events.append({"t": t + beat / 2, "dur": 0.03, "ch": "noise",
                       "freq": 1789773 / 32.0, "gain": 0.22,
                       "env": (8, 4), "kind": "hat", "emphasis": False})
        root = roots[bar] if in_bar in (0, 1) else roots[bar] * 1.5
        events.append({"t": t, "dur": beat * 0.95, "ch": "tri",
                       "freq": root, "gain": 0.5, "env": (15, 16),
                       "kind": "bass", "emphasis": emph})
        for sixteenth in range(4):
            if run_pos >= len(scale):
                direction = -1
            elif run_pos <= 0:
                direction = 1
            freq = scale[run_pos]
            events.append({"t": t + sixteenth * beat / 4,
                           "dur": beat / 4 * 0.95, "ch": "pulse",
                           "freq": freq, "duty": 0.5, "gain": 0.26,
                           "env": (15, 10), "kind": "melody",
                           "emphasis": sixteenth == 0})
            run_pos += direction
            if direction == 1 and run_pos >= len(scale):
                run_pos = len(scale) - 1
                direction = -1
            elif direction == -1 and run_pos < 0:
                run_pos = 0
                direction = 1
        t_beat += 1
        beat_i += 1
    return events


def generate_nes_scale_runner(seconds: float = 60.0) -> bytes:
    """140 BPM, C major (see nes_scale_runner_score — the score IS the song)."""
    return _nes_render(nes_scale_runner_score(seconds), seconds)


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
