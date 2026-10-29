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

    def n(s):
        return max(1, int(s * SR))

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




# ── Song 3: "NES BeatTour 2026" — a tour of drum patterns ───────────────────

def nes_beattour_score(seconds: float = 96.0) -> list:
    """'NES BeatTour 2026' (128 BPM): a TOUR of drum patterns — each beat
    style plays for 4 measures (16 beats) before the next: 4/4 rock,
    halftime, double-time, funk (syncopated snare), bossa-ish, breakbeat,
    the big 80s fill, and a drum solo ending. Bass + a sparse pulse riff
    hold the harmony under the tour. The drum patterns are the ground
    truth — the oracle measures whether charts follow the BEAT CHANGES."""
    bpm = 128.0
    beat = 60.0 / bpm
    events = []
    A1 = 110.0

    # the tour: (name, kicks[beats-in-bar], snares[beats-in-bar], hats, hats_density)
    tour = [
        ("rock",       [0, 2],          [1, 3],           2,  "8ths"),
        ("halftime",   [0],             [2],              2,  "quarters"),
        ("doubletime", [0, 1, 2, 3],    [1, 3],           4,  "16ths"),
        ("funk",       [0, 2.5],        [0.75, 1.5, 3],   2,  "8ths"),
        ("bossa",      [0, 1.5, 3],     [1.75, 3.75],     2,  "8ths"),
        ("breakbeat",  [0, 2.25, 3.5],  [1, 2, 3.75],     2,  "16ths"),
        ("eighties",   [0, 2],          [1, 3],           4,  "8ths-open"),
        ("solo",       [0, 1, 2, 3],    [0.5, 1.5, 2.5, 3.5], 4, "16ths"),
    ]
    beats_per_style = 16
    kick_freq = 1789773 / 4068.0
    snare_freq = 1789773 / 508.0
    hat_freq = 1789773 / 32.0
    tom_freq = 1789773 / 1016.0

    total_beats = int(seconds / beat)
    for beat_i in range(total_beats):
        style_i = (beat_i // beats_per_style) % len(tour)
        name, kicks, snares, hat_div, hat_style = tour[style_i]
        in_style = beat_i % beats_per_style
        in_bar = beat_i % 4
        t = beat_i * beat
        # the tour boundary: a fill at the end of each style's last bar
        is_fill_bar = in_style >= beats_per_style - 4

        # the bass holds the root (a different root per style — the tour
        # modulates through the circle of fifths-ish: A, D, G, C, F, Bb, Eb, Ab)
        root_cycle = [A1 / 2, 73.42, 98.0 / 2, 65.41, 87.31 / 2, 58.27, 77.78, 51.91]
        root = root_cycle[style_i]

        # the kick/snare pattern for this beat (sub-beat positions)
        for kb in kicks:
            if abs(in_bar - kb) < 0.001 or (kb >= 1 and abs(in_bar + 1 - kb) < 0.001 and False):
                pass
        # place the pattern events per beat: the events at (bar + pos) where
        # pos's integer part == in_bar
        for kb in kicks:
            if int(kb) == in_bar:
                events.append({"t": t + (kb - in_bar) * beat, "dur": 0.10,
                               "ch": "noise", "freq": kick_freq, "gain": 0.85,
                               "env": (15, 12), "kind": "kick",
                               "emphasis": in_bar == 0})
        for sb in snares:
            if int(sb) == in_bar:
                events.append({"t": t + (sb - in_bar) * beat, "dur": 0.15,
                               "ch": "noise", "freq": snare_freq, "gain": 0.5,
                               "env": (13, 14), "kind": "snare",
                               "emphasis": in_bar == 1})
        # hats per the style's density
        if hat_style == "8ths" and in_bar % 1 == 0:
            for h in (0, 0.5):
                events.append({"t": t + h * beat, "dur": 0.03, "ch": "noise",
                               "freq": hat_freq, "gain": 0.25, "env": (9, 5),
                               "kind": "hat", "emphasis": False})
        elif hat_style == "16ths":
            for h in range(4):
                events.append({"t": t + h * beat / 4, "dur": 0.025, "ch": "noise",
                               "freq": hat_freq, "gain": 0.2, "env": (8, 4),
                               "kind": "hat", "emphasis": h == 0})
        elif hat_style == "quarters":
            if in_bar % 2 == 0:
                events.append({"t": t, "dur": 0.04, "ch": "noise",
                               "freq": hat_freq, "gain": 0.25, "env": (9, 5),
                               "kind": "hat", "emphasis": False})
        elif hat_style == "8ths-open":
            events.append({"t": t, "dur": 0.06, "ch": "noise",
                           "freq": 1789773 / 64.0, "gain": 0.3, "env": (11, 6),
                           "kind": "hat", "emphasis": False})

        # the fill: the last bar of each style — a tom roll on the 16ths
        if is_fill_bar and in_bar == 3:
            for f in range(4):
                events.append({"t": t + f * beat / 4, "dur": 0.08, "ch": "noise",
                               "freq": tom_freq, "gain": 0.4, "env": (12, 8),
                               "kind": "tom", "emphasis": False})

        # the bass: root eighths under everything
        for h in (0, 0.5):
            events.append({"t": t + h * beat, "dur": beat / 2, "ch": "tri",
                           "freq": root, "gain": 0.45, "env": (15, 16),
                           "kind": "bass", "emphasis": in_bar == 0})

        # the melody: a sparse pulse arpeggio on the style's root (one note
        # per beat — leaves the drums as the star)
        arp = [root * 4, root * 6, root * 5, root * 6]
        events.append({"t": t, "dur": beat * 0.85, "ch": "pulse",
                       "freq": arp[in_bar], "duty": 0.25, "gain": 0.22,
                       "env": (13, 18), "kind": "melody", "emphasis": in_bar == 0})
    return events


def generate_nes_beattour(seconds: float = 96.0) -> bytes:
    """128 BPM — the drum-pattern tour (see nes_beattour_score)."""
    return _nes_render(nes_beattour_score(seconds), seconds)


# ── Song 4: "NES Scale Expedition" — every scale, thoroughly ────────────────

def nes_scale_expedition_score(seconds: float = 120.0) -> list:
    """'NES Scale Expedition' (132 BPM): a TOUR OF SCALES — each scale gets
    8 measures explored THOROUGHLY (runs up, runs down, thirds, the pivot
    figure, an octave jump), with the drum pattern changing per scale. The
    scales: C major, A natural minor, A harmonic minor, C major pentatonic,
    A minor pentatonic + blues, D dorian, G mixolydian, C whole-tone (the
    finale). The oracle's richest test: every note's scale-degree is known."""
    bpm = 132.0
    beat = 60.0 / bpm
    events = []

    def scale_from_root(root, steps):
        return [root * (2 ** (s / 12.0)) for s in steps]

    major = [0, 2, 4, 5, 7, 9, 11, 12]
    nat_minor = [0, 2, 3, 5, 7, 8, 10, 12]
    harm_minor = [0, 2, 3, 5, 7, 8, 11, 12]
    maj_pent = [0, 2, 4, 7, 9, 12, 14, 16]
    min_pent_blues = [0, 3, 5, 6, 7, 10, 12, 15]
    dorian = [0, 2, 3, 5, 7, 9, 10, 12]
    mixolydian = [0, 2, 4, 5, 7, 9, 10, 12]
    whole_tone = [0, 2, 4, 6, 8, 10, 12, 14]

    expedition = [
        ("C major", scale_from_root(261.63, major), [0, 2], "8ths"),
        ("A natural minor", scale_from_root(220.0, nat_minor), [0, 2], "quarters"),
        ("A harmonic minor", scale_from_root(220.0, harm_minor), [0, 1, 2, 3], "16ths"),
        ("C major pentatonic", scale_from_root(261.63, maj_pent), [0, 2], "8ths"),
        ("A blues", scale_from_root(220.0, min_pent_blues), [0, 2.5], "swing"),
        ("D dorian", scale_from_root(293.66, dorian), [0, 1, 2, 3], "16ths"),
        ("G mixolydian", scale_from_root(392.0, mixolydian), [0, 2], "8ths-open"),
        ("C whole-tone", scale_from_root(261.63, whole_tone), [0, 1, 2, 3], "16ths"),
    ]
    kick_freq = 1789773 / 4068.0
    snare_freq = 1789773 / 508.0
    hat_freq = 1789773 / 32.0

    beats_per_scale = 32      # 8 measures × 4
    total_beats = int(seconds / beat)
    for beat_i in range(total_beats):
        scale_i = (beat_i // beats_per_scale) % len(expedition)
        name, sc, kicks, hat_style = expedition[scale_i]
        in_scale = beat_i % beats_per_scale
        in_bar = beat_i % 4
        t = beat_i * beat
        emph = in_scale == 0 or in_bar == 0

        # drums (a different pattern per scale — from the beattour patterns)
        if int(kicks[0]) == in_bar or (in_bar == 0):
            events.append({"t": t, "dur": 0.09, "ch": "noise",
                           "freq": kick_freq, "gain": 0.8, "env": (15, 12),
                           "kind": "kick", "emphasis": emph})
        if in_bar in (1, 3):
            events.append({"t": t, "dur": 0.14, "ch": "noise",
                           "freq": snare_freq, "gain": 0.5, "env": (13, 14),
                           "kind": "snare", "emphasis": in_bar == 1})
        hat_div = 4 if hat_style == "16ths" else 2
        for h in range(hat_div):
            events.append({"t": t + h * beat / hat_div, "dur": 0.028,
                           "ch": "noise", "freq": hat_freq, "gain": 0.22,
                           "env": (8, 4), "kind": "hat", "emphasis": h == 0})

        # bass: the scale's root (a triangle, on every beat)
        root = sc[0] / 2
        events.append({"t": t, "dur": beat * 0.9, "ch": "tri", "freq": root,
                       "gain": 0.48, "env": (15, 16), "kind": "bass",
                       "emphasis": emph})

        # melody: THOROUGH scale exploration — a 4-note figure per beat
        # cycling through: run up, run down, thirds, the pivot+octave
        section = in_scale // 8           # 8-measure blocks: the variation
        figures = {
            0: lambda pos: pos,                            # the run up
            1: lambda pos: (len(sc) - 1) - (pos % len(sc)),  # the run down
            2: lambda pos: (pos * 2) % len(sc),            # thirds-ish
            3: lambda pos: (len(sc) - 1) - (pos % len(sc)) if pos % 2 else (pos * 2) % len(sc),
        }
        fig = figures[section % len(figures)]
        for sixteenth in range(4):
            idx = (in_scale * 4 + sixteenth)
            pos = idx % len(sc)
            note_idx = fig(pos) % len(sc)
            freq = sc[note_idx]
            events.append({"t": t + sixteenth * beat / 4, "dur": beat / 4 * 0.95,
                           "ch": "pulse", "freq": freq * 2, "duty": 0.5,
                           "gain": 0.25, "env": (15, 10), "kind": "melody",
                           "emphasis": sixteenth == 0})
    return events


def generate_nes_scale_expedition(seconds: float = 120.0) -> bytes:
    """132 BPM — the scale expedition (see nes_scale_expedition_score)."""
    return _nes_render(nes_scale_expedition_score(seconds), seconds)


# ── Song 5: "One And a Half Dragons" — the NES action-theme homage ──────────

def one_and_half_dragons_score(seconds: float = 84.0) -> list:
    """'One And a Half Dragons' (150 BPM, E minor): the NES beat-'em-up
    action-theme homage — driving 16th bass, a heroic wide-interval melody
    (the iv-VI-VII-I lift), the palm-muted-style low pulse stabs, and a
    bridge that drops to the half-time snare before the final chorus lift.
    The drums: kick 1&3, snare 2&4 with the classic fill every 8 bars."""
    bpm = 150.0
    beat = 60.0 / bpm
    events = []
    # E minor: E2 bass, the melody in E4-E5
    E2 = 82.41
    C2 = 65.41
    E4, FS4, G4, A4, B4, D5, E5 = 329.63, 369.99, 392.0, 440.0, 493.88, 587.33, 659.26
    kick_freq = 1789773 / 4068.0
    snare_freq = 1789773 / 508.0
    hat_freq = 1789773 / 32.0
    tom_freq = 1789773 / 1016.0

    # the iconic progression: Em - C - D - Em (the action lift) ×2, then
    # Am - C - D - E (the bridge tension)
    prog = [
        (E2, [E4, G4, B4, E5]),      # Em
        (C2 * 2, [G4, B4, E5, G4]),  # C (first inversion feel)
        (73.42, [FS4, A4, D5, FS4]),                 # D
        (E2, [E4, G4, B4, E5]),      # Em
    ]

    total_beats = int(seconds / beat)
    for beat_i in range(total_beats):
        t = beat_i * beat
        in_bar = beat_i % 4
        bar_i = beat_i // 4
        section = bar_i // 8           # 8-bar sections
        emph = in_bar == 0
        chord_idx = (bar_i % 8) // 2   # 2 bars per chord
        bass_root, melody_bar = prog[chord_idx % len(prog)]

        # the driving 16th bass (the beat-'em-up engine)
        for s16 in range(4):
            accent = s16 == 0
            freq = bass_root * (2 if accent and s16 == 0 else 1)
            events.append({"t": t + s16 * beat / 4, "dur": beat / 4 * 0.9,
                           "ch": "tri", "freq": freq, "gain": 0.5 if accent else 0.38,
                           "env": (15, 8), "kind": "bass", "emphasis": emph and s16 == 0})

        # drums: kick 1&3, snare 2&4, hats 16ths
        if in_bar in (0, 2):
            events.append({"t": t, "dur": 0.10, "ch": "noise", "freq": kick_freq,
                           "gain": 0.85, "env": (15, 12), "kind": "kick",
                           "emphasis": emph})
        if in_bar in (1, 3):
            events.append({"t": t, "dur": 0.14, "ch": "noise", "freq": snare_freq,
                           "gain": 0.55, "env": (13, 14), "kind": "snare",
                           "emphasis": in_bar == 1})
        for s16 in range(4):
            events.append({"t": t + s16 * beat / 4, "dur": 0.025, "ch": "noise",
                           "freq": hat_freq, "gain": 0.2, "env": (8, 4),
                           "kind": "hat", "emphasis": s16 == 0})

        # the fill: the last bar of each 8-bar section
        if bar_i % 8 == 7 and in_bar == 3:
            for f in range(4):
                events.append({"t": t + f * beat / 4, "dur": 0.09, "ch": "noise",
                               "freq": tom_freq, "gain": 0.45, "env": (13, 8),
                               "kind": "tom", "emphasis": False})

        # the melody: the heroic wide-interval hook (the section A melody)
        hook = [E4, G4, B4, E5, D5, B4, G4, A4]   # the lift
        bridge = [B4, A4, G4, FS4, G4, A4, B4, D5]  # the bridge tension
        mel = bridge if section % 2 == 1 else hook
        idx = beat_i % 8
        if not (section % 2 == 1 and in_bar in (0, 1) and beat_i % 2 == 0):
            events.append({"t": t, "dur": beat * 0.8, "ch": "pulse",
                           "freq": mel[idx], "duty": 0.5, "gain": 0.3,
                           "env": (15, 20), "kind": "melody",
                           "emphasis": emph and idx in (0, 4)})

        # the low pulse stabs (the palm-muted-style power chord approximation)
        if in_bar == 0 or in_bar == 2:
            events.append({"t": t, "dur": beat / 4, "ch": "pulse",
                           "freq": bass_root * 2, "duty": 0.125, "gain": 0.25,
                           "env": (12, 6), "kind": "stab", "emphasis": emph})
    return events


def generate_one_and_half_dragons(seconds: float = 84.0) -> bytes:
    """150 BPM, E minor — the beat-'em-up action theme homage."""
    return _nes_render(one_and_half_dragons_score(seconds), seconds)


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
    "nes_beattour": {
        "label": "NES BeatTour 2026 — a tour of drum patterns (96s, 128 BPM)",
        "seconds": 96,
        "generate": generate_nes_beattour,
    },
    "nes_scale_expedition": {
        "label": "NES Scale Expedition — every scale, thoroughly (120s, 132 BPM)",
        "seconds": 120,
        "generate": generate_nes_scale_expedition,
    },
    "one_and_half_dragons": {
        "label": "One And a Half Dragons — the NES action-theme homage (84s, 150 BPM)",
        "seconds": 84,
        "generate": generate_one_and_half_dragons,
    },
}
