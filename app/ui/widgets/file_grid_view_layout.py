"""
Layout helpers for FileGridView.

Handles grid layout setup and tile clearing.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout

from app.ui.widgets.file_tile import FileTile


def setup_grid_layout(content_widget) -> QGridLayout:
    """Setup grid layout for content widget."""
    grid_layout = QGridLayout(content_widget)
    grid_layout.setSpacing(20)
    # No left margin - dock should be flush with left edge
    grid_layout.setContentsMargins(0, 0, 24, 24)  # Top margin also 0 for dock
    # IMPORTANT: Do NOT set alignment - it centers the content!
    # grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    # Set column stretch to respect fixed-width widgets (like Focus dock)
    grid_layout.setColumnStretch(0, 0)  # Column 0 (dock) - no stretch
    grid_layout.setColumnStretch(1, 0)  # Column 1 (separator) - no stretch
    grid_layout.setColumnStretch(2, 1)  # Column 2+ (content) - stretch to fill
    return grid_layout


def clear_old_tiles(view) -> dict:
    """Clear old tiles preserving expanded ones for exit animation."""
    old_expanded_tiles_to_animate = {}
    if view._is_desktop_window and view._expanded_file_tiles:
        old_expanded_tiles_to_animate = view._expanded_file_tiles.copy()
    
    widgets_to_delete = []
    items_to_keep = []
    
    # Preserve dock and separator widgets
    for i in range(view._grid_layout.count()):
        item = view._grid_layout.itemAt(i)
        if item:
            widget = item.widget()
            if widget:
                # Keep Focus dock and separator
                if (hasattr(widget, '__class__') and 
                    (widget.__class__.__name__ == 'FocusDockWidget' or 
                     widget.__class__.__name__ == 'DockSeparator')):
                    items_to_keep.append((i, item))
                    continue
                
                # Keep expanded tiles for animation
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

