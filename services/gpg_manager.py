"""
GPG Key Manager Service.
Handles importing, listing, and verifying GPG keys for repositories.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from utils.logger import log_info, log_error, log_warning

class GPGManager:
    """Manager for GPG keys."""
    
    def __init__(self):
        self.keyrings_dir = '/usr/share/keyrings'
        self.etc_keyrings_dir = '/etc/apt/keyrings'
        self._ensure_keyrings_dir()
    
    def _ensure_keyrings_dir(self):
        """Ensures /etc/apt/keyrings exists."""
        if not os.path.exists(self.etc_keyrings_dir):
            try:
                subprocess.run(['pkexec', 'mkdir', '-p', self.etc_keyrings_dir], 
                               check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                log_warning(f"Could not create {self.etc_keyrings_dir}: {e}")

    def get_all_keys(self) -> List[Dict[str, str]]:
        """Gets all available GPG keys."""
        keys = []
        for keyring_dir in [self.keyrings_dir, self.etc_keyrings_dir]:
            if os.path.exists(keyring_dir):
                for file in os.listdir(keyring_dir):
                    if file.endswith(('.gpg', '.asc', '.pgp')):
                        key_path = os.path.join(keyring_dir, file)
                        keys.append(self._get_key_info(key_path))
        return keys

    def _get_key_info(self, key_path: str) -> Dict[str, str]:
        """Gets info for a specific key."""
        info = {
            'name': os.path.basename(key_path),
            'path': key_path,
            'format': 'ASCII' if key_path.endswith('.asc') else 'GPG Binary',
            'description': 'GPG Key'
        }
        
        try:
            result = subprocess.run(
                ["gpg", "--show-keys", "--with-colons", key_path],
                check=False, capture_output=True, text=True, timeout=2
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    parts = line.split(':')
                    if len(parts) > 9:
                        if parts[0] == "uid":
                            info['description'] = parts[9]
                            break
                        elif parts[0] == "pub" and len(parts) > 4:
                            info['description'] = f"ID: {parts[4]}"
        except Exception as e:
            log_warning(f"Error getting key info needed for {key_path}: {e}")
            
        return info

    def import_key_from_file(self, source_path: str, key_name: str = None) -> Tuple[bool, str]:
        """
        Imports a GPG key from a file.
        Returns (success, message/path).
        """
        try:
            if not os.path.exists(source_path):
                return False, f"File {source_path} does not exist"
            
            if not key_name:
                key_name = os.path.basename(source_path)
            
            if not key_name.endswith(('.gpg', '.asc', '.pgp')):
                key_name += '.gpg'
            
            dst_dir = self.etc_keyrings_dir if os.path.exists(self.etc_keyrings_dir) else self.keyrings_dir
            dst_path = os.path.join(dst_dir, key_name)
            
            is_ascii = self._is_ascii_armored(source_path)
            
            # Use pkexec for root privileges
            cmd = []
            if is_ascii:
                # cat source | gpg --dearmor > dst
                # This complex piping with pkexec is tricky. 
                # Better to use a small helper script or `sh -c` inside pkexec
                script = f"cat '{source_path}' | gpg --dearmor > '{dst_path}' && chmod 644 '{dst_path}'"
                cmd = ['pkexec', 'sh', '-c', script]
            else:
                script = f"cp '{source_path}' '{dst_path}' && chmod 644 '{dst_path}'"
                cmd = ['pkexec', 'sh', '-c', script]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, dst_path
            else:
                return False, result.stderr
                
        except Exception as e:
            log_error(f"Error importing key: {e}")
            return False, str(e)

    def _is_ascii_armored(self, file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                header = f.read(100).decode('utf-8', errors='ignore')
            return "-----BEGIN PGP" in header
        except:
            return False

# Global instance
_gpg_manager = None

def get_gpg_manager() -> GPGManager:
    global _gpg_manager
    if _gpg_manager is None:
        _gpg_manager = GPGManager()
    return _gpg_manager
