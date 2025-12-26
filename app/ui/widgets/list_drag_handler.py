"""
ListDragHandler - Drag and drop handler for list view.

Handles drag out and drop in operations for the list view.
"""

import os
from typing import Callable, Optional, Union

from PySide6.QtCore import QMimeData, QPoint, QSize, Qt, QUrl
from PySide6.QtGui import QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QTableWidgetItem

from app.managers.tab_manager import TabManager
from app.services.icon_service import IconService
from app.ui.widgets.drag_common import (
    is_same_folder_drop,
    should_reject_dock_to_dock_drop
)
from app.ui.widgets.drag_preview_helper import (
    calculate_drag_hotspot,
    get_drag_preview_pixmap
)


def handle_start_drag(
    selected_items: list[QTableWidgetItem],
    icon_service: IconService
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
    
    # Marcar como drag interno para que los drop handlers puedan detectarlo
    mime_data.setProperty("internal_drag_source", id(selected_items[0].tableWidget()))
    
    drag.setMimeData(mime_data)
    
    preview_pixmap = get_drag_preview_pixmap(file_paths, icon_service)
    if not preview_pixmap.isNull():
        drag.setPixmap(preview_pixmap)
        drag.setHotSpot(calculate_drag_hotspot(preview_pixmap))
    
    returned_action = drag.exec(Qt.DropAction.CopyAction)
    
    if returned_action == Qt.DropAction.CopyAction:
        pass
    elif returned_action == Qt.DropAction.IgnoreAction:
        pass


def _extract_file_paths_from_items(selected_items: list[QTableWidgetItem]) -> list[str]:
    """Extract unique file paths from selected table items."""
    file_paths = []
    seen_paths = set()
    
    for item in selected_items:
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and file_path not in seen_paths:
            file_paths.append(file_path)
            seen_paths.add(file_path)
    
    return file_paths


def _handle_drag_event(event: Union[QDragEnterEvent, QDragMoveEvent], mime_data: QMimeData, tab_manager: Optional[TabManager] = None) -> bool:
    """
    Handle common drag event logic.
    
    Args:
        event: Drag event (QDragEnterEvent or QDragMoveEvent).
        mime_data: MIME data from event.
        tab_manager: TabManager instance for checking active folder.
    
    Returns:
        True if event should be accepted, False otherwise.
    """
    if not mime_data.hasUrls():
        return False
    
    # Prevent dock-to-dock drops (igual que grid)
    if should_reject_dock_to_dock_drop(mime_data, tab_manager):
        return False
    
    # Aceptar acción propuesta por Windows (igual que grid)
    return True


def handle_drag_enter(event: QDragEnterEvent, mime_data: QMimeData, tab_manager: Optional[TabManager] = None) -> None:
    """Handle drag enter for file drop - igual que grid."""
    if _handle_drag_event(event, mime_data, tab_manager):
        event.acceptProposedAction()
    else:
        event.ignore()


def handle_drag_move(event: QDragMoveEvent, mime_data: QMimeData, tab_manager: Optional[TabManager] = None) -> None:
    """Handle drag move to maintain drop acceptance - igual que grid."""
    if _handle_drag_event(event, mime_data, tab_manager):
        event.acceptProposedAction()
    else:
        event.ignore()

def handle_drop(
    event: QDropEvent,
    mime_data: QMimeData,
    tab_manager: TabManager,
    file_dropped_signal: Callable[[str], None]
) -> None:
    """
    Handle file drop into list view - igual que grid.

    Args:
        event: Drop event.
        mime_data: MIME data from event.
        tab_manager: TabManager for checking active folder.
        file_dropped_signal: Signal to emit when file is dropped.
    """
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    # Prevent drag and drop FROM dock TO dock (igual que grid)
    if should_reject_dock_to_dock_drop(mime_data, tab_manager):
        event.ignore()
        return
    
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if file_path and (os.path.isfile(file_path) or os.path.isdir(file_path)):
            # Check if same-folder drop before emitting
            if is_same_folder_drop(file_path, tab_manager):
                event.ignore()
                return
            file_dropped_signal.emit(file_path)
    
    # Usar acción propuesta o MoveAction como fallback (igual que grid)
    if event.proposedAction() != Qt.DropAction.IgnoreAction:
        event.setDropAction(event.proposedAction())
    else:
        event.setDropAction(Qt.DropAction.MoveAction)
    event.accept()

