"""
Event handlers for FileListView.

Handles drag, mouse, and checkbox events.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QCheckBox, QTableWidgetItem, QWidget

from app.ui.widgets.list_drag_handler import (
    handle_drag_enter,
    handle_drag_move,
    handle_drop,
    handle_start_drag,
)


def start_drag(view, supported_actions, icon_service, file_deleted_signal) -> None:
    """Handle drag start for file copy or move using checkbox selection."""
    if not view._checked_paths:
        return
    selected_items = get_selected_items_for_drag(view)
    if selected_items:
        handle_start_drag(selected_items, icon_service, None, file_deleted_signal)


def get_selected_items_for_drag(view) -> list:
    """Get selected items for drag operation."""
    selected_items = []
    for row in range(view.rowCount()):
        item = view.item(row, 1)
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path and path in view._checked_paths:
                selected_items.append(path)
    return selected_items


def drag_enter_event(view, event, tab_manager) -> None:
    """Handle drag enter for file drop."""
    handle_drag_enter(event, event.mimeData(), tab_manager)


def drag_move_event(view, event, tab_manager) -> None:
    """Handle drag move to maintain drop acceptance."""
    handle_drag_move(event, event.mimeData(), tab_manager)


def drop_event(view, event, tab_manager, file_dropped_signal) -> None:
    """Handle file drop into list view."""
    handle_drop(event, event.mimeData(), tab_manager, file_dropped_signal)


def mouse_press_event(view, event: QMouseEvent) -> None:
    """Handle mouse press - toggle checkbox with Ctrl+click."""
    if event.button() == Qt.MouseButton.RightButton:
        return
    
    if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
        if toggle_checkbox_at_position(view, event.pos()):
            event.accept()
            return
    
    view.__class__.__bases__[0].mousePressEvent(view, event)


def toggle_checkbox_at_position(view, pos) -> bool:
    """Toggle checkbox at given position. Returns True if toggled."""
    item = view.itemAt(pos)
    if not item:
        return False
    checkbox = get_checkbox_from_row(view, item.row())
    if checkbox:
        checkbox.setChecked(not checkbox.isChecked())
        return True
    return False


def get_checkbox_from_row(view, row: int) -> Optional[QCheckBox]:
    """Get checkbox widget from row's column 0."""
    widget = view.cellWidget(row, 0)
    if not isinstance(widget, QWidget):
        return None
    layout = widget.layout()
    if layout and layout.count() > 0:
        checkbox = layout.itemAt(0).widget()
        if isinstance(checkbox, QCheckBox):
            return checkbox
    return None


def on_item_double_clicked(view, item: QTableWidgetItem, open_file_signal) -> None:
    """Handle double-click on table row."""
    file_path = item.data(Qt.ItemDataRole.UserRole)
    if file_path:
        open_file_signal.emit(file_path)


def on_checkbox_changed(view, file_path: str, state: int) -> None:
    """Handle checkbox state change to update selection set."""
    if Qt.CheckState(state) == Qt.CheckState.Checked:
        view._checked_paths.add(file_path)
    else:
        view._checked_paths.discard(file_path)

