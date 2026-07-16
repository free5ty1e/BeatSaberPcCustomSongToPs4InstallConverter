#!/usr/bin/env python3
"""
Build patched pack bundle: UnityPy CAB serialization + manual bundle injection.

The crash was caused by UnityPy's bf.save() corrupting the UnityFS bundle wrapper.
Fix: use UnityPy only for CAB serialization (correct object table), then build
the bundle manually to ensure format compatibility.

Approach:
  1. Modify BeatmapLevelSO via UnityPy (5 modes, preserve all PPtrs)
  2. Save CAB via UnityPy (correct object table, externals, types)
  3. Build bundle manually: decompress original, replace CAB, recompress
"""

import struct, os, lz4.block
from UnityPy import Environment

ORIGINAL_BUNDLE = (
    "/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/"
    "aa/PS4/therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle"
)
OUT_BUNDLE = "/workspace/beat_saber_deluxe/rollingstones_pack_patched.bundle"

CHAR_PATH_IDS = {
    "Standard":  -7286399427822119286,
    "OneSaber":  -8583864861369561029,
    "NoArrows":   -5623662769225589684,
    "90Degree":    4533580413116749821,
    "360Degree":  1189643819550092755,
}


def main():
    print("=" * 70)
    print("Pack Bundle Builder — UnityPy CAB + Manual Bundle")
    print("=" * 70)

    # 1. Load original bundle and modify BeatmapLevelSO
    env = Environment(ORIGINAL_BUNDLE)
    bf = list(env.files.values())[0]

    cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
    resS_key = cab_key + ".resS"
    res_key = cab_key + ".resource"

    cab = bf.files[cab_key]
    resS_raw = bytes(bf.files[resS_key].bytes)
    res_raw = bytes(bf.files[res_key].bytes)

    print(f"CAB: {cab_key}")
    print(f"resS: {len(resS_raw):,} bytes")
    print(f"resource: {len(res_raw):,} bytes")

    # 2. Modify BeatmapLevelSO to have 5 modes
    obj = cab.objects[2287600824654271910]
    tree = obj.read_typetree()
    orig_pds = tree.get('_previewDifficultyBeatmapSets', [])
    template_set = orig_pds[0]

    new_pds = [template_set]
    for mode in ["OneSaber", "NoArrows", "90Degree", "360Degree"]:
        ms = dict(template_set)
        ms['_beatmapCharacteristic'] = {'m_FileID': 3, 'm_PathID': CHAR_PATH_IDS[mode]}
        ms['_previewDifficultyBeatmaps'] = []
        new_pds.append(ms)
    tree['_previewDifficultyBeatmapSets'] = new_pds

    # Verify m_Script PPtr is correct
    m_script = tree.get('m_Script', {})
    print(f"m_Script PPtr: fileID={m_script.get('m_FileID')}, pathID={m_script.get('m_PathID')}")
    assert m_script.get('m_PathID') != CHAR_PATH_IDS["Standard"], \
        "m_Script pathID must NOT be the Standard char pathID!"

    # 3. Save CAB via UnityPy (correct serialization with updated object table)
    obj.save_typetree(tree)
    patched_cab = cab.save()
    print(f"Patched CAB (UnityPy serialized): {len(patched_cab):,} bytes")

    # 4. Load original bundle data for manual reconstruction
    with open(ORIGINAL_BUNDLE, 'rb') as f:
        orig = bytearray(f.read())

    data_flags = struct.unpack('>I', orig[46:50])[0]
    blk_comp_sz = struct.unpack('>I', orig[38:42])[0]
    blk_decomp_sz = struct.unpack('>I', orig[42:46])[0]
    blk_start = (50 + 15) & ~15

    # Parse original block info to get per-block compression types
    orig_blk_info = lz4.block.decompress(
        bytes(orig[blk_start:blk_start + blk_comp_sz]),
        uncompressed_size=blk_decomp_sz
    )
    r = 16 + 4
    orig_block_count = struct.unpack('>I', orig_blk_info[r-4:r])[0]
    orig_blocks = []
    for i in range(orig_block_count):
        bd = struct.unpack('>I', orig_blk_info[r:r+4])[0]; r += 4
        bc = struct.unpack('>I', orig_blk_info[r:r+4])[0]; r += 4
        bf = struct.unpack('>H', orig_blk_info[r:r+2])[0]; r += 2
        orig_blocks.append((bd, bc, bf))

    # 5. Decompress original data blocks
    data_start = blk_start + blk_comp_sz
    if data_flags & 0x200:
        data_start = (data_start + 15) & ~15  # align to 16

    decompressed = bytearray()
    for bd, bc, bf in orig_blocks:
        raw = bytes(orig[data_start:data_start + bc])
        if bf & 2:
            dec = lz4.block.decompress(raw, uncompressed_size=bd)
            decompressed.extend(dec)
        else:
            decompressed.extend(raw)
        data_start += bc

    print(f"Decompressed stream: {len(decompressed):,} bytes")

    # 6. Get original CAB size from parsed blocks info (nodes)
    orig_r = 16 + 4 + orig_block_count * 10
    orig_node_count = struct.unpack('>i', orig_blk_info[orig_r:orig_r+4])[0]
    orig_r += 4
    orig_nodes = []
    for i in range(orig_node_count):
        off = struct.unpack('>q', orig_blk_info[orig_r:orig_r+8])[0]; orig_r += 8
        sz = struct.unpack('>q', orig_blk_info[orig_r:orig_r+8])[0]; orig_r += 8
        nf = struct.unpack('>i', orig_blk_info[orig_r:orig_r+4])[0]; orig_r += 4
        p_end = orig_blk_info.find(b'\x00', orig_r)
        path = orig_blk_info[orig_r:p_end].decode('utf-8'); orig_r = p_end + 1
        orig_nodes.append((path, off, sz, nf))

    cab_off = orig_nodes[0][1]  # Usually 0
    cab_orig_sz = orig_nodes[0][2]  # Should be 89180
    print(f"Original CAB: offset={cab_off}, size={cab_orig_sz}")

    # 7. Replace CAB in decompressed stream
    new_stream = bytearray(decompressed)
    new_stream[cab_off:cab_off + cab_orig_sz] = patched_cab

    total_delta = len(patched_cab) - cab_orig_sz
    print(f"CAB size changed by {total_delta:+d} bytes")

    # 8. Update directory info (nodes)
    new_nodes = [
        (cab_key, 0, len(patched_cab), 4),
        (resS_key, len(patched_cab), len(resS_raw), 0),
        (res_key, len(patched_cab) + len(resS_raw), len(res_raw), 0),
    ]

    # 8. Recompress - use LZ4 for blocks that benefit, uncompressed otherwise
    BLOCK_SZ = 0x20000
    new_blocks = []
    new_comp = bytearray()
    for bs in range(0, len(new_stream), BLOCK_SZ):
        chunk = bytes(new_stream[bs:bs + BLOCK_SZ])
        comp = lz4.block.compress(chunk, store_size=False)
        if len(comp) < len(chunk):
            new_blocks.append((len(chunk), len(comp), 2))
            new_comp.extend(comp)
        else:
            new_blocks.append((len(chunk), len(chunk), 0))
            new_comp.extend(chunk)

    print(f"Recompressed: {len(new_blocks)} blocks -> {len(new_comp):,} bytes")

    # 9. Build blocks info (BIG ENDIAN for UnityFS)
    info_buf = b'\x00' * 16  # hash
    info_buf += struct.pack('>I', len(new_blocks))
    for bd, bc, bf in new_blocks:
        info_buf += struct.pack('>IIH', bd, bc, bf)
    info_buf += struct.pack('>I', len(new_nodes))
    for path, off, sz, nf in new_nodes:
        pb = path.encode('utf-8') + b'\x00'
        info_buf += struct.pack('>QQI', off, sz, nf)
        info_buf += pb

    info_comp = lz4.block.compress(bytes(info_buf), store_size=False)
    print(f"Blocks info: {len(info_buf)} -> {len(info_comp)} bytes")

    # 10. Write new bundle
    with open(OUT_BUNDLE, 'wb') as f:
        f.write(b'UnityFS\x00')
        f.write(struct.pack('>I', 8))
        f.write(b'5.x.x\x00')
        f.write(b'2022.3.33f1\x00')
        f.write(struct.pack('>Q', 0))  # file_size placeholder
        f.write(struct.pack('>I', len(info_comp)))
        f.write(struct.pack('>I', len(info_buf)))
        f.write(struct.pack('>I', data_flags))
        while f.tell() % 16:
            f.write(b'\x00')  # align to 16
        f.write(info_comp)  # compressed blocks info
        if data_flags & 0x200:
            while f.tell() % 16:
                f.write(b'\x00')  # BlockInfoNeedPaddingAtStart
        f.write(bytes(new_comp))  # data blocks
        final_size = f.tell()
        f.seek(30)
        f.write(struct.pack('>Q', final_size))

    final_size = final_size or os.path.getsize(OUT_BUNDLE)
    print(f"\n✅ {OUT_BUNDLE.split('/')[-1]}: {final_size:,} bytes (orig: {len(orig):,})")

    # 11. Verify with UnityPy (read-only parse)
    print(f"\nVerifying with UnityPy...")
    try:
        env2 = Environment(OUT_BUNDLE)
        bf2 = list(env2.files.values())[0]
        for key in bf2.files:
            if key.startswith("CAB-") and '.res' not in key:
                cab2 = bf2.files[key]
                obj2 = cab2.objects[2287600824654271910]
                tree2 = obj2.read_typetree()
                pds2 = tree2.get('_previewDifficultyBeatmapSets', [])
                m_script2 = tree2.get('m_Script', {})
                print(f"  m_Name: {tree2.get('m_Name', '?')}")
                print(f"  m_Script: fileID={m_script2.get('m_FileID')}, pathID={m_script2.get('m_PathID')}")
                print(f"  _pds count: {len(pds2)}")
                if len(pds2) == 5:
                    print("  ✅ 5 modes confirmed!")
                for i, p in enumerate(pds2):
                    bc = p.get('_beatmapCharacteristic', {})
                    print(f"    [{i}] fileID={bc.get('m_FileID')}, pathID={bc.get('m_PathID')}")
                break
    except Exception as e:
        print(f"  ❌ Verification failed: {e}")
        import traceback; traceback.print_exc()


if __name__ == '__main__':
    main()
