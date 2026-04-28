#!/usr/bin/env python3
"""PS4 fPKG Builder v7 - Template Clone from Reference"""
import struct
import hashlib
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
OUTPUT_DIR = WORK_DIR / "output"
REF_PKG = WORK_DIR / "dlc_reference/CUSA12878_RIOT-Overkill.pkg"

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


def create_param_sfo(content_id, title, title_id):
    """Create param.sfo for our custom content"""
    sfo = bytearray(0x2000)
    sfo[0:4] = b'PSF\x00'
    sfo[4:8] = b'\x01\x01\x00\x00'
    struct.pack_into('<I', sfo, 8, 7)
    struct.pack_into('<I', sfo, 12, 0x1000)
    struct.pack_into('<I', sfo, 16, 0x1800)
    
    keys = b'ATTRIBUTE\x00CATEGORY\x00CONTENT_ID\x00FORMAT\x00TITLE\x00TITLE_ID\x00VERSION\x00'
    key_offs = [0, 10, 20, 32, 40, 52, 64]
    data_offs = [0, 4, 8, 40, 48, 96, 144]
    
    for i, off in enumerate(key_offs):
        struct.pack_into('<I', sfo, 0x20 + i*4, off)
    for i, off in enumerate(data_offs):
        struct.pack_into('<I', sfo, 0x38 + i*4, off)
        
    sfo[0x1000:0x1000+len(keys)] = keys
    
    struct.pack_into('<I', sfo, 0x1800, 0)
    sfo[0x1804:0x1806] = b'ac\x00'
    sfo[0x1808:0x1808+len(content_id)] = content_id.encode()
    sfo[0x1840:0x1842] = b'ob\x00'
    sfo[0x1850:0x1860] = title.encode('utf-16-le') + b'\x00\x00'
    sfo[0x18C0:0x18D0] = title_id.encode('utf-16-le') + b'\x00\x00'
    sfo[0x1910:0x1913] = b'01.00'
    
    return bytes(sfo)


