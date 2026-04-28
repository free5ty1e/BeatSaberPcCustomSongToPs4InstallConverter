#!/usr/bin/env python3
"""Create unlocker PKG for Beat Saber custom songs"""
import struct
import hashlib
import datetime
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")

PKG_MAGIC = b'\x7f\x43\x4e\x54'

def sha256(data):
    return hashlib.sha256(data).digest()

CONTENT_ID = "UP4882-CUSA12878_00-P1S5CUSTOM001"
TITLE_ID = "CUSA12878"

def create_unlocker():
    pkg = bytearray(0x6A000)
    
    # Header
    pkg[0:4] = PKG_MAGIC
    struct.pack_into('>H', pkg, 0x04, 0x0001)
    struct.pack_into('>H', pkg, 0x06, 0x0002)
    struct.pack_into('>I', pkg, 0x08, 9)
    struct.pack_into('<H', pkg, 0x0C, 9)
    struct.pack_into('<H', pkg, 0x0E, 9)
    struct.pack_into('>I', pkg, 0x10, 0x1000)
    struct.pack_into('>I', pkg, 0x14, 9 * 0x20)
    struct.pack_into('>Q', pkg, 0x18, 0x200)
    struct.pack_into('>Q', pkg, 0x20, 0x70000)
    pkg[0x40:0x40+36] = CONTENT_ID.encode('ascii')
    struct.pack_into('>I', pkg, 0x70, 0x0f)
    struct.pack_into('>I', pkg, 0x74, 0x1b)
    struct.pack_into('>I', pkg, 0x78, 0x0a0000)
    version_date = int(datetime.datetime.now().strftime('%Y%m%d'))
    struct.pack_into('>I', pkg, 0x80, version_date)
    
    # Entry table
    entries = [
        (0x01, 0x3000, 0x40),
        (0x10, 0x3040, 0x800),
        (0x20, 0x3840, 0x100),
        (0x80, 0x3940, 0x180),
        (0x100, 0x3AC0, 0x100),
        (0x200, 0x3CC0, 0x100),
        (0x400, 0x3EC0, 0x100),
        (0x500, 0x3FC0, 0x100),
        (0x600, 0x40C0, 0x1000),
    ]
    
    for i, (eid, off, size) in enumerate(entries):
        te = 0x1000 + i * 0x20
        struct.pack_into('>I', pkg, te, eid)
        struct.pack_into('>Q', pkg, te + 4, off)
        struct.pack_into('>I', pkg, te + 12, size)
    
    # Entry data
    pkg[0x3000:0x3020] = sha256(b'\x00' * 0x40)
    
    # ENTRY_KEYS (zeros - will be rejected but has structure)
    pkg[0x3040:0x3840] = b'\x00' * 0x800
    for i in range(7):
        pkg[0x3400 + i*0x20:0x3420 + i*0x20] = sha256(bytes([i] * 32))
    
    # IMAGE_KEY
    pkg[0x3840:0x3940] = b'\xFA' * 0x100
    
    # GENERAL_DIGESTS
    pkg[0x3940:0x3960] = sha256(b'\x00' * 0x5A0)
    pkg[0x3960:0x3980] = sha256(b'\x00' * 0x100)
    content_data = CONTENT_ID.encode() + b'\x00\x00\x00\x00' + struct.pack('>II', 0x0f, 0x1b)
    pkg[0x3980:0x39A0] = sha256(content_data)
    pkg[0x39A0:0x39C0] = sha256(b'\x00' * 0x800)
    
    # METAS
    pkg[0x3AC0:0x3BC0] = b'\x00' * 0x100
    
    # ENTRY_NAMES
    names = b'param.sfo\x00license.dat\x00license.info\x00'
    pkg[0x3CC0:0x3CC0+len(names)] = names
    
    # LICENSE_DAT - ENTITLEMENT!
    pkg[0x3EC0:0x3EC0+4] = b'RIF\x00'
    struct.pack_into('<I', pkg, 0x3EC4, 0x00000001)
    pkg[0x3ED0:0x3ED0+len(CONTENT_ID)] = CONTENT_ID.encode()
    pkg[0x3EF8:0x3EFA] = b'\x00\x00'
    
    # LICENSE_INFO
    pkg[0x3FC0:0x3FD0] = b'license info'
    
    # PARAM_SFO
    sfo = bytearray(0x3000)
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
    sfo[0x1808:0x1808+len(CONTENT_ID)] = CONTENT_ID.encode()
    sfo[0x1840:0x1842] = b'ob\x00'
    title = "Custom Unlock"
    sfo[0x1850:0x1860] = title.encode('utf-16-le') + b'\x00\x00'
    sfo[0x18C0:0x18D0] = TITLE_ID.encode('utf-16-le') + b'\x00\x00'
    sfo[0x1910:0x1913] = b'01.00'
    
    pkg[0x40C0:0x50C0] = sfo
    
    # Body digest
    body_digest = sha256(bytes(pkg[0x200:]))
    pkg[0x160:0x180] = body_digest
    
    return bytes(pkg[:0x6A000])

if __name__ == "__main__":
    unlocker = create_unlocker()
    output = WORK_DIR / "output" / "custom_unlocker.pkg"
    output.write_bytes(unlocker)
    print(f"Created: {output}")
    print(f"Size: {len(unlocker):,} bytes")