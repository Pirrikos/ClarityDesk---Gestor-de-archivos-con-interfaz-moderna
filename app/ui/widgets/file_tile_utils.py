"""
FileTileUtils - Utilidades compartidas para FileTile.

Funciones comunes usadas por múltiples módulos de FileTile.
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def is_grid_view(tile: 'FileTile') -> bool:
    """Verificar si el tile está en GridView usando verificación robusta."""
    if not hasattr(tile, '_parent_view') or not tile._parent_view:
        return False
    
    # Verificar nombre de clase y atributo característico para detección robusta
    parent_class_name = tile._parent_view.__class__.__name__
    if parent_class_name == 'FileGridView':
        return hasattr(tile._parent_view, '_grid_layout')
    return False


def format_filename(file_path: str) -> str:
    """Format filename: remove extension, preserve original case."""
    filename = os.path.basename(file_path)
    # Si es una carpeta, devolver el nombre completo sin modificar
    if os.path.isdir(file_path):
        return filename
    
    # Para archivos, quitar solo extensiones reales (ej: .pdf, .txt)
    # No quitar puntos que son parte del nombre (ej: "1. PLATON")
    name_without_ext, ext = os.path.splitext(filename)
    # Solo quitar extensión si tiene formato válido (al menos 2 chars, alfanumérica)
    if ext and len(ext) >= 2 and ext[1:].replace('_', '').isalnum():
        return name_without_ext
    return filename
