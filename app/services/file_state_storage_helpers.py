"""
FileStateStorageHelpers - Helper functions for file state storage.

Database path, connection, and file ID computation utilities.
"""

import hashlib
import sqlite3
from pathlib import Path
import os

from app.services.storage_path_service import get_storage_file
from app.models.path_utils import normalize_path

# Database file location
DB_PATH = get_storage_file("claritydesk.db")


def get_db_path() -> Path:
    """Get database file path."""
    return DB_PATH


def compute_file_id(path: str, size: int, modified: int) -> str:
    """
    Calcular identificador único de archivo/carpeta.
    
    Regla clave:
    - Para carpetas: usar SOLO el path normalizado para evitar cambios de ID por mtime/size.
    - Para archivos: usar path + size + modified para detectar cambios reales de contenido.
    """
    normalized_path = normalize_path(path)
    if os.path.isdir(normalized_path):
        # Comentario: las carpetas cambian mtime con operaciones internas; no debe invalidar el estado
        content = normalized_path.encode('utf-8')
    else:
        content = f"{normalized_path}|{size}|{modified}".encode('utf-8')
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

