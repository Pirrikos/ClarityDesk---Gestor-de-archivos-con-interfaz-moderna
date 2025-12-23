"""
FolderTreeModel - Tree model management for FolderTreeSidebar.

Handles tree node insertion, removal, and parent finding logic.
"""

import os
import re

from PySide6.QtCore import QMimeData, QModelIndex, QSize, Qt
from PySide6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTreeView

from app.services.path_utils import normalize_path
from app.ui.widgets.folder_tree_icon_utils import load_folder_icon_with_fallback, FOLDER_ICON_SIZE


class FolderTreeModel(QStandardItemModel):
    """
    Modelo personalizado para el sidebar que previene cambios de jerarquía internos.
    
    Sobrescribe flags() y canDropMimeData() para:
    - Solo permitir arrastrar carpetas raíz (no hijas)
    - Permitir drag externo (con URLs) → mover archivos/carpetas al filesystem
    - Permitir drag interno solo sobre carpetas raíz → reordenar visualmente
    - Bloquear cualquier cambio de jerarquía interna
    """
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        default_flags = super().flags(index)
        
        # Si el índice no es válido o tiene padre, no permitir drag
        if not index.isValid() or index.parent().isValid():
            # Carpeta hija o índice inválido → remover flag de drag
            return default_flags & ~Qt.ItemFlag.ItemIsDragEnabled
        
        # Carpeta raíz → permitir drag para reordenamiento
        return default_flags
    
    def canDropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex
    ) -> bool:
        """
        Determinar si se puede hacer drop en el índice especificado.
        
        Reglas:
        - Drag externo (hasUrls): permitir (validaciones en handle_drop)
        - Drag interno (!hasUrls): solo permitir si parent es inválido (carpeta raíz)
        """
        # Drag externo: permitir (las validaciones de seguridad están en handle_drop)
        if data.hasUrls():
            return True
        
        # Drag interno: solo permitir sobre carpetas raíz (sin padre)
        # Esto previene que Qt cambie jerarquía internamente
        if not parent.isValid():
            # Target es raíz → permitir reordenamiento
            return True
        
        # Target tiene padre → rechazar (no permitir meter dentro de otras carpetas)
        return False


def _natural_sort_key(path: str) -> tuple:
    """Ordenamiento natural: convierte números a enteros. Ejemplo: "1. PLATON" < "10. NIETZSCHE"."""
    filename = os.path.basename(path).lower()
    parts = []
    for part in re.split(r'(\d+)', filename):
        if part.isdigit():
            parts.append((0, int(part)))
        else:
            parts.append((1, part))
    return tuple(parts)


# Rol personalizado para guardar path original (case-preserving)
# UserRole (256) = path normalizado (para comparaciones internas)
# UserRole + 1 (257) = path original (case-preserving, para guardar estado)
ORIGINAL_PATH_ROLE = Qt.ItemDataRole.UserRole + 1


def _get_original_path(item: QStandardItem) -> str | None:
    """
    Obtener path original (case-preserving) desde un item.
    
    Intenta leer desde ORIGINAL_PATH_ROLE, si no existe usa UserRole (normalizado).
    
    Args:
        item: QStandardItem del modelo.
        
    Returns:
        Path original si existe, path normalizado si no, None si no hay path.
    """
    if not item:
        return None
    
    # Intentar obtener path original (case-preserving)
    original_path = item.data(ORIGINAL_PATH_ROLE)
    if original_path:
        return original_path
    
    # Fallback: usar path normalizado
    normalized_path = item.data(Qt.ItemDataRole.UserRole)
    return normalized_path if normalized_path else None


