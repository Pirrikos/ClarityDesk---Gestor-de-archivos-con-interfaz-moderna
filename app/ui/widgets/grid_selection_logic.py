"""
GridSelectionLogic - Selection handling for FileGridView.

Handles tile selection and state management.
"""

from PySide6.QtCore import Qt

from app.ui.widgets.file_tile import FileTile
from app.ui.widgets.grid_selection_manager import handle_tile_selection


def clear_selection(view) -> None:
    """Clear all tile selections."""
    for tile in list(view._selected_tiles):
        try:
            tile.set_selected(False)
        except RuntimeError:
            pass
    view._selected_tiles.clear()


def select_tile(view, tile: FileTile, modifiers: Qt.KeyboardModifiers) -> None:
    """Handle tile selection based on keyboard modifiers."""
    handle_tile_selection(
        tile,
        modifiers,
        view._selected_tiles,
        lambda: clear_selection(view)
    )


def get_selected_paths(view) -> list[str]:
    """
    Get paths of currently selected files.
    
    Returns:
        List of file paths for selected tiles.
    """
    paths = []
    for tile in list(view._selected_tiles):
        try:
            paths.append(tile.get_file_path())
        except RuntimeError:
            pass
    return paths


def set_selected_states(view, state) -> None:
    """
    Set state for all selected files.
    
    La actualización visual se maneja a través de las señales state_changed/states_changed
    emitidas por FileStateManager, que son procesadas por FileViewContainer._on_state_changed
    y _on_states_changed para decidir si refrescar la vista o solo actualizar badges.
    
    Args:
        view: FileGridView instance.
        state: State constant or None to remove state.
    """
    if not view._state_manager:
        return
    
    selected_paths = get_selected_paths(view)
    if not selected_paths:
        return
    
    # Update states in manager - esto emitirá states_changed que será procesado por FileViewContainer
    view._state_manager.set_files_state(selected_paths, state)
    
    # NO actualizar badges visualmente aquí - dejar que las señales manejen la actualización