def build_pkg():
    """Build PKG by cloning reference header template"""
    print("Building fPKG v7 - Template Clone Method")
    print("=" * 50)
    
    # Load reference PKG
    ref_data = REF_PKG.read_bytes()
    ref_size = len(ref_data)
    print(f"Reference PKG size: {ref_size:,} (0x{ref_size:x})")
    
    # Parse reference header to find PFS boundaries
    ref_header = ref_data[:0x200]
    ref_body = ref_data[0x200:]
    
    # Find PFS location in reference
    # Looking for PSF magic in body
    pfs_search = ref_body.find(b'PSF\x00')
    if pfs_search >= 0:
        ref_pfs_offset = 0x200 + pfs_search
        print(f"Reference PFS starts at: 0x{ref_pfs_offset:x}")
    else:
        # Try different approach - check header for PFS offset
        ref_pfs_offset = 0x2000  # Common offset
        print(f"Assuming PFS at: 0x{ref_pfs_offset:x}")
    
    # Create our param.sfo
    param_data = create_param_sfo(CONTENT_ID, GAME_TITLE, TITLE_ID)
    
    # Get icon from reference
    icon_data = b''
    icon_offset = ref_body.find(b'\x89PNG')
    if icon_offset > 0:
        # Extract PNG
        for end_offset in range(icon_offset + 4, len(ref_body)):
            if ref_body[end_offset:end_offset+4] == b'IEND':
                icon_data = ref_body[icon_offset:end_offset+8]
                break
        if icon_data:
            print(f"Icon size: {len(icon_data):,}")
    
    # Build our PFS (param + icon)
    pfs_data = param_data + icon_data
    while len(pfs_data) % 0x10 != 0:
        pfs_data += b'\x00'
    
    our_pfs_size = len(pfs_data)
    our_pfs_enc = simple_xor(pfs_data, FAKE_KEY)
    print(f"Our PFS size: {our_pfs_size:#x}")
    
    # Now build PKG by cloning reference template
    # Strategy: Copy reference header, replace PFS region with ours
    # Make header bigger to include PFS metadata region (0x400+)
    
    header = bytearray(0x1000)  # Bigger header to include PFS region
    header[:len(ref_header[:0x200])] = ref_header[:0x200]
    
    # Find where PFS starts in reference - we'll replace our content there
    # Common: body starts at 0x200 with metadata, PFS at 0x2000
    
    # Copy reference header but update critical fields
    # Keep: magic, flags, entry table info
    # Update: Content ID, Title ID, PFS info, digests
    
    # Update Content ID at 0x30
    header[0x30:0x58] = CONTENT_ID.encode('ascii').ljust(36, b'\x00')
    
    # Update Title ID at 0x58
    header[0x58:0x68] = TITLE_ID.encode('ascii').ljust(10, b'\x00')
    
    # Update DRM/Type (should already be correct: DRM=0x0f, type=0x1b)
    struct.pack_into('<I', header, 0x64, 0x0f000000)  # DRM free
    struct.pack_into('<I', header, 0x68, 0x1b000000)  # DLC
    
    # Get our PFS digest
    pfs_digest = sha256(pfs_data)
    
    # Update PFS info at 0x400+
    # PFS count at 0x400
    struct.pack_into('<I', header, 0x400, 1)
    # PFS offset at 0x408
    struct.pack_into('<Q', header, 0x408, 0x2000)
    # PFS size at 0x410
    struct.pack_into('<Q', header, 0x410, our_pfs_size)
    # Body size at 0x420 (same as PFS size + header)
    struct.pack_into('<Q', header, 0x420, 0x2000 + our_pfs_size)
    # PFS size again at 0x438
    struct.pack_into('<I', header, 0x438, our_pfs_size)
    # PFS digest at 0x440
    header[0x440:0x460] = pfs_digest
    
    # Body size at 0x20 (using LE as reference shows)
    body_size = 0x2000 + our_pfs_size
    struct.pack_into('<I', header, 0x20, body_size)
    struct.pack_into('<I', header, 0x24, 0)
    struct.pack_into('<I', header, 0x28, 0x2000)  # PFS offset
    
    # Body size again at 0x28+4 (redundant but may be needed)
    struct.pack_into('<I', header, 0x2c, 0)
    
    # Calculate body digest
    body_data = b'\x00' * 0x2000 + our_pfs_enc
    body_digest = sha256(body_data)
    header[0x160:0x180] = body_digest
    
    # Header digest at 0xFE0
    header_digest = sha256(bytes(header[:0xFE0]))
    header[0xFE0:0x1000] = header_digest[:0x100]
    
    # Build complete body
    body = bytearray(0x2000 + our_pfs_size)
    
    # Fill entry table region (0x1000-0x2000)
    for i in range(16):
        offset = 0x1000 + i * 0x20
        body[offset:offset+0x20] = sha256(bytes([i] * 32))
    
    # PFS at 0x2000
    body[0x2000:0x2000+our_pfs_size] = our_pfs_enc
    
    # Combine header + body
    pkg = bytes(header) + bytes(body)
    
    print(f"\nNew PKG size: {len(pkg):,} (0x{len(pkg):x})")
    print(f"Header size: 0x200")
    print(f"Body size: 0x{len(body):x}")
    print(f"PFS size: 0x{our_pfs_size:x}")
    
    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "custom_songs_v7.pkg"
    output.write_bytes(pkg)
    
    print(f"Created: {output}")
    
    # Also print header comparison for debugging
    print("\n--- Header Comparison (Reference vs v7) ---")
    compare_ref_ours(ref_header, bytes(header))
    
    return pkg


def compare_ref_ours(ref, ours):
    """Compare reference header to ours for debugging"""
    import struct
    
    fields = [
        (0x00, 4, "magic"),
        (0x04, 2, "flags_h"),
        (0x06, 2, "flags_l"),
        (0x10, 4, "entry_off"),
        (0x14, 4, "entry_cnt"),
        (0x18, 4, "body_off"),
        (0x20, 4, "body_size"),
        (0x28, 4, "pfs_off"),
    ]
    
    print(f"{'Offset':<10} {'Reference':<20} {'Ours':<20}")
    print("-" * 50)
    for off, size, name in fields:
        r = struct.unpack('<I', ref[off:off+4])[0]
        o = struct.unpack('<I', ours[off:off+4])[0]
        match = "✓" if r == o else "��"
        print(f"0x{off:<04x}   0x{r:<18x} 0x{o:<18x} {match}")


if __name__ == "__main__":
    build_pkg()