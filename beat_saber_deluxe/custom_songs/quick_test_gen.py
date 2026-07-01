#!/usr/bin/env python3
"""
Quick Test Bundle Generator
===========================
Generates a small test AssetBundle with all 5 major beatmap features
(notes, bombs, obstacles, arcs, chains) appearing within ~20 seconds
of gameplay. Used for rapid regression testing.

Usage:
    python3 quick_test_gen.py [output_path]

The generated bundle is ~12MB due to template overhead (AudioClip,
ScriptableObjects, lightshows). The actual beatmap data is ~340 bytes gzipped.
"""
import UnityPy, json, struct, gzip, sys, os

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(__file__), "quick_test.bundle")

TEMPLATE = "/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/startmeup"

V3_DATA = {
    "version": "4.0.0",
    "colorNotes": [
        {"b": 1.0},
        {"b": 1.5, "i": 1},
        {"b": 2.0, "i": 2},
        {"b": 2.5, "i": 3},
        {"b": 3.0},
        {"b": 3.5, "i": 1},
        {"b": 4.0},
        {"b": 4.5, "i": 1},
        {"b": 5.0},
    ],
    "colorNotesData": [
        {"x": 1, "d": 1},
        {"x": 3, "c": 1, "d": 3},
        {"x": 0, "y": 2, "d": 5},
        {"x": 2, "y": 1, "c": 1, "d": 7},
        {"x": 3, "y": 2, "c": 1, "d": 1},
        {"x": 0, "y": 0, "d": 1},
        {"x": 2, "y": 0, "c": 1, "d": 3},
    ],
    "bombNotes": [
        {"b": 1.75},
        {"b": 2.25, "i": 1},
        {"b": 3.25, "i": 2},
    ],
    "bombNotesData": [
        {"x": 3},
        {"x": 0},
        {"y": 2},
    ],
    "obstacles": [
        {"b": 6.0, "i": 1},
        {"b": 8.0},
    ],
    "obstaclesData": [
        {"d": 2.0, "w": 1, "h": 5},
        {"d": 1.5, "w": 4, "h": 5},
        {"d": 1.0, "w": 1, "h": 5},
    ],
    "arcs": [
        {"hb": 10.0, "hi": 0, "tb": 12.0, "ti": 4, "ai": 0},
        {"hb": 14.0, "hi": 4, "tb": 15.5, "ti": 0, "ai": 1},
    ],
    "arcsData": [
        {"m": 0.75, "tm": 0.5},
        {"m": 0.5, "tm": 0.75},
    ],
    "chains": [
        {"hb": 18.0, "tb": 18.625, "i": 5, "ci": 0},
        {"hb": 20.0, "tb": 20.5, "i": 6, "ci": 1},
    ],
    "chainsData": [
        {"tx": 2, "c": 4, "s": 0.5},
        {"c": 4, "s": 0.4},
    ],
    "spawnRotations": [],
    "spawnRotationsData": [],
}

def main():
    if not os.path.isdir(os.path.dirname(TEMPLATE)):
        print(f"Error: template bundle not found at {TEMPLATE}")
        return 1

    json_bytes = json.dumps(V3_DATA, separators=(',', ':')).encode('utf-8')
    compressed = gzip.compress(json_bytes)
    print(f"Beatmap: {len(json_bytes)}B JSON → {len(compressed)}B gzip")

    env = UnityPy.load(TEMPLATE)
    bf = list(env.files.values())[0]
    cab = next(v for v in bf.files.values() if hasattr(v, 'objects'))

    replaced = 0
    for pid in sorted(cab.objects.keys()):
        reader = cab.objects[pid]
        if reader.class_id != 49:
            continue
        name = reader.peek_name()
        if not name or '.beatmap' not in name:
            continue
        tt = reader.read_typetree()
        c = gzip.compress(json_bytes)
        tt['m_Script'] = c.decode('utf-8', 'surrogateescape')
        reader.save_typetree(tt)
        replaced += 1

    print(f"Replaced {replaced} beatmap TextAssets")
    result = bf.save(packer="none")

    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    with open(OUTPUT, 'wb') as f:
        f.write(result)

    print(f"Bundle: {len(result)} bytes ({len(result)/1024:.1f} KB)")
    print(f"Saved to: {OUTPUT}")

    # Quick verify
    env2 = UnityPy.load(OUTPUT)
    cab2 = next(v for v in list(env2.files.values())[0].files.values() if hasattr(v, 'objects'))
    ok = fail = 0
    for _, r2 in cab2.objects.items():
        try:
            t2 = r2.read_typetree()
            if '.beatmap' in t2.get('m_Name', ''):
                bm = json.loads(gzip.decompress(r2.get_raw_data()[r2.get_raw_data().find(b'\x1f\x8b'):]))
                print(f"  ✅ {t2['m_Name']}: {len(bm['colorNotes'])}n {len(bm['bombNotes'])}b {len(bm['obstacles'])}o {len(bm['arcs'])}a {len(bm['chains'])}c")
            ok += 1
        except:
            fail += 1
    print(f"Verify: {ok} OK, {fail} FAILED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
