"""
FileViewSync - View synchronization for FileViewContainer.

Handles file updates, view switching, and state synchronization.
"""

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

from app.core.constants import SELECTION_RESTORE_DELAY_MS
from app.models.file_stack import FileStack
from app.services.path_utils import normalize_path

if TYPE_CHECKING:
    from app.ui.widgets.file_grid_view import FileGridView
    from app.ui.widgets.file_list_view import FileListView


def update_files(container) -> None:
    """Update both views with files from active tab."""
    # Cache result to avoid repeated checks
    if not hasattr(container, '_cached_is_desktop'):
        container._cached_is_desktop = _check_if_desktop_window(container)
    use_stacks = container._cached_is_desktop
    active_folder = container._tab_manager.get_active_folder()
    
    items = container._tab_manager.get_files(use_stacks=use_stacks)
    container._grid_view.update_files(items)
    container._list_view.update_files(items)
    
    # Cleanup states for files that no longer exist
    if container._state_manager:
        file_paths = []
        for item in items:
            if hasattr(item, 'files'):  # FileStack
                file_paths.extend(item.files)
            else:  # String path
                file_paths.append(item)
        container._state_manager.cleanup_missing_files(set(file_paths))


def switch_view(container, view_type: str) -> None:
    """
    Switch between grid and list views.
    
    Saves current selection before switching and restores it when switching back.

    Args:
        container: FileViewContainer instance.
        view_type: "grid" or "list".
    """
    # Save current selection before switching
    current_selection = get_selected_files(container)
    if not hasattr(container, '_saved_selections'):
        container._saved_selections = {}
    container._saved_selections[container._current_view] = current_selection
    
    # Switch view
    if view_type == "grid":
        container._stacked.setCurrentWidget(container._grid_view)
        if hasattr(container, '_grid_button') and container._grid_button:
            container._grid_button.setChecked(True)
        if hasattr(container, '_list_button') and container._list_button:
            container._list_button.setChecked(False)
        container._current_view = "grid"
        # Actualizar estilos en toolbar o header, según exista
        if hasattr(container, '_toolbar') and container._toolbar:
            container._toolbar.update_button_styles(True)
        elif hasattr(container, '_header') and hasattr(container._header, 'update_button_styles'):
            container._header.update_button_styles(True)
    else:
        container._stacked.setCurrentWidget(container._list_view)
        if hasattr(container, '_list_button') and container._list_button:
            container._list_button.setChecked(True)
        if hasattr(container, '_grid_button') and container._grid_button:
            container._grid_button.setChecked(False)
        container._current_view = "list"
        if hasattr(container, '_toolbar') and container._toolbar:
            container._toolbar.update_button_styles(False)
        elif hasattr(container, '_header') and hasattr(container._header, 'update_button_styles'):
            container._header.update_button_styles(False)

    # Update files first
    update_files(container)
    
    # Restore selection after a short delay to ensure tiles/rows are created
    if hasattr(container, '_saved_selections') and view_type in container._saved_selections:
        saved_paths = container._saved_selections[view_type]
        if saved_paths:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(SELECTION_RESTORE_DELAY_MS, lambda: _restore_selection(container, view_type, saved_paths))


def get_selected_files(container) -> list[str]:
    """
    Get paths of currently selected files in the active view.
    
    Returns:
        List of file paths for selected files (grid or list).
    """
    if container._current_view == "grid":
        return container._grid_view.get_selected_paths()
    else:
        return container._list_view.get_selected_paths()


def set_selected_states(container, state: str) -> None:
    """Set state for selected files in active view."""
    if container._current_view == "grid":
        container._grid_view.set_selected_states(state)
    else:
        container._list_view.set_selected_states(state)


def _restore_selection(container, view_type: str, paths: list[str]) -> None:
    """Restore selection in the specified view."""
    if view_type == "grid":
        _restore_grid_selection(container._grid_view, paths)
    else:
        _restore_list_selection(container._list_view, paths)


def _restore_grid_selection(view, paths: list[str]) -> None:
    """Restore selection in grid view by finding tiles matching paths."""
    path_set = {normalize_path(p) for p in paths}
    
    # Find tiles matching saved paths
    for tile in view._selected_tiles.copy():
        try:
            tile_path = normalize_path(tile.get_file_path())
            if tile_path not in path_set:
                tile.set_selected(False)
                view._selected_tiles.discard(tile)
        except (RuntimeError, AttributeError):
            view._selected_tiles.discard(tile)
    
    # Find and select tiles matching saved paths
    # Iterate through all tiles in the grid layout
    for i in range(view._grid_layout.count()):
        item = view._grid_layout.itemAt(i)
        if item:
            widget = item.widget()
            if widget and hasattr(widget, 'get_file_path'):
                try:
                    tile_path = normalize_path(widget.get_file_path())
                    if tile_path in path_set:
                        widget.set_selected(True)
                        view._selected_tiles.add(widget)
                except (RuntimeError, AttributeError):
                    pass


def _restore_list_selection(view, paths: list[str]) -> None:
    """Restore selection in list view by finding rows matching paths."""
    path_set = {normalize_path(p) for p in paths}
    
    # Clear current selection
    view.clearSelection()
    view._checked_paths.clear()
    
    # Find and select rows matching saved paths
    for row in range(view.rowCount()):
        item = view.item(row, 1)  # Path is in column 1
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path and normalize_path(path) in path_set:
                # Select checkbox if available
                checkbox_item = view.item(row, 0)
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.CheckState.Checked)
                    view._checked_paths.add(path)
                # Also select the row
                view.selectRow(row)


def _check_if_desktop_window(container) -> bool:
    """Check if this container is inside a DesktopWindow."""
    # Use explicit flag instead of inferring from hierarchy
    return getattr(container, '_is_desktop', False)

