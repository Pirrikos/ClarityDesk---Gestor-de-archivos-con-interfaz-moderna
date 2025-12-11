"""
FileStateStorage - SQLite persistence service for file states.

Handles database operations for storing and retrieving file states.
No UI logic, pure storage layer.

This module re-exports all public APIs for backward compatibility.
Actual implementations are in separate modules:
- file_state_storage_helpers.py: Database path, connection, file ID computation
- file_state_storage_init.py: Database initialization and schema
- file_state_storage_crud.py: Single file CRUD operations
- file_state_storage_batch.py: Batch operations
- file_state_storage_rename.py: Rename operations
"""

# Re-export public APIs for backward compatibility
from app.services.file_state_storage_batch import (
    remove_missing_files,
    remove_states_batch,
    set_states_batch
)
from app.services.file_state_storage_crud import (
    get_file_id_from_path,
    get_state_by_path,
    load_all_states,
    remove_state,
    set_state
)
from app.services.file_state_storage_init import initialize_database
from app.services.file_state_storage_rename import update_path_for_rename

__all__ = [
    'initialize_database',
    'load_all_states',
    'set_state',
    'set_states_batch',
    'remove_state',
    'remove_states_batch',
    'remove_missing_files',
    'get_file_id_from_path',
    'get_state_by_path',
    'update_path_for_rename',
]