def add_focus_path_to_model(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str,
    skip_sort: bool = False
) -> QStandardItem:
    if not path or not os.path.isdir(path):
        return None
    
    normalized_path = normalize_path(path)
    
    # Skip if already exists
    if normalized_path in path_to_item:
        return None
    
    # Usar el path ORIGINAL para preservar el caso del nombre visible
    folder_name = os.path.basename(path) or path
    item = QStandardItem(folder_name)
    
    # Find parent (only if exists, don't create)
    parent_item = find_parent_item(model, path_to_item, normalized_path)
    
    # Verificar si es raíz de forma segura (proteger contra objetos C++ eliminados)
    is_root = False
    if parent_item is None:
        is_root = True
    else:
        try:
            is_root = parent_item == model.invisibleRootItem()
        except RuntimeError:
            # El objeto C++ fue eliminado, tratar como raíz
            is_root = True
    
    if is_root:
        try:
            icon = load_folder_icon_with_fallback(FOLDER_ICON_SIZE)
            item.setIcon(icon)
        except Exception:
            item.setIcon(QIcon())
    else:
        # No asignar icono para carpetas hijas
        item.setIcon(QIcon())
    
    item.setData(normalized_path, Qt.ItemDataRole.UserRole)  # Path normalizado para comparaciones
    item.setData(path, ORIGINAL_PATH_ROLE)  # Path original (case-preserving) para guardar estado
    item.setEditable(False)
    
    # Agregar el elemento al final primero
    parent_item.appendRow(item)
    path_to_item[normalized_path] = item
    
    # Solo ordenar si no se está restaurando (skip_sort=False)
    if not skip_sort:
        # Ordenar todos los hijos del padre usando ordenamiento natural
        # Obtener todos los hijos con sus rutas
        children_data = []
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            if child:
                child_path = child.data(Qt.ItemDataRole.UserRole)
                if child_path:
                    children_data.append((child_path, child))
        
        # Ordenar por nombre usando ordenamiento natural
        children_data.sort(key=lambda x: _natural_sort_key(x[0]))
        
        # Reorganizar los hijos en el orden correcto
        # Primero, remover todos los hijos temporalmente (de atrás hacia adelante para mantener índices)
        temp_rows = []
        for i in range(parent_item.rowCount() - 1, -1, -1):
            row_data = parent_item.takeRow(i)
            if row_data and len(row_data) > 0:
                temp_rows.append(row_data[0])
        
        # Crear un diccionario para acceso rápido
        temp_dict = {}
        for temp_item in temp_rows:
            path = temp_item.data(Qt.ItemDataRole.UserRole)
            if path:
                temp_dict[path] = temp_item
        
        # Insertar en el orden correcto
        for child_path, _ in children_data:
            if child_path in temp_dict:
                parent_item.appendRow(temp_dict[child_path])
    
    return item


def find_parent_item(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str
) -> QStandardItem:
    parent_path = os.path.dirname(path)
    if not parent_path or parent_path == path:
        return model.invisibleRootItem()
    
    normalized_parent = normalize_path(parent_path)
    
    if normalized_parent in path_to_item:
        return path_to_item[normalized_parent]
    
    return model.invisibleRootItem()


def remove_focus_path_from_model(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str
) -> None:
    normalized_path = normalize_path(path)
    
    if normalized_path not in path_to_item:
        return
    
    item = path_to_item[normalized_path]
    
    # Remove all children recursively from dict first
    _remove_item_recursive(path_to_item, normalized_path)
    
    # Remove item from model
    parent = item.parent()
    if parent:
        parent.removeRow(item.row())
    else:
        root = model.invisibleRootItem()
        root.removeRow(item.row())


def _remove_item_recursive(path_to_item: dict[str, QStandardItem], path: str) -> None:
    if path not in path_to_item:
        return
    
    item = path_to_item[path]
    
    # Remove all children first
    try:
        row_count = item.rowCount()
        for i in range(row_count):
            try:
                child_item = item.child(i)
                if child_item:
                    child_path = child_item.data(Qt.ItemDataRole.UserRole)
                    if child_path:
                        _remove_item_recursive(path_to_item, child_path)
            except RuntimeError:
                # Objeto C++ ya fue eliminado, continuar con siguiente hijo
                continue
    except RuntimeError:
        # Objeto C++ ya fue eliminado, solo eliminar del diccionario
        pass
    
    # Remove this item
    del path_to_item[path]


