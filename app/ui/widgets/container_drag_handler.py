"""
ContainerDragHandler - Drag and drop handler for grid view container.

Handles drag enter, move, and drop events for the main grid view widget.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import is_file_in_dock
from app.ui.widgets.drag_common import is_same_folder_drop


def handle_drag_enter(event: QDragEnterEvent, tab_manager=None) -> None:
    """Handle drag enter for file drop on main widget."""
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
    
    # Accept any action Windows proposes (Copy, Move, or Link)
    event.acceptProposedAction()


def handle_drag_move(event: QDragMoveEvent, tab_manager=None) -> None:
    """
    Handle drag move to maintain drop acceptance.
    
    Mejora: Determina acción (move/copy) según tecla modificadora para mejor feedback visual.
    """
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
    
    # Determinar acción según tecla modificadora (mejora feedback visual)
    # Ctrl = Copy, Sin modificador = Move
    modifiers = event.keyboardModifiers()
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        event.setDropAction(Qt.DropAction.CopyAction)
    else:
        # Usar acción propuesta o MoveAction como fallback
        if event.proposedAction() != Qt.DropAction.IgnoreAction:
            event.setDropAction(event.proposedAction())
        else:
            event.setDropAction(Qt.DropAction.MoveAction)
    
    event.accept()


def handle_drop(event: QDropEvent, tab_manager, file_dropped_signal) -> None:
    """
    Handle file drop on main widget.

    Args:
        event: Drop event.
        tab_manager: TabManager instance for checking active folder.
        file_dropped_signal: Signal to emit when file is dropped.
    """
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
            # Check if same-folder drop before emitting
            if is_same_folder_drop(file_path, tab_manager):
                event.ignore()
                return
            file_dropped_signal.emit(file_path)
    # Desktop Focus y otras carpetas: usar MoveAction (mover archivos, no copiar)
    if event.proposedAction() != Qt.DropAction.IgnoreAction:
        event.setDropAction(event.proposedAction())
    else:
        event.setDropAction(Qt.DropAction.MoveAction)
    event.accept()

