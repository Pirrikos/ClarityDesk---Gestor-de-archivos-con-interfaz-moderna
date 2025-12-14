"""
FolderTreeReorderHandler - Drag and drop handler for reordering root folders.

Handles internal drag and drop operations to reorder root folders in the sidebar.
Only affects visual order, does not modify filesystem.
"""

import os

from PySide6.QtCore import QDataStream, QIODevice, QMimeData, Qt
from PySide6.QtGui import QDragMoveEvent, QDropEvent, QStandardItemModel
from PySide6.QtWidgets import QMessageBox, QTreeView

from app.ui.widgets.folder_tree_model import (
    is_root_folder_item,
    reorder_root_folders,
)


def is_internal_reorder_drag(event, tree_view: QTreeView) -> bool:
    """
    Check if event is an internal reorder drag (not external file drag).
    
    Args:
        event: QDragMoveEvent or QDropEvent.
        tree_view: QTreeView instance.
        
    Returns:
        True if internal reorder drag, False otherwise.
    """
    # Must be from same tree view
    if event.source() != tree_view:
        return False
    
    # Internal drags don't have URLs (external file drags do)
    mime_data = event.mimeData()
    has_urls = mime_data.hasUrls()
    
    # If it has URLs, it's an external file drag
    if has_urls:
        return False
    
    # Check if it's our custom reorder mime type or standard internal move
    # Qt's InternalMove uses "application/x-qabstractitemmodeldatalist"
    return mime_data.hasFormat("application/x-qabstractitemmodeldatalist")


def handle_reorder_drag_move(
    event: QDragMoveEvent,
    tree_view: QTreeView,
    model: QStandardItemModel
) -> bool:
    """
    Validate drag move for reordering root folders.
    
    Solo permite drop directamente sobre carpetas raíz, no dentro de ellas.
    Solo permite intercambiar posiciones arriba/abajo, no meter dentro.
    
    Args:
        event: QDragMoveEvent.
        tree_view: QTreeView instance.
        model: QStandardItemModel instance.
        
    Returns:
        True if drop is valid (target is root folder at same level), False otherwise.
    """
    # Only handle internal drags
    if not is_internal_reorder_drag(event, tree_view):
        return False
    
    tree_pos = tree_view.mapFromParent(event.pos())
    index = tree_view.indexAt(tree_pos)
    
    if not index.isValid():
        return False
    
    # Verificar que el índice no tenga padre (debe ser raíz)
    if index.parent().isValid():
        return False
    
    item = model.itemFromIndex(index)
    if not item:
        return False
    
    # Solo permitir drop sobre carpetas raíz (no dentro de ellas)
    return is_root_folder_item(item, model)


def get_dragged_index_from_mime_data(
    event: QDropEvent,
    model: QStandardItemModel,
    tree_view: QTreeView
):
    """
    Extract dragged index from Qt's internal move mime data.
    
    Args:
        event: QDropEvent.
        model: QStandardItemModel instance.
        tree_view: QTreeView instance.
        
    Returns:
        QModelIndex of dragged item, or None if not found.
    """
    mime_data = event.mimeData()
    if not mime_data.hasFormat("application/x-qabstractitemmodeldatalist"):
        return None
    
    try:
        # Decode Qt's internal format
        encoded_data = mime_data.data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)
        
        # Read the data
        while not stream.atEnd():
            row = stream.readInt32()
            col = stream.readInt32()
            map_items = stream.readInt32()
            
            # Read item data
            for _ in range(map_items):
                role = stream.readInt32()
                value = stream.readQVariant()
            
            # Return index for the first row found
            if row >= 0:
                return model.index(row, col)
    except Exception:
        # Fallback: try to get from selection or current index
        pass
    
    # Fallback: use current selection or current index
    selected_indexes = tree_view.selectedIndexes()
    if selected_indexes:
        return selected_indexes[0]
    
    return tree_view.currentIndex()


def _show_reorder_warning(parent_widget) -> None:
    """Muestra un aviso cuando se intenta meter una carpeta raíz dentro de otra."""
    msg = QMessageBox(parent_widget)
    msg.setWindowTitle("Reordenamiento no permitido")
    msg.setText(
        "No se puede meter una carpeta raíz dentro de otra.\n\n"
        "Solo se permite intercambiar posiciones entre carpetas raíz."
    )
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()


