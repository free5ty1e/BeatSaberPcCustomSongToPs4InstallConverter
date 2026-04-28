#!/usr/bin/env python3
"""Unlocker PKG v3 - Fixed header format (32-bit LE fields)"""
import struct
import hashlib
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
OUTPUT_DIR = WORK_DIR / "output"

CONTENT_ID = "UP4882-CUSA12878_00-P1S5CUSTOM001"
TITLE_ID = "CUSA12878"
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
    struct.pack_into('<I', sfo, 8, 6)
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

def build_unlocker():
    print("Building unlocker v3")
    
    # Param SFO (smaller payload)
    param_data = create_param_sfo(CONTENT_ID, "Custom Unlock", TITLE_ID)
    
    # Align PFS
    pfs_data = param_data
    while len(pfs_data) % 0x10 != 0:
        pfs_data += b'\x00'
    
    pfs_size = len(pfs_data)
    print(f"PFS size: {pfs_size:#x}")
    
    # Encrypt PFS
    pfs_enc = simple_xor(pfs_data, FAKE_KEY)
    
    # Body 
    body_offset = 0x200
    body = bytearray(0x2000 + pfs_size)
    
    # Fill entry table region with fake hashes
    for i in range(16):
        body[0x1000 + i*0x20:0x1000 + i*0x20 + 0x20] = sha256(bytes([i] * 32))
    
    # Body data at 0x2000 (PFS)
    body[0x2000:0x2000+pfs_size] = pfs_enc
    
    # Header (bigger to include PFS region)
    header = bytearray(0x1000)
    header[0:4] = b'\x7fCNT'
    
    # Flags
    struct.pack_into('>H', header, 4, 0x0001)
    struct.pack_into('>H', header, 6, 0x0002)
    struct.pack_into('>I', header, 8, 0)
    
    # 0x0c: unknown
    struct.pack_into('<I', header, 0x0c, 0x0f000000)
    
    # Entry table - using BE format
    struct.pack_into('>I', header, 0x10, 0x00000000)  # entry offset = 0
    struct.pack_into('>I', header, 0x14, 0x00000000)  # entry count = 0 (PFS mode)
    
    # Body offset and size - using BE format
    body_size = len(body)
    struct.pack_into('>I', header, 0x18, body_offset)  # body at 0x200
    struct.pack_into('>I', header, 0x1c, 0x00000000)
    struct.pack_into('>I', header, 0x20, body_size)
    struct.pack_into('>I', header, 0x24, 0x00000000)
    
    # PFS offset
    pfs_offset = 0x2000
    struct.pack_into('>I', header, 0x28, pfs_offset)
    
    # Content ID
    header[0x30:0x30+36] = CONTENT_ID.encode('ascii')
    
    # Title ID
    header[0x58:0x58+10] = TITLE_ID.encode('ascii')
    
    # DRM, type
    struct.pack_into('<I', header, 0x64, 0x0f000000)  # DRM free
    struct.pack_into('<I', header, 0x68, 0x1b000000)  # DLC
    
    # PFS info at 0x400
    struct.pack_into('<I', header, 0x400, 1)  # pfs count
    struct.pack_into('<Q', header, 0x408, pfs_offset)
    struct.pack_into('<Q', header, 0x410, pfs_size)
    struct.pack_into('<Q', header, 0x420, body_size)
    
    # PFS digest
    pfs_digest = sha256(pfs_data)
    header[0x440:0x460] = pfs_digest
    
    # Body digest
    body_digest = sha256(bytes(body))
    header[0x160:0x180] = body_digest
    
    # Header digest
    header[0xFE0:0x1000] = sha256(bytes(header[:0xFE0]))[:0x100]
    
    # Combine
    pkg = bytes(header) + bytes(body)
    
    print(f"PKG size: {len(pkg):,}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "custom_unlocker_v3.pkg"
    output.write_bytes(pkg)
    print(f"Created: {output}")

if __name__ == "__main__":
    build_unlocker()