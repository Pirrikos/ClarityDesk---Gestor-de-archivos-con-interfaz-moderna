"""
FileTileEvents - Event handling for FileTile.

Handles mouse and drag events for file tiles.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent

from app.ui.widgets.file_tile_drag import handle_drag_enter, handle_drag_move, handle_drop
from app.ui.widgets.tile_drag_handler import handle_tile_drag


def mouse_press_event(tile, event: QMouseEvent) -> None:
    """Handle mouse press."""
    if event.button() == Qt.MouseButton.LeftButton:
        tile._drag_start_position = event.pos()
        if not tile._disable_hover:
            if tile._parent_view is not None and hasattr(tile._parent_view, '_select_tile'):
                tile._parent_view._select_tile(tile, event.modifiers())
    event.accept()


def mouse_move_event(tile, event: QMouseEvent) -> None:
    """Handle mouse move for drag."""
    if not (event.buttons() & Qt.MouseButton.LeftButton) or tile._drag_start_position is None:
        return
    
    selected_tiles = tile._get_selected_tiles()
    icon_service = tile._get_icon_service()
    
    if handle_tile_drag(
        tile._file_path, tile._icon_pixmap, tile._parent_view,
        tile._drag_start_position, event.pos(),
        selected_tiles=selected_tiles,
        icon_service=icon_service
    ):
        tile._drag_start_position = None


def mouse_release_event(tile, event: QMouseEvent) -> None:
    """Reset drag start position."""
    tile._drag_start_position = None
    from PySide6.QtWidgets import QWidget
    QWidget.mouseReleaseEvent(tile, event)


def mouse_double_click_event(tile, event: QMouseEvent) -> None:
    """Handle double-click to open file."""
    tile._parent_view.open_file.emit(tile._file_path)
    from PySide6.QtWidgets import QWidget
    QWidget.mouseDoubleClickEvent(tile, event)


def drag_enter_event(tile, event: QDragEnterEvent) -> None:
    """Handle drag enter on folder tile."""
    handle_drag_enter(tile, event)


def drag_move_event(tile, event: QDragMoveEvent) -> None:
    """Handle drag move on folder tile."""
    handle_drag_move(tile, event)


def drop_event(tile, event: QDropEvent) -> None:
    """Handle file drop on folder tile."""
    handle_drop(tile, event)

