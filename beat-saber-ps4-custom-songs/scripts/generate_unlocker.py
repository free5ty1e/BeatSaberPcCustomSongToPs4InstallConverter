#!/usr/bin/env python3
"""
Generate Unlocker PKG for Beat Saber
Enables custom DLC installation for the game
"""
import struct
import hashlib
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
OUTPUT_DIR = WORK_DIR / "output"
GAME_ID = "CUSA12878"
CONTENT_ID = "UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX"


def create_paramsfo(content_id, title):
    """Create proper PARAM.SFO."""
    buf = bytearray(0x400)
    buf[0:4] = b'PSF\x00'
    struct.pack_into('<I', buf, 4, 0x00010100)
    struct.pack_into('<I', buf, 8, 0x18)
    struct.pack_into('<I', buf, 12, 6)
    
    entries = [
        (b"CATEGORY", 0x04, b"ac"),
        (b"CONTENT_ID", 0x24, content_id.encode('utf-8')),
        (b"FORMAT", 0x04, b"obs"),
        (b"TITLE", 0x2C, title.encode('utf-8')),
        (b"TITLE_ID", 0x18, GAME_ID.encode('utf-8')),
        (b"VERSION", 0x04, b"01.00"),
    ]
    
    table_start = 0x18
    data_offset = table_start + len(entries) * 0x10
    
    for i, (name, typ, data) in enumerate(entries):
        base = table_start + i * 0x10
        buf[base:base+len(name)] = name
        struct.pack_into('<H', buf, base + len(name), typ)
        struct.pack_into('<H', buf, base + len(name) + 2, 0)
        struct.pack_into('<I', buf, base + 8, len(data))
        struct.pack_into('<I', buf, base + 12, data_offset)
        buf[data_offset:data_offset+len(data)] = data
        data_offset += len(data) + (4 - len(data) % 4) % 4
    
    return bytes(buf[:data_offset])


def create_icon0():
    """Get icon from reference."""
    ref_icon = WORK_DIR / "ref_extract/sce_sys/icon0.png"
    if ref_icon.exists():
        return ref_icon.read_bytes()
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 100


def create_pkg(content_id, title, file_entries):
    """Create a proper DLC PKG."""
    
    num_entries = len(file_entries)
    header_size = 0x1000
    toc_size = num_entries * 0x20
    data_start = header_size + toc_size
    
    if data_start % 0x10:
        data_start = (data_start // 0x10 + 1) * 0x10
    
    body_size = sum(len(d) for _, d in file_entries)
    final_size = data_start + body_size + 0x100
    
    buf = bytearray(final_size)
    
    buf[0:4] = b'\x7f\x43\x4e\x54'
    struct.pack_into('>I', buf, 0x04, 0x00000001)
    struct.pack_into('>I', buf, 0x08, 0x00000000)
    struct.pack_into('>I', buf, 0x0C, 0x0000000f)
    struct.pack_into('>I', buf, 0x10, 0)
    struct.pack_into('>I', buf, 0x14, num_entries)
    struct.pack_into('>I', buf, 0x18, num_entries)
    struct.pack_into('>H', buf, 0x1C, 0)
    struct.pack_into('>H', buf, 0x1E, num_entries)
    struct.pack_into('>I', buf, 0x20, header_size)
    struct.pack_into('>I', buf, 0x24, 0)
    struct.pack_into('<Q', buf, 0x28, data_start)
    struct.pack_into('<Q', buf, 0x30, body_size)
    struct.pack_into('<Q', buf, 0x38, 0x30)
    struct.pack_into('<Q', buf, 0x40, 0x24)
    
    cid_bytes = content_id.encode('utf-8')[:36].ljust(36, b'\x00')
    buf[0x48:0x48+36] = cid_bytes
    
    struct.pack_into('>I', buf, 0x70, 0x0000000f)
    struct.pack_into('>I', buf, 0x74, 0x0000001b)
    struct.pack_into('>I', buf, 0x78, 0x0a000000)
    struct.pack_into('>I', buf, 0x7C, 0)
    struct.pack_into('>I', buf, 0x80, 0x1c59c940)
    struct.pack_into('>I', buf, 0x84, 0)
    for offset in [0x88, 0x8C, 0x90, 0x94]:
        struct.pack_into('>I', buf, offset, 0)
    struct.pack_into('>I', buf, 0x98, 0)
    struct.pack_into('>I', buf, 0x9C, 0)
    struct.pack_into('<Q', buf, 0x430, final_size)
    
    toc_offset = header_size
    data_offset = data_start
    
    for name, data in file_entries:
        name_bytes = name.encode('utf-8')
        struct.pack_into('<Q', buf, toc_offset, 0)
        struct.pack_into('<Q', buf, toc_offset + 8, data_offset)
        struct.pack_into('<I', buf, toc_offset + 16, len(data))
        struct.pack_into('<I', buf, toc_offset + 20, len(name_bytes) + 1)
        buf[toc_offset + 24:toc_offset + 24 + len(name_bytes)] = name_bytes
        buf[toc_offset + 24 + len(name_bytes)] = 0
        toc_offset += 0x20
        data_offset += len(data)
    
    file_offset = data_start
    for name, data in file_entries:
        buf[file_offset:file_offset + len(data)] = data
        file_offset += len(data)
    
    pkg_without_digest = bytes(buf[:data_start + body_size])
    digest = hashlib.sha256(pkg_without_digest).digest()
    buf[data_start + body_size:data_start + body_size + 0x100] = digest + b'\x00' * (0x100 - len(digest))
    
    return bytes(buf)


def generate_unlocker():
    """Generate unlocker PKG."""
    print("Generating unlocker PKG...")
    
    file_entries = [
        ("PARAM_SFO", create_paramsfo(CONTENT_ID, "Beat Saber Unlocker")),
        ("ICON0_PNG", create_icon0()),
    ]
    
    pkg_data = create_pkg(CONTENT_ID, "Beat Saber Unlocker", file_entries)
    
    output_path = OUTPUT_DIR / "UP4882-CUSA12878_00-BSCUSTOMSONG-unlock.pkg"
    with open(output_path, "wb") as f:
        f.write(pkg_data)
    
    print(f"Created: {output_path}")
    print(f"Size: {len(pkg_data):,} bytes")
    
    return output_path


if __name__ == "__main__":
    generate_unlocker()