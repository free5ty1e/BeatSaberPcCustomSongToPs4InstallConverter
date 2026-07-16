#!/usr/bin/env python3
"""
Build patched pack bundle — manual blob builder + raw CAB injection + object table update.

save_typetree() ignores modifications for this object type (stuck at 440 bytes).
Fix: use inject_pack_bundle.py's blob builder (struct packing, byte-verified) with
the CORRECT m_Script PPtr, then raw-inject into the CAB with object table offset update.

Header format (v22+): metadata_size(BE) at 0x14, file_size(BE) at 0x1C,
data_offset = align16(48 + metadata_size).
Object table: pathID(int64) + offset(int64 relative to data_offset) + size(int32)
"""

import struct, os, lz4.block
from UnityPy import Environment

ORIGINAL_BUNDLE = "/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/aa/PS4/therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle"
OUT_BUNDLE = "/workspace/beat_saber_deluxe/rollingstones_pack_patched.bundle"

# ── Fixed PPtr values ────────────────────────────────────────────────
SCRIPT_PATHID_CORRECT = 2140275054477726686  # MonoScript, NOT BeatmapCharacteristicSO!
CHAR_PATH_IDS = {
    "Standard":  -7286399427822119286,
    "OneSaber":  -8583864861369561029,
    "NoArrows":   -5623662769225589684,
    "90Degree":    4533580413116749821,
    "360Degree":  1189643819550092755,
}

def encode_utf8_string(s):
    """Unity serialized UTF-8 string: stored_size = char count (no null), content without null, null after.
    NOTE: Original CAB format does NOT include null in stored_size!
    """
    if not s:
        return b'\x00\x00'  # stored_size=0 + null
    data = s.encode('utf-8')  # NO null in content
    return struct.pack('<i', len(data)) + data + b'\x00'  # size=char_count, content, then null

def build_blob(song_name="Espresso", artist="Sabrina Carpenter", bpm=126.5, level_id="custom/espresso"):
    """Build BeatmapLevelSO blob with 5 modes and correct m_Script PPtr. Returns 1257 bytes."""
    b = bytearray()
    b += struct.pack('<i', 0)                                      # m_GameObject fileID
    b += struct.pack('<q', 0)                                      # m_GameObject pathID
    b += struct.pack('<I', 1)                                      # class/metadata
    b += struct.pack('<i', 1)                                      # m_Script fileID = 1
    b += struct.pack('<q', SCRIPT_PATHID_CORRECT)                  # FIXED: MonoScript pathID

    b.extend(encode_utf8_string(f"{song_name}CustomBeatmapLevel"))  # m_Name
    b.append(0x78); b.append(1); b.append(1)                       # _version

    b.extend(encode_utf8_string(level_id))                          # _levelID
    b.extend(encode_utf8_string(song_name))                         # _songName
    b.extend(b'\x00\x00')                                          # _songSubName
    b.extend(encode_utf8_string(artist))                            # _songAuthorName
    b.extend(encode_utf8_string(artist))                            # _levelAuthorName

    b += struct.pack('<i', 0) + struct.pack('<q', 0)               # _previewAudioClip (zeroed)
    for val in [bpm, -8.2, 0.0, 0.0, 0.0, 138.0, 10.0, 213.7]:
        b += struct.pack('<d', val)
    b += struct.pack('<i', 0) + struct.pack('<q', 0)               # _coverImage (zeroed)

    b.extend(encode_utf8_string(""))
    b.extend(encode_utf8_string(""))
    b += struct.pack('<i', 1)
    b.extend(encode_utf8_string("TheRollingStonesEnvironment"))
    b += struct.pack('<i', 0)

    # 5 modes
    b += struct.pack('<i', 5)
    for mode in ["Standard", "OneSaber", "NoArrows", "90Degree", "360Degree"]:
        b += struct.pack('<i', 3)                                   # fileID = 3 (external)
        b += struct.pack('<q', CHAR_PATH_IDS[mode])                 # pathID
        b += struct.pack('<i', 5)                                   # diff_count = 5
        b += b'\x00' * (5 * 36)                                    # zeroed diffs

    return bytes(b)


