"""
FileStateStorageCRUD - CRUD operations for file state storage.

Handles single file state operations: set, get, remove.
"""

import os
import sqlite3
import time
from typing import Optional

from app.services.file_state_storage_helpers import compute_file_id, get_connection
from app.models.path_utils import normalize_path


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
        normalized_path = normalize_path(path)
        
        # Comprobar si existe una entrada antigua con el mismo path (ignorando mayúsculas/minúsculas)
        # Caso de cambio de file_id por metadatos o normalización
        cursor.execute(
            "SELECT file_id, state FROM file_states WHERE lower(path) = lower(?)",
            (normalized_path,)
        )
        old_row = cursor.fetchone()
        
        if old_row and old_row[0] != file_id:
            # Path exists but file_id changed (file renamed/modified)
            # Remove old entry and create new one
            cursor.execute("DELETE FROM file_states WHERE file_id = ?", (old_row[0],))
        
        cursor.execute("""
            INSERT OR REPLACE INTO file_states 
            (file_id, path, size, modified, state, last_update)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_id, normalized_path, size, modified, state, last_update))
        
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
    normalized_path = normalize_path(path)
    file_id = get_file_id_from_path(normalized_path)
    if not file_id:
        return None
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Intento primario: buscar por file_id actual
        cursor.execute("SELECT state FROM file_states WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        
        if row:
            conn.close()
            return row[0]
        
        # Fallback robusto: buscar por path (ignorando mayúsculas/minúsculas) si el file_id cambió
        cursor.execute(
            "SELECT state, file_id FROM file_states WHERE lower(path) = lower(?) ORDER BY last_update DESC LIMIT 1",
            (normalized_path,)
        )
        fallback = cursor.fetchone()
        if not fallback:
            conn.close()
            return None
        
        state, old_file_id = fallback[0], fallback[1]
        conn.close()
        
        # Migración silenciosa del registro: reinsertar con el nuevo file_id
        # Comentario: esto elimina el registro antiguo para ese path y asegura consistencia futura
        try:
            import os
            stat = os.stat(normalized_path)
            set_state(file_id, normalized_path, stat.st_size, int(stat.st_mtime), state)
        except OSError:
            # Si falla el stat, al menos devolvemos el estado encontrado por path
            pass
        
        return state
        
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

