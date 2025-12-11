"""
SubfolderOverlay - Floating widget for subfolder navigation during drag.

Temporary overlay that appears during drag & drop to allow navigation
into subfolders. Reuses folder_tree_model and folder_tree_handlers.
"""

import os
from typing import Optional

from PySide6.QtCore import QModelIndex, QPoint, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.folder_tree_drag_handler import (
    get_drop_target_path,
    handle_drag_enter,
    handle_drag_move,
    handle_drop,
)
from app.ui.widgets.folder_tree_handlers import handle_tree_click
from app.ui.widgets.folder_tree_model import (
    add_focus_path_to_model,
    find_parent_item,
)


class SubfolderOverlay(QWidget):
    """Floating overlay widget for subfolder navigation."""

    file_dropped = Signal(str, str)  # Emitted when file is dropped (source_path, target_path)

    def __init__(self, root_path: str, parent=None):
        """Initialize subfolder overlay."""
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._root_path = root_path
        self._path_to_item: dict[str, QStandardItem] = {}
        self._setup_ui()
        self._populate_tree()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        self._setup_model()
        self.setWindowFlags(
            Qt.WindowType.Popup | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(300, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        
        # Tree view
        self._tree_view = QTreeView(self)
        self._tree_view.setModel(self._model)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setAnimated(True)
        self._tree_view.setExpandsOnDoubleClick(False)
        self._tree_view.setRootIsDecorated(True)
        self._tree_view.setIndentation(12)
        self._tree_view.setWordWrap(False)
        
        # Enable drag & drop
        self._tree_view.setAcceptDrops(True)
        self._tree_view.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        
        self._tree_view.clicked.connect(self._on_tree_clicked)
        
        layout.addWidget(self._tree_view)
        
        # Dark theme styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTreeView {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QTreeView::item {
                padding: 4px;
                border-radius: 2px;
            }
            QTreeView::item:hover {
                background-color: #404040;
            }
            QTreeView::item:selected {
                background-color: #4a90e2;
            }
        """)

    def _setup_model(self) -> None:
        """Setup QStandardItemModel for subfolder tree."""
        self._model = QStandardItemModel(self)
        self._model.setHorizontalHeaderLabels(["Folders"])

    def _populate_tree(self) -> None:
        """Populate tree with subfolders of root path."""
        if not os.path.isdir(self._root_path):
            return
        
        # Add root path
        add_focus_path_to_model(self._model, self._path_to_item, self._root_path)
        
        # Add immediate subfolders
        try:
            for item in os.listdir(self._root_path):
                subfolder_path = os.path.join(self._root_path, item)
                if os.path.isdir(subfolder_path):
                    add_focus_path_to_model(self._model, self._path_to_item, subfolder_path)
        except (OSError, PermissionError):
            pass
        
        # Expand root
        if self._root_path in self._path_to_item:
            root_item = self._path_to_item[self._root_path]
            root_index = self._model.indexFromItem(root_item)
            if root_index.isValid():
                self._tree_view.expand(root_index)

    def _on_tree_clicked(self, index: QModelIndex) -> None:
        """Handle tree item click - expand/collapse and load subfolders."""
        folder_path = handle_tree_click(index, self._model, self._tree_view)
        if folder_path and os.path.isdir(folder_path):
            # Load subfolders of clicked folder
            self._load_subfolders(folder_path)

    def _load_subfolders(self, folder_path: str) -> None:
        """Load immediate subfolders of a folder into tree."""
        if not os.path.isdir(folder_path):
            return
        
        try:
            for item in os.listdir(folder_path):
                subfolder_path = os.path.join(folder_path, item)
                if os.path.isdir(subfolder_path):
                    add_focus_path_to_model(self._model, self._path_to_item, subfolder_path)
        except (OSError, PermissionError):
            pass

    def show_at_position(self, global_pos: QPoint) -> None:
        """Show overlay at specified global position."""
        # Adjust position to keep overlay on screen
        screen_geometry = self.screen().availableGeometry()
        x = global_pos.x()
        y = global_pos.y()
        
        # Ensure overlay fits on screen
        if x + self.width() > screen_geometry.right():
            x = screen_geometry.right() - self.width()
        if y + self.height() > screen_geometry.bottom():
            y = screen_geometry.bottom() - self.height()
        if x < screen_geometry.left():
            x = screen_geometry.left()
        if y < screen_geometry.top():
            y = screen_geometry.top()
        
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter on tree view."""
        handle_drag_enter(event)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move over tree view."""
        handle_drag_move(event, self._tree_view, self._model)

    def dropEvent(self, event) -> None:
        """Handle file drop on tree node - move files to target folder."""
        # Get watcher from parent if available
        watcher = None
        parent = self.parent()
        while parent:
            if hasattr(parent, '_tab_manager'):
                tab_manager = parent._tab_manager
                if hasattr(tab_manager, 'get_watcher'):
                    watcher = tab_manager.get_watcher()
                break
            parent = parent.parent()
        
        source_paths = handle_drop(event, self._tree_view, self._model, watcher=watcher)
        
        if source_paths:
            target_path = get_drop_target_path(event, self._tree_view, self._model)
            if target_path:
                for source_path in source_paths:
                    self.file_dropped.emit(source_path, target_path)
            event.accept()
            self.close()  # Auto-close after drop
        else:
            event.ignore()

