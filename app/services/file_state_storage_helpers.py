"""
FileStateStorageHelpers - Helper functions for file state storage.

Database path, connection, and file ID computation utilities.
"""

import hashlib
import sqlite3
from pathlib import Path

# Database file location
DB_PATH = Path("storage/claritydesk.db")


def get_db_path() -> Path:
    """Get database file path, creating storage directory if needed."""
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def compute_file_id(path: str, size: int, modified: int) -> str:
    """
    Compute unique file identifier from path, size, and modification time.
    
    Args:
        path: Full file path.
        size: File size in bytes.
        modified: File modification timestamp.
    
    Returns:
        SHA256 hash string as file_id.
    """
    content = f"{path}|{size}|{modified}".encode('utf-8')
    return hashlib.sha256(content).hexdigest()


def get_connection() -> sqlite3.Connection:
    """
    Get database connection with error handling.
    
    Returns:
        SQLite connection.
    
    Raises:
        sqlite3.Error: If database cannot be opened or created.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

