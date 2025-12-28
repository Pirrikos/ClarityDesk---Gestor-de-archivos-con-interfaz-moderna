"""
TileDragHandler - Drag out handler for file tiles.

Handles drag out operations from file tiles with file deletion logic.
Supports single and multiple tile drag operations.
"""

from PySide6.QtCore import QMimeData, QPoint, Qt, QUrl
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QApplication

from app.services.icon_service import IconService
from app.ui.widgets.drag_preview_helper import (
    calculate_drag_hotspot,
    get_drag_preview_pixmap
)


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
    
    # Allow both Move and Copy - Windows will choose based on drop target
    # MoveAction: file moves to destination (deleted from source)
    # CopyAction: file copied to destination (source remains)
    allowed_actions = Qt.DropAction.MoveAction | Qt.DropAction.CopyAction
    drag.exec(allowed_actions, Qt.DropAction.MoveAction)
    
    # Force cleanup of drag preview artifacts (Qt/Windows bug workaround)
    _cleanup_drag_visual(parent_view)
    
    return True


def _cleanup_drag_visual(parent_view) -> None:
    """Force cleanup of drag preview visual artifacts."""
    # Reset cursor to ensure drag cursor is cleared
    QApplication.restoreOverrideCursor()
    
    # Force repaint without processEvents (avoids triggering stale signals)
    if hasattr(parent_view, 'update'):
        parent_view.update()


def _create_drag_object(parent_view, file_paths: list[str], icon_pixmap, icon_service: IconService) -> QDrag:
    """Create and configure QDrag object with preview and hot spot."""
    drag = QDrag(parent_view)
    mime_data = QMimeData()
    urls = [QUrl.fromLocalFile(path) for path in file_paths]
    mime_data.setUrls(urls)
    
    # Marcar como drag interno para que los drop handlers puedan detectarlo
    # Los drop handlers internos pueden usar MoveAction para reorganización
    mime_data.setProperty("internal_drag_source", id(parent_view))
    
    drag.setMimeData(mime_data)
    
    preview_pixmap = get_drag_preview_pixmap(file_paths, icon_service, icon_pixmap)
    if not preview_pixmap.isNull():
        drag.setPixmap(preview_pixmap)
        drag.setHotSpot(calculate_drag_hotspot(preview_pixmap))
    
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

