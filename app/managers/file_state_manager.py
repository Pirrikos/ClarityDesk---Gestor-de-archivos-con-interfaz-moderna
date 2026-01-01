"""
FileStateManager - Manager for file state persistence with SQLite.

Orchestrates state management: cache + SQLite storage sync.
Emits signals to notify UI of state changes.
"""

import os
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from app.core.logger import get_logger

logger = get_logger(__name__)

from app.services.file_state_storage import (
    get_file_id_from_path,
    get_state_by_path,
    initialize_database,
    load_all_states,
    remove_missing_files,
    remove_state as storage_remove_state,
    remove_states_batch as storage_remove_states_batch,
    set_state as storage_set_state,
    set_states_batch as storage_set_states_batch,
)
from app.services.file_state_storage_query import get_items_by_state as query_get_items_by_state


class FileStateManager(QObject):
    """Manager for file states with SQLite persistence and cache."""
    
    # Signals emitted when states change
    state_changed = Signal(str, str)  # (file_path, state) - state can be None
    states_changed = Signal(list)  # List of (file_path, state) tuples
    
    def __init__(self):
        """Initialize manager and load states from database."""
        super().__init__()
        # Cache: file_id -> state (loaded from DB on startup)
        self._state_cache: dict[str, str] = {}
        # Cache: file_path -> file_id (for fast lookups)
        self._path_to_id_cache: dict[str, str] = {}
        
        # Initialize database
        initialize_database()
        
        # Load all states from database into cache
        self._load_cache_from_db()
    
    def _load_cache_from_db(self) -> None:
        """Load all states from database into cache."""
        db_states = load_all_states()
        self._state_cache = db_states
    
    def _get_file_id(self, file_path: str) -> Optional[str]:
        """
        Get file_id for a path, using cache if available.
        
        Args:
            file_path: Full path to file.
            
        Returns:
            file_id or None if file doesn't exist.
        """
        # Check cache first
        if file_path in self._path_to_id_cache:
            cached_id = self._path_to_id_cache[file_path]
            # Verify file still exists and metadata matches
            current_id = get_file_id_from_path(file_path)
            if current_id == cached_id:
                return cached_id
            # Metadata changed, update cache
            if current_id:
                self._path_to_id_cache[file_path] = current_id
                return current_id
            # File deleted, remove from cache
            self._path_to_id_cache.pop(file_path, None)
            return None
        
        # Compute and cache
        file_id = get_file_id_from_path(file_path)
        if file_id:
            self._path_to_id_cache[file_path] = file_id
        return file_id
    
    def get_file_state(self, file_path: str) -> Optional[str]:
        """
        Get state for a file.
        
        Args:
            file_path: Full path to the file.
            
        Returns:
            State constant or None if no state assigned.
        """
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        
        file_id = self._get_file_id(file_path)
        if not file_id:
            logger.debug(f"get_file_state: NO file_id for '{file_path}'")
            return None
        
        # Check cache first
        if file_id in self._state_cache:
            cached_state = self._state_cache[file_id]
            logger.debug(f"get_file_state: CACHED state='{cached_state}' for '{os.path.basename(file_path)}' (id={file_id})")
            return cached_state
        
        # Fallback to DB lookup (for files not in cache)
        state = get_state_by_path(file_path)
        logger.debug(f"get_file_state: DB LOOKUP state='{state}' for '{os.path.basename(file_path)}' (id={file_id})")
        if state and file_id:
            self._state_cache[file_id] = state
        return state
    
    def set_file_state(self, file_path: str, state: Optional[str]) -> None:
        """
        Set state for a file.
        
        Args:
            file_path: Full path to the file.
            state: State constant or None to remove state.
        """
        file_id = self._get_file_id(file_path)
        if not file_id:
            return
        
        if state is None:
            self._state_cache.pop(file_id, None)
            storage_remove_state(file_id)
        else:
            self._state_cache[file_id] = state
            try:
                stat = os.stat(file_path)
                storage_set_state(file_id, file_path, stat.st_size, int(stat.st_mtime), state)
            except OSError:
                self._state_cache.pop(file_id, None)
                return
        
        self.state_changed.emit(file_path, state)
    
    def set_files_state(self, file_paths: list[str], state: Optional[str]) -> int:
        """
        Set state for multiple files using batch transaction for atomicity.
        
        Args:
            file_paths: List of file paths.
            state: State constant or None to remove state.
            
        Returns:
            Number of files updated.
        """
        if not file_paths:
            return 0
        batch_states = []
        batch_remove_ids = []
        updated_paths = []
        
        for file_path in file_paths:
            file_id = self._get_file_id(file_path)
            if not file_id:
                continue
            
            if self._state_cache.get(file_id) == state:
                continue
            
            try:
                stat = os.stat(file_path)
                if state is None:
                    batch_remove_ids.append(file_id)
                else:
                    batch_states.append((file_id, file_path, stat.st_size, int(stat.st_mtime), state))
                updated_paths.append((file_path, state))
            except OSError:
                continue
        
        count = 0
        if batch_remove_ids:
            count += storage_remove_states_batch(batch_remove_ids)
            for file_id in batch_remove_ids:
                self._state_cache.pop(file_id, None)
        
        if batch_states:
            count += storage_set_states_batch(batch_states)
            for file_id, _, _, _, state_val in batch_states:
                self._state_cache[file_id] = state_val
        
        # Emit batch signal if any changes
        if updated_paths:
            self.states_changed.emit(updated_paths)
        
        return count
    
    def cleanup_missing_files(self, existing_paths: set[str]) -> int:
        """
        Remove database entries for files that no longer exist.
        
        Args:
            existing_paths: Set of file paths that currently exist.
            
        Returns:
            Number of entries removed.
        """
        removed_count = remove_missing_files(existing_paths)
        
        # Update cache: remove entries for missing files
        if removed_count > 0:
            # Rebuild cache from DB
            self._load_cache_from_db()
            # Clear path cache (will be rebuilt on demand)
            self._path_to_id_cache.clear()
        
        return removed_count
    
    def get_items_by_state(self, state: str) -> List[str]:
        """
        Obtener lista de archivos y carpetas con un estado específico.
        
        Incluye tanto archivos como carpetas (items).
        
        Args:
            state: Estado constante (e.g., "pending", "delivered").
            
        Returns:
            Lista de paths de archivos y carpetas con el estado especificado.
        """
        return query_get_items_by_state(state)

