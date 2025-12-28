"""
DragCommon - Shared drag and drop utilities.

Common functions for handling file drag operations across different views.
Supports Desktop Focus (uses TrashService).
"""

import os
from typing import Optional, Callable

from PySide6.QtCore import QMimeData

from app.managers.tab_manager import TabManager
from app.services.desktop_path_helper import get_desktop_path, is_desktop_focus
from app.services.desktop_operations import is_file_in_dock
from app.services.file_delete_service import delete_file


def should_reject_dock_to_dock_drop(mime_data: QMimeData, tab_manager: Optional[TabManager]) -> bool:
    """
    Check if drop should be rejected (dock-to-dock drop prevention).
    
    REGLA CRÍTICA: No se puede arrastrar archivos desde el dock hacia el mismo dock.
    Esto evita duplicación innecesaria de archivos en el Desktop Focus.
    
    Verifica:
    1. Si hay contexto de estado activo (rechazar siempre)
    2. Si el folder activo es Desktop Focus
    3. Si algún archivo arrastrado está en el dock (is_file_in_dock)
    4. Si las condiciones 2 y 3 son verdaderas, rechaza el drop
    
    Args:
        mime_data: QMimeData from drag event.
        tab_manager: TabManager instance for checking active folder.
    
    Returns:
        True if drop should be rejected, False otherwise.
    """
    if not tab_manager:
        return False
    
    # REGLA CRÍTICA: Drag & drop NO funciona en vistas por estado
    if tab_manager.has_state_context():
        return True
    
    active_folder = tab_manager.get_active_folder()
    if not (active_folder and is_desktop_focus(active_folder)):
        return False
    
    # Check if any dragged file is from dock
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if file_path and is_file_in_dock(file_path):
            return True
    
    return False


def is_same_folder_drop(source_path: str, tab_manager: Optional[TabManager]) -> bool:
    """
    Check if source file/folder is in the same folder as active target folder.
    
    REGLA CRÍTICA: No se puede hacer drop de un archivo/carpeta en la misma carpeta donde ya está.
    Esto evita operaciones innecesarias (mover archivo a su propia ubicación).
    
    Maneja correctamente Desktop Focus usando la ruta real del escritorio.
    
    Args:
        source_path: Path to the source file or folder.
        tab_manager: TabManager instance for checking active folder.

    Returns:
        True if source and target are in the same folder, False otherwise.
    """
    if not tab_manager:
        return False
    
    # REGLA CRÍTICA: Drag & drop NO funciona en vistas por estado
    if tab_manager.has_state_context():
        return True  # Rechazar siempre en vistas por estado
    
    active_folder = tab_manager.get_active_folder()
    if not active_folder:
        return False

    # Obtener la ruta real del destino (puede ser Desktop Focus)
    if is_desktop_focus(active_folder):
        real_active_folder = get_desktop_path()
    else:
        real_active_folder = active_folder

    # If source is a folder, check if it's the same as active folder
    if os.path.isdir(source_path):
        source_abs = os.path.abspath(source_path)
        active_abs = os.path.abspath(real_active_folder)
        return source_abs == active_abs
    
    # If source is a file, check if it's in the active folder
    source_dir = os.path.dirname(os.path.abspath(source_path))
    active_dir = os.path.abspath(real_active_folder)
    
    return source_dir == active_dir


def check_files_after_drag(
    original_file_paths: list[str],
    original_dir: str,
    emit_file_deleted: Callable[[str], None],
    watcher: Optional[object] = None,
    tab_manager: Optional[TabManager] = None
) -> None:
    """
    Check file status after drag and emit signals for moved/deleted files.
    
    Args:
        original_file_paths: List of file paths that were dragged.
        original_dir: Original directory where files were located.
        emit_file_deleted: Callback function to emit file_deleted signal.
        watcher: Optional watcher to block events during delete.
    """
    for file_path in original_file_paths:
        if os.path.exists(file_path):
            current_dir = os.path.dirname(os.path.abspath(file_path))
            if current_dir == original_dir:
                _delete_if_dragged_out(file_path, emit_file_deleted, watcher, tab_manager)
            else:
                emit_file_deleted(file_path)
        else:
            emit_file_deleted(file_path)


def is_folder_inside_itself(source_path: str, target_path: str) -> bool:
    """
    Verificar si una carpeta se está moviendo dentro de sí misma.
    
    REGLA CRÍTICA: No se puede mover una carpeta dentro de sí misma.
    Esto previene errores del sistema de archivos y bucles infinitos.
    
    Usa comparación de rutas absolutas para detectar si source está dentro de target.
    
    Args:
        source_path: Ruta de la carpeta fuente.
        target_path: Ruta de la carpeta destino.
    
    Returns:
        True si la carpeta fuente está dentro de la carpeta destino, False en caso contrario.
    """
    source_abs = os.path.abspath(source_path)
    target_abs = os.path.abspath(target_path)
    return source_abs == target_abs or source_abs.startswith(target_abs + os.sep)


def get_watcher_from_view(view: object) -> Optional[object]:
    """
    Obtener filesystem watcher desde una vista que tiene tab_manager.
    
    Args:
        view: Vista que puede tener _tab_manager como atributo.
    
    Returns:
        Watcher instance si está disponible, None en caso contrario.
    """
    if hasattr(view, '_tab_manager') and view._tab_manager:
        if hasattr(view._tab_manager, 'get_watcher'):
            return view._tab_manager.get_watcher()
    return None


def _delete_if_dragged_out(
    file_path: str,
    emit_file_deleted: Callable[[str], None],
    watcher: Optional[object] = None,
    tab_manager: Optional[TabManager] = None
) -> None:
    """Delete file if it was dragged outside (still in same directory)."""
    result = delete_file(file_path, watcher=watcher, is_trash_focus=False)
    if result.success:
        emit_file_deleted(file_path)

