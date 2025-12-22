"""
FileViewUtils - Utility functions for file view widgets.

Shared utilities to avoid code duplication between FileGridView and FileListView.
"""

from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from app.ui.widgets.file_view_container import FileViewContainer


def find_file_view_container(widget) -> Optional['FileViewContainer']:
    """
    Find FileViewContainer parent in widget hierarchy.
    
    Args:
        widget: Widget to start search from.
        
    Returns:
        FileViewContainer instance if found, None otherwise.
    """
    # Import here to avoid circular dependency
    from app.ui.widgets.file_view_container import FileViewContainer
    
    parent = widget.parent()
    while parent:
        if isinstance(parent, FileViewContainer):
            return parent
        parent = parent.parent()
    return None


def create_refresh_callback(widget) -> Optional[Callable[[], None]]:
    """
    Create refresh callback for file view operations.
    
    Args:
        widget: Widget to find FileViewContainer from.
        
    Returns:
        Callback function to refresh view, or None if container not found.
    """
    container = find_file_view_container(widget)
    if container:
        from app.ui.widgets.file_view_sync import update_files
        return lambda: update_files(container)
    return None

