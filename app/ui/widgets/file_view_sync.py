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
    from app.ui.widgets.file_view_container import FileViewContainer


def update_files(container: 'FileViewContainer') -> None:
    """Update both views with files from active tab or search results."""
    if hasattr(container, '_is_search_mode') and container._is_search_mode:
        file_paths = [result.file_path for result in container._search_results]
        container._grid_view.update_files(file_paths)
        container._list_view.update_files(file_paths)
        return
    
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    detector = getattr(QApplication.instance(), '_top_level_detector', None)
    if detector:
        detector.set_workspace_switch_active(True)
        QTimer.singleShot(500, lambda: detector.set_workspace_switch_active(False) if detector else None)
    
    if not hasattr(container, '_cached_is_desktop'):
        container._cached_is_desktop = _check_if_desktop_window(container)
    use_stacks = container._cached_is_desktop
    
    items = container._tab_manager.get_files(use_stacks=use_stacks)
    container._grid_view.update_files(items)
    container._list_view.update_files(items)
    
    if container._state_manager:
        file_paths = []
        for item in items:
            if hasattr(item, 'files'):
                file_paths.extend(item.files)
            else:
                file_paths.append(item)
        container._state_manager.cleanup_missing_files(set(file_paths))


def _update_workspace_view_buttons(container: 'FileViewContainer', is_grid: bool) -> None:
    """Update workspace selector view buttons state."""
    if container._workspace_grid_button:
        container._workspace_grid_button.setChecked(is_grid)
    if container._workspace_list_button:
        container._workspace_list_button.setChecked(not is_grid)
    if container._workspace_selector:
        container._workspace_selector.update_button_styles(is_grid)


def switch_view(container: 'FileViewContainer', view_type: str) -> None:
    """
    Switch between grid and list views.
    
    Saves current selection before switching and restores it when switching back.
    
    Si hay contexto de estado activo, guarda el modo para ese estado.

    Args:
        container: FileViewContainer instance.
        view_type: "grid" or "list".
    """
    current_selection = get_selected_files(container)
    if not hasattr(container, '_saved_selections'):
        container._saved_selections = {}
    container._saved_selections[container._current_view] = current_selection
    
    if view_type == "grid":
        container._stacked.setCurrentWidget(container._grid_view)
        container._current_view = "grid"
        if hasattr(container, '_toolbar') and container._toolbar:
            container._toolbar.update_button_styles(True)
        _update_workspace_view_buttons(container, True)
    else:
        container._stacked.setCurrentWidget(container._list_view)
        container._current_view = "list"
        if hasattr(container, '_toolbar') and container._toolbar:
            container._toolbar.update_button_styles(False)
        _update_workspace_view_buttons(container, False)
    
    # Solo guardar para contexto de estado. Para carpetas normales, el workspace ya fue actualizado.
    # Llamar a set_view_mode aquí causaría recursión porque emite view_mode_changed que dispara switch_view.
    if container._tab_manager and container._tab_manager.has_state_context():
        container._tab_manager.save_state_view_mode(view_type)

    update_files(container)
    
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


def clear_selection(container: 'FileViewContainer') -> None:
    """
    Limpiar selección en ambas vistas (grid y list).
    
    Se usa al navegar a un estado para evitar que archivos seleccionados
    antes del cambio aparezcan seleccionados en la nueva vista.
    """
    from app.ui.widgets.grid_selection_logic import clear_selection as clear_grid_selection
    
    # Limpiar selección en grid view
    clear_grid_selection(container._grid_view)
    
    # Limpiar selección en list view
    container._list_view.clearSelection()
    if hasattr(container._list_view, '_checked_paths'):
        container._list_view._checked_paths.clear()


def _restore_selection(container, view_type: str, paths: list[str]) -> None:
    """Restore selection in the specified view."""
    if view_type == "grid":
        _restore_grid_selection(container._grid_view, paths)
    else:
        _restore_list_selection(container._list_view, paths)


def _restore_grid_selection(view, paths: list[str]) -> None:
    """Restore selection in grid view by finding tiles matching paths."""
    path_set = {normalize_path(p) for p in paths}
    
    for tile in view._selected_tiles.copy():
        try:
            tile_path = normalize_path(tile.get_file_path())
            if tile_path not in path_set:
                tile.set_selected(False)
                view._selected_tiles.discard(tile)
        except (RuntimeError, AttributeError):
            view._selected_tiles.discard(tile)
    
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
    
    view.clearSelection()
    view._checked_paths.clear()
    
    for row in range(view.rowCount()):
        item = view.item(row, 1)
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path and normalize_path(path) in path_set:
                checkbox_item = view.item(row, 0)
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.CheckState.Checked)
                    view._checked_paths.add(path)
                view.selectRow(row)


def _check_if_desktop_window(container) -> bool:
    """Check if this container is inside a DesktopWindow."""
    return getattr(container, '_is_desktop', False)

