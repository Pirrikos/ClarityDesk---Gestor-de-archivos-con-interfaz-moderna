"""
FileDropHandler - File drop handling for view container.

Handles file drop operations and same-folder drop detection.
Supports Desktop Focus and Trash Focus.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

from app.core.logger import get_logger
from app.managers.tab_manager import TabManager
from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import is_file_in_dock
from app.services.file_move_service import move_file
from app.services.trash_storage import TRASH_FOCUS_PATH
from app.ui.widgets.drag_common import is_same_folder_drop

logger = get_logger(__name__)


def handle_file_drop(
    source_file_path: str,
    tab_manager: TabManager,
    update_files_callback
) -> tuple[bool, str, str]:
    """
    Handle file drop into active folder (MOVE operation).
    Supports Desktop Focus and Trash Focus.

    Args:
        source_file_path: Path to the file being dropped.
        tab_manager: TabManager instance for getting active folder.
        update_files_callback: Callback to refresh file list after move.
    
    Returns:
        Tuple of (success, source_path, new_path) where new_path is the new location
        if a folder was moved, None otherwise.
    """
    # REGLA CRÍTICA: Drag & drop NO funciona en vistas por estado
    if tab_manager.has_state_context():
        return False, source_file_path, None
    
    active_folder = tab_manager.get_active_folder()
    if not active_folder:
        return False, source_file_path, None

    # Prevent dropping into Trash Focus (use delete action instead)
    if active_folder == TRASH_FOCUS_PATH:
        return False, source_file_path, None

    # Check if file is already in the active folder (same-folder drop)
    if is_same_folder_drop(source_file_path, tab_manager):
        return False, source_file_path, None

    # Verificar si el archivo ya está en el destino (Windows puede haberlo movido)
    from pathlib import Path
    source_path_obj = Path(source_file_path)
    
    # Obtener la ruta real del destino (puede ser Desktop Focus)
    if is_desktop_focus(active_folder):
        from app.services.desktop_path_helper import get_desktop_path
        real_dest_folder = get_desktop_path()
    else:
        real_dest_folder = active_folder
    
    dest_path_obj = Path(real_dest_folder) / source_path_obj.name
    
    # Si el archivo ya está en el destino, Windows ya lo movió
    if dest_path_obj.exists():
        print(f"[HANDLE_FILE_DROP] Archivo ya existe en destino: {dest_path_obj}")
        # Verificar que realmente existe (puede ser un problema de case sensitivity)
        if not dest_path_obj.exists():
            # Buscar con nombre modificado o variaciones
            import glob
            pattern = str(Path(real_dest_folder) / f"{source_path_obj.stem}*{source_path_obj.suffix}")
            matches = glob.glob(pattern)
            if matches:
                dest_path_obj = Path(matches[0])
                print(f"[HANDLE_FILE_DROP] Archivo encontrado con nombre modificado: {dest_path_obj}")
        # No llamar a update_callback aquí - dejar que el código externo lo maneje
        new_path = str(dest_path_obj) if os.path.isdir(source_file_path) else None
        return True, source_file_path, new_path
    
    # Verificar si el archivo fuente aún existe
    if not os.path.exists(source_file_path):
        # Verificar si está en el destino (Windows puede haberlo movido)
        if dest_path_obj.exists():
            # Windows ya movió el archivo, no llamar a update_callback aquí
            new_path = str(dest_path_obj) if os.path.isdir(source_file_path) else None
            return True, source_file_path, new_path
        
        # Buscar archivo con nombre modificado (conflict resolution)
        import glob
        pattern = str(Path(real_dest_folder) / f"{source_path_obj.stem}*{source_path_obj.suffix}")
        matches = glob.glob(pattern)
        if matches:
            # Archivo encontrado con nombre modificado
            new_path = matches[0] if os.path.isdir(source_file_path) else None
            return True, source_file_path, new_path
        
        # Archivo fue movido o eliminado, no intentar moverlo
        return False, source_file_path, None

    # Get watcher from TabManager to block events during move
    watcher = tab_manager.get_watcher() if hasattr(tab_manager, 'get_watcher') else None
    
    is_folder = os.path.isdir(source_file_path)
    new_path = None
    
    # Desktop Focus: mover archivos (no copiar)
    # Otras carpetas: mover archivos normalmente
    print(f"[HANDLE_FILE_DROP] Moviendo archivo: {source_file_path} -> {real_dest_folder}")
    result = move_file(source_file_path, real_dest_folder, watcher=watcher)
    
    if result.success:
        print(f"[HANDLE_FILE_DROP] Movimiento exitoso")
        # Verificar que el archivo realmente existe después del movimiento
        final_dest = Path(real_dest_folder) / source_path_obj.name
        if not final_dest.exists():
            # Buscar con nombre modificado (conflict resolution)
            import glob
            pattern = str(Path(real_dest_folder) / f"{source_path_obj.stem}*{source_path_obj.suffix}")
            matches = glob.glob(pattern)
            if matches:
                final_dest = Path(matches[0])
                logger.debug(f"Archivo encontrado con nombre modificado: {final_dest}")
            else:
                logger.warning("Archivo movido pero no encontrado en destino")
        else:
            logger.debug(f"Archivo encontrado en destino: {final_dest}")
    
    # Calculate new path if folder was moved
    if result.success and is_folder:
        new_path = str(final_dest) if 'final_dest' in locals() and final_dest.exists() else str(dest_path_obj)
    
    # No llamar a update_callback aquí - dejar que el código externo lo maneje
    # cuando verifique que el archivo realmente existe
    
    return result.success, source_file_path, new_path


def handle_drag_enter(event: QDragEnterEvent, tab_manager: TabManager = None) -> None:
    """Handle drag enter as fallback."""
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    # Prevent drag and drop FROM dock TO dock
    if tab_manager:
        active_folder = tab_manager.get_active_folder()
        if active_folder and is_desktop_focus(active_folder):
            # Check if any dragged file is from dock
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path and is_file_in_dock(file_path):
                    # Dragging from dock to dock - ignore
                    event.ignore()
                    return
    
    # Accept any action Windows proposes
    event.acceptProposedAction()


def handle_drag_move(event: QDragMoveEvent, tab_manager: TabManager = None) -> None:
    """Handle drag move as fallback."""
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    # Prevent drag and drop FROM dock TO dock
    if tab_manager:
        active_folder = tab_manager.get_active_folder()
        if active_folder and is_desktop_focus(active_folder):
            # Check if any dragged file is from dock
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path and is_file_in_dock(file_path):
                    # Dragging from dock to dock - ignore
                    event.ignore()
                    return
    
    # Always accept if we have URLs
    event.accept()


def handle_drop(
    event: QDropEvent,
    tab_manager: TabManager,
    update_files_callback
) -> None:
    """
    Handle file drop as fallback.

    Args:
        event: Drop event.
        tab_manager: TabManager instance for checking active folder.
        update_files_callback: Callback to refresh file list after move.
    """
    # REGLA CRÍTICA: Drag & drop NO funciona en vistas por estado
    if tab_manager.has_state_context():
        event.ignore()
        return
    
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    active_folder = tab_manager.get_active_folder()
    is_desktop = is_desktop_focus(active_folder) if active_folder else False
    
    # Prevent drag and drop FROM dock TO dock
    if is_desktop:
        # Check if any dragged file is from dock
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and is_file_in_dock(file_path):
                # Dragging from dock to dock - ignore
                event.ignore()
                return
    
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if file_path and (os.path.isfile(file_path) or os.path.isdir(file_path)):
            # Process both files and folders
            # Check if same-folder drop before processing
            if is_same_folder_drop(file_path, tab_manager):
                event.ignore()
                return
            handle_file_drop(file_path, tab_manager, update_files_callback)
    
    # Desktop Focus y otras carpetas: usar MoveAction (mover archivos, no copiar)
    if event.proposedAction() != Qt.DropAction.IgnoreAction:
        event.setDropAction(event.proposedAction())
    else:
        event.setDropAction(Qt.DropAction.MoveAction)
    event.accept()

