"""
GridSelectionManager - Selection management for grid view.

Handles tile selection logic with keyboard modifiers support.
"""

from PySide6.QtCore import Qt

from app.ui.widgets.file_tile import FileTile


def handle_tile_selection(
    tile: FileTile,
    modifiers: Qt.KeyboardModifiers,
    selected_tiles: set[FileTile],
    clear_selection_func
) -> None:
    """
    Handle tile selection based on keyboard modifiers.

    Args:
        tile: Tile widget to select/deselect.
        modifiers: Keyboard modifiers (Ctrl, Shift, etc.).
        selected_tiles: Set of currently selected tiles.
        clear_selection_func: Function to clear all selections.
    """
    if tile is None:
        return
    
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        if tile in selected_tiles:
            tile.set_selected(False)
            selected_tiles.discard(tile)
        else:
            tile.set_selected(True)
            selected_tiles.add(tile)
    else:
        # If clicking on already selected tile, keep selection for drag
        if tile in selected_tiles:
            # Already selected, maintain selection (for multi-drag)
            return
        # Clicking on unselected tile: clear and select only this one
        clear_selection_func()
        tile.set_selected(True)
        selected_tiles.add(tile)

