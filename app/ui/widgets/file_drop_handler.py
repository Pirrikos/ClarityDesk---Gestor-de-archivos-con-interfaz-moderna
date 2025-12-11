"""
FileDropHandler - File drop handling for view container.

Handles file drop operations and same-folder drop detection.
Supports Desktop Focus and Trash Focus.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

from app.managers.tab_manager import TabManager
from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import copy_into_dock, is_file_in_dock, move_into_desktop
from app.services.file_move_service import move_file
from app.services.trash_storage import TRASH_FOCUS_PATH
from app.ui.widgets.drag_common import is_same_folder_drop


def handle_file_drop(
    source_file_path: str,
    tab_manager: TabManager,
    update_files_callback
) -> None:
    """
    Handle file drop into active folder (MOVE operation).
    Supports Desktop Focus and Trash Focus.

    Args:
        source_file_path: Path to the file being dropped.
        tab_manager: TabManager instance for getting active folder.
        update_files_callback: Callback to refresh file list after move.
    """
    active_folder = tab_manager.get_active_folder()
    if not active_folder:
        return

    # Prevent dropping into Trash Focus (use delete action instead)
    if active_folder == TRASH_FOCUS_PATH:
        return

    # Check if file is already in the active folder (same-folder drop)
    if is_same_folder_drop(source_file_path, tab_manager):
        return

    # Check if source file still exists before moving
    if not os.path.exists(source_file_path):
        # File was already moved or deleted, don't try to move it
        return

    # Get watcher from TabManager to block events during move
    watcher = tab_manager.get_watcher() if hasattr(tab_manager, 'get_watcher') else None
    
    # Handle Desktop Focus specially - COPY files (don't move)
    if is_desktop_focus(active_folder):
        result = copy_into_dock(source_file_path, watcher=watcher)
    else:
        # Normal folder move
        result = move_file(source_file_path, active_folder, watcher=watcher)
    
    if result.success:
        update_files_callback()


def handle_drag_enter(event: QDragEnterEvent, tab_manager: TabManager = None) -> None:
    """Handle drag enter as fallback."""
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    # Prevent drag and drop FROM dock TO dock
    if tab_manager:
        active_folder = tab_manager.get_active_folder()
        if active_folder and is_desktop_focus(active_folder):
            # Check if any dragged file is from dock
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path and is_file_in_dock(file_path):
                    # Dragging from dock to dock - ignore
                    event.ignore()
                    return
    
    # Accept any action Windows proposes
    event.acceptProposedAction()


def handle_drag_move(event: QDragMoveEvent, tab_manager: TabManager = None) -> None:
    """Handle drag move as fallback."""
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    # Prevent drag and drop FROM dock TO dock
    if tab_manager:
        active_folder = tab_manager.get_active_folder()
        if active_folder and is_desktop_focus(active_folder):
            # Check if any dragged file is from dock
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path and is_file_in_dock(file_path):
                    # Dragging from dock to dock - ignore
                    event.ignore()
                    return
    
    # Always accept if we have URLs
    event.accept()


def handle_drop(
    event: QDropEvent,
    tab_manager: TabManager,
    update_files_callback
) -> None:
    """
    Handle file drop as fallback.

    Args:
        event: Drop event.
        tab_manager: TabManager instance for checking active folder.
        update_files_callback: Callback to refresh file list after move.
    """
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    active_folder = tab_manager.get_active_folder()
    is_desktop = is_desktop_focus(active_folder) if active_folder else False
    
    # Prevent drag and drop FROM dock TO dock
    if is_desktop:
        # Check if any dragged file is from dock
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and is_file_in_dock(file_path):
                # Dragging from dock to dock - ignore
                event.ignore()
                return
    
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if file_path and (os.path.isfile(file_path) or os.path.isdir(file_path)):
            # Process both files and folders
            # Check if same-folder drop before processing
            if is_same_folder_drop(file_path, tab_manager):
                event.ignore()
                return
            handle_file_drop(file_path, tab_manager, update_files_callback)
    
    # For Desktop Focus, use CopyAction (files are copied, not moved)
    # For other folders, use MoveAction
    if is_desktop:
        event.setDropAction(Qt.DropAction.CopyAction)
    else:
        if event.proposedAction() != Qt.DropAction.IgnoreAction:
            event.setDropAction(event.proposedAction())
        else:
            event.setDropAction(Qt.DropAction.MoveAction)
    event.accept()

