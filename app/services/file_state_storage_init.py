"""
FileStateStorageInit - Database initialization for file state storage.

Handles database schema creation and initialization.
"""

import sqlite3

from app.services.file_state_storage_helpers import get_connection, get_db_path


def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create database schema (table and index)."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_states (
            file_id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            size INTEGER,
            modified INTEGER,
            state TEXT NOT NULL,
            last_update INTEGER
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_path ON file_states(path)
    """)


def initialize_database() -> None:
    """
    Initialize database and create table if not exists.
    
    Handles corrupted database by recreating it.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        create_schema(cursor)
        conn.commit()
        conn.close()
        
    except sqlite3.Error:
        # If database is corrupted, delete and recreate
        db_path = get_db_path()
        if db_path.exists():
            try:
                db_path.unlink()
            except OSError:
                pass
        
        # Retry initialization
        conn = get_connection()
        cursor = conn.cursor()
        create_schema(cursor)
        conn.commit()
        conn.close()

