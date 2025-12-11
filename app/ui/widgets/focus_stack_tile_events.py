"""
Event handlers for FocusStackTile.

Handles mouse, drag & drop, and hover events.
"""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QCursor, QMouseEvent


def handle_mouse_press(event: QMouseEvent, drag_start_position: QPoint) -> QPoint:
    """Handle mouse press - store drag start position."""
    if event.button() == Qt.MouseButton.LeftButton:
        return event.pos()
    return drag_start_position


def handle_mouse_release(
    event: QMouseEvent,
    drag_start_position: QPoint,
    folder_path: str,
    focus_clicked_signal
) -> QPoint:
    """Handle mouse release - emit clicked signal if it was a click."""
    if event.button() == Qt.MouseButton.LeftButton:
        if drag_start_position:
            distance = (event.pos() - drag_start_position).manhattanLength()
            if distance < 5:  # Click threshold
                focus_clicked_signal.emit(folder_path)
        return None
    return drag_start_position


def update_remove_button_position(remove_button, container_widget) -> None:
    """Update remove button position relative to container."""
    if remove_button and container_widget:
        container_x = container_widget.x()
        container_y = container_widget.y()
        button_x = container_x + container_widget.width() - 20
        button_y = container_y + 2
        remove_button.move(button_x, button_y)
        remove_button.raise_()


def hide_remove_button_if_not_hovered(remove_button, is_hovered: bool) -> None:
    """Hide remove button if tile is not hovered."""
    if not is_hovered and remove_button:
        cursor_pos = QCursor.pos()
        button_global_rect = remove_button.geometry()
        button_global_rect.moveTopLeft(remove_button.mapToGlobal(button_global_rect.topLeft()))
        if not button_global_rect.contains(cursor_pos):
            remove_button.setVisible(False)

