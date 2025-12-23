"""
FileViewContextMenu - Context menu for file grid and list views.

Provides context menu functionality for creating folders and other operations.
Separates background menu (empty space) from item menu (file/folder).
"""

import os
from typing import Optional, Callable

from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import QInputDialog, QMenu, QMessageBox, QWidget

from app.core.logger import get_logger
from app.managers.tab_manager import TabManager
from app.services.folder_creation_service import create_folder
from app.services.file_deletion_service import is_folder_empty
from app.services.file_delete_service import delete_file
from app.services.file_creation_service import (
    create_text_file,
    create_markdown_file,
    create_docx_file
)
from app.ui.widgets.folder_tree_styles import get_menu_stylesheet

logger = get_logger(__name__)

# Información de diálogos por tipo de archivo
_FILE_TYPE_DIALOG_INFO = {
    "docx": ("Nuevo documento Word", "Nombre del documento:"),
    "txt": ("Nuevo documento de texto", "Nombre del archivo:"),
    "md": ("Nuevo documento Markdown", "Nombre del archivo:")
}

# Funciones de creación por tipo de archivo
_FILE_CREATORS = {
    "docx": create_docx_file,
    "txt": create_text_file,
    "md": create_markdown_file
}

# Configuración de acciones del submenú "Nuevo"
_FILE_MENU_ACTIONS = [
    ("Documento Word", "docx"),
    ("Documento de texto", "txt"),
    ("Documento Markdown", "md")
]