def get_cab_raw(path):
    """Decompress bundle and extract CAB raw bytes + metadata."""
    with open(path, 'rb') as f:
        buf = bytearray(f.read())
    blk_cs = struct.unpack('>I', buf[38:42])[0]
    blk_ds = struct.unpack('>I', buf[42:46])[0]
    flags = struct.unpack('>I', buf[46:50])[0]
    bs = (50 + 15) & ~15
    info = lz4.block.decompress(bytes(buf[bs:bs+blk_cs]), uncompressed_size=blk_ds)
    r = 16; bc = struct.unpack('>I', info[r:r+4])[0]; r += 4
    blocks = []
    for _ in range(bc):
        bd = struct.unpack('>I', info[r:r+4])[0]; r += 4
        bc2 = struct.unpack('>I', info[r:r+4])[0]; r += 4
        bf = struct.unpack('>H', info[r:r+2])[0]; r += 2
        blocks.append((bd, bc2, bf))
    ds = bs + blk_cs
    if flags & 0x200: ds = (ds + 15) & ~15
    dec = bytearray()
    for bd, bc2, bf in blocks:
        raw = bytes(buf[ds:ds+bc2])
        d = lz4.block.decompress(raw, uncompressed_size=bd) if bf & 2 else raw
        dec.extend(d); ds += bc2
    node_cnt = struct.unpack('>i', info[r:r+4])[0]; r += 4
    nodes = []
    for _ in range(node_cnt):
        off = struct.unpack('>q', info[r:r+8])[0]; r += 8
        sz = struct.unpack('>q', info[r:r+8])[0]; r += 8
        nf = struct.unpack('>i', info[r:r+4])[0]; r += 4
        pe = info.find(b'\x00', r); p = info[r:pe].decode(); r = pe + 1
        nodes.append((p, off, sz, nf))
    return bytes(dec[:nodes[0][2]]), blocks, flags, nodes, dec, buf


