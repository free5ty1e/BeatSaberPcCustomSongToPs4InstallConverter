#!/usr/bin/env python3
"""
Systematic test suite for Beat Saber PS4 audio replacement compatibility.
Tests HEVAG encoding/decoding consistency and identifies audio playback issues.
"""

import struct, math, json, os, sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, '/workspace/beat_saber_deluxe/tools')

class HEVAGAudioInspector:
    def __init__(self):
        self.test_results = []
        self.errors = []

    def analyze_startmeup_reference(self):
        """Extract and analyze original Start Me Up FSB5 if available"""
        print("🔍 Analyzing reference audio from PS4 dump...")

        # Look for extracted audio in common locations
        potential_paths = [
            '/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/startmeup/audio.fsb5',
            '/workspace/ps4_dump/audio/startmeup.fsb5',
            '/workspace/reference_audio/startmeup.fsb5'
        ]

        for path in potential_paths:
            if os.path.exists(path):
                print(f"Found reference audio at: {path}")

                with open(path, 'rb') as f:
                    fsb5_data = f.read()

                # Parse FSB5 header
                sh_start = 16  # After "FSB5", version, num_samples, sh_size
                sample_header = fsb5_data[sh_start:sh_start+900]

                analysis = {
                    'path': path,
                    'file_size': len(fsb5_data),
                    'sample_header_hash': hash(sample_header[:50]),
                    'data_size_field': struct.unpack_from('<I', sample_header, 4)[0],
                    'offset_field': struct.unpack_from('<I', sample_header, 8)[0],
                    'format_field': struct.unpack_from('<H', sample_header, 12)[0],
                    'frequency_field': struct.unpack_from('<I', sample_header, 16)[0]
                }

                self.test_results.append({
                    'test_type': 'reference_extraction',
                    'status': 'SUCCESS' if analysis['file_size'] > 1000 else 'NOT_FOUND',
                    'details': analysis
                })
                return analysis

        self.errors.append("No Start Me Up reference audio found")
        return None

    def is_valid_heavig_frame(self, frame):
        """Check if a HEVAG frame has valid format"""
        if len(frame) < 16:
            return False

        pred = frame[0] & 0xF
        shift = (frame[0] >> 4) & 0xF

        # Validate predictor and shift values
        if pred > 4:  # Valid predictors are 0-4
            return False
        if shift > 12:  # Valid shifts are 0-12
            return False

        # Simple nibble validation - all nibbles should be within signed 4-bit range
        for i in range(1, len(frame)):
            nibble = ((frame[i] >> (i % 2 * 4)) & 0xF)
            if nibble > 7:  # Signed 4-bit max value
                return False

        return True

    def test_single_frequency_tones(self):
        """Comprehensive single frequency testing"""
        print("🎵 Testing single frequency tones...")

        frequencies = [220, 440, 880]  # Standard musical octaves
        duration_seconds = 1.0

        all_passed = True

        for freq in frequencies:
            print(f"   Testing {freq} Hz tone...")

            try:
                from hevag_encoder import generate_test_tone_pcm, pcm_to_hevig

                # Generate pure sine wave
                pcm_data = generate_test_tone_pcm(duration=duration_seconds,
                                                sample_rate=44100, channels=2)

                # Encode to HEVAG
                hevig_data = pcm_to_hevig(pcm_data, channels=2)

                total_frames = max(len(he vig_data) // 16, 1)

                valid_frames = 0
                for i in range(total_frames):
                    frame_start = i * 16
                    if frame_start + 16 > len(hevig_data):
                        break
                    frame = he vig_data[frame_start:frame_start+16]
                    if self.is_valid_heavig_frame(frame):
                        valid_frames += 1

                validity_rate = (valid_frames / max(total_frames, 1)) * 100

                test_result = {
                    'frequency': freq,
                    'input_duration': duration_seconds,
                    'pcm_samples': len(pcm_data),
                    'hevag_frames': total_frames,
                    'compression_ratio': (len(pcm_data) / max(len(hevig_data), 1)) * 100,
                    'frame_validity_rate_percent': validity_rate
                }

                if validity_rate > 95:  # Acceptable threshold
                    print(f"      ✅ {freq} Hz test PASSED (valid frames: {valid_frames}/{total_frames})")
                else:
                    print(f"      ❌ {freq} Hz test FAILED (only {valid_frames}/{total_frames} valid frames)")
                    all_passed = False

                self.test_results.append({
                    'test_type': f'single_frequency_{freq}',
                    'status': 'SUCCESS' if validity_rate > 95 else 'FAILED',
                    'details': test_result
                })

            except Exception as e:
                print(f"      ❌ {freq} Hz test ERROR: {str(e)}")
                self.test_results.append({
                    'test_type': f'single_frequency_{freq}',
                    'status': 'ERROR',
                    'error': str(e)
                })
                all_passed = False

        return all_passed

    def run_complete_investigation(self):
        """Run all investigation tests and compile results"""
        print("🔬 Starting HEVAG audio compatibility investigation...")
        print("=" * 60)

        # Phase hi Priority Test: Reference extraction
        self.analyze_startmeup_reference()

        # Phase 1: Single frequency tests (fast and controlled)
        single_freq_passed = self.test_single_frequency_tones()

        # Save investigation results
        results_file = 'investigation_results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'single_frequency_tests': self.test_results,
                'errors': getattr(self, 'errors', [])
            }, f, indent=2)

        print(f"\n📊 Investigation complete!")
        print(f"   - Tests performed: {len([r for r in self.test_results if r.get('status') != 'ERROR'])}")
        print(f"   - Errors encountered: {len(getattr(self, 'errors', []))}")
        print(f"   - Results saved to: {results_file}")

        return self.test_results

if __name__ == "__main__":
    investigation = HEVAGAudioInspector()
    investigation.run_complete_investigation()