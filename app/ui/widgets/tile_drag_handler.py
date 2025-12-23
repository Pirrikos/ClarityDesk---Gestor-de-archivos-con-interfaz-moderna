"""
TileDragHandler - Drag out handler for file tiles.

Handles drag out operations from file tiles with file deletion logic.
Supports single and multiple tile drag operations.
"""

import os

from PySide6.QtCore import QMimeData, QPoint, QSize, Qt, QUrl, QTimer
from PySide6.QtGui import QDrag, QPixmap
from PySide6.QtWidgets import QApplication

from app.services.desktop_path_helper import get_desktop_path
from app.services.desktop_operations import is_file_in_dock
from app.services.icon_service import IconService
from app.ui.widgets.drag_preview_helper import create_multi_file_preview


def handle_tile_drag(
    file_path: str,
    icon_pixmap,
    parent_view,
    drag_start_position: QPoint,
    mouse_pos: QPoint,
    selected_tiles: set = None,
    icon_service: IconService = None,
    all_files: list[str] = None  # For stacks: all files to drag
) -> bool:
    """
    Handle drag operation from file tile.
    
    Args:
        file_path: Path of the tile being dragged.
        icon_pixmap: Icon pixmap for the tile.
        parent_view: Parent view widget.
        drag_start_position: Position where drag started.
        mouse_pos: Current mouse position.
        selected_tiles: Set of selected tiles (optional, for multi-select).
        icon_service: IconService for generating previews (optional).
    
    Returns:
        True if drag was initiated, False otherwise.
    """
    distance = (mouse_pos - drag_start_position).manhattanLength()
    if distance <= 4:
        return False

    # Use all_files if provided (for stacks), otherwise get from selected tiles
    if all_files:
        file_paths = all_files
    else:
        file_paths = _get_drag_file_paths(file_path, selected_tiles)
    
    if not file_paths:
        return False

    drag = _create_drag_object(parent_view, file_paths, icon_pixmap, icon_service)
    if not drag:
        return False
    
    original_file_paths = file_paths.copy()
    
    # Check if files are from dock
    files_from_dock = [fp for fp in original_file_paths if is_file_in_dock(fp)]
    
    # Allow both MoveAction and CopyAction
    # Windows will choose:
    # - CopyAction for external services (mail, web, etc.)
    # - MoveAction for desktop and folders (we handle this)
    returned_action = drag.exec(Qt.DropAction.MoveAction | Qt.DropAction.CopyAction)
    
    # Emit deleted for files that were moved (not copied)
    # Files from dock that are moved should be removed from dock
    if returned_action == Qt.DropAction.MoveAction:
        for file_path in original_file_paths:
            if not os.path.exists(file_path):
                parent_view.file_deleted.emit(file_path)
    elif returned_action == Qt.DropAction.CopyAction:
        # Copy action - files remain in dock (Windows handles copy to external services)
        # But if file was copied to desktop, we might want to handle it differently
        # For now, files remain in dock when copied
        pass
    
    # Force cleanup of drag preview artifacts (Qt/Windows bug workaround)
    _cleanup_drag_visual(parent_view)
    
    return True


def _cleanup_drag_visual(parent_view) -> None:
    """Force cleanup of drag preview visual artifacts."""
    # Clear any pending events
    QApplication.processEvents()
    
    # Reset cursor to ensure drag cursor is cleared
    QApplication.restoreOverrideCursor()
    
    # Force immediate repaint of view
    if hasattr(parent_view, 'update'):
        parent_view.update()
    
    # Force repaint of window
    if hasattr(parent_view, 'window'):
        window = parent_view.window()
        if window:
            window.update()
    
    # Schedule additional cleanup after event loop processes
    QTimer.singleShot(50, lambda: _delayed_cleanup(parent_view))


def _delayed_cleanup(parent_view) -> None:
    """Delayed cleanup to ensure drag artifacts are cleared."""
    try:
        QApplication.processEvents()
        if hasattr(parent_view, 'repaint'):
            parent_view.repaint()
        if hasattr(parent_view, 'window'):
            window = parent_view.window()
            if window:
                window.repaint()
    except RuntimeError:
        # Widget may have been deleted
        pass


def _create_drag_object(parent_view, file_paths: list[str], icon_pixmap, icon_service: IconService) -> QDrag:
    """Create and configure QDrag object with preview and hot spot."""
    drag = QDrag(parent_view)
    mime_data = QMimeData()
    urls = [QUrl.fromLocalFile(path) for path in file_paths]
    mime_data.setUrls(urls)
    drag.setMimeData(mime_data)
    
    preview_pixmap = _get_drag_preview(file_paths, icon_pixmap, icon_service)
    if not preview_pixmap.isNull():
        drag.setPixmap(preview_pixmap)
        # Center cursor on pixmap
        hot_spot = QPoint(preview_pixmap.width() // 2, preview_pixmap.height() // 2)
        drag.setHotSpot(hot_spot)
    
    return drag


def _get_drag_file_paths(file_path: str, selected_tiles: set) -> list[str]:
    """Get list of file paths to include in drag operation."""
    if not selected_tiles or len(selected_tiles) <= 1:
        return [file_path]
    
    file_paths = []
    seen_paths = set()
    
    for tile in selected_tiles:
        if hasattr(tile, '_file_path'):
            tile_path = tile._file_path
            if tile_path and tile_path not in seen_paths:
                file_paths.append(tile_path)
                seen_paths.add(tile_path)
    
    if file_path not in seen_paths:
        file_paths.insert(0, file_path)
    
    return file_paths if file_paths else [file_path]


def _get_drag_preview(
    file_paths: list[str],
    icon_pixmap: QPixmap,
    icon_service: IconService
) -> QPixmap:
    """Get preview pixmap for drag operation."""
    if len(file_paths) == 1 and icon_pixmap and not icon_pixmap.isNull():
        return icon_pixmap
    
    if icon_service and len(file_paths) > 1:
        return create_multi_file_preview(file_paths, icon_service, QSize(48, 48))
    
    if icon_pixmap and not icon_pixmap.isNull():
        return icon_pixmap
    
    return QPixmap()



