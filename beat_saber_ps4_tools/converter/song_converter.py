#!/usr/bin/env python3
"""
Beat Saber PS4 Song Converter
Converts PC BeatSaver songs to PS4 binary format.

Usage:
    python3 converter.py <beat_saver_folder> [--output OUTPUT_DIR]

This tool converts PC custom songs (from BeatSaver) to PS4-compatible format,
following the Backporter PS4-Beat-Saber-Converter methodology.
"""

import json
import struct
import os
import sys
import zlib
import hashlib
import argparse
from pathlib import Path

class BeatSaberSongConverter:
    def __init__(self, output_dir='output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_pc_song(self, song_folder):
        """Load a PC BeatSaver song from folder."""
        song_folder = Path(song_folder)
        
        # Load info.dat
        info_path = song_folder / 'info.dat'
        if not info_path.exists():
            # Try older format: info.json
            info_path = song_folder / 'info.json'
        
        if not info_path.exists():
            raise FileNotFoundError(f"No info.dat/info.json found in {song_folder}")
        
        with open(info_path, 'r', encoding='utf-8') as f:
            self.info = json.load(f)
        
        self.song_folder = song_folder
        self.song_name = self.info.get('_songName', self.info.get('songName', 'Unknown'))
        self.song_subname = self.info.get('_songSubName', self.info.get('songSubName', ''))
        self.song_author = self.info.get('_songAuthorName', self.info.get('authorName', 'Unknown'))
        self.level_author = self.info.get('_levelAuthorName', self.info.get('mapper', ''))
        self.bpm = self.info.get('_beatsPerMinute', self.info.get('beatsPerMinute', 120))
        self.preview_start = self.info.get('_previewStartTime', self.info.get('previewStartTime', 0))
        self.preview_duration = self.info.get('_previewDuration', self.info.get('previewDuration', 10))
        self.song_offset = self.info.get('_songTimeOffset', self.info.get('songTimeOffset', 0))
        self.shuffle = self.info.get('_shuffle', 0)
        self.shuffle_period = self.info.get('_shufflePeriod', 0.5)
        self.environment = self.info.get('_environmentName', self.info.get('environmentName', 'DefaultEnvironment'))
        
        # Audio filename
        audio_path = self.info.get('_songFilename', self.info.get('audioPath', ''))
        self.audio_file = song_folder / audio_path if audio_path else None
        
        # Cover image
        cover_path = self.info.get('_coverImageFilename', self.info.get('coverImagePath', 'cover.png'))
        self.cover_file = song_folder / cover_path
        
        # Difficulty levels
        self.difficulties = self.info.get('_difficultyBeatmapSets', self.info.get('difficultyLevels', []))
        
        return True

    def create_ps4_info_dat(self):
        """Create PS4 Info.dat (binary song metadata)."""
        # PS4 Info.dat format:
        # The PS4 format is binary with null-terminated strings and fixed-size fields
        
        buffer = bytearray()
        
        # Version string ("2.0.0" for v2 format)
        version = "2.0.0\0"
        buffer.extend(version.encode('ascii'))
        
        # Null padding to fixed size (0x80 bytes typical for string fields)
        def write_string(s, max_len=128):
            s = str(s) if s else ''
            encoded = s.encode('utf-8') + b'\x00'
            if len(encoded) > max_len:
                encoded = encoded[:max_len]
            buffer.extend(encoded)
            # Pad to max_len
            while len(buffer) % max_len != 0:
                buffer.append(0)
        
        # Song name
        write_string(self.song_name)
        
        # Song sub name
        write_string(self.song_subname)
        
        # Song author name
        write_string(self.song_author)
        
        # Level author name
        write_string(self.level_author)
        
        # BPM (float)
        buffer.extend(struct.pack('<f', self.bpm))
        
        # Preview start time (float)
        buffer.extend(struct.pack('<f', self.preview_start))
        
        # Preview duration (float)
        buffer.extend(struct.pack('<f', self.preview_duration))
        
        # Song time offset (float)
        buffer.extend(struct.pack('<f', self.song_offset))
        
        # Shuffle (float)
        buffer.extend(struct.pack('<f', float(self.shuffle)))
        
        # Shuffle period (float)
        buffer.extend(struct.pack('<f', self.shuffle_period))
        
        # Environment name
        write_string(self.environment)
        
        # Song filename
        audio_name = self.audio_file.name if self.audio_file else 'song.ogg'
        write_string(audio_name)
        
        # Cover image filename
        cover_name = self.cover_file.name if self.cover_file else 'cover.png'
        write_string(cover_name)
        
        return bytes(buffer)

    def create_ps4_beatmap(self, difficulty_data, difficulty_name, difficulty_rank):
        """Convert PC difficulty JSON to PS4 binary beatmap format.
        
        The PS4 binary format stores note/event/obstacle data in a compact binary format.
        Based on Backporter's converter, the format uses:
        - 4-byte count for number of items
        - 4-byte type/flags
        - Binary-encoded note data
        """
        buffer = bytearray()
        
        # Version
        version = "2.0.0\0"
        buffer.extend(version.encode('ascii'))
        # Pad to 0x20 bytes
        while len(buffer) < 0x20:
            buffer.append(0)
        
        # BPM (float)
        buffer.extend(struct.pack('<f', self.bpm))
        
        # Note jump speed
        njs = difficulty_data.get('_noteJumpMovementSpeed', 
                                  difficulty_data.get('_noteJumpSpeed', 10))
        buffer.extend(struct.pack('<f', njs))
        
        # Note jump start beat offset
        njs_start = difficulty_data.get('_noteJumpStartBeatOffset', 0)
        buffer.extend(struct.pack('<f', njs_start))
        
        # Shuffle
        buffer.extend(struct.pack('<f', float(self.shuffle)))
        
        # Shuffle period
        buffer.extend(struct.pack('<f', self.shuffle_period))
        
        # Notes array
        notes = difficulty_data.get('_notes', [])
        buffer.extend(struct.pack('<I', len(notes)))
        for note in notes:
            # Color note data:
            # time (float), lineIndex (byte), lineLayer (byte), type (byte), color (byte), 
            # cutDirection (byte), angleOffset (float), tunnel (byte)
            time = float(note.get('_time', 0))
            line_index = int(note.get('_lineIndex', 0))
            line_layer = int(note.get('_lineLayer', 0))
            note_type = int(note.get('_type', 0))
            color = int(note.get('_color', 0))
            cut_dir = int(note.get('_cutDirection', 0))
            angle_offset = float(note.get('_angleOffset', 0))
            
            buffer.extend(struct.pack('<f', time))
            buffer.extend(struct.pack('<BBBB', line_index, line_layer, note_type, color))
            buffer.extend(struct.pack('<Bf', cut_dir, angle_offset))
            buffer.append(0)  # tunnel/extra byte
        
        # Obstacles array
        obstacles = difficulty_data.get('_obstacles', [])
        buffer.extend(struct.pack('<I', len(obstacles)))
        for obs in obstacles:
            time = float(obs.get('_time', 0))
            obs_type = int(obs.get('_type', 0))
            duration = float(obs.get('_duration', 0))
            line_index = int(obs.get('_lineIndex', 0))
            y_mult = float(obs.get('_lineLayer', 0))  # Height in PS4 format
            
            buffer.extend(struct.pack('<f', time))
            buffer.extend(struct.pack('<B', obs_type))
            buffer.extend(struct.pack('<f', duration))
            buffer.extend(struct.pack('<B', line_index))
            buffer.extend(struct.pack('<f', y_mult))
        
        # Events array  
        events = difficulty_data.get('_events', [])
        buffer.extend(struct.pack('<I', len(events)))
        for evt in events:
            time = float(evt.get('_time', 0))
            type_val = int(evt.get('_type', 0))
            value = float(evt.get('_value', 0))
            
            buffer.extend(struct.pack('<f', time))
            buffer.extend(struct.pack('<Bi', type_val, int(value)))
        
        return bytes(buffer)

    def convert_song(self, song_folder, output_name=None):
        """Convert a complete PC song to PS4 format."""
        song_folder = Path(song_folder)
        
        if output_name is None:
            # Sanitize song name for output
            safe_name = self.song_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            output_name = safe_name
        
        song_output = self.output_dir / output_name
        song_output.mkdir(parents=True, exist_ok=True)
        
        # Load the song
        self.load_pc_song(song_folder)
        
        # Create output directories
        (song_output / 'audio').mkdir(exist_ok=True)
        (song_output / 'cover').mkdir(exist_ok=True)
        
        # Convert and copy audio
        if self.audio_file and self.audio_file.exists():
            # Convert audio to PS4-compatible format
            self.convert_audio(self.audio_file, song_output / 'audio' / 'song')
        else:
            print(f"  Warning: No audio file found")
        
        # Copy cover image
        if self.cover_file.exists():
            import shutil
            shutil.copy(self.cover_file, song_output / 'cover' / self.cover_file.name)
        else:
            print(f"  Warning: No cover image found")
        
        # Create Info.dat
        info_dat = self.create_ps4_info_dat()
        with open(song_output / 'Info.dat', 'wb') as f:
            f.write(info_dat)
        
        # Create difficulty files
        difficulty_map = {
            'easy': 1, 'normal': 3, 'hard': 5, 'expert': 7, 'expertplus': 9
        }
        
        # Handle both v2 (_difficultyBeatmapSets) and v3 (flat array) formats
        beatmaps = self.difficulties
        
        # For v2 format with characteristic grouping
        if beatmaps and isinstance(beatmaps[0], dict) and '_beatmapCharacteristicName' in beatmaps[0]:
            # v2 format: _difficultyBeatmapSets
            for char_set in beatmaps:
                for diff in char_set.get('_difficultyBeatmaps', []):
                    diff_name = diff.get('_difficulty', 'Expert').lower().replace('plus', '+')
                    if diff_name.endswith('+'):
                        diff_name = diff_name.replace('+', '+')
                    diff_rank = diff.get('_difficultyRank', 5)
                    beatmap_file = diff.get('_beatmapFilename', f'{diff_name}.dat')
                    
                    # Load the actual difficulty data
                    diff_path = self.song_folder / beatmap_file.replace('.dat', '.json')
                    if diff_path.exists():
                        with open(diff_path, 'r') as f:
                            diff_data = json.load(f)
                        ps4_dat = self.create_ps4_beatmap(diff_data, diff_name, diff_rank)
                        
                        # Use standardized name
                        output_diff_name = f"{diff_name.replace('+', 'Plus').replace(' ', '')}.dat"
                        with open(song_output / output_diff_name, 'wb') as f:
                            f.write(ps4_dat)
        
        # For v3 format (flat array with 'difficulty' key)
        elif beatmaps and isinstance(beatmaps[0], dict) and 'difficulty' in beatmaps[0]:
            # v3 format
            for diff in beatmaps:
                diff_name = diff.get('difficulty', 'Expert').lower()
                diff_rank = diff.get('difficultyRank', 5)
                json_path = diff.get('jsonPath', '')
                
                # Load difficulty file
                diff_path = self.song_folder / json_path
                if diff_path.exists():
                    with open(diff_path, 'r') as f:
                        diff_data = json.load(f)
                    ps4_dat = self.create_ps4_beatmap(diff_data, diff_name, diff_rank)
                    
                    output_diff_name = f"{diff_name.replace('+', 'Plus').replace(' ', '')}.dat"
                    with open(song_output / output_diff_name, 'wb') as f:
                        f.write(ps4_dat)
        
        # Create song metadata file
        metadata = {
            'songName': self.song_name,
            'songSubName': self.song_subname,
            'songAuthor': self.song_author,
            'levelAuthor': self.level_author,
            'bpm': self.bpm,
            'environment': self.environment,
            'difficulties': [d.get('_difficulty', d.get('difficulty', 'Unknown')) for d in 
                            (beatmaps[0].get('_difficultyBeatmaps', beatmaps) if beatmaps else [])],
        }
        
        with open(song_output / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"  Converted to {song_output}")
        return song_output

    def convert_audio(self, audio_path, output_path):
        """Convert audio to PS4-compatible format.
        
        PS4 Beat Saber uses:
        - Unity AudioClip format internally
        - FMOD audio engine
        - Support for OGG Vorbis (PC format)
        
        For now, we copy the audio and note the format.
        Full conversion requires Unity asset bundle creation with UABE.
        """
        audio_path = Path(audio_path)
        
        # Check audio format
        ext = audio_path.suffix.lower()
        
        if ext == '.ogg':
            # OGG is natively supported by Unity/Beat Saber
            import shutil
            shutil.copy(audio_path, f"{output_path}.ogg")
            print(f"  Audio: Copied OGG file")
            
        elif ext in ['.wav', '.mp3']:
            # These need conversion to OGG or WAV
            # For now, copy as-is and note it needs conversion
            import shutil
            shutil.copy(audio_path, f"{output_path}{ext}")
            print(f"  Audio: Copied {ext[1:].upper()} (needs conversion to OGG)")
            
        else:
            print(f"  Audio: Unsupported format {ext}")

    def batch_convert(self, songs_folder, pattern='*'):
        """Convert all songs in a folder."""
        songs_folder = Path(songs_folder)
        results = []
        
        for song_dir in songs_folder.glob(pattern):
            if song_dir.is_dir():
                try:
                    print(f"\nConverting: {song_dir.name}")
                    result = self.convert_song(song_dir)
                    results.append(result)
                except Exception as e:
                    print(f"  Error: {e}")
        
        print(f"\n\nConverted {len(results)} songs")
        return results


def main():
    parser = argparse.ArgumentParser(description='Convert PC BeatSaver songs to PS4 format')
    parser.add_argument('song_folder', help='Path to BeatSaver song folder')
    parser.add_argument('--output', '-o', default='output', help='Output directory')
    parser.add_argument('--list', '-l', help='Batch convert all songs in folder')
    parser.add_argument('--api', help='Download song by BeatSaver hash or key')
    
    args = parser.parse_args()
    
    converter = BeatSaberSongConverter(output_dir=args.output)
    
    if args.list:
        # Batch convert
        results = converter.batch_convert(args.list)
        print(f"\nConverted {len(results)} songs to {args.output}/")
    else:
        # Single song convert
        try:
            result = converter.convert_song(args.song_folder)
            print(f"\nSuccess! Converted to {result}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()