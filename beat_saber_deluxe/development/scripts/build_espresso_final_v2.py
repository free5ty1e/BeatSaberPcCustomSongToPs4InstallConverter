#!/usr/bin/env python3
"""Final approach: use v4 bundle (correct size) + brute-force CRC correction on 9 padding bytes."""
import struct, lz4.block, zlib

ORIGINAL_BUNDLE = "/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/aa/PS4/therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle"
V4_BUNDLE = "/workspace/beat_saber_deluxe/espresso_pack_patched.bundle"  # From v4 build (correct size)
OUT_BUNDLE = "/workspace/beat_saber_deluxe/espresso_pack_final.bundle"
TARGET_CRC = 0xdc8b314f

def main():
    print("Espresso Bundle — Final Approach: Correct Size + Brute-Force CRC")
    
    # Load v4 bundle (has correct size but wrong CRC)
    with open(V4_BUNDLE, 'rb') as f:
        patched = bytearray(f.read())
    
    original_size = 7902803
    print(f"V4 bundle: {len(patched):,} bytes (CRC=0x{zlib.crc32(bytes(patched)) & 0xFFFFFFFF:08x})")
    
    # Load original to find alignment padding location
    with open(ORIGINAL_BUNDLE, 'rb') as f:
        orig = bytearray(f.read())
    
    # Parse blocks to find where alignment padding is
    blk_cs = struct.unpack('>I', orig[38:42])[0]
    blk_ds = struct.unpack('>I', orig[42:46])[0]
    flags = struct.unpack('>I', orig[46:50])[0]
    
    bs = (50 + 15) & ~15
    info = lz4.block.decompress(bytes(orig[bs:bs+blk_cs]), uncompressed_size=blk_ds)
    
    # Raw data starts after blocks_info (with alignment if needed)
    raw_data_start = bs + blk_cs
    if flags & 0x200:
        raw_data_start = (raw_data_start + 15) & ~15
    
    padding_offset = bs + blk_cs
    padding_size = raw_data_start - padding_offset
    
    print(f"Alignment padding: offset {padding_offset}, size {padding_size} bytes")
    
    # Check if v4 bundle has the same structure as original
    # (blocks_info at same location, etc.)
    v4_blk_cs = struct.unpack('>I', patched[38:42])[0]
    v4_blk_ds = struct.unpack('>I', patched[42:46])[0]
    v4_flags = struct.unpack('>I', patched[46:50])[0]
    
    print(f"Original flags: 0x{flags:08x}")
    print(f"V4 flags: 0x{v4_flags:08x}")
    print(f"Flags match: {'✅' if flags == v4_flags else '❌'}")
    
    # The padding should be at the same location in v4 bundle
    # (since we only modified uncompressed block content, not structure)
    
    current_crc = zlib.crc32(bytes(patched)) & 0xFFFFFFFF
    print(f"\nCurrent CRC: 0x{current_crc:08x}")
    print(f"Target CRC: 0x{TARGET_CRC:08x}")
    
    if current_crc == TARGET_CRC:
        print("✅ CRC already matches!")
    else:
        # Brute-force the 9 padding bytes (4^9 = 262,144 combinations)
        print(f"\nBrute-forcing {padding_size} padding bytes ({256**padding_size:,} combos)...")
        
        found = False
        
        # Generate all combinations recursively
        def brute_force(idx, current_vals):
            nonlocal found
            
            if found:
                return
            
            if idx == padding_size:
                # Test this combination
                test_buf = bytearray(patched)
                for i, val in enumerate(current_vals):
                    test_buf[padding_offset + i] = val
                
                test_crc = zlib.crc32(bytes(test_buf)) & 0xFFFFFFFF
                if test_crc == TARGET_CRC:
                    print(f"✅ Found! Padding values: {[hex(v) for v in current_vals]}")
                    # Apply and save
                    for i, val in enumerate(current_vals):
                        patched[padding_offset + i] = val
                    found = True
                return
            
            # Try all 256 values for this position
            for d in range(256):
                current_vals.append(d)
                brute_force(idx + 1, current_vals)
                current_vals.pop()
                
                if found:
                    return
        
        # This will be too slow for 9 bytes (262K iterations with CRC computation each)
        # Let's use a smarter approach: fix first 8 bytes, solve for last byte
        
        print("Using smart search: fix first 8 bytes, solve for last byte...")
        
        # For the last padding byte (position 8):
        # contribution = table[last_byte] XOR table[orig_val_at_pos_8]
        # We need: CRC_after_all_padding = TARGET_CRC
        
        # Compute CRC state after processing first 8 padding bytes (with current values)
        # Then find what last byte value makes final CRC = TARGET_CRC
        
        # Actually, let's use the approach from build_patched_pack_bundle.py which worked
        
        # Precompute CRC table
        crc_table = [0] * 256
        for i in range(256):
            v = i
            for _ in range(8):
                v = (v >> 1) ^ (0xEDB88320 if v & 1 else 0)
            crc_table[i] = v
        
        # Try all combinations of first 8 bytes, solve for last byte
        import itertools
        
        count = 0
        for combo in itertools.product(range(256), repeat=padding_size - 1):
            count += 1
            if count % 10000 == 0:
                print(f"  Progress: {count:,} combinations...")
            
            # Apply first 8 bytes
            test_buf = bytearray(patched)
            for i, val in enumerate(combo):
                test_buf[padding_offset + i] = val
            
            # Compute CRC after first 8 padding bytes
            crc_state = zlib.crc32(bytes(test_buf[:padding_offset])) & 0xFFFFFFFF
            for b in test_buf[padding_offset:padding_offset + (padding_size - 1)]:
                crc_state = (crc_state >> 8) ^ crc_table[(crc_state & 0xFF) ^ b]
            
            # Now find last byte that makes final CRC = TARGET_CRC
            # CRC_final = process_byte(crc_state, last_byte)
            # We need: process_byte(crc_state, last_byte) = TARGET_CRC
            
            # Try all 256 values for last byte
            suf_crc = zlib.crc32(bytes(test_buf[padding_offset + (padding_size - 1):])) & 0xFFFFFFFF
            
            for d in range(256):
                test_buf[padding_offset + padding_size - 1] = d
                
                # Compute final CRC
                final_crc = zlib.crc32(bytes(test_buf)) & 0xFFFFFFFF
                
                if final_crc == TARGET_CRC:
                    print(f"✅ Found! First 8 bytes: {[hex(v) for v in combo]}, last byte: {d}")
                    
                    # Apply and save
                    for i, val in enumerate(combo):
                        patched[padding_offset + i] = val
                    patched[padding_offset + padding_size - 1] = d
                    
                    found = True
                    break
            
            if found:
                break
        
        if not found:
            print("❌ Could not find CRC correction with brute-force")
    
    # Final verification
    final_crc = zlib.crc32(bytes(patched)) & 0xFFFFFFFF
    
    print(f"\n{'='*60}")
    size_ok = "✅" if len(patched) == original_size else f"+{len(patched)-original_size:,}"
    crc_ok = "✅" if final_crc == TARGET_CRC else "❌"
    print(f"FINAL: size={len(patched):,} ({size_ok}), CRC=0x{final_crc:08x} {crc_ok}, target=0x{TARGET_CRC:08x}")
    
    with open(OUT_BUNDLE, 'wb') as f:
        f.write(bytes(patched))
    print(f"Output: {OUT_BUNDLE}")

if __name__ == '__main__':
    main()
