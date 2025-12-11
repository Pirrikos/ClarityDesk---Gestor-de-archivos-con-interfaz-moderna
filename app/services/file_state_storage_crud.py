"""
FileStateStorageCRUD - CRUD operations for file state storage.

Handles single file state operations: set, get, remove.
"""

import os
import sqlite3
import time
from typing import Optional

from app.services.file_state_storage_helpers import compute_file_id, get_connection


def set_state(file_id: str, path: str, size: int, modified: int, state: str) -> None:
    """
    Set or update file state in database.
    
    Args:
        file_id: Unique file identifier.
        path: Full file path.
        size: File size in bytes.
        modified: File modification timestamp.
        state: State constant.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        last_update = int(time.time())
        
        # Check if old entry exists with same path but different file_id (rename case)
        cursor.execute("SELECT file_id, state FROM file_states WHERE path = ?", (path,))
        old_row = cursor.fetchone()
        
        if old_row and old_row[0] != file_id:
            # Path exists but file_id changed (file renamed/modified)
            # Remove old entry and create new one
            cursor.execute("DELETE FROM file_states WHERE file_id = ?", (old_row[0],))
        
        cursor.execute("""
            INSERT OR REPLACE INTO file_states 
            (file_id, path, size, modified, state, last_update)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_id, path, size, modified, state, last_update))
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error:
        # Silently fail - state will be lost but app continues
        pass


def get_state_by_path(path: str) -> Optional[str]:
    """
    Get state for a file by path (computes file_id and looks up).
    
    Args:
        path: Full file path.
    
    Returns:
        State constant or None if not found.
    """
    file_id = get_file_id_from_path(path)
    if not file_id:
        return None
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT state FROM file_states WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        return row[0] if row else None
        
    except sqlite3.Error:
        return None


def remove_state(file_id: str) -> None:
    """
    Remove file state from database.
    
    Args:
        file_id: Unique file identifier.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM file_states WHERE file_id = ?", (file_id,))
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error:
        pass


def load_all_states() -> dict[str, str]:
    """
    Load all file states from database.
    
    Returns:
        Dictionary mapping file_id to state.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT file_id, state FROM file_states")
        rows = cursor.fetchall()
        
        conn.close()
        
        return {file_id: state for file_id, state in rows}
        
    except sqlite3.Error:
        return {}


def get_file_id_from_path(path: str) -> Optional[str]:
    """
    Compute file_id from file path (reads file metadata).
    
    Args:
        path: Full file path.
    
    Returns:
        file_id if file exists, None otherwise.
    """
    try:
        if not os.path.exists(path):
            return None
        
        stat = os.stat(path)
        size = stat.st_size
        modified = int(stat.st_mtime)
        
        return compute_file_id(path, size, modified)
        
    except (OSError, ValueError):
        return None

