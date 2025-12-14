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
    """Format filename: remove extension, apply title case."""
    filename = os.path.basename(file_path)
    name_without_ext, _ = os.path.splitext(filename)
    return name_without_ext.title() if name_without_ext else ""
