"""
FileStateMigration - State migration helpers for file rename operations.

Handles migration of file states when files are renamed.
"""

import hashlib
import os
from typing import List

from app.services.file_state_storage import update_path_for_rename


def migrate_states_on_rename(
    state_manager,
    old_paths: List[str],
    new_names: List[str]
) -> None:
    """
    Migrate file states when files are renamed.
    
    Args:
        state_manager: FileStateManager instance.
        old_paths: List of old file paths.
        new_names: List of new file names (not full paths).
    """
    for old_path, new_name in zip(old_paths, new_names):
        # Get new path
        dir_path = os.path.dirname(old_path)
        new_path = os.path.join(dir_path, new_name)
        
        # Skip if path didn't actually change
        if old_path == new_path:
            continue
        
        # Check if old path has state in DB
        if not state_manager.get_file_state(old_path):
            continue
        
        # Get new file_id (after rename, file will exist at new_path)
        # We compute it now, but it will be correct after rename
        try:
            # Try to get metadata from old path first
            stat = os.stat(old_path)
            size = stat.st_size
            modified = int(stat.st_mtime)
        except (OSError, ValueError):
            continue
        
        # Compute new file_id with new path (file doesn't exist at new_path yet)
        # Calculate manually using same algorithm as storage service
        content = f"{new_path}|{size}|{modified}".encode('utf-8')
        new_file_id = hashlib.sha256(content).hexdigest()
        
        # Migrate state in database
        state = update_path_for_rename(old_path, new_path, new_file_id, size, modified)
        
        # Update cache after migration
        if state and state_manager:
            # Remove old entry from cache
            old_file_id = state_manager._get_file_id(old_path)
            if old_file_id:
                state_manager._state_cache.pop(old_file_id, None)
                state_manager._path_to_id_cache.pop(old_path, None)
            
            # Add new entry to cache
            state_manager._state_cache[new_file_id] = state
            state_manager._path_to_id_cache[new_path] = new_file_id