def collect_children_paths(item: QStandardItem) -> list[str]:
    children_paths = []
    for i in range(item.rowCount()):
        child = item.child(i)
        if child:
            child_path = child.data(Qt.ItemDataRole.UserRole)
            if child_path:
                children_paths.append(child_path)
                children_paths.extend(collect_children_paths(child))
    return children_paths


def _collect_expanded_recursive(
    item: QStandardItem,
    path: str,
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    tree_view: QTreeView,
    expanded_paths: list[str]
) -> None:
    if item is None:
        return
    
    # Usar path normalizado para buscar en path_to_item (las claves están normalizadas)
    normalized_path = normalize_path(path) if path else None
    if normalized_path and normalized_path in path_to_item:
        index = model.indexFromItem(item)
        if index.isValid() and tree_view.isExpanded(index):
            # Guardar path original (case-preserving) para el estado
            original_path = _get_original_path(item)
            if original_path:
                expanded_paths.append(original_path)
    
    for i in range(item.rowCount()):
        child = item.child(i)
        if child:
            child_path = _get_original_path(child)
            if child_path:
                _collect_expanded_recursive(child, child_path, model, path_to_item, tree_view, expanded_paths)


def collect_expanded_paths(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    tree_view: QTreeView,
    root_item: QStandardItem
) -> list[str]:
    expanded_paths = []
    
    for i in range(root_item.rowCount()):
        item = root_item.child(i)
        if item:
            item_path = _get_original_path(item)
            if item_path:
                _collect_expanded_recursive(item, item_path, model, path_to_item, tree_view, expanded_paths)
    
    return expanded_paths


def is_root_folder_item(item: QStandardItem, model: QStandardItemModel) -> bool:
    if not item:
        return False
    
    try:
        parent = item.parent()
        if parent is None:
            return True
        try:
            return parent == model.invisibleRootItem()
        except RuntimeError:
            # El objeto C++ fue eliminado, tratar como raíz
            return True
    except RuntimeError:
        # El objeto item fue eliminado, no es raíz válido
        return False


def get_root_folder_items(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem]
) -> list[QStandardItem]:
    root = model.invisibleRootItem()
    root_items = []
    
    for i in range(root.rowCount()):
        item = root.child(i)
        if item and is_root_folder_item(item, model):
            root_items.append(item)
    
    return root_items


def get_root_folder_paths(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem]
) -> list[str]:
    root_items = get_root_folder_items(model, path_to_item)
    paths = []
    
    for item in root_items:
        path = _get_original_path(item)
        if path:
            paths.append(path)
    
    return paths


def reorder_root_folders(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    source_path: str,
    target_path: str
) -> bool:
    normalized_source = normalize_path(source_path)
    normalized_target = normalize_path(target_path)
    
    if normalized_source not in path_to_item or normalized_target not in path_to_item:
        return False
    
    source_item = path_to_item[normalized_source]
    target_item = path_to_item[normalized_target]
    
    if not is_root_folder_item(source_item, model) or not is_root_folder_item(target_item, model):
        return False
    
    if source_item == target_item:
        return False
    
    root = model.invisibleRootItem()
    source_parent = source_item.parent()
    target_parent = target_item.parent()
    
    if (source_parent and source_parent != root) or (target_parent and target_parent != root):
        return False
    
    source_row = source_item.row()
    target_row = target_item.row()
    
    if source_row < 0 or target_row < 0:
        return False
    
    source_row_data = root.takeRow(source_row)
    adjusted_target_row = target_row if target_row < source_row else target_row - 1
    target_row_data = root.takeRow(adjusted_target_row)
    
    root.insertRow(target_row, source_row_data[0])
    root.insertRow(source_row, target_row_data[0])
    
    if not is_root_folder_item(source_row_data[0], model) or not is_root_folder_item(target_row_data[0], model):
        root.removeRow(target_row)
        root.removeRow(source_row)
        root.insertRow(source_row, source_row_data[0])
        root.insertRow(target_row, target_row_data[0])
        return False
    
    return True