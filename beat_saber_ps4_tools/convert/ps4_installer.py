#!/usr/bin/env python3
"""
PS4 Song Installer
Uploads converted songs to PS4 via FTP and configures the GoldHEN plugin.

Usage:
    python3 ps4_installer.py --upload converted_songs/ --ps4 192.168.1.100 --port 2121

Requirements:
    - PS4 with GoldHEN running
    - FTP enabled on PS4
    - Network connectivity between PC and PS4
"""

import ftplib
import os
import json
import argparse
import hashlib
import shutil
from pathlib import Path

class PS4SongInstaller:
    def __init__(self, ps4_ip, ps4_port=2121):
        self.ps4_ip = ps4_ip
        self.ps4_port = ps4_port
        self.ftp = None
    
    def connect(self):
        """Connect to PS4 FTP."""
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.ps4_ip, self.ps4_port, timeout=30)
            self.ftp.login()
            self.ftp.encoding = 'utf-8'
            print(f"Connected to PS4 at {self.ps4_ip}:{self.ps4_port}")
            return True
        except Exception as e:
            print(f"FTP connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from PS4."""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                pass
            self.ftp = None
    
    def ensure_directory(self, path):
        """Ensure directory exists on PS4."""
        try:
            self.ftp.cwd(path)
            self.ftp.cwd('..')
        except:
            # Directory doesn't exist, try to create it
            parts = Path(path).parts
            current = ''
            for part in parts:
                current = f"{current}/{part}" if current else part
                try:
                    self.ftp.cwd(current)
                except:
                    try:
                        self.ftp.mkd(current)
                    except:
                        pass  # May already exist or no permission
        return True
    
    def upload_file(self, local_path, remote_path):
        """Upload a file to PS4."""
        try:
            self.ftp.cwd('/')
            # Ensure directory exists
            remote_dir = str(Path(remote_path).parent)
            self.ensure_directory(remote_dir)
            
            with open(local_path, 'rb') as f:
                self.ftp.storbinary(f'STOR {remote_path}', f)
            return True
        except Exception as e:
            print(f"  Upload error: {e}")
            return False
    
    def upload_songs(self, songs_dir, clean_install=False):
        """Upload converted songs to PS4.
        
        Songs will be placed at:
        /user/data/GoldHEN/BeatSaber/songs/
        """
        songs_dir = Path(songs_dir)
        
        # PS4 target directory
        ps4_songs_dir = '/user/data/GoldHEN/BeatSaber/songs'
        
        print(f"Ensuring PS4 directory exists: {ps4_songs_dir}")
        self.ensure_directory(ps4_songs_dir)
        
        # Upload each song folder
        uploaded = 0
        skipped = 0
        
        for song_path in sorted(songs_dir.iterdir()):
            if not song_path.is_dir():
                continue
            
            song_name = song_path.name
            ps4_song_dir = f"{ps4_songs_dir}/{song_name}"
            
            print(f"\nUploading: {song_name}")
            
            # Check if song already exists (for update mode)
            try:
                self.ftp.cwd(ps4_song_dir)
                exists = True
            except:
                exists = False
            
            if exists and not clean_install:
                print(f"  Song exists, skipping (use --clean to reinstall)")
                skipped += 1
                continue
            
            # Create song directory
            try:
                self.ftp.mkd(ps4_song_dir)
            except:
                pass  # May exist
            
            # Upload song files
            files_uploaded = 0
            for file_path in song_path.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(song_path)
                    ps4_file = f"{ps4_song_dir}/{rel_path}"
                    
                    size = file_path.stat().st_size
                    print(f"  {rel_path} ({size:,} bytes)")
                    
                    if self.upload_file(file_path, ps4_file):
                        files_uploaded += 1
                    else:
                        print(f"    FAILED")
            
            if files_uploaded > 0:
                uploaded += 1
                print(f"  Uploaded {files_uploaded} files")
            else:
                print(f"  No files uploaded")
        
        print(f"\n{'='*50}")
        print(f"Upload complete!")
        print(f"  Songs uploaded: {uploaded}")
        print(f"  Songs skipped: {skipped}")
        print(f"  PS4 location: {ps4_songs_dir}")
        print(f"\nNext: Start Beat Saber with GoldHEN plugin enabled")
        
        return uploaded, skipped
    
    def create_plugin_config(self):
        """Create or update GoldHEN plugin configuration for Beat Saber."""
        plugins_ini_path = '/user/data/GoldHEN/plugins.ini'
        
        # Read existing config
        config_content = ""
        try:
            self.ftp.cwd('/user/data/GoldHEN')
            lines = []
            self.ftp.retrlines('RETR plugins.ini', lines.append)
            config_content = '\n'.join(lines)
        except:
            config_content = ""
        
        # Add Beat Saber plugin section if needed
        beat_saber_section = """
[BeatSaber]
# Beat Saber Custom Songs Plugin (when available)
/data/GoldHEN/plugins/BeatSaber-Plugin.prx
"""
        if '[BeatSaber]' not in config_content:
            config_content += beat_saber_section
        
        # Write updated config
        try:
            from io import BytesIO
            bio = BytesIO(config_content.encode('utf-8'))
            self.ftp.storbinary(f'STOR {plugins_ini_path}', bio)
            print(f"Updated {plugins_ini_path}")
        except Exception as e:
            print(f"Could not update plugins.ini: {e}")
    
    def install_plugin(self, plugin_path):
        """Install a GoldHEN plugin .prx file to PS4."""
        plugin_path = Path(plugin_path)
        
        if not plugin_path.exists():
            print(f"Plugin file not found: {plugin_path}")
            return False
        
        ps4_plugin_path = '/user/data/GoldHEN/plugins/BeatSaber-Plugin.prx'
        
        print(f"Installing plugin: {plugin_path.name}")
        if self.upload_file(plugin_path, ps4_plugin_path):
            print(f"Plugin installed to {ps4_plugin_path}")
            
            # Update config
            self.create_plugin_config()
            return True
        
        return False
    
    def list_installed_songs(self):
        """List songs already installed on PS4."""
        songs_dir = '/user/data/GoldHEN/BeatSaber/songs'
        
        try:
            self.ftp.cwd(songs_dir)
            songs = []
            self.ftp.retrlines('LIST', lambda x: songs.append(x))
            
            print(f"Songs on PS4 ({songs_dir}):")
            for line in songs:
                print(f"  {line}")
            
            return len(songs)
        except:
            print("No songs directory found")
            return 0
    
    def create_beat_saber_folders(self):
        """Create the Beat Saber modding folder structure."""
        base = '/user/data/GoldHEN/BeatSaber'
        
        folders = [
            base,
            f'{base}/songs',
            f'{base}/songs/custom',
            f'{base}/config',
            f'{base}/logs',
        ]
        
        print("Creating Beat Saber modding folders on PS4...")
        for folder in folders:
            try:
                self.ftp.mkd(folder)
                print(f"  Created: {folder}")
            except:
                pass  # May already exist
        
        # Create default config
        config = {
            'version': '1.0',
            'songFolder': 'songs',
            'maxSongs': 100,
            'customSongsEnabled': True,
            'logLevel': 'info'
        }
        
        config_path = f'{base}/config/settings.json'
        try:
            from io import BytesIO
            bio = BytesIO(json.dumps(config, indent=2).encode('utf-8'))
            self.ftp.storbinary(f'STOR {config_path}', bio)
            print(f"  Created config: {config_path}")
        except Exception as e:
            print(f"  Config error: {e}")
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Install songs to PS4 Beat Saber')
    parser.add_argument('--upload', '-u', help='Folder with converted songs to upload')
    parser.add_argument('--ps4', '-p', default='192.168.100.117', help='PS4 IP address')
    parser.add_argument('--port', type=int, default=2121, help='PS4 FTP port')
    parser.add_argument('--plugin', help='Install a GoldHEN plugin .prx file')
    parser.add_argument('--list', action='store_true', help='List installed songs')
    parser.add_argument('--init', action='store_true', help='Initialize folder structure')
    parser.add_argument('--clean', action='store_true', help='Clean install (replace existing)')
    
    args = parser.parse_args()
    
    installer = PS4SongInstaller(args.ps4, args.port)
    
    if not installer.connect():
        return 1
    
    try:
        if args.init:
            installer.create_beat_saber_folders()
        
        elif args.plugin:
            installer.install_plugin(args.plugin)
        
        elif args.list:
            installer.list_installed_songs()
        
        elif args.upload:
            songs_dir = Path(args.upload)
            if not songs_dir.exists():
                print(f"Folder not found: {songs_dir}")
                return 1
            
            uploaded, skipped = installer.upload_songs(songs_dir, clean_install=args.clean)
            print(f"\nDone! {uploaded} songs uploaded, {skipped} skipped")
        
        else:
            parser.print_help()
    
    finally:
        installer.disconnect()
    
    return 0


if __name__ == '__main__':
    exit(main())