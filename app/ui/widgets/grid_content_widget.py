"""
GridContentWidget - Content widget for grid view that handles drag-in.

Widget that contains the grid layout and handles file drop events.
"""

import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import is_file_in_dock
from app.ui.widgets.drag_common import is_same_folder_drop


def _check_if_desktop_focus(parent_view) -> bool:
    """Check if active folder is Desktop Focus."""
    if not hasattr(parent_view, '_tab_manager'):
        return False
    active_folder = parent_view._tab_manager.get_active_folder()
    return is_desktop_focus(active_folder) if active_folder else False


def _is_dock_to_dock_drop(mime_data) -> bool:
    """Check if any dragged file is from dock (prevent dock-to-dock drops)."""
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if file_path and is_file_in_dock(file_path):
            return True
    return False


def _process_dropped_files(mime_data, parent_view, is_desktop: bool, event: QDropEvent) -> None:
    """Process dropped files and set appropriate drop action."""
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if file_path and (os.path.isfile(file_path) or os.path.isdir(file_path)):
            if hasattr(parent_view, '_tab_manager') and is_same_folder_drop(file_path, parent_view._tab_manager):
                event.ignore()
                return
            parent_view.file_dropped.emit(file_path)
    
    if is_desktop:
        event.setDropAction(Qt.DropAction.CopyAction)
    else:
        if event.proposedAction() != Qt.DropAction.IgnoreAction:
            event.setDropAction(event.proposedAction())
        else:
            event.setDropAction(Qt.DropAction.MoveAction)
    event.accept()


class GridContentWidget(QWidget):
    """Content widget for grid view that handles drag-in."""

    def __init__(self, parent_view):
        """Initialize content widget."""
        super().__init__(parent_view)
        self._parent_view = parent_view
        self.setAcceptDrops(True)
        
        # Remove any margins or padding
        self.setContentsMargins(0, 0, 0, 0)
        
        # Allow both horizontal and vertical expansion for proper scrolling
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum  # Minimum height based on content
        )
        # Ensure minimum size hint allows expansion
        self.setMinimumSize(0, 0)
    
    def sizeHint(self) -> QSize:
        """Return size hint based on layout contents."""
        layout = self.layout()
        if layout:
            return layout.sizeHint()
        return super().sizeHint()
    
    def minimumSizeHint(self) -> QSize:
        """Return minimum size hint based on layout contents."""
        layout = self.layout()
        if layout:
            return layout.minimumSize()
        return super().minimumSizeHint()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter for file drop."""
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            event.ignore()
            return
        
        if _check_if_desktop_focus(self._parent_view) and _is_dock_to_dock_drop(mime_data):
            event.ignore()
            return
        
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move to maintain drop acceptance."""
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            event.ignore()
            return
        
        if _check_if_desktop_focus(self._parent_view) and _is_dock_to_dock_drop(mime_data):
            event.ignore()
            return
        
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle file and folder drop into grid view."""
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            event.ignore()
            return
        
        is_desktop = _check_if_desktop_focus(self._parent_view)
        
        if is_desktop and _is_dock_to_dock_drop(mime_data):
            event.ignore()
            return
        
        _process_dropped_files(mime_data, self._parent_view, is_desktop, event)

