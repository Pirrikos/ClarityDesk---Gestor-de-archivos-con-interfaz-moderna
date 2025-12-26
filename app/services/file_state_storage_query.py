"""
FileStateStorageQuery - Query service for file states.

Handles queries to retrieve files and folders by state.
"""

import sqlite3
from typing import List

from app.services.file_state_storage_helpers import get_connection


def get_items_by_state(state: str) -> List[str]:
    """
    Obtener lista de paths de archivos y carpetas con un estado específico.
    
    Incluye tanto archivos como carpetas (items).
    Retorna lista ordenada alfabéticamente.
    
    Args:
        state: Estado constante (e.g., "pending", "delivered").
        
    Returns:
        Lista de paths de archivos y carpetas con el estado especificado.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Consultar todos los paths con el estado especificado
        cursor.execute("SELECT DISTINCT path FROM file_states WHERE state = ? ORDER BY path", (state,))
        rows = cursor.fetchall()
        
        conn.close()
        
        # Extraer paths de las tuplas
        return [row[0] for row in rows]
        
    except sqlite3.Error:
        return []

