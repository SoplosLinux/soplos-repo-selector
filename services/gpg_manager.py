"""
GPG Key Manager Service.
Handles importing, listing, and verifying GPG keys for repositories.
"""

import os
import shutil
import subprocess
import glob
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from utils.logger import log_info, log_error, log_warning
from core.i18n_manager import _

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
                log_warning(_("Could not create {path}: {err}").format(path=self.etc_keyrings_dir, err=e))

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
            log_warning(_("Error getting key info needed for {path}: {err}").format(path=key_path, err=e))
            
        return info

    def get_key_details(self, key_path: str) -> Optional[Dict[str, Optional[str]]]:
        """Return fingerprint, expiry (ISO) and uid for a key file, or None."""
        try:
            result = subprocess.run(
                ["gpg", "--show-keys", "--with-colons", key_path],
                check=False, capture_output=True, text=True, timeout=3
            )
            if result.returncode != 0:
                return None

            fingerprint = ''
            expiry: Optional[str] = None
            uid = ''

            for line in result.stdout.split('\n'):
                parts = line.split(':')
                if not parts:
                    continue
                tag = parts[0]
                if tag == 'fpr' and len(parts) >= 10:
                    fingerprint = parts[-1]
                elif tag == 'pub' and len(parts) > 6:
                    exp_field = parts[6]
                    if exp_field and exp_field.isdigit():
                        try:
                            ts = int(exp_field)
                            expiry = datetime.utcfromtimestamp(ts).isoformat() + 'Z'
                        except Exception:
                            expiry = None
                elif tag == 'uid' and len(parts) > 9:
                    uid = parts[9]

            return {'fingerprint': fingerprint, 'expiry': expiry, 'uid': uid}
        except Exception as e:
            log_warning(_("Error extracting key details for {path}: {err}").format(path=key_path, err=e))
            return None

    def import_key_from_file(self, source_path: str, key_name: str = None) -> Tuple[bool, str]:
        """
        Imports a GPG key from a file.
        Returns (success, message/path).
        """
        try:
            if not os.path.exists(source_path):
                return False, _("File {path} does not exist").format(path=source_path)
            
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
            log_error(_("Error importing key: {err}").format(err=e))
            return False, str(e)

    def export_key(self, src_path: str, dst_path: str) -> Tuple[bool, str]:
        """
        Export a key file from `src_path` to `dst_path`.
        If the source is ASCII-armored and the destination ends with `.gpg`,
        it will attempt to dearmor into a binary `.gpg` file.
        Returns (success, message_or_dst).
        """
        try:
            if not os.path.exists(src_path):
                return False, _("Source {path} does not exist").format(path=src_path)

            # If destination parent doesn't exist, try to create (may fail if needs root)
            dst_dir = os.path.dirname(dst_path) or '.'
            if not os.path.exists(dst_dir):
                try:
                    os.makedirs(dst_dir, exist_ok=True)
                except PermissionError:
                    return False, _("Permission denied creating destination directory {dir}").format(dir=dst_dir)

            if self._is_ascii_armored(src_path) and dst_path.endswith('.gpg'):
                # dearmor ASCII to binary
                cmd = ['gpg', '--dearmor', '-o', dst_path, src_path]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    return True, dst_path
                else:
                    return False, res.stderr or _('gpg --dearmor failed')
            else:
                try:
                    shutil.copyfile(src_path, dst_path)
                    return True, dst_path
                except PermissionError:
                    return False, _("Permission denied writing to {path}").format(path=dst_path)
                except Exception as e:
                    return False, str(e)

        except Exception as e:
            log_error(_("Error exporting key: {err}").format(err=e))
            return False, str(e)

    def delete_key(self, key_path: str, force: bool = False) -> Tuple[bool, str]:
        """
        Delete a key file at `key_path` after validating it's not referenced by APT sources.
        If `force` is True, deletion proceeds even if references are found.
        Returns (success, message).
        """
        try:
            if not os.path.exists(key_path):
                return False, _("Key {path} does not exist").format(path=key_path)

            # Search for references in apt sources
            referenced_in = []
            candidates = ['/etc/apt/sources.list']
            candidates.extend(glob.glob('/etc/apt/sources.list.d/*'))
            for conf in candidates:
                try:
                    if not os.path.isfile(conf):
                        continue
                    with open(conf, 'r', errors='ignore') as f:
                        data = f.read()
                        if key_path in data or os.path.basename(key_path) in data:
                            referenced_in.append(conf)
                except Exception:
                    continue

            if referenced_in and not force:
                return False, _("Key referenced in: {list}").format(list=', '.join(referenced_in))

            # Attempt to remove file (may require root)
            try:
                os.remove(key_path)
                return True, _("Deleted {path}").format(path=key_path)
            except PermissionError:
                # Fallback to pkexec rm
                try:
                    res = subprocess.run(['pkexec', 'rm', '-f', key_path], capture_output=True, text=True)
                    if res.returncode == 0:
                        return True, _("Deleted {path} (via pkexec)").format(path=key_path)
                    else:
                        return False, res.stderr or _('pkexec rm failed')
                except Exception as e:
                    return False, str(e)
            except FileNotFoundError:
                return False, _("Key {path} not found").format(path=key_path)
            except Exception as e:
                return False, str(e)
        except Exception as e:
            log_error(_("Error deleting key: {err}").format(err=e))
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
