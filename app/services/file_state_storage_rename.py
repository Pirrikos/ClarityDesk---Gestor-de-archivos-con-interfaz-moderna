"""
FileStateStorageRename - Rename operations for file state storage.

Handles updating file state entries when files are renamed.
"""

import sqlite3
import time
from typing import Optional

from app.services.file_state_storage_helpers import get_connection


def update_path_for_rename(old_path: str, new_path: str, new_file_id: str, 
                           size: int, modified: int) -> Optional[str]:
    """
    Update database entry when file is renamed.
    
    Args:
        old_path: Original file path.
        new_path: New file path after rename.
        new_file_id: New file_id computed from new path.
        size: File size in bytes.
        modified: File modification timestamp.
    
    Returns:
        State constant if migration successful, None otherwise.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Find state by old path
        cursor.execute("SELECT state FROM file_states WHERE path = ?", (old_path,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        state = row[0]
        last_update = int(time.time())
        
        # Remove old entry
        cursor.execute("DELETE FROM file_states WHERE path = ?", (old_path,))
        
        # Create new entry with new path and file_id
        cursor.execute("""
            INSERT INTO file_states 
            (file_id, path, size, modified, state, last_update)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (new_file_id, new_path, size, modified, state, last_update))
        
        conn.commit()
        conn.close()
        
        return state
        
    except sqlite3.Error:
        return None

