"""
FileTileEvents - Event handling for FileTile.

Handles mouse and drag events for file tiles.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QWidget

from app.ui.widgets.file_tile_drag import handle_drag_enter, handle_drag_move, handle_drop
from app.ui.widgets.tile_drag_handler import handle_tile_drag
from app.ui.widgets.window_focus_utils import activate_parent_window

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def mouse_press_event(tile: 'FileTile', event: QMouseEvent) -> None:
    """Handle mouse press."""
    if event.button() == Qt.MouseButton.LeftButton:
        tile._drag_start_position = event.pos()
        if tile._parent_view is not None:
            select_tile = getattr(tile._parent_view, '_select_tile', None)
            if select_tile:
                select_tile(tile, event.modifiers())
        activate_parent_window(tile)
    event.accept()


def mouse_move_event(tile: 'FileTile', event: QMouseEvent) -> None:
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


def mouse_release_event(tile: 'FileTile', event: QMouseEvent) -> None:
    """Reset drag start position."""
    tile._drag_start_position = None
    QWidget.mouseReleaseEvent(tile, event)


def mouse_double_click_event(tile: 'FileTile', event: QMouseEvent) -> None:
    """Handle double-click to open file."""
    tile._parent_view.open_file.emit(tile._file_path)
    QWidget.mouseDoubleClickEvent(tile, event)


def drag_enter_event(tile: 'FileTile', event: QDragEnterEvent) -> None:
    """Handle drag enter on folder tile."""
    handle_drag_enter(tile, event)


def drag_move_event(tile: 'FileTile', event: QDragMoveEvent) -> None:
    """Handle drag move on folder tile."""
    handle_drag_move(tile, event)


def drop_event(tile: 'FileTile', event: QDropEvent) -> None:
    """Handle file drop on folder tile."""
    handle_drop(tile, event)