def main():
    print("=" * 70)
    print("Manual Blob Builder + Raw CAB Injection + Object Table Update")
    print("=" * 70)

    cab_raw, blocks, flags, nodes, dec, buf = get_cab_raw(ORIGINAL_BUNDLE)
    meta_sz = struct.unpack('>I', cab_raw[0x14:0x18])[0]
    file_sz_be = struct.unpack('>I', cab_raw[0x1C:0x20])[0]
    data_off = (48 + meta_sz + 15) & ~15  # 53456
    print(f"CAB: {len(cab_raw)}B, meta_sz={meta_sz}, file_sz={file_sz_be}, data_off={data_off}")

    # Load via UnityPy for object metadata (byte_start, byte_size)
    env = Environment(ORIGINAL_BUNDLE)
    bf = list(env.files.values())[0]
    cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
    resS_key = cab_key + ".resS"; res_key = cab_key + ".resource"
    cab_obj = bf.files[cab_key]
    resS_raw = bytes(bf.files[resS_key].bytes)
    res_raw = bytes(bf.files[res_key].bytes)

    obj = cab_obj.objects[2287600824654271910]
    blb_start = obj.byte_start
    blb_size = obj.byte_size
    print(f"BeatmapLevelSO: offset={blb_start}, size={blb_size}")

    # Build modified blob
    new_blob = build_blob()
    delta = len(new_blob) - blb_size
    print(f"Blob: {blb_size} -> {len(new_blob)} (delta: {delta:+d})")
    assert delta > 0, "Expected blob to be larger!"

    # Patch CAB: replace blob
    patched = bytearray(cab_raw)
    patched[blb_start:blb_start + blb_size] = new_blob
    blob_end = blb_start + len(new_blob)

    # Update object table entries (objects AFTER the blob + blob's own size)
    cab_header_sz = 48
    meta_region_end = data_off
    obj_list = sorted(
        [(pid, o.byte_start, o.byte_size) for pid, o in cab_obj.objects.items()],
        key=lambda x: x[1]
    )
    updated_off = 0
    not_found = 0
    for pid, bstart, bsize in obj_list:
        if bstart < blb_start + blb_size:
            continue  # before or inside old blob
        old_stored = bstart - data_off
        new_stored = old_stored + delta
        pat = struct.pack('<q', pid) + struct.pack('<Q', old_stored)
        pos = patched.find(pat, cab_header_sz, meta_region_end)
        if pos >= 0:
            patched[pos + 8:pos + 16] = struct.pack('<Q', new_stored)
            updated_off += 1
        else:
            not_found += 1
    print(f"Object table: {updated_off} offsets updated, {not_found} not found")

    # Update the blob's own size in the object table
    pat = struct.pack('<q', obj.path_id) + struct.pack('<Q', blb_start - data_off)
    pos = patched.find(pat, cab_header_sz, meta_region_end)
    if pos >= 0:
        # size is at pos+16 (after pathID=8 + offset=8)
        patched[pos + 16:pos + 20] = struct.pack('<I', len(new_blob))
        print(f"Updated blob size: 440 -> {len(new_blob)}")
    else:
        print("  ⚠️  Could not find beatmap level SO entry in object table!")

    # Update file_size in CAB header
    new_cab_sz = len(patched)
    patched[0x1C:0x20] = struct.pack('>I', new_cab_sz)
    print(f"CAB: {len(cab_raw)} -> {new_cab_sz}")

    # Build bundle
    cab_orig_sz = nodes[0][2]
    stream = bytearray(dec)
    stream[:cab_orig_sz] = bytes(patched)
    new_nodes = [
        (cab_key, 0, new_cab_sz, 4),
        (resS_key, new_cab_sz, len(resS_raw), 0),
        (res_key, new_cab_sz + len(resS_raw), len(res_raw), 0),
    ]
    BLOCK_SZ = 0x20000
    n_blocks = []; n_comp = bytearray()
    for bs in range(0, len(stream), BLOCK_SZ):
        chunk = bytes(stream[bs:bs + BLOCK_SZ])
        comp = lz4.block.compress(chunk, store_size=False)
        if len(comp) < len(chunk):
            n_blocks.append((len(chunk), len(comp), 2)); n_comp.extend(comp)
        else:
            n_blocks.append((len(chunk), len(chunk), 0)); n_comp.extend(chunk)
    info_buf = b'\x00' * 16
    info_buf += struct.pack('>I', len(n_blocks))
    for bd, bc, bf in n_blocks:
        info_buf += struct.pack('>IIH', bd, bc, bf)
    info_buf += struct.pack('>I', len(new_nodes))
    for p, o, s, nf in new_nodes:
        info_buf += struct.pack('>QQI', o, s, nf) + p.encode() + b'\x00'
    info_comp = lz4.block.compress(bytes(info_buf), store_size=False)

    with open(OUT_BUNDLE, 'wb') as f:
        f.write(b'UnityFS\x00'); f.write(struct.pack('>I', 8))
        f.write(b'5.x.x\x00'); f.write(b'2022.3.33f1\x00')
        f.write(struct.pack('>Q', 0))
        f.write(struct.pack('>I', len(info_comp)))
        f.write(struct.pack('>I', len(info_buf)))
        f.write(struct.pack('>I', flags))
        f.flush()
        f.write(b'\x00' * ((16 - f.tell() % 16) % 16))
        f.write(info_comp)
        if flags & 0x200:
            f.write(b'\x00' * ((16 - f.tell() % 16) % 16))
        f.write(bytes(n_comp))
        fsz = f.tell()
        f.seek(30); f.write(struct.pack('>Q', fsz))

    print(f"\n✅ {OUT_BUNDLE.split('/')[-1]}: {fsz:,} bytes")

    # Verify with UnityPy
    env2 = Environment(OUT_BUNDLE)
    bf2 = list(env2.files.values())[0]
    for key in bf2.files:
        if key.startswith("CAB-") and '.res' not in key:
            c2 = bf2.files[key]
            o2 = c2.objects[2287600824654271910]
            t2 = o2.read_typetree()
            pds2 = t2.get('_previewDifficultyBeatmapSets', [])
            ms2 = t2.get('m_Script', {})
            print(f"  m_Script: fileID={ms2.get('m_FileID')}, pathID={ms2.get('m_PathID')}")
            print(f"  Song: {t2.get('_songName','?')}")
            print(f"  Modes: {len(pds2)} {'✅ 5 MODES!' if len(pds2)==5 else ''}")
            for i, p in enumerate(pds2):
                bc = p.get('_beatmapCharacteristic', {})
                print(f"    [{i}] fileID={bc.get('m_FileID')}, pathID={bc.get('m_PathID')}")
            break


if __name__ == '__main__':
    main()
