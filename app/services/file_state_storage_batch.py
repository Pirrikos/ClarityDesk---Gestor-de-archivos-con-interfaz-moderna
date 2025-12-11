"""
FileStateStorageBatch - Batch operations for file state storage.

Handles multiple file state operations in transactions.
"""

import os
import sqlite3
import time

from app.services.file_state_storage_helpers import get_connection


def set_states_batch(file_states: list[tuple]) -> int:
    """
    Set multiple file states in a single atomic transaction.
    
    Args:
        file_states: List of tuples (file_id, path, size, modified, state).
    
    Returns:
        Number of states successfully written.
    """
    if not file_states:
        return 0
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        last_update = int(time.time())
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        count = 0
        for file_id, path, size, modified, state in file_states:
            try:
                # Check if old entry exists with same path but different file_id
                cursor.execute("SELECT file_id FROM file_states WHERE path = ?", (path,))
                old_row = cursor.fetchone()
                
                if old_row and old_row[0] != file_id:
                    # Path exists but file_id changed, remove old entry
                    cursor.execute("DELETE FROM file_states WHERE file_id = ?", (old_row[0],))
                
                cursor.execute("""
                    INSERT OR REPLACE INTO file_states 
                    (file_id, path, size, modified, state, last_update)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (file_id, path, size, modified, state, last_update))
                count += 1
            except sqlite3.Error:
                # Skip this entry but continue with others
                continue
        
        # Commit transaction
        conn.commit()
        conn.close()
        
        return count
        
    except sqlite3.Error:
        # Rollback on error
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return 0


def remove_states_batch(file_ids: list[str]) -> int:
    """
    Remove multiple file states in a single atomic transaction.
    
    Args:
        file_ids: List of file_id strings to remove.
    
    Returns:
        Number of states successfully removed.
    """
    if not file_ids:
        return 0
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        placeholders = ','.join('?' * len(file_ids))
        cursor.execute(f"DELETE FROM file_states WHERE file_id IN ({placeholders})", 
                      tuple(file_ids))
        
        removed_count = cursor.rowcount
        
        # Commit transaction
        conn.commit()
        conn.close()
        
        return removed_count
        
    except sqlite3.Error:
        # Rollback on error
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return 0


def remove_missing_files(existing_paths: set[str]) -> int:
    """
    Remove database entries for files that no longer exist.
    
    Only removes entries for files that actually don't exist on disk,
    not just files that aren't in the current folder view.
    
    Args:
        existing_paths: Set of file paths (ignored, checks all DB paths against disk).
    
    Returns:
        Number of entries removed.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all paths from database
        cursor.execute("SELECT DISTINCT path FROM file_states")
        db_paths = [row[0] for row in cursor.fetchall()]
        
        if not db_paths:
            conn.close()
            return 0
        
        # Verify each path actually exists on disk
        missing_paths = []
        for path in db_paths:
            if not os.path.exists(path):
                missing_paths.append(path)
        
        if not missing_paths:
            conn.close()
            return 0
        
        # Remove entries for files that don't exist on disk
        placeholders = ','.join('?' * len(missing_paths))
        cursor.execute(f"DELETE FROM file_states WHERE path IN ({placeholders})", 
                      tuple(missing_paths))
        
        removed_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return removed_count
        
    except sqlite3.Error:
        return 0

