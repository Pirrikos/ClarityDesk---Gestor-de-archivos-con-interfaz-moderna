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
    grid_layout.setContentsMargins(24, 24, 24, 24)  # Márgenes uniformes, centrados en contenido
    # No alinear explícitamente para evitar centrado forzado
    grid_layout.setColumnStretch(0, 1)  # Una sola columna que estira el contenido
    return grid_layout


def clear_old_tiles(view) -> dict:
    """Clear tiles antiguos preservando los expandidos para animación de salida."""
    old_expanded_tiles_to_animate = {}
    if view._is_desktop_window and view._expanded_file_tiles:
        old_expanded_tiles_to_animate = view._expanded_file_tiles.copy()
    
    widgets_to_delete = []
    items_to_keep = []
    
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
            
            # Mark for deletion
            widgets_to_delete.append((i, item))
    
    # Remove items in reverse order to avoid index shifting
    for i, item in reversed(widgets_to_delete):
        widget = item.widget()
        view._grid_layout.removeItem(item)
        if widget:
            # Cleanup badge overlay for FileStackTile before deleting
            if hasattr(widget, '_cleanup_badge'):
                widget._cleanup_badge()
            widget.deleteLater()
    
    return old_expanded_tiles_to_animate
