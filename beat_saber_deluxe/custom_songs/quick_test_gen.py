#!/usr/bin/env python3
"""
Quick Test Bundle Generator
===========================
Generates a small test AssetBundle with:
- All 5 major beatmap features (notes, bombs, obstacles, arcs, chains)
  within ~30 seconds of gameplay
- Custom 3-second test audio (440/880/660Hz sine tones)
- All metadata updated

The generated bundle is ~220 KB — small enough to commit to git.

Usage:
    python3 quick_test_gen.py [output_path]
    python3 quick_test_gen.py /path/to/startmeup_v3  # for PS4 deployment

Feature timing (beats):
  1-5   9 notes (alternating red/blue, various positions)
  1.75  3 bombs (at columns 3, 0, top row)
  6-11  5 floor walls (full-height, short, tall, mid, very short)
  10-14 2 arc sliders (left->right, reverse)
  18-20 2 chain bursts (right-moving, stationary)
  24-28 3 floating walls (y=3/h=2 duck, y=2/h=2 mid, y=4/h=1 ceiling)
  Audio: 3 seconds of test tones (440Hz -> 880Hz -> 660Hz)
"""
import UnityPy, json, struct, gzip, sys, os, math, io

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(__file__), "quick_test.bundle")
TEMPLATE = "/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/startmeup"
FSB5_TEMPLATE = "/workspace/ps4_dump/beatsaber_song_exports/CAB-0183cf5e66ff23724b3e1bc22e7ea951.resource"

# ===== BEATMAP DATA (V3 format) =====
V3_DATA = {
    "version": "4.0.0",
    "colorNotes": [
        {"b": 1.0}, {"b": 1.5, "i": 1}, {"b": 2.0, "i": 2}, {"b": 2.5, "i": 3},
        {"b": 3.0}, {"b": 3.5, "i": 1}, {"b": 4.0}, {"b": 4.5, "i": 1}, {"b": 5.0},
    ],
    "colorNotesData": [
        {"x": 1, "d": 1}, {"x": 3, "c": 1, "d": 3}, {"x": 0, "y": 2, "d": 5},
        {"x": 2, "y": 1, "c": 1, "d": 7}, {"x": 3, "y": 2, "c": 1, "d": 1},
        {"x": 0, "y": 0, "d": 1}, {"x": 2, "y": 0, "c": 1, "d": 3},
    ],
    "bombNotes": [{"b": 1.75}, {"b": 2.25, "i": 1}, {"b": 3.25, "i": 2}],
    "bombNotesData": [{"x": 3}, {"x": 0}, {"y": 2}],
    "obstacles": [
        {"b": 6.0, "i": 1}, {"b": 7.0, "i": 2}, {"b": 8.0, "i": 3},
        {"b": 9.0, "i": 4}, {"b": 11.0, "i": 5},
        {"b": 24.0, "i": 6}, {"b": 26.0, "i": 7}, {"b": 28.0, "i": 8},
    ],
    "obstaclesData": [
        {"d": 2.0, "w": 1, "h": 5},          # [0] default
        {"d": 0.5, "w": 4, "h": 5, "x": 0},  # [1] wide full-height -> duck
        {"d": 0.5, "w": 1, "h": 2, "x": 0},  # [2] short left -> step
        {"d": 0.5, "w": 1, "h": 5, "x": 3},  # [3] tall right -> duck+dodge
        {"d": 0.5, "w": 2, "h": 3, "x": 1},  # [4] mid-height -> medium duck
        {"d": 0.5, "w": 1, "h": 1, "x": 2},  # [5] very short -> barely duck
        {"d": 1.0, "w": 2, "h": 2, "x": 1, "y": 3},  # [6] floating y=3
        {"d": 1.0, "w": 2, "h": 2, "x": 0, "y": 2},  # [7] floating y=2
        {"d": 1.0, "w": 4, "h": 1, "x": 0, "y": 4},  # [8] ceiling y=4
    ],
    "arcs": [
        {"hb": 10.0, "hi": 0, "tb": 12.0, "ti": 4, "ai": 0},
        {"hb": 14.0, "hi": 4, "tb": 15.5, "ti": 0, "ai": 1},
    ],
    "arcsData": [{"m": 0.75, "tm": 0.5}, {"m": 0.5, "tm": 0.75}],
    "chains": [
        {"hb": 18.0, "tb": 18.625, "i": 5, "ci": 0},
        {"hb": 20.0, "tb": 20.5, "i": 6, "ci": 1},
    ],
    "chainsData": [{"tx": 2, "c": 4, "s": 0.5}, {"c": 4, "s": 0.4}],
    "spawnRotations": [], "spawnRotationsData": [],
}

