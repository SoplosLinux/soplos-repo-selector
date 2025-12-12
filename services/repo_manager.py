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
    
    def save_repos(self, repos: List[Dict[str, Any]]) -> bool:
        """
        Saves changes to repositories file(s).
        
        Args:
            repos: List of all repositories (modified)
            
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
        
        # Handle files that had repos but now don't (deleted repos)
        # We need to know which files we originally had
        # (This logic implies we should track original state, but for now 
        # we can just iterate over the keys we found)
        
        # Attempt to write all files in a single grouped operation so we can
        # perform privilege escalation only once when needed.
        success = self.file_manager.write_multiple_sources_files(repos_by_file)
        if not success:
            for file_path in repos_by_file.keys():
                log_error(f"Failed to save {file_path}")
        
        if success:
            self.repo_cache = repos
            self.cache_valid = True
            
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


# Global instance
_repo_manager = None

def get_repo_manager() -> RepoManager:
    """Returns global RepoManager instance."""
    global _repo_manager
    if _repo_manager is None:
        _repo_manager = RepoManager()
    return _repo_manager
