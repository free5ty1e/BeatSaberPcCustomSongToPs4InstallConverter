#!/usr/bin/env python3
"""
PS4 PKG Builder
Creates PS4 package files (FPKG) for DLC content

Based on/Inspired by: orbis-pub-gen.exe (Sony SDK)
- Original: https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87
- This is a Python reimplementation for Linux/server environments

PKG Format Reference:
- PS4 Development Wiki: https://www.ps4dev.wiki/ps4pkg
- flat_z's research: https://github.com/flat-z
"""
import struct
import os
import hashlib
import zlib
from pathlib import Path

class PS4PKGBuilder:
    """Build PS4 PKG files for DLC"""

    # PKG magic
    MAGIC = b'\x7F\xD8\xCF\x63'  # SCE, PKG

    def __init__(self, content_id=None):
        self.content_id = content_id or "UP8802-CUSA12878_00-BSCUSTOMSONGS01"
        self.title = "Beat Saber Custom Songs"
        self.files = []  # List of (path, data) tuples
        self.output_path = None

    def add_file(self, filepath, data=None):
        """Add a file to the PKG"""
        if data is None:
            with open(filepath, 'rb') as f:
                data = f.read()
        self.files.append((filepath, data))

    def add_directory(self, dirpath):
        """Add all files from a directory recursively"""
        dirpath = Path(dirpath)
        for filepath in dirpath.rglob('*'):
            if filepath.is_file():
                rel_path = filepath.relative_to(dirpath)
                self.add_file(filepath, None)

    def build(self):
        """Build the PKG binary data"""
        import io

        # Calculate sizes
        header_size = 0xC0  # Fixed header size
        toc_entries = []
        data_offset = header_size + (len(self.files) * 0x20)  # 0x20 per TOC entry

        # Align data offset
        if data_offset % 0x10 != 0:
            data_offset = (data_offset // 0x10 + 1) * 0x10

        # First pass: collect file info
        total_size = data_offset
        for filepath, data in self.files:
            toc_entries.append({
                'name': filepath,
                'data': data,
                'offset': total_size,
                'size': len(data)
            })
            total_size += len(data)
            # Align to 0x10
            if total_size % 0x10 != 0:
                total_size = (total_size // 0x10 + 1) * 0x10

        # Build header
        pkg = io.BytesIO()

        # Entry count
        entry_count = len(self.files)

        # Data size (everything after header)
        data_size = total_size - header_size

        # Write header
        pkg.write(self.MAGIC)  # Magic (4)
        pkg.write(b'\x01')  # Format version (1)
        pkg.write(b'\x00')  # Type (0 = pkg)
        pkg.write(b'\x00')  # Flags (0)
        pkg.write(struct.pack('<I', 0x00480000))  # Data offset
        pkg.write(struct.pack('<I', data_size))  # Data size
        pkg.write(struct.pack('<I', entry_count))  # Entry count
        pkg.write(b'\x00' * 0x10)  # Unknown
        pkg.write(struct.pack('<I', 0))  # Metadata offset
        pkg.write(struct.pack('<I', 0))  # Metadata size
        pkg.write(b'\x00' * 0x3C)  # Padding

        # Content ID (48 bytes, null-padded)
        content_id_bytes = self.content_id.encode('utf-8')
        pkg.write(content_id_bytes[:48].ljust(48, b'\x00'))

        # More header fields
        pkg.write(struct.pack('<Q', 0))  # Title ID
        pkg.write(struct.pack('<Q', 0))  # Type
        pkg.write(struct.pack('<Q', 0x05005000))  # System version
        pkg.write(struct.pack('<Q', 0x00010030))  # App version
        pkg.write(b'\x00' * 0x18)  # Padding

        # Table of Contents
        for entry in toc_entries:
            name = entry['name'].replace('\\', '/')  # PS4 uses forward slashes
            name_bytes = name.encode('utf-8')

            # Flags (directory bit, etc)
            flags = 0
            if entry['name'].endswith('/'):
                flags |= 0x10  # Directory

            pkg.write(struct.pack('<Q', flags))  # Flags
            pkg.write(struct.pack('<Q', entry['offset']))  # Data offset
            pkg.write(struct.pack('<I', entry['size']))  # Size
            pkg.write(struct.pack('<I', len(name_bytes) + 1))  # Name size
            pkg.write(name_bytes)
            pkg.write(b'\x00')  # Null terminator
            pkg.write(b'\x00' * (0x20 - (len(name_bytes) + 1) % 0x20))  # Pad to 0x20

        # Fill remaining header space
        current_pos = pkg.tell()
        if current_pos < header_size:
            pkg.write(b'\x00' * (header_size - current_pos))

        # File data
        for entry in toc_entries:
            data = entry['data']
            pkg.write(data)
            # Align to 0x10
            padding = (0x10 - len(data) % 0x10) % 0x10
            if padding:
                pkg.write(b'\x00' * padding)

        return pkg.getvalue()

    def save(self, output_path):
        """Save PKG to file"""
        self.output_path = output_path
        pkg_data = self.build()

        with open(output_path, 'wb') as f:
            f.write(pkg_data)

        print(f"Created PKG: {output_path}")
        print(f"  Content ID: {self.content_id}")
        print(f"  Files: {len(self.files)}")
        print(f"  Size: {len(pkg_data):,} bytes")

        return output_path

def create_dlc_pkg(dlc_folder, content_id, output_path):
    """Create DLC PKG from folder"""
    builder = PS4PKGBuilder(content_id)

    # Add files from folder
    dlc_path = Path(dlc_folder)
    for filepath in dlc_path.rglob('*'):
        if filepath.is_file():
            rel_path = filepath.relative_to(dlc_path)
            with open(filepath, 'rb') as f:
                builder.add_file(str(rel_path), f.read())

    return builder.save(output_path)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Create PS4 PKG for DLC')
    parser.add_argument('--content-id', '-c', default='UP8802-CUSA12878_00-BSCUSTOMSONGS01',
                        help='Content ID')
    parser.add_argument('--folder', '-f', required=True,
                        help='Folder containing DLC files')
    parser.add_argument('--output', '-o', required=True,
                        help='Output PKG path')

    args = parser.parse_args()

    create_dlc_pkg(args.folder, args.content_id, args.output)

if __name__ == "__main__":
    main()