def show_background_menu(
    widget: QWidget,
    event: QContextMenuEvent,
    tab_manager: Optional[TabManager],
    on_refresh_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Show context menu for background (empty space).
    
    Args:
        widget: Widget that triggered the context menu.
        event: Context menu event with position.
        tab_manager: TabManager instance to get active folder path.
        on_refresh_callback: Optional callback to refresh view after folder creation.
    """
    if not tab_manager:
        return
    
    # Obtener ruta activa
    active_folder = tab_manager.get_active_folder()
    if not active_folder:
        return
    
    # Crear menú
    menu = QMenu(widget)
    menu.setStyleSheet(get_menu_stylesheet())
    
    # Acción: Nueva carpeta (solo en menú de fondo)
    new_folder_action = menu.addAction("Nueva carpeta")
    new_folder_action.triggered.connect(
        lambda: _create_folder_dialog(widget, active_folder, on_refresh_callback)
    )
    
    # Separador antes del submenú "Nuevo"
    menu.addSeparator()
    
    # Submenú: Nuevo (para crear archivos)
    new_submenu = QMenu("Nuevo", widget)
    new_submenu.setStyleSheet(get_menu_stylesheet())
    
    # Crear acciones del submenú desde configuración
    for action_text, file_type in _FILE_MENU_ACTIONS:
        action = new_submenu.addAction(action_text)
        action.triggered.connect(
            lambda checked, ft=file_type: _create_file_dialog(widget, active_folder, ft, on_refresh_callback)
        )
    
    # Añadir submenú al menú principal
    menu.addMenu(new_submenu)
    
    # Mostrar menú en posición del evento
    menu.exec(event.globalPos())


def show_item_menu(
    widget: QWidget,
    event: QContextMenuEvent,
    item_paths: list[str],
    tab_manager: Optional[TabManager],
    on_refresh_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Show context menu for file/folder item(s).
    
    Args:
        widget: Widget that triggered the context menu.
        event: Context menu event with position.
        item_paths: List of paths of file/folder items (always a list, never empty).
        tab_manager: TabManager instance (for future operations).
        on_refresh_callback: Optional callback to refresh view after operations.
    """
    if not item_paths or not tab_manager:
        return
    
    # Crear menú
    menu = QMenu(widget)
    menu.setStyleSheet(get_menu_stylesheet())
    
    # Separador antes de la acción de eliminar
    menu.addSeparator()
    
    # Acción: Mover a la papelera (siempre al final)
    move_to_trash_action = menu.addAction("Mover a la papelera")
    move_to_trash_action.triggered.connect(
        lambda: _move_to_trash_dialog(widget, item_paths, tab_manager, on_refresh_callback)
    )
    
    # Mostrar menú en posición del evento
    menu.exec(event.globalPos())


def _create_folder_dialog(
    parent: QWidget,
    parent_path: str,
    on_refresh_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Show dialog to create a new folder.
    
    Args:
        parent: Parent widget for dialogs.
        parent_path: Path where folder will be created.
        on_refresh_callback: Optional callback to refresh view after creation.
    """
    # Mostrar diálogo de entrada
    name, ok = QInputDialog.getText(
        parent,
        "Nueva carpeta",
        "Nombre de la carpeta:",
        text="Nueva carpeta"
    )
    
    if not ok or not name.strip():
        return
    
    # Crear carpeta usando servicio
    result = create_folder(parent_path, name.strip())
    
    if result.success:
        # Refrescar vista si hay callback
        if on_refresh_callback:
            on_refresh_callback()
        logger.info(f"Carpeta creada exitosamente en {parent_path}")
    else:
        # Mostrar error al usuario
        QMessageBox.warning(
            parent,
            "Error al crear carpeta",
            result.error_message
        )


def _move_to_trash_dialog(
    parent: QWidget,
    item_paths: list[str],
    tab_manager: Optional[TabManager],
    on_refresh_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Show confirmation dialog and move items to trash.
    
    Args:
        parent: Parent widget for dialogs.
        item_paths: List of file/folder paths to move to trash.
        tab_manager: TabManager instance to get watcher if available.
        on_refresh_callback: Optional callback to refresh view after deletion.
    """
    if not item_paths:
        return
    
    # Determinar si necesita confirmación
    needs_confirmation = _needs_confirmation(item_paths)
    
    if needs_confirmation:
        # Mostrar diálogo de confirmación
        confirmed = _show_confirmation_dialog(parent, item_paths)
        if not confirmed:
            return
    
    # Mover cada path a la papelera usando delete_file con lógica contextual
    success_count = 0
    error_messages = []
    
    # Obtener watcher del tab_manager si está disponible
    watcher = None
    if tab_manager and hasattr(tab_manager, 'get_watcher'):
        watcher = tab_manager.get_watcher()
    
    for path in item_paths:
        # Usar delete_file que maneja Desktop Focus, Trash Focus y carpetas normales
        result = delete_file(path, watcher=watcher, is_trash_focus=False)
        if result.success:
            success_count += 1
        else:
            error_messages.append(f"{os.path.basename(path)}: {result.error_message}")
    
    # Mostrar errores si los hay
    if error_messages:
        error_text = "\n".join(error_messages)
        QMessageBox.warning(
            parent,
            "Error al mover a la papelera",
            f"No se pudieron mover algunos elementos:\n\n{error_text}"
        )
    
    # Refrescar vista si hubo al menos un éxito
    if success_count > 0:
        if on_refresh_callback:
            on_refresh_callback()
        logger.info(f"{success_count} elemento(s) movido(s) a la papelera")


def _needs_confirmation(item_paths: list[str]) -> bool:
    """
    Determine if confirmation is needed before moving to trash.
    
    Always returns True - confirmation is always required for any file or folder.
    
    Args:
        item_paths: List of file/folder paths.
        
    Returns:
        Always True (confirmation always required).
    """
    return True


def _show_confirmation_dialog(parent: QWidget, item_paths: list[str]) -> bool:
    """
    Show confirmation dialog for moving items to trash.
    
    Args:
        parent: Parent widget for dialog.
        item_paths: List of file/folder paths.
        
    Returns:
        True if user confirmed, False otherwise.
    """
    if len(item_paths) > 1:
        # Selección múltiple
        message = f"¿Mover {len(item_paths)} elementos a la papelera?"
    else:
        # Un solo elemento - archivo o carpeta
        path = item_paths[0]
        item_name = os.path.basename(path) or path
        
        # Verificar si es carpeta con contenido
        if os.path.isdir(path) and not is_folder_empty(path):
            message = f"¿Mover '{item_name}' y todo su contenido a la papelera?"
        else:
            # Archivo o carpeta vacía
            message = f"¿Mover '{item_name}' a la papelera?"
    
    # Crear diálogo explícitamente para asegurar que se muestre correctamente
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle("Mover a la papelera")
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg_box.setDefaultButton(QMessageBox.StandardButton.No)
    msg_box.setModal(True)
    
    # Mostrar diálogo y obtener respuesta
    reply = msg_box.exec()
    
    return reply == QMessageBox.StandardButton.Yes


def _create_file_dialog(
    parent: QWidget,
    parent_path: str,
    file_type: str,
    on_refresh_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Show dialog to create a new file.
    
    Args:
        parent: Parent widget for dialogs.
        parent_path: Path where file will be created.
        file_type: Type of file to create ("docx", "txt", "md").
        on_refresh_callback: Optional callback to refresh view after creation.
    """
    # Obtener información del diálogo según tipo de archivo
    title, label = _FILE_TYPE_DIALOG_INFO.get(file_type, ("Nuevo archivo", "Nombre del archivo:"))
    
    # Mostrar diálogo de entrada
    name, ok = QInputDialog.getText(
        parent,
        title,
        label,
        text=""
    )
    
    if not ok or not name.strip():
        return
    
    # Obtener función de creación según tipo
    creator = _FILE_CREATORS.get(file_type)
    if not creator:
        QMessageBox.warning(
            parent,
            "Error",
            f"Tipo de archivo no soportado: {file_type}"
        )
        return
    
    # Crear archivo usando servicio
    result = creator(parent_path, name.strip())
    
    if result.success:
        # Refrescar vista si hay callback
        if on_refresh_callback:
            on_refresh_callback()
        logger.info(f"Archivo {file_type} creado exitosamente en {parent_path}")
    else:
        # Mostrar error al usuario
        QMessageBox.warning(
            parent,
            f"Error al crear archivo {file_type}",
            result.error_message
        )

