"""
FileViewSync - View synchronization for FileViewContainer.

Handles file updates, view switching, and state synchronization.
"""

from app.models.file_stack import FileStack
from app.ui.widgets.file_grid_view import FileGridView
from app.ui.widgets.file_list_view import FileListView


def update_files(container) -> None:
    """Update both views with files from active tab."""
    use_stacks = _check_if_desktop_window(container)
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

    Args:
        container: FileViewContainer instance.
        view_type: "grid" or "list".
    """
    if view_type == "grid":
        container._stacked.setCurrentWidget(container._grid_view)
        container._grid_button.setChecked(True)
        container._list_button.setChecked(False)
        container._current_view = "grid"
        container._toolbar.update_button_styles(True)
    else:
        container._stacked.setCurrentWidget(container._list_view)
        container._list_button.setChecked(True)
        container._grid_button.setChecked(False)
        container._current_view = "list"
        container._toolbar.update_button_styles(False)

    update_files(container)


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


def _check_if_desktop_window(container) -> bool:
    """Check if this container is inside a DesktopWindow."""
    parent = container.parent()
    while parent:
        if parent.__class__.__name__ == 'DesktopWindow':
            return True
        parent = parent.parent()
    return False

