#!/usr/bin/env python3
"""
PARAM.SFO Creator for PS4 DLC
Creates the system file that defines DLC metadata

Based on/Inspired by: orbis-pub-sfo.exe (Sony SDK)
- Original: https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87
- This is a Python reimplementation for Linux/server environments

PARAM.SFO Format Reference: PS4 Development Wiki
https://www.ps4dev.wiki/param.sfo
"""
import struct
import os
from pathlib import Path

class ParamSFO:
    """Create PS4 PARAM.SFO for Additional Content (DLC)"""

    def __init__(self):
        self.entries = {}
        self.title = "Beat Saber Custom Songs"
        self.title_id = "UP8802-CUSA12878_00-BSCUSTOMSONGS"
        self.category = 2  # 2 = Additional Content (AC)

    def set_title(self, title):
        """Set DLC title"""
        self.title = title

    def set_content_id(self, content_id):
        """Set Content ID (e.g., UP8802-CUSA12878_00-BSCUSTOMSONGS01)"""
        self.title_id = content_id

    def create(self):
        """Create PARAM.SFO binary data"""
        # PARAM.SFO structure:
        # Header: magic, version, key_table_offset, data_table_offset, num_entries
        # Key Table: null-terminated strings
        # Data Table: type, size, offset, data

        entries = [
            ("Category", self.category),
            ("ContentID", self.title_id),
            ("TITLE", self.title),
            ("TITLE_0", self.title),
            ("VERSION", "01.00"),
            ("APP_VER", "01.00"),
            ("SYSTEM_VER", "05.0500"),  # Firmware version
        ]

        # Calculate offsets
        key_table_offset = 20  # Header size
        data_offset_start = key_table_offset

        # First pass: calculate sizes
        key_table_size = 0
        for name, value in entries:
            key_table_size += len(name) + 1  # null-terminated

        data_table_offset = key_table_offset + key_table_size

        # Align to 4 bytes
        if data_table_offset % 4 != 0:
            padding = 4 - (data_table_offset % 4)
            data_table_offset += padding

        # Build key table
        key_table = bytearray()
        key_offsets = []
        current_offset = 0

        for name, value in entries:
            key_offsets.append(current_offset)
            key_table.extend(name.encode('utf-8'))
            key_table.append(0)  # null terminator
            current_offset = len(key_table)

        # Pad key table to data_table_offset
        while len(key_table) < data_table_offset:
            key_table.append(0)

        # Build data table
        data_table = bytearray()
        data_offsets = []
        current_data_offset = 0

        for name, value in entries:
            data_offsets.append(len(data_table))

            if isinstance(value, int):
                # Integer type (0x04)
                data_table.append(0x04)  # type: integer
                data_table.extend(struct.pack('<I', 4))  # size
                data_table.extend(struct.pack('<I', current_data_offset))  # offset
                data_table.extend(struct.pack('<I', value))  # value
                current_data_offset += 4
            else:
                # String type (0x01)
                value_bytes = value.encode('utf-8')
                data_table.append(0x01)  # type: string
                data_table.extend(struct.pack('<I', len(value_bytes) + 1))  # size
                data_table.extend(struct.pack('<I', current_data_offset))  # offset
                data_table.extend(value_bytes)
                data_table.append(0)  # null terminator
                current_data_offset += len(value_bytes) + 1

        # Build header
        header = bytearray(20)
        struct.pack_into('<I', header, 0, 0x46535000)  # Magic: PSFM
        struct.pack_into('<I', header, 4, 0x00000101)  # Version
        struct.pack_into('<I', header, 8, key_table_offset)  # Key table offset
        struct.pack_into('<I', header, 12, data_table_offset)  # Data table offset
        struct.pack_into('<I', header, 16, len(entries))  # Num entries

        # Combine all parts
        param_sfo = header + key_table + data_table

        return bytes(param_sfo)

    def save(self, filepath):
        """Save PARAM.SFO to file"""
        data = self.create()
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"Created: {filepath}")
        return True

def create_dlc_paramsfo(content_id, title, output_path):
    """Convenience function to create DLC PARAM.SFO"""
    paramsfo = ParamSFO()
    paramsfo.set_content_id(content_id)
    paramsfo.set_title(title)
    paramsfo.save(output_path)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Create PS4 PARAM.SFO for DLC')
    parser.add_argument('--content-id', '-c', default='UP8802-CUSA12878_00-BSCUSTOMSONGS01',
                        help='Content ID (e.g., UP8802-CUSA12878_00-BSCUSTOMSONGS01)')
    parser.add_argument('--title', '-t', default='Beat Saber Custom Songs',
                        help='DLC Title')
    parser.add_argument('--output', '-o', default='param.sfo',
                        help='Output file path')

    args = parser.parse_args()

    create_dlc_paramsfo(args.content_id, args.title, args.output)

if __name__ == "__main__":
    main()