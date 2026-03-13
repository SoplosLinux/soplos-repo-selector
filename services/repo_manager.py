"""
Repository Manager Service.
High-level management of APT repositories: listing, adding, removing, updating.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from .repo_file_manager import RepoFileManager
from utils.logger import log_info, log_error

class RepoManager:
    """High-level repository management service."""
    
    def __init__(self):
        self.file_manager = RepoFileManager()
        self.repo_cache = None
        self.cache_valid = False
        
        # Standard paths
        self.sources_list = '/etc/apt/sources.list'
        self.sources_parts = '/etc/apt/sources.list.d'
    
    def get_all_repos(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Gets all repositories from system files.
        
        Args:
            use_cache: If True, return cached results if available
            
        Returns:
            List of repository objects
        """
        if use_cache and self.cache_valid and self.repo_cache is not None:
            return self.repo_cache
        
        repos = []
        
        # Read main sources.list
        if os.path.exists(self.sources_list):
            repos.extend(self.file_manager.read_sources_file(self.sources_list))
        
        # Read parts directory
        if os.path.exists(self.sources_parts):
            for filename in sorted(os.listdir(self.sources_parts)):
                if filename.endswith(('.list', '.sources')):
                    file_path = os.path.join(self.sources_parts, filename)
                    repos.extend(self.file_manager.read_sources_file(file_path))
        
        self.repo_cache = repos
        self.cache_valid = True
        return repos
    
    def save_repos(self, repos: List[Dict[str, Any]], files_to_delete: List[str] = None) -> bool:
        """
        Saves changes to repositories file(s).
        
        Args:
            repos: List of all repositories (modified)
            files_to_delete: Optional list of file paths to remove
            
        Returns:
            True if all writes were successful
        """
        # Group repos by file
        repos_by_file = {}
        
        # First, ensure all repos have a destination file
        for repo in repos:
            file_path = repo.get('file')
            if not file_path:
                # Assign default file for new repos
                # Using a generic name or checking repo name
                file_path = self._determine_file_for_repo(repo)
                repo['file'] = file_path
                
            if file_path not in repos_by_file:
                repos_by_file[file_path] = []
            repos_by_file[file_path].append(repo)
        
        # Attempt to write all files in a single grouped operation so we can
        # perform privilege escalation only once when needed.
        success = self.file_manager.write_multiple_sources_files(repos_by_file, files_to_delete)
        if not success:
            for file_path in repos_by_file.keys():
                log_error(f"Failed to save {file_path}")
        
        if success:
            self.repo_cache = repos
            self.cache_valid = True
            
        return success
    
    def apply_batch(self, tasks: List[Dict[str, Any]]) -> bool:
        """Executes a batch of operations through the file manager."""
        success = self.file_manager.run_batch_operation(tasks)
        if success:
            self.invalidate_cache()
        return success
    
    def _determine_file_for_repo(self, repo: Dict[str, Any]) -> str:
        """Determines the appropriate file path for a new repository."""
        # Clean specific characters from URI or suite to make a filename
        name = "custom"
        uri = repo.get('uri', '')
        suite = repo.get('distribution', '')
        
        if 'soplos' in uri:
            return os.path.join(self.sources_parts, 'soplos.list')
        
        # Try to make a slug from the domain
        try:
            domain = uri.split('://')[-1].split('/')[0]
            name = f"{domain}-{suite}".replace('.', '_').replace('/', '-')
        except:
            pass
            
        return os.path.join(self.sources_parts, f"{name}.list")

    def invalidate_cache(self):
        """Invalidates the repository cache."""
        self.cache_valid = False
        self.repo_cache = None

    def modernize_repo(self, repo_data: Dict[str, Any]) -> bool:
        """
        Convert a legacy (.list) repository to modern (.sources) format.
        Creates a backup of the original file.
        
        Args:
           repo_data: The repository dictionary to modernize
           
        Returns:
            True if modernization succeeded
        """
        original_file = repo_data.get('file')
        if not original_file or not original_file.endswith('.list'):
            return False
            
        # 1. Prepare new data
        path_obj = Path(original_file)
        new_file = str(path_obj.with_suffix('.sources'))
        
        # Deep copy to avoid modifying original until success
        new_repo = repo_data.copy()
        new_repo['format'] = 'deb822'
        new_repo['file'] = new_file
        
        # 2. Build tasks for atomic operation
        tasks = []
        
        # Backup task (we'll do this via RUN_COMMAND for simplicity in the batch)
        backup_file = f"{original_file}.bak"
        tasks.append({
            'type': 'RUN_COMMAND',
            'command': f"cp '{original_file}' '{backup_file}'"
        })
        
        # WRITE_FILE task for the new format
        # We need to generate the content. We can use the file_manager for this.
        content = self.file_manager._generate_deb822_content([new_repo])
        tasks.append({
            'type': 'WRITE_FILE',
            'path': new_file,
            'content': content
        })
        
        # DELETE_FILE task for the old file
        tasks.append({
            'type': 'DELETE_FILE',
            'path': original_file
        })
        
        # 3. Execute
        log_info(f"Modernizing {original_file} -> {new_file}")
        success = self.apply_batch(tasks)
        
        if success:
            # Update the original dict object if it's still in use
            repo_data.update(new_repo)
            
        return success


# Global instance
_repo_manager = None

def get_repo_manager() -> RepoManager:
    """Returns global RepoManager instance."""
    global _repo_manager
    if _repo_manager is None:
        _repo_manager = RepoManager()
    return _repo_manager
