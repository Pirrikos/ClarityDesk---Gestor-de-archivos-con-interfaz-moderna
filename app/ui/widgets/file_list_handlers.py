"""
Event handlers for FileListView.

Handles drag, mouse, and checkbox events.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QCheckBox, QTableWidgetItem

from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import is_file_in_dock, move_out_of_desktop
from app.services.file_move_service import move_file
from app.ui.widgets.drag_common import get_watcher_from_view, is_folder_inside_itself
from app.ui.widgets.list_drag_handler import (
    handle_drag_enter,
    handle_drag_move,
    handle_drop,
    handle_start_drag,
)

if TYPE_CHECKING:
    from app.managers.tab_manager import TabManager
    from app.services.icon_service import IconService
    from app.ui.widgets.file_list_view import FileListView


def start_drag(
    view: 'FileListView',
    icon_service: 'IconService',
    file_deleted_signal: Callable[[str], None]
) -> None:
    """Handle drag start for file copy or move using checkbox selection or traditional selection."""
    selected_items = get_selected_items_for_drag(view)
    if selected_items:
        handle_start_drag(selected_items, icon_service, None, file_deleted_signal)


def get_selected_items_for_drag(view: 'FileListView') -> list[QTableWidgetItem]:
    """Get selected items for drag operation - uses checkboxes if available, otherwise traditional selection."""
    selected_items = []
    
    if view._checked_paths:
        for row in range(view.rowCount()):
            item = view.item(row, 1)
            if item:
                path = item.data(Qt.ItemDataRole.UserRole)
                if path and path in view._checked_paths:
                    selected_items.append(item)
    
    if not selected_items:
        for item in view.selectedItems():
            if item and item.column() == 1:
                selected_items.append(item)
    
    if not selected_items:
        current_row = view.currentRow()
        if current_row >= 0:
            current_item = view.item(current_row, 1)
            if current_item:
                selected_items.append(current_item)
    
    return selected_items


def drag_enter_event(
    view: 'FileListView',
    event: QDragEnterEvent,
    tab_manager: Optional['TabManager']
) -> None:
    """Handle drag enter for file drop - supports folders in list."""
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    item = view.itemAt(event.pos())
    if item:
        item_path = item.data(Qt.ItemDataRole.UserRole)
        if item_path and os.path.isdir(item_path):
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path and os.path.exists(file_path) and os.path.isdir(file_path):
                    if is_folder_inside_itself(file_path, item_path):
                        event.ignore()
                        return
            event.acceptProposedAction()
            return
    
    handle_drag_enter(event, mime_data, tab_manager)


def drag_move_event(
    view: 'FileListView',
    event: QDragMoveEvent,
    tab_manager: Optional['TabManager']
) -> None:
    """Handle drag move to maintain drop acceptance - supports folders in list."""
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    item = view.itemAt(event.pos())
    if item:
        item_path = item.data(Qt.ItemDataRole.UserRole)
        if item_path and os.path.isdir(item_path):
            event.accept()
            return
    
    handle_drag_move(event, mime_data, tab_manager)


def drop_event(
    view: 'FileListView',
    event: QDropEvent,
    tab_manager: 'TabManager',
    file_dropped_signal: Callable[[str], None]
) -> None:
    """Handle file drop into list view - supports drop on specific folder items."""
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    item = view.itemAt(event.pos())
    target_folder_path = None
    
    if item:
        item_path = item.data(Qt.ItemDataRole.UserRole)
        if item_path and os.path.isdir(item_path):
            target_folder_path = item_path
    
    if target_folder_path:
        _handle_drop_on_folder(view, event, mime_data, target_folder_path, file_dropped_signal)
        return
    
    handle_drop(event, mime_data, tab_manager, file_dropped_signal)


def mouse_press_event(view: 'FileListView', event: QMouseEvent) -> None:
    """Handle mouse press - toggle checkbox with Ctrl+click."""
    if event.button() == Qt.MouseButton.RightButton:
        return
    
    if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
        if toggle_checkbox_at_position(view, event.pos()):
            event.accept()
            return
    
    view.__class__.__bases__[0].mousePressEvent(view, event)


def toggle_checkbox_at_position(view: 'FileListView', pos: QPoint) -> bool:
    """Toggle checkbox at given position. Returns True if toggled."""
    item = view.itemAt(pos)
    if not item:
        return False
    checkbox = get_checkbox_from_row(view, item.row())
    if checkbox:
        checkbox.setChecked(not checkbox.isChecked())
        return True
    return False


def get_checkbox_from_row(view: 'FileListView', row: int) -> Optional[QCheckBox]:
    """Get checkbox widget from row's column 0."""
    widget = view.cellWidget(row, 0)
    if isinstance(widget, QCheckBox):
        return widget
    return None


def on_item_double_clicked(
    view: 'FileListView',
    item: QTableWidgetItem,
    open_file_signal: Callable[[str], None]
) -> None:
    """Handle double-click on table row."""
    file_path = item.data(Qt.ItemDataRole.UserRole)
    if file_path:
        open_file_signal.emit(file_path)


def on_checkbox_changed(view: 'FileListView', file_path: str, state: int) -> None:
    """Handle checkbox state change to update selection set."""
    if Qt.CheckState(state) == Qt.CheckState.Checked:
        view._checked_paths.add(file_path)
    else:
        view._checked_paths.discard(file_path)
    
    # Actualizar estado del checkbox del header
    if hasattr(view, '_update_header_checkbox_state'):
        view._update_header_checkbox_state()


def _handle_drop_on_folder(
    view: 'FileListView',
    event: QDropEvent,
    mime_data: QMimeData,
    target_folder_path: str,
    file_dropped_signal: Callable[[str], None]
) -> None:
    """Handle file drop on specific folder item in list view."""
    moved_any = False
    
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if not file_path or not os.path.exists(file_path):
            continue
        
        if os.path.isdir(file_path):
            if is_folder_inside_itself(file_path, target_folder_path):
                continue
        
        watcher = get_watcher_from_view(view)
        
        file_dir = os.path.dirname(os.path.abspath(file_path))
        is_folder = os.path.isdir(file_path)
        
        if is_desktop_focus(file_dir) and not is_file_in_dock(file_path):
            result = move_out_of_desktop(file_path, target_folder_path, watcher=watcher)
        else:
            result = move_file(file_path, target_folder_path, watcher=watcher)
        
        if result.success:
            moved_any = True
            if is_folder:
                new_path = str(Path(target_folder_path) / Path(file_path).name)
                if hasattr(view, 'folder_moved'):
                    view.folder_moved.emit(file_path, new_path)
            if hasattr(view, 'file_deleted'):
                view.file_deleted.emit(file_path)
    
    if moved_any:
        event.accept()
    else:
        event.ignore()

