"""
Layout helpers for FileGridView.

Handles grid layout setup and tile clearing.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout

from app.ui.widgets.file_tile import FileTile


def setup_grid_layout(content_widget) -> QGridLayout:
    """Setup grid layout para el contenido sin panel dock."""
    grid_layout = QGridLayout(content_widget)
    grid_layout.setSpacing(20)
    grid_layout.setContentsMargins(24, 8, 24, 24)  # Margen superior reducido de 24px a 8px
    # No alinear explícitamente para evitar centrado forzado
    grid_layout.setColumnStretch(0, 1)  # Una sola columna que estira el contenido
    return grid_layout


def clear_old_tiles(view) -> dict:
    """Clear tiles antiguos preservando los expandidos para animación de salida y tiles reutilizables."""
    old_expanded_tiles_to_animate = {}
    if view._is_desktop_window and view._expanded_file_tiles:
        old_expanded_tiles_to_animate = view._expanded_file_tiles.copy()
    
    widgets_to_delete = []
    items_to_keep = []
    
    # Construir set de archivos actuales para determinar qué tiles reutilizar
    current_files_set = set()
    if hasattr(view, '_files') and view._files:
        if isinstance(view._files[0], tuple):
            # Lista categorizada: extraer todos los archivos
            for _, files in view._files:
                current_files_set.update(files)
        else:
            # Lista simple de archivos
            current_files_set.update(view._files)
    
    for i in range(view._grid_layout.count()):
        item = view._grid_layout.itemAt(i)
        if item:
            widget = item.widget()
            if widget:
                # Mantener tiles expandidas para animación de salida suave
                is_old_expanded = any(widget in tiles for tiles in old_expanded_tiles_to_animate.values())
                if is_old_expanded:
                    widget.setParent(view)
                    continue
                
                # Preservar tiles reutilizables en cache
                if isinstance(widget, FileTile):
                    file_path = widget.get_file_path()
                    if file_path in current_files_set:
                        # Tile todavía está en la lista de archivos, preservarlo en cache
                        view._tile_cache[file_path] = widget
                        widget.setParent(view)  # Remover del layout pero mantener widget
                        continue
            
            # Mark for deletion
            widgets_to_delete.append((i, item))
    
    # Remove items in reverse order to avoid index shifting
    for i, item in reversed(widgets_to_delete):
        widget = item.widget()
        view._grid_layout.removeItem(item)
        if widget:
            # Si es un FileTile que no está en la lista actual, remover del cache también
            if isinstance(widget, FileTile):
                file_path = widget.get_file_path()
                view._tile_cache.pop(file_path, None)
            
            # Cleanup badge overlay for FileStackTile before deleting
            if hasattr(widget, '_cleanup_badge'):
                widget._cleanup_badge()
            widget.deleteLater()
    
    return old_expanded_tiles_to_animate
