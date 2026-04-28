#!/usr/bin/env python3
"""PS4 fPKG Builder v6 - Based on reference PKG template"""
import struct
import hashlib
import datetime
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
OUTPUT_DIR = WORK_DIR / "output"
REF_PKG = "dlc_reference/CUSA12878_RIOT-Overkill.pkg"

# Use content ID from reference
CONTENT_ID = "UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX"
TITLE_ID = "CUSA12878"
GAME_TITLE = "Custom Songs"

FAKE_KEY = bytes([0x46, 0x41, 0x4b, 0x45] * 32)


def sha256(data):
    return hashlib.sha256(data).digest()


def simple_xor(data, key):
    result = bytearray(data)
    for i in range(len(result)):
        result[i] ^= key[i % len(key)]
    return bytes(result)


def unpack_le(data, offset, size):
    """Unpack as little-endian based on size"""
    if size == 4:
        return struct.unpack('<I', data[offset:offset+4])[0]
    elif size == 8:
        return struct.unpack('<Q', data[offset:offset+8])[0]
    return 0


def build_pkg():
    print(f"Building fPKG v6 based on reference template")
    
    # Load reference PKG as template
    with open(REF_PKG, 'rb') as f:
        ref_data = f.read()
    
    ref_size = len(ref_data)
    print(f"Reference PKG size: {ref_size:,}")
    
    # Get reference header
    ref_header = ref_data[:0x200]
    ref_body = ref_data[0x200:]
    
    # Get key header fields from reference
    print("\nReference header fields:")
    print(f"  0x10 (entry_off): 0x{unpack_le(ref_header, 0x10, 4):08x}")
    print(f"  0x14 (entry_cnt): 0x{unpack_le(ref_header, 0x14, 4):08x}")
    print(f"  0x18 (body_off):  0x{unpack_le(ref_header, 0x18, 4):08x}")
    print(f"  0x20 (body_size): 0x{unpack_le(ref_header, 0x20, 4):08x}")
    print(f"  0x28 (pfs_size): 0x{unpack_le(ref_header, 0x28, 4):08x}")
    
    # Create new param.sfo
    sfo = bytearray(0x2000)
    sfo[0:4] = b'PSF\x00'
    sfo[4:8] = b'\x01\x01\x00\x00'
    struct.pack_into('<I', sfo, 8, 7)  # version
    struct.pack_into('<I', sfo, 12, 0x1000)
    struct.pack_into('<I', sfo, 16, 0x1800)
    
    # SFO keys
    keys = b'ATTRIBUTE\x00CATEGORY\x00CONTENT_ID\x00FORMAT\x00TITLE\x00TITLE_ID\x00VERSION\x00'
    key_offs = [0, 10, 20, 32, 40, 52, 64]
    data_offs = [0, 4, 8, 40, 48, 96, 144]
    
    for i, off in enumerate(key_offs):
        struct.pack_into('<I', sfo, 0x20 + i*4, off)
    for i, off in enumerate(data_offs):
        struct.pack_into('<I', sfo, 0x38 + i*4, off)
    
    sfo[0x1000:0x1000+len(keys)] = keys
    
    # SFO data
    struct.pack_into('<I', sfo, 0x1800, 0)
    sfo[0x1804:0x1806] = b'ac\x00'
    sfo[0x1808:0x1808+len(CONTENT_ID)] = CONTENT_ID.encode()
    sfo[0x1840:0x1842] = b'ob\x00'
    sfo[0x1850:0x1860] = GAME_TITLE.encode('utf-16-le') + b'\x00\x00'
    sfo[0x18C0:0x18D0] = TITLE_ID.encode('utf-16-le') + b'\x00\x00'
    sfo[0x1910:0x1913] = b'01.00'
    
    param_data = bytes(sfo)
    
    # Get icon from reference
    # Find icon in reference body
    icon_offset = ref_body.find(b'\x89PNG')
    if icon_offset > 0:
        print(f"\nFound icon in reference at offset: 0x{icon_offset:x}")
        # Extract PNG
        icon_data = b''
        for end_offset in range(icon_offset + 4, len(ref_body)):
            if ref_body[end_offset:end_offset+4] == b'IEND':
                icon_data = ref_body[icon_offset:end_offset+8]
                break
        print(f"Icon size: {len(icon_data):,}")
    else:
        icon_data = b''
        print("No icon found in reference")
    
    # Build PFS (param + icon)
    pfs_data = param_data + icon_data
    while len(pfs_data) % 0x10 != 0:
        pfs_data += b'\x00'
    
    pfs_size = len(pfs_data)
    print(f"PFS size: {pfs_size:#x} ({pfs_size})")
    
    # Encrypt PFS
    pfs_enc = simple_xor(pfs_data, FAKE_KEY)
    
    # Try to match reference structure
    # For DLC: body_offset = 0x200 seems common
    body_offset = 0x200
    body = bytearray(0x2000 + pfs_size)
    
    # Fill entry table region (0x1000-0x1400) with fake hashes
    for i in range(16):
        offset = 0x1000 + i * 0x20
        body[offset:offset+0x20] = sha256(bytes([i] * 32))
    
    # Body data at 0x2000
    body[0x2000:0x2000+pfs_size] = pfs_enc
    
    # Now build header - make it bigger to include PFS region
    header = bytearray(0x1000)
    
    # Magic
    header[0:4] = b'\x7fCNT'
    
    # Flags
    struct.pack_into('>H', header, 4, 0x0001)
    struct.pack_into('>H', header, 6, 0x0002)
    
    # pkg_id
    struct.pack_into('>I', header, 8, 0)
    
    # The critical 0x0c-0x30 region - use reference values!
    # 0x0c: 0x0f000000 (same as reference)
    struct.pack_into('<I', header, 0x0c, 0x0f000000)
    
    # Entry table - using BE format for these!
    # 0x10: entry table offset (BE)
    # 0x14: entry count (BE)
    struct.pack_into('>I', header, 0x10, 0x00000000)  # entry offset (no entry table)
    struct.pack_into('>I', header, 0x14, 0x00000000)  # entry count = 0 for PFS style
    
    # Body offset and size - use BE!
    # 0x18: body offset (BE)
    # 0x20: body size (BE)
    struct.pack_into('>I', header, 0x18, 0x00000200)  # body at 0x200
    struct.pack_into('>I', header, 0x1c, 0x00000000)  # unk
    
    body_size = len(body)
    struct.pack_into('>I', header, 0x20, body_size)  # body_size
    struct.pack_into('>I', header, 0x24, 0x00000000)  # unk
    
    # 0x28: pfs image offset (BE)
    pfs_offset = 0x2000
    struct.pack_into('>I', header, 0x28, pfs_offset)
    
    # Content ID at 0x30
    header[0x30:0x30+36] = CONTENT_ID.encode('ascii')
    
    # Title ID at 0x58
    header[0x58:0x58+10] = TITLE_ID.encode('ascii')
    
    # DRM, type at 0x64
    struct.pack_into('<I', header, 0x64, 0x0f000000)  # DRM = free
    struct.pack_into('<I', header, 0x68, 0x1b000000)  # type = DLC
    struct.pack_into('<I', header, 0x6c, 0x0a000000)  # version info?
    
    # More header fields
    # PFS info at 0x400
    struct.pack_into('<I', header, 0x400, 1)  # pfs_count
    struct.pack_into('<Q', header, 0x408, pfs_offset)  # pfs_offset
    struct.pack_into('<Q', header, 0x410, pfs_size)  # pfs_size
    struct.pack_into('<Q', header, 0x420, body_size)  # body_size (again)
    
    # PFS digest
    pfs_digest = sha256(pfs_data)
    header[0x440:0x460] = pfs_digest
    
    # Body digest
    body_digest = sha256(bytes(body))
    header[0x160:0x180] = body_digest
    
    # Header digest at end
    header[0xFE0:0x1000] = sha256(bytes(header[:0xFE0]))[:0x100]
    
    # Combine and write
    pkg = bytes(header) + bytes(body)
    
    print(f"\nNew PKG size: {len(pkg):,} (0x{len(pkg):x})")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "custom_songs_v6.pkg"
    output.write_bytes(pkg)
    
    print(f"Created: {output}")
    return pkg


if __name__ == "__main__":
    build_pkg()