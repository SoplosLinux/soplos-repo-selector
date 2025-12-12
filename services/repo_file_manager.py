"""
APT repository file manager (sources.list and DEB822 format).
Handles low-level reading and parsing of source files.
"""

import os
import re
import tempfile
import shutil
import subprocess
from typing import List, Dict, Any
from pathlib import Path

from utils.logger import log_info, log_error, log_warning

class RepoFileManager:
    """Manager for reading and writing APT source files."""
    
    def __init__(self):
        self.comment_pattern = re.compile(r'^\s*#')
        self.deb_line_pattern = re.compile(
            r'^\s*(deb|deb-src)\s+(\[.*?\]\s+)?(\S+)\s+(\S+)\s*(.*?)\s*$'
        )
    
    def read_sources_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Reads a sources file and returns a list of repositories.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            List of repository dictionaries
        """
        repos = []
        file_path_obj = Path(file_path)
        
        try:
            if not file_path_obj.exists():
                return repos
            
            content = file_path_obj.read_text(encoding='utf-8')
            
            # Determine format
            if file_path_obj.suffix == '.sources' or self._is_deb822_format(content):
                repos = self._parse_deb822_format(content, str(file_path_obj))
            else:
                repos = self._parse_legacy_format(content, str(file_path_obj))
            
            log_info(f"Read {len(repos)} repositories from {file_path}")
            return repos
            
        except Exception as e:
            log_error(f"Error reading file {file_path}", e)
            return []
    
    def write_sources_file(self, file_path: str, repos: List[Dict[str, Any]]) -> bool:
        """
        Writes repositories to a sources file.
        
        Args:
            file_path: Path to the file to write
            repos: List of repositories to write
            
        Returns:
            True if successful
        """
        try:
            file_path_obj = Path(file_path)
            
            # Determine format based on extension and repo metadata
            use_deb822 = (file_path_obj.suffix == '.sources' or 
                         any(r.get('format') == 'deb822' for r in repos))
            
            # Filter repos for this file
            file_repos = [r for r in repos if r.get('file') == file_path]
            
            if use_deb822:
                content = self._generate_deb822_content(file_repos)
            else:
                content = self._generate_legacy_content(file_repos)
            
            # Write safely using temporary file
            return self._write_file_safely(file_path, content)
            
        except Exception as e:
            log_error(f"Error writing file {file_path}", e)
            return False
    
    def _is_deb822_format(self, content: str) -> bool:
        """Detects if content is in DEB822 format."""
        deb822_patterns = [
            re.compile(r'^\s*Types:\s*', re.MULTILINE),
            re.compile(r'^\s*URIs:\s*', re.MULTILINE),
            re.compile(r'^\s*Suites:\s*', re.MULTILINE),
            re.compile(r'^\s*Components:\s*', re.MULTILINE)
        ]
        return any(pattern.search(content) for pattern in deb822_patterns)
    
    def _parse_legacy_format(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parses legacy format (sources.list)."""
        repos = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and full comments
            if not line or self.comment_pattern.match(line):
                continue
            
            # Check if line is disabled (commented out code)
            disabled = False
            if line.startswith('# '):
                uncommented = line[2:].strip()
                if self.deb_line_pattern.match(uncommented):
                    line = uncommented
                    disabled = True
                else:
                    continue
            
            # Parse repository line
            match = self.deb_line_pattern.match(line)
            if match:
                repo_type = match.group(1)
                options = match.group(2) or ''
                uri = match.group(3)
                distribution = match.group(4)
                components = match.group(5) or ''
                
                # Extract options (e.g. [arch=amd64])
                signed_by = ''
                if options:
                    signed_by_match = re.search(r'signed-by=([^\]\s]+)', options)
                    if signed_by_match:
                        signed_by = signed_by_match.group(1)
                
                repos.append({
                    'disabled': disabled,
                    'type': repo_type,
                    'uri': uri,
                    'distribution': distribution,
                    'components': components.strip(),
                    'comment': '',
                    'signed_by': signed_by,
                    'file': file_path,
                    'format': 'legacy',
                    'line': line_num,
                    'raw_options': options.strip()
                })
        
        return repos
    
    def _parse_deb822_format(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parses DEB822 format (.sources)."""
        repos = []
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block_num, block in enumerate(blocks, 1):
            if not block.strip():
                continue
            
            # Check if block is disabled
            disabled = False
            if block.strip().startswith('#'):
                # Try to uncomment
                lines = block.split('\n')
                uncommented_lines = []
                for line in lines:
                    if line.strip().startswith('#'):
                        uncommented_lines.append(line[1:])
                    else:
                        uncommented_lines.append(line)
                block = '\n'.join(uncommented_lines)
                disabled = True
            
            # Parse fields
            fields = {}
            for line in block.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    fields[key.strip().lower()] = value.strip()
            
            if 'types' in fields and 'uris' in fields and 'suites' in fields:
                repo_types = fields['types'].split()
                uris = fields['uris'].split()
                suites = fields['suites'].split()
                components = fields.get('components', '').strip()
                signed_by = fields.get('signed-by', '')
                
                # Create entry for each combination (flattening for UI simplicity)
                # But careful not to duplicate too much if we want to save back as blocks
                # Ideally we should keep them grouped, but for legacy compatibility we flatten
                
                for repo_type in repo_types:
                    for uri in uris:
                        for suite in suites:
                            repos.append({
                                'disabled': disabled,
                                'type': repo_type,
                                'uri': uri,
                                'distribution': suite,
                                'components': components,
                                'comment': '',
                                'signed_by': signed_by,
                                'file': file_path,
                                'format': 'deb822',
                                'block': block_num
                            })
        
        return repos
    
    def _generate_legacy_content(self, repos: List[Dict[str, Any]]) -> str:
        """Generates legacy format content."""
        lines = []
        lines.append("# Generated by Soplos Repo Selector")
        lines.append("# Do not edit manually")
        lines.append("")
        
        for repo in repos:
            prefix = "# " if repo.get('disabled', False) else ""
            
            # Reconstruct options
            options = repo.get('raw_options', '')
            if not options and repo.get('signed_by'):
                 options = f"[signed-by={repo['signed_by']}] "
            elif repo.get('signed_by') and 'signed-by' not in options:
                 # If options existed but signed-by wasn't in them (unlikely if strictly parsed)
                 # but for safety:
                 options = options.strip() + f" [signed-by={repo['signed_by']}] "
            
            # Clean up options spacing
            if options and not options.endswith(' '):
                options += ' '
                
            line = f"{prefix}{repo['type']} {options}{repo['uri']} {repo['distribution']}"
            if repo.get('components'):
                line += f" {repo['components']}"
            
            if repo.get('comment'):
                lines.append(f"# {repo['comment']}")
            
            lines.append(line)
            # lines.append("") # Optional spacing
        
        return '\n'.join(lines) + '\n'
    
    def _generate_deb822_content(self, repos: List[Dict[str, Any]]) -> str:
        """Generates DEB822 format content."""
        lines = []
        lines.append("# Generated by Soplos Repo Selector")
        lines.append("# Format: DEB822")
        lines.append("")
        # If repos include a 'block' key (parsed from DEB822), preserve block
        # structure and regenerate each original block separately. This avoids
        # flattening all suites/uris/components into a single hybrid block.
        if repos and any('block' in r for r in repos):
            # Group by block preserving numeric order
            blocks: Dict[int, List[Dict[str, Any]]] = {}
            for r in repos:
                b = r.get('block', 0) or 0
                blocks.setdefault(b, []).append(r)

            for b in sorted(blocks.keys()):
                group = blocks[b]
                disabled = any(r.get('disabled', False) for r in group)
                prefix = "# " if disabled else ""

                # Keep ordering predictable but unique
                uris = []
                types = []
                suites = []
                components = []
                signed_by = ''

                for r in group:
                    if r['uri'] not in uris:
                        uris.append(r['uri'])
                    if r['type'] not in types:
                        types.append(r['type'])
                    if r['distribution'] not in suites:
                        suites.append(r['distribution'])
                    comp = r.get('components', '')
                    if comp and comp not in components:
                        components.append(comp)
                    if not signed_by and r.get('signed_by'):
                        signed_by = r.get('signed_by')

                lines.append(f"{prefix}Types: {' '.join(types)}")
                lines.append(f"{prefix}URIs: {' '.join(uris)}")
                lines.append(f"{prefix}Suites: {' '.join(suites)}")

                if components:
                    lines.append(f"{prefix}Components: {' '.join(components)}")

                if signed_by:
                    lines.append(f"{prefix}Signed-By: {signed_by}")

                lines.append("")

            return '\n'.join(lines)

        # Fallback: group similar repos as before
        grouped_repos = self._group_similar_repos(repos)

        for group in grouped_repos:
            disabled = any(r.get('disabled', False) for r in group)
            prefix = "# " if disabled else ""

            uris = sorted(list(set(r['uri'] for r in group)))
            types = sorted(list(set(r['type'] for r in group)))
            suites = sorted(list(set(r['distribution'] for r in group)))
            components = sorted(list(set(r['components'] for r in group if r['components'])))
            signed_by = next((r['signed_by'] for r in group if r.get('signed_by')), '')

            # TODO: Handle multiple comments?

            lines.append(f"{prefix}Types: {' '.join(types)}")
            lines.append(f"{prefix}URIs: {' '.join(uris)}")
            lines.append(f"{prefix}Suites: {' '.join(suites)}")

            if components:
                lines.append(f"{prefix}Components: {' '.join(components)}")

            if signed_by:
                lines.append(f"{prefix}Signed-By: {signed_by}")

            lines.append("")

        return '\n'.join(lines)
    
    def _group_similar_repos(self, repos: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Groups similar repos for DEB822 compactness."""
        groups = []
        for repo in repos:
            compatible_group = None
            for group in groups:
                if self._repos_compatible_for_grouping(repo, group[0]):
                    compatible_group = group
                    break
            
            if compatible_group:
                compatible_group.append(repo)
            else:
                groups.append([repo])
        return groups
    
    def _repos_compatible_for_grouping(self, repo1: Dict[str, Any], repo2: Dict[str, Any]) -> bool:
        """Checks if two repos can be grouped."""
        # Must share signed-by and disabled status
        # Ideally should also share components if URI/Suite differs, but that's complex logic
        # For simplicity, we group if signed-by and disabled status matches.
        # But wait, DEB822 allows multiple URIs/Suites/Components only if they are cross-compatible.
        # E.g. All Types apply to All URIs apply to All Suites apply to All Components.
        # If repo1 has components "main" and repo2 has "contrib", joining them implies
        # both URIs have both components. 
        # Safer strategy: Group only if sets are identical OR if single-value fields match.
        
        # Strict matching for safety in this version:
        # Group if URIs match AND Suites match (allowing Type variance)
        # OR URIs match AND Types match (allowing Suite variance)
        # For now let's just use the logic from Legacy which seemed to only check signed-by/disabled
        return (repo1.get('signed_by') == repo2.get('signed_by') and
                repo1.get('disabled', False) == repo2.get('disabled', False))

    def _write_file_safely(self, file_path: str, content: str) -> bool:
        """Writes to file using temp file and pkexec/mv if needed."""
        try:
            file_path_obj = Path(file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            # Create temp in system tempdir to avoid permission errors when
            # target dir (e.g. /etc) is not writable. The caller higher up may
            # batch these temps and invoke pkexec once for all moves.
            fd, temp_path = tempfile.mkstemp(suffix='.tmp', text=True)

            try:
                with open(fd, 'w', encoding='utf-8') as f:
                    f.write(content)

                temp_path_obj = Path(temp_path)

                # preserve permissions if exists
                if file_path_obj.exists():
                    temp_path_obj.chmod(file_path_obj.stat().st_mode)
                else:
                    temp_path_obj.chmod(0o644)

                # Attempt direct move if possible
                if file_path_obj.parent.is_dir() and os.access(str(file_path_obj.parent), os.W_OK):
                    shutil.move(temp_path, file_path)
                    log_info(f"File written successfully: {file_path}")
                    return True

                # Otherwise return the temp path so a grouped mover can handle pkexec
                # The caller (grouped writer) will be responsible for moving this
                # temp into place (possibly invoking pkexec once for all moves).
                # To keep backward compatibility for callers that expect a bool,
                # we perform the pkexec move here as a fallback.
                result = subprocess.run(
                    ['pkexec', 'mv', temp_path, file_path],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    # Cleanup temp
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    raise PermissionError(f"pkexec failed: {result.stderr}")

                log_info(f"File written successfully: {file_path}")
                return True

            except Exception as e:
                # Cleanup temp
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise e
                
        except Exception as e:
            log_error(f"Error writing file safely {file_path}", e)
            return False

    def write_multiple_sources_files(self, repos_by_file: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Write multiple source files in a grouped operation.

        This creates temporary files in the system temp directory for each
        destination and then either moves them directly (if writable) or
        generates a single shell script that moves all temp files into place
        and runs it via `pkexec` once to avoid multiple password prompts.
        """
        temp_items = []  # tuples of (temp_path, dest_path, mode)
        try:
            # Generate all contents and write temps
            for file_path, file_repos in repos_by_file.items():
                file_path_obj = Path(file_path)
                use_deb822 = (file_path_obj.suffix == '.sources' or
                             any(r.get('format') == 'deb822' for r in file_repos))

                if use_deb822:
                    content = self._generate_deb822_content(file_repos)
                else:
                    content = self._generate_legacy_content(file_repos)

                fd, temp_path = tempfile.mkstemp(suffix='.tmp', text=True)
                try:
                    with open(fd, 'w', encoding='utf-8') as f:
                        f.write(content)
                except Exception:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    raise

                temp_path_obj = Path(temp_path)
                if file_path_obj.exists():
                    mode = file_path_obj.stat().st_mode
                else:
                    mode = 0o644
                temp_path_obj.chmod(mode)
                temp_items.append((str(temp_path_obj), str(file_path_obj), mode))

            # Try to move directly where possible
            all_parents = set(Path(dest).parent for _, dest, _ in temp_items)
            parents_writable = all(os.access(str(p), os.W_OK) for p in all_parents)

            if parents_writable:
                for temp_path, dest_path, _ in temp_items:
                    shutil.move(temp_path, dest_path)
                for _, dest, mode in temp_items:
                    Path(dest).chmod(mode)
                log_info("All files written successfully (direct move)")
                return True

            # Need escalation: create a single script that moves all files
            script_fd, script_path = tempfile.mkstemp(suffix='.sh', text=True)
            try:
                with os.fdopen(script_fd, 'w', encoding='utf-8') as script:
                    script.write('#!/bin/sh\nset -e\n')
                    for temp_path, dest_path, mode in temp_items:
                        dest_dir = os.path.dirname(dest_path)
                        # Ensure we pass only permission bits (e.g. 0o644), not file type bits
                        perm = mode & 0o777
                        perm_str = oct(perm)[2:]
                        script.write(f"mkdir -p '{dest_dir}'\n")
                        script.write(f"mv '{temp_path}' '{dest_path}'\n")
                        script.write(f"chmod {perm_str} '{dest_path}'\n")

                os.chmod(script_path, 0o700)

                result = subprocess.run(['pkexec', 'sh', script_path], capture_output=True, text=True)
                if result.returncode != 0:
                    log_error('pkexec grouped move failed', result.stderr)
                    # Attempt cleanup of temps
                    for temp_path, _, _ in temp_items:
                        try:
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                        except:
                            pass
                    try:
                        os.unlink(script_path)
                    except:
                        pass
                    return False

                # Success; cleanup script
                try:
                    os.unlink(script_path)
                except:
                    pass

                log_info('All files written successfully (grouped pkexec)')
                return True

            except Exception as e:
                # Cleanup
                try:
                    os.unlink(script_path)
                except:
                    pass
                raise e

        except Exception as e:
            log_error('Error in grouped write', e)
            # Cleanup any leftover temps
            for temp_path, _, _ in temp_items:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except:
                    pass
            return False