def handle_reorder_drop(
    event: QDropEvent,
    tree_view: QTreeView,
    model: QStandardItemModel,
    path_to_item: dict[str, object]
) -> bool:
    """
    Handle drop for reordering root folders.
    
    Solo permite intercambiar posiciones entre carpetas raíz.
    No permite meter una carpeta raíz dentro de otra.
    Muestra aviso si se detecta intento de meter dentro.
    
    Args:
        event: QDropEvent.
        tree_view: QTreeView instance.
        model: QStandardItemModel instance.
        path_to_item: Dictionary mapping paths to items.
        
    Returns:
        True if reordering was successful, False otherwise.
    """
    # Only handle internal drags
    if not is_internal_reorder_drag(event, tree_view):
        return False
    
    # Get target index first (before Qt potentially moves items)
    tree_pos = tree_view.mapFromParent(event.pos())
    target_index = tree_view.indexAt(tree_pos)
    
    if not target_index.isValid():
        return False
    
    # Verificar que el target no tenga padre (debe ser raíz, no hijo)
    if target_index.parent().isValid():
        _show_reorder_warning(tree_view)
        return False
    
    target_item = model.itemFromIndex(target_index)
    if not target_item or not is_root_folder_item(target_item, model):
        _show_reorder_warning(tree_view)
        return False
    
    target_path = target_item.data(Qt.ItemDataRole.UserRole)
    if not target_path:
        return False
    
    # Get source index from mime data or current selection
    source_index = get_dragged_index_from_mime_data(event, model, tree_view)
    if not source_index or not source_index.isValid():
        return False
    
    # Verificar que el source tampoco tenga padre (debe ser raíz)
    if source_index.parent().isValid():
        _show_reorder_warning(tree_view)
        return False
    
    # Verify source index is still valid (Qt may have moved it)
    source_item = model.itemFromIndex(source_index)
    if not source_item:
        # Qt may have moved the item, try to find it by path
        # This shouldn't happen if we prevent the move, but just in case
        _show_reorder_warning(tree_view)
        return False
    
    if not is_root_folder_item(source_item, model):
        _show_reorder_warning(tree_view)
        return False
    
    source_path = source_item.data(Qt.ItemDataRole.UserRole)
    if not source_path:
        return False
    
    # Cannot drop on itself
    if source_path == target_path:
        return False
    
    # Verificar que ambos items están al mismo nivel (ambos son hijos del root invisible)
    root = model.invisibleRootItem()
    source_parent = source_item.parent()
    target_parent = target_item.parent()
    
    # Ambos deben tener el mismo padre (root invisible o None)
    if source_parent != target_parent:
        _show_reorder_warning(tree_view)
        return False
    
    # Si tienen padre, debe ser el root invisible
    if source_parent and source_parent != root:
        _show_reorder_warning(tree_view)
        return False
    if target_parent and target_parent != root:
        _show_reorder_warning(tree_view)
        return False
    
    # Normalizar paths para verificación posterior
    normalized_source = os.path.normpath(source_path)
    normalized_target = os.path.normpath(target_path)
    
    # Perform reordering (this will swap positions)
    success = reorder_root_folders(model, path_to_item, source_path, target_path)
    
    # Verificar después del cambio que ambas sigan siendo raíz
    if success:
        # Re-verificar que ambas carpetas siguen siendo raíz
        if normalized_source not in path_to_item or normalized_target not in path_to_item:
            _show_reorder_warning(tree_view)
            return False
        
        source_item_after = path_to_item[normalized_source]
        target_item_after = path_to_item[normalized_target]
        
        if not is_root_folder_item(source_item_after, model) or not is_root_folder_item(target_item_after, model):
            # Una carpeta se convirtió en hija, mostrar aviso
            _show_reorder_warning(tree_view)
            # Intentar revertir el cambio
            reorder_root_folders(model, path_to_item, target_path, source_path)
            return False
    
    if not success:
        _show_reorder_warning(tree_view)
    
    return success