# ===== HEVAG AUDIO ENCODER =====
# HEVAG is PS4 ADPCM format used in FSB5 containers
HEVAG_COEFFS = [[0, 0], [60, 0], [115, -52], [98, -55], [122, -60]]

def _hevag_block(samples, h1, h2):
    best_pred = best_shift = 0
    best_err = float('inf')
    for pred in range(len(HEVAG_COEFFS)):
        c1, c2 = HEVAG_COEFFS[pred]
        for shift in range(13):
            err = eh1 = h1; eh2 = h2
            for s in samples:
                p = ((eh1 * c1 + eh2 * c2) + 32) >> 6
                d = max(-32768, min(32767, s - p))
                n = max(-8, d >> shift) & 0xF if d < 0 else min(7, d >> shift) & 0xF
                err += (d - ((n | 0xF0) << shift if n & 0x8 else n << shift)) ** 2
                eh2, eh1 = eh1, s
            if err < best_err: best_err, best_pred, best_shift = err, pred, shift
    c1, c2 = HEVAG_COEFFS[best_pred]
    frame = bytearray(16)
    struct.pack_into('<H', frame, 0, best_pred | (best_shift << 4))
    for i in range(28):
        p = ((h1 * c1 + h2 * c2) + 32) >> 6
        d = max(-32768, min(32767, samples[i] - p))
        n = max(-8, d >> best_shift) & 0xF if d < 0 else min(7, d >> best_shift) & 0xF
        bi = 1 + (i // 2)
        if i % 2 == 0: frame[bi] = (frame[bi] & 0xF0) | n
        else: frame[bi] = (frame[bi] & 0x0F) | (n << 4)
        h2, h1 = h1, samples[i]
    return bytes(frame), h1, h2

def pcm_to_hevag(pcm, channels=2):
    samples = [struct.unpack_from('<h', pcm, i*2)[0] for i in range(len(pcm)//2)]
    left = samples[0::2] if channels == 2 else samples
    right = samples[1::2] if channels == 2 else []
    result = bytearray()
    frames = len(left) // 28
    h1_l = h2_l = h1_r = h2_r = 0
    for i in range(frames):
        fl, h1_l, h2_l = _hevag_block(left[i*28:(i+1)*28], h1_l, h2_l)
        result.extend(fl)
        if right:
            fr, h1_r, h2_r = _hevag_block(right[i*28:(i+1)*28], h1_r, h2_r)
            result.extend(fr)
    return bytes(result)

def make_test_audio():
    """Generate 3-second test audio: 440Hz -> 880Hz -> 660Hz tones"""
    sr, ch, dur = 44100, 2, 3
    pcm = bytearray()
    for i in range(sr * dur):
        t = i / sr
        if t < 0.5: s = int(math.sin(2*math.pi*440*t) * 32767 * 0.4)
        elif t < 1.0: s = int(math.sin(2*math.pi*880*t) * 32767 * 0.4)
        elif t < 1.5: s = 0
        elif t < 2.0: s = int(math.sin(2*math.pi*660*t) * 32767 * 0.4)
        else: s = 0
        pcm.extend(struct.pack('<h', s))
        pcm.extend(struct.pack('<h', s))
    return bytes(pcm), sr, ch, dur

def build_fsb5(pcm_data, sample_rate, channels):
    """Build an FSB5 file with HEVAG-encoded audio"""
    existing = open(FSB5_TEMPLATE, "rb").read()
    sample_hdr = bytearray(existing[16:16+900])
    hevag = pcm_to_hevag(pcm_data, channels)
    struct.pack_into('<I', sample_hdr, 4, len(hevag))
    buf = io.BytesIO()
    buf.write(b'FSB5')
    buf.write(struct.pack('<I', 1)); buf.write(struct.pack('<I', 1))
    buf.write(struct.pack('<I', 900)); buf.write(bytes(sample_hdr))
    buf.write(hevag)
    return buf.getvalue(), len(hevag)

def main():
    if not os.path.isdir(os.path.dirname(TEMPLATE)):
        print(f"Error: template bundle not found at {TEMPLATE}")
        return 1
    if not os.path.exists(FSB5_TEMPLATE):
        print(f"Error: FSB5 template not found at {FSB5_TEMPLATE}")
        return 1

    # Generate audio
    pcm_data, sr, ch, dur = make_test_audio()
    fsb5_bytes, hevag_size = build_fsb5(pcm_data, sr, ch)
    print(f"Audio: {dur}s, PCM={len(pcm_data)}b, HEVAG={hevag_size}b, FSB5={len(fsb5_bytes)}b")

    # Build V3 beatmap JSON
    json_bytes = json.dumps(V3_DATA, separators=(',', ':')).encode('utf-8')
    v3_compressed = gzip.compress(json_bytes)
    print(f"Beatmap: {len(json_bytes)}B JSON -> {len(v3_compressed)}B gzip")

    # Load template bundle
    env = UnityPy.load(TEMPLATE)
    bf = list(env.files.values())[0]
    cab = bf.files['CAB-6c9e66546e3e23434517417298a18b91']
    resource_key = 'CAB-6c9e66546e3e23434517417298a18b91.resource'

    # Replace resource (FSB5 audio)
    from UnityPy.streams import EndianBinaryReader
    new_res = EndianBinaryReader(fsb5_bytes)
    new_res.flags = 0
    new_res.BaseOffset = 0
    bf.files[resource_key] = new_res

    # Update AudioClip
    for pid, reader in cab.objects.items():
        if reader.class_id == 83:
            tt = reader.read_typetree()
            tt['m_Resource']['m_Size'] = len(fsb5_bytes)
            tt['m_Length'] = float(dur)
            reader.save_typetree(tt)
            print(f"AudioClip: {dur}s, resource={len(fsb5_bytes)}b")
            break

    # Update audio.gz metadata
    for pid, reader in cab.objects.items():
        if reader.class_id == 49 and 'audio.gz' in (reader.peek_name() or ''):
            sls = len(pcm_data) // (2 * ch)
            meta = json.dumps({
                "version": "4.0.0", "songChecksum": "custom",
                "songSampleCount": sls, "songFrequency": sr,
                "bpmData": [{"si": 0, "ei": sls, "sb": 0.0, "eb": float(dur)}]
            }, separators=(',', ':'))
            tt = reader.read_typetree()
            tt['m_Script'] = gzip.compress(meta.encode()).decode('utf-8', 'surrogateescape')
            reader.save_typetree(tt)
            print(f"audio.gz: {sls} samples @ {sr}Hz")
            break

    # Replace beatmaps
    replaced = 0
    for pid, reader in cab.objects.items():
        if reader.class_id == 49:
            n = reader.peek_name() or ''
            if '.beatmap' in n:
                tt = reader.read_typetree()
                tt['m_Script'] = v3_compressed.decode('utf-8', 'surrogateescape')
                reader.save_typetree(tt)
                replaced += 1
    print(f"Beatmaps: {replaced} replaced")

    # Save bundle
    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    result = bf.save(packer="none")
    with open(OUTPUT, 'wb') as f:
        f.write(result)
    print(f"\nBundle: {len(result)} bytes ({len(result)/1024:.1f} KB)")
    print(f"Saved to: {OUTPUT}")

    # Verify
    env2 = UnityPy.load(OUTPUT)
    cab2 = next(v for v in list(env2.files.values())[0].files.values() if hasattr(v, 'objects'))
    ok = fail = 0
    for _, r2 in cab2.objects.items():
        try:
            t2 = r2.read_typetree()
            n = t2.get('m_Name', '')
            if 'beatmap' in n:
                bm = json.loads(gzip.decompress(r2.get_raw_data()[r2.get_raw_data().find(b'\x1f\x8b'):]))
                print(f"  ✅ {n}: {len(bm['colorNotes'])}n {len(bm['bombNotes'])}b {len(bm['obstacles'])}o {len(bm['arcs'])}a {len(bm['chains'])}c")
            elif n == 'StartMeUp' and r2.class_id == 83:
                print(f"  ✅ AudioClip: {t2['m_Length']:.1f}s")
            ok += 1
        except:
            fail += 1
    print(f"Verify: {ok} OK, {fail} FAILED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
