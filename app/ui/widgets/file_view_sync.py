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
from app.services.file_path_utils import is_office_temp_file

if TYPE_CHECKING:
    from app.ui.widgets.file_grid_view import FileGridView
    from app.ui.widgets.file_list_view import FileListView
    from app.ui.widgets.file_view_container import FileViewContainer


def update_files(container: 'FileViewContainer') -> None:
    """Update both views with files from active tab or search results."""
    # Si estamos navegando, forzar salida del modo búsqueda para cargar contenido normal
    if hasattr(container, '_is_navigating') and container._is_navigating:
        container._is_search_mode = False
        container._search_results = []
        container._file_to_workspace = {}

    if hasattr(container, '_is_search_mode') and container._is_search_mode:
        file_paths = [result.file_path for result in container._search_results]
        # Filter Office temporary files from search results
        file_paths = _filter_office_temp_files(file_paths)
        container._grid_view.update_files(file_paths)
        container._list_view.update_files(file_paths)
        return

    # Calcular si usar stacks en cada actualización para evitar desajustes por caché
    use_stacks = _check_if_desktop_window(container)

    items = container._tab_manager.get_files(use_stacks=use_stacks)

    # Filter Office temporary files from regular file lists
    items = _filter_office_temp_files_from_items(items)

    container._grid_view.update_files(items)
    container._list_view.update_files(items)

    # NOTA: NO llamamos a cleanup_missing_files aquí porque eliminaría estados
    # de archivos que no están en la carpeta actual pero sí existen en otras carpetas.
    # cleanup_missing_files solo debe llamarse cuando se eliminan archivos físicamente,
    # no durante la navegación normal entre carpetas.


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

    # Emitir señal para actualizar contador de selección
    if hasattr(view, 'selection_changed'):
        view.selection_changed.emit()


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


def _filter_office_temp_files(file_paths: list[str]) -> list[str]:
    """
    Filter out Microsoft Office temporary files from a list of file paths.

    Args:
        file_paths: List of file paths to filter.

    Returns:
        Filtered list without Office temporary files.
    """
    return [path for path in file_paths if not is_office_temp_file(path)]


def _filter_office_temp_files_from_items(items: list) -> list:
    """
    Filter Office temporary files from a list that may contain FileStacks or file paths.

    Args:
        items: List of FileStack objects or file path strings.

    Returns:
        Filtered list with Office temp files removed from both stacks and regular files.
    """
    if not items:
        return items

    # Check if items are FileStack objects
    if hasattr(items[0], 'files'):
        # Filter files within each FileStack
        filtered_items = []
        for stack in items:
            filtered_files = [f for f in stack.files if not is_office_temp_file(f)]
            # Only include stack if it has files after filtering
            if filtered_files:
                # Create new FileStack with filtered files
                filtered_stack = FileStack(
                    stack_type=stack.stack_type,
                    files=filtered_files
                )
                filtered_items.append(filtered_stack)
        return filtered_items
    else:
        # Simple list of file paths
        return _filter_office_temp_files(items)
