"""
Drag & drop handlers for FocusStackTile.

Handles drag enter, leave, move, and drop events.
"""

from PySide6.QtCore import QTimer


def handle_drag_enter(event, hover_timer, tile_instance) -> None:
    """Handle drag enter - accept if dragging files and start hover timer."""
    if event.mimeData().hasUrls():
        tile_instance._is_dragging_over = True
        tile_instance.update()
        
        if not hover_timer:
            hover_timer = QTimer(tile_instance)
            hover_timer.setSingleShot(True)
            hover_timer.timeout.connect(tile_instance._on_hover_timeout)
            tile_instance._hover_timer = hover_timer
        hover_timer.start(600)
        
        event.acceptProposedAction()
    else:
        event.ignore()


def handle_drag_leave(tile_instance) -> None:
    """Handle drag leave - reset state."""
    tile_instance._is_dragging_over = False
    tile_instance.update()


def handle_drag_move(event) -> None:
    """Handle drag move - keep accepting."""
    if event.mimeData().hasUrls():
        event.acceptProposedAction()
    else:
        event.ignore()


def handle_drop(event, folder_path: str, tile_instance) -> None:
    """Handle drop - emit signal for file move to Focus root."""
    if event.mimeData().hasUrls():
        import os
        file_paths = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path and os.path.exists(local_path):
                file_paths.append(local_path)
        
        if file_paths and hasattr(tile_instance.parent(), 'files_dropped_on_focus'):
            tile_instance.parent().files_dropped_on_focus.emit(folder_path, file_paths)
        
        tile_instance._is_dragging_over = False
        tile_instance.update()
        event.acceptProposedAction()
    else:
        event.ignore()

