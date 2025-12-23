"""
FolderTreeDragHandler - Drag and drop handler for FolderTreeSidebar.

Handles drag and drop operations on tree nodes.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QTreeView

from app.services.file_move_service import move_file
from app.services.path_utils import normalize_path


def _is_invalid_drop_target(source_path: str, target_path: str) -> bool:
    """
    Verificar si el drop es inválido (mismo path o uno dentro del otro).
    """
    source_abs = normalize_path(os.path.abspath(source_path))
    target_abs = normalize_path(os.path.abspath(target_path))
    return (source_abs == target_abs or 
            source_abs.startswith(target_abs + os.sep) or 
            target_abs.startswith(source_abs + os.sep))


def handle_drag_enter(event) -> None:
    """Handle drag enter on tree view."""
    # Drag externo: solo acepta archivos/carpetas con URLs
    mime_data = event.mimeData()
    if mime_data.hasUrls():
        # Check if at least one valid file/folder
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and os.path.exists(file_path):
                event.acceptProposedAction()
                return
    event.ignore()


def handle_drag_move(event, tree_view: QTreeView, model: QStandardItemModel) -> None:
    """Handle drag move over tree view."""
    # Convert widget coordinates to tree view coordinates
    tree_pos = tree_view.mapFromParent(event.pos())
    index = tree_view.indexAt(tree_pos)
    if not index.isValid():
        event.ignore()
        return
    
    item = model.itemFromIndex(index)
    if not item:
        event.ignore()
        return
    
    target_path = item.data(Qt.ItemDataRole.UserRole)
    if not target_path or not os.path.isdir(target_path):
        event.ignore()
        return
    
    mime_data = event.mimeData()
    if mime_data.hasUrls():
        # Validación: target debe ser carpeta válida, bloquear soltar dentro de sí misma
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and os.path.exists(file_path):
                if os.path.isdir(file_path):
                    if _is_invalid_drop_target(file_path, target_path):
                        event.ignore()
                        return
        event.accept()
    else:
        event.ignore()


def handle_drop(event, tree_view: QTreeView, model: QStandardItemModel, watcher=None, path_to_item: dict[str, object] = None) -> list[str]:
    """Mover archivos a carpeta destino al soltar en nodo del árbol."""
    target_path = get_drop_target_path(event, tree_view, model)
    if not target_path:
        return []
    
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        return []
    
    # Validación centralizada: rechazar drag externo si el origen está en el sidebar
    if path_to_item is not None:
        normalized_target = normalize_path(os.path.abspath(target_path))
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and os.path.exists(file_path):
                normalized_source = normalize_path(os.path.abspath(file_path))
                # Verificar si source está en el sidebar
                if normalized_source in path_to_item:
                    # Source está en el sidebar, rechazar drop completo
                    return []
                
                # También verificar si el target está en el sidebar Y es diferente del source
                # (esto previene mover carpetas del sidebar a otras carpetas del sidebar)
                if normalized_target in path_to_item and normalized_source != normalized_target:
                    # Intentando mover dentro del sidebar, rechazar
                    return []
    
    return _process_dropped_files(mime_data, target_path, watcher)


def get_drop_target_path(event, tree_view: QTreeView, model: QStandardItemModel) -> str:
    """Get target folder path from drop event (public for reuse)."""
    tree_pos = tree_view.mapFromParent(event.pos())
    index = tree_view.indexAt(tree_pos)
    if not index.isValid():
        return None
    
    item = model.itemFromIndex(index)
    if not item:
        return None
    
    target_path = item.data(Qt.ItemDataRole.UserRole)
    if not target_path or not os.path.isdir(target_path):
        return None
    
    return target_path


def _process_dropped_files(mime_data, target_path: str, watcher=None) -> list[str]:
    """Procesar archivos soltados y retornar lista de paths movidos exitosamente."""
    # Drag externo: mover archivos al filesystem según origen
    moved_paths = []
    
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if not file_path or not os.path.exists(file_path):
            continue
        
        # Skip if trying to move folder into itself
        if os.path.isdir(file_path):
            if _is_invalid_drop_target(file_path, target_path):
                continue
        
        # Check if file is from Desktop Focus
        from app.services.desktop_path_helper import is_desktop_focus
        from app.services.desktop_operations import move_out_of_desktop
        file_dir = os.path.dirname(os.path.abspath(file_path))
        if is_desktop_focus(file_dir):
            result = move_out_of_desktop(file_path, target_path, watcher=watcher)
        else:
            result = move_file(file_path, target_path, watcher=watcher)
        if result.success:
            moved_paths.append(file_path)
    
    return moved_paths

