"""
ListDragHandler - Drag and drop handler for list view.

Handles drag out and drop in operations for the list view.
"""

import os

from PySide6.QtCore import QMimeData, QPoint, QSize, Qt, QUrl
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QTableWidgetItem

from app.managers.tab_manager import TabManager
from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import is_file_in_dock
from app.services.icon_service import IconService
from app.ui.widgets.drag_common import check_files_after_drag, is_same_folder_drop
from app.ui.widgets.drag_preview_helper import create_multi_file_preview


def handle_start_drag(
    selected_items: list,
    icon_service: IconService,
    delete_service,
    file_deleted_signal
) -> None:
    """
    Handle drag start for file copy or move.
    
    Supports multiple file selection - includes all selected files in drag operation.
    """
    if not selected_items:
        return
    
    file_paths = _extract_file_paths_from_items(selected_items)
    if not file_paths:
        return
    
    drag = QDrag(selected_items[0].tableWidget())
    mime_data = QMimeData()
    urls = [QUrl.fromLocalFile(path) for path in file_paths]
    mime_data.setUrls(urls)
    drag.setMimeData(mime_data)
    
    preview_pixmap = create_multi_file_preview(file_paths, icon_service, QSize(48, 48))
    if not preview_pixmap.isNull():
        drag.setPixmap(preview_pixmap)
        # Center cursor on pixmap
        hot_spot = QPoint(preview_pixmap.width() // 2, preview_pixmap.height() // 2)
        drag.setHotSpot(hot_spot)
    
    original_file_paths = file_paths.copy()
    original_dir = os.path.dirname(os.path.abspath(original_file_paths[0])) if original_file_paths else None
    returned_action = drag.exec(Qt.DropAction.MoveAction | Qt.DropAction.CopyAction)
    
    if returned_action != Qt.DropAction.IgnoreAction:
        check_files_after_drag(original_file_paths, original_dir, file_deleted_signal.emit)


def _extract_file_paths_from_items(selected_items: list) -> list[str]:
    """Extract unique file paths from selected table items."""
    file_paths = []
    seen_paths = set()
    
    for item in selected_items:
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and file_path not in seen_paths:
            file_paths.append(file_path)
            seen_paths.add(file_path)
    
    return file_paths




def handle_drag_enter(event, mime_data: QMimeData, tab_manager: TabManager = None) -> None:
    """Handle drag enter for file drop."""
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


def handle_drag_move(event, mime_data: QMimeData, tab_manager: TabManager = None) -> None:
    """Handle drag move to maintain drop acceptance."""
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
    event,
    mime_data: QMimeData,
    tab_manager: TabManager,
    file_dropped_signal
) -> None:
    """
    Handle file drop into list view.

    Args:
        event: Drop event.
        mime_data: MIME data from event.
        tab_manager: TabManager for checking active folder.
        file_dropped_signal: Signal to emit when file is dropped.
    """
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
            # Check if same-folder drop before emitting
            if is_same_folder_drop(file_path, tab_manager):
                event.ignore()
                return
            file_dropped_signal.emit(file_path)
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

