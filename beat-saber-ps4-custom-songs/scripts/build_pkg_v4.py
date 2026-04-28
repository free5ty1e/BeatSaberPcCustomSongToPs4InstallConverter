#!/usr/bin/env python3
"""PS4 fPKG Builder v4 - PFS mode (entry_count=0 like working DLC)"""
import struct
import hashlib
import datetime
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
OUTPUT_DIR = WORK_DIR / "output"

PKG_MAGIC = b'\x7f\x43\x4e\x54'
CONTENT_ID = "UP4882-CUSA12878_00-P1S5CUSTOM001"
TITLE_ID = "CUSA12878"
GAME_TITLE = "Custom Songs"

# Simple fake key (just for structure)
FAKE_KEY = bytes([0x46, 0x41, 0x4b, 0x45] * 32)


def sha256(data):
    return hashlib.sha256(data).digest()


def simple_xor(data, key):
    result = bytearray(data)
    for i in range(len(result)):
        result[i] ^= key[i % len(key)]
    return bytes(result)


def create_param_sfo(content_id, title, title_id):
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
    print(f"Building fPKG v4 (PFS mode): {GAME_TITLE}")
    
    # Get files
    param_data = create_param_sfo(CONTENT_ID, GAME_TITLE, TITLE_ID)
    
    ref_icon = WORK_DIR / "ref_extract/sce_sys/icon0.png"
    icon_data = b''
    if ref_icon.exists():
        icon_data = ref_icon.read_bytes()
        print(f"Icon size: {len(icon_data):,}")
    
    # Build PFS (concatenate files)
    pfs_data = param_data + icon_data
    
    # Align PFS
    while len(pfs_data) % 0x10 != 0:
        pfs_data += b'\x00'
        
    pfs_size = len(pfs_data)
    pfs_digest = sha256(pfs_data)
    
    # Encrypt PFS (GoldHen will decrypt on install)
    pfs_enc = simple_xor(pfs_data, FAKE_KEY)
    
    print(f"PFS size: {pfs_size:#x} ({pfs_size:,})")
    
    # Header
    header = bytearray(0x5A0)
    header[0:4] = PKG_MAGIC
    struct.pack_into('>H', header, 0x04, 0x0001)
    struct.pack_into('>H', header, 0x06, 0x0002)
    struct.pack_into('>I', header, 0x08, 0)  # entry_count = 0 (KEY!)
    struct.pack_into('<H', header, 0x0C, 0)
    struct.pack_into('<H', header, 0x0E, 0)
    struct.pack_into('>I', header, 0x10, 0x1000)
    struct.pack_into('>I', header, 0x14, 0)
    
    # Body
    body_offset = 0x200
    body_size = 0x2000 + pfs_size
    struct.pack_into('>Q', header, 0x18, body_offset)
    struct.pack_into('>Q', header, 0x20, body_size)
    
    header[0x40:0x40+36] = CONTENT_ID.encode('ascii')
    
    struct.pack_into('>I', header, 0x70, 0x0f)
    struct.pack_into('>I', header, 0x74, 0x1b)
    struct.pack_into('>I', header, 0x78, 0x0a0000)
    
    version = int(datetime.datetime.now().strftime('%Y%m%d'))
    struct.pack_into('>I', header, 0x80, version)
    
    # PFS info at 0x400
    struct.pack_into('>I', header, 0x400, 1)
    struct.pack_into('>Q', header, 0x408, 0x2000)  # pfs offset
    struct.pack_into('>Q', header, 0x410, pfs_size)   # pfs size
    struct.pack_into('>Q', header, 0x420, body_size)  # package size (approx)
    struct.pack_into('>I', header, 0x438, pfs_size)  # pfs data size
    header[0x440:0x460] = pfs_digest
    
    # Body digest (placeholder)
    body_digest = sha256(b'\x00' * body_size)
    header[0x160:0x180] = body_digest
    
    # Header signature placeholder at 0xFE0
    header[0xFE0:0x1000] = sha256(bytes(header)[:0x100])
    
    # Body
    body = bytearray(0x2000 + pfs_size)
    
    # ENTRY_KEYS at 0x1000 (RSA encrypted keys - zeros for now)
    body[0x1000:0x1800] = b'\xFA' * 0x800
    
    # Digests at 0x1800
    for i in range(7):
        offset = 0x1800 + i * 0x20
        body[offset:offset+0x20] = sha256(bytes([i] * 32))
    
    # IMAGE_KEY at 0x1A00
    body[0x1A00:0x1B00] = b'\xFA' * 0x100
    
    # PFS at 0x2000
    body[0x2000:0x2000+pfs_size] = pfs_enc
    
    # Combine
    pkg = bytes(header) + bytes(body)
    
    print(f"PKG size: {len(pkg):,} bytes")
    print(f"Entry count: 0 (PFS mode)")
    
    return pkg


def main():
    pkg = build_pkg()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "custom_songs_v4.pkg"
    output.write_bytes(pkg)
    
    print(f"\nCreated: {output}")
    print(f"Size: {output.stat().st_size:,} bytes")
    print(f"Content ID: {CONTENT_ID}")


if __name__ == "__main__":
    main()