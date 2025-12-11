"""
FolderTreeSidebar - Navigation history tree widget.

Displays hierarchical tree of opened Focus (tabs) as navigation history.
Only shows folders that have been opened as Focus.
"""

import os

from PySide6.QtCore import QModelIndex, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QMenu,
    QPushButton,
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
from app.ui.widgets.folder_tree_handlers import (
    handle_add_button_click,
    handle_context_menu,
    handle_tree_click,
)
from app.ui.widgets.folder_tree_model import (
    add_focus_path_to_model,
    find_parent_item,
    remove_focus_path_from_model,
)
from app.ui.widgets.folder_tree_styles import get_complete_stylesheet


class FolderTreeSidebar(QWidget):
    """Navigation history tree showing opened Focus folders."""
    
    folder_selected = Signal(str)  # Emitted when folder is clicked (folder path)
    new_focus_requested = Signal(str)  # Emitted when + button is clicked (folder path)
    focus_remove_requested = Signal(str)  # Emitted when remove is requested (folder path)
    files_moved = Signal(str, str)  # Emitted when files are moved (source_path, target_path)
    
    def __init__(self, parent=None):
        """
        Initialize FolderTreeSidebar.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setObjectName("FolderTreeSidebar")  # Para stylesheet
        self.setFixedWidth(240)  # Ancho Arc-style
        self._path_to_item: dict[str, QStandardItem] = {}
        self.setAcceptDrops(True)  # Enable drop on widget
        self._setup_model()
        self._setup_ui()
        self._apply_styling()
    
    def _setup_model(self) -> None:
        """Setup QStandardItemModel for navigation history."""
        self._model = QStandardItemModel(self)
        self._model.setHorizontalHeaderLabels(["Folders"])
    
    def _setup_ui(self) -> None:
        """Build UI layout with QTreeView and + button."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add button at top
        self._add_button = QPushButton("+")
        self._add_button.setObjectName("AddButton")  # Para stylesheet
        self._add_button.setFixedHeight(52)  # Altura suficiente para texto 20px + padding 8px arriba/abajo
        self._add_button.setMinimumWidth(50)  # Ancho mínimo para que se vea
        self._add_button.setMaximumWidth(240)  # Respetar ancho del sidebar
        self._add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(self._add_button)
        
        # Tree view
        self._tree_view = QTreeView(self)
        self._tree_view.setModel(self._model)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setAnimated(True)
        self._tree_view.setExpandsOnDoubleClick(False)
        self._tree_view.setRootIsDecorated(False)  # Sin flechas expand/collapse
        self._tree_view.setIndentation(24)  # Arc-style (era 12)
        self._tree_view.setUniformRowHeights(True)  # Optimización
        self._tree_view.setIconSize(QSize(22, 22))  # Iconos Arc-style
        self._tree_view.setWordWrap(False)  # Prevent text wrapping, use ellipsis
        
        # Enable drag & drop
        self._tree_view.setAcceptDrops(True)
        self._tree_view.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        
        self._tree_view.clicked.connect(self._on_tree_clicked)
        self._tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree_view.customContextMenuRequested.connect(self._on_context_menu)
        
        layout.addWidget(self._tree_view, 1)  # Stretch factor to fill space
    
    def _on_tree_clicked(self, index: QModelIndex) -> None:
        """Handle tree item click - expand node and emit folder_selected signal."""
        folder_path = handle_tree_click(index, self._model, self._tree_view)
        if folder_path:
            self.folder_selected.emit(folder_path)
    
    def _on_add_clicked(self) -> None:
        """Handle + button click - open folder picker."""
        folder_path = handle_add_button_click(self)
        if folder_path:
            self.new_focus_requested.emit(folder_path)
    
    def _on_context_menu(self, position: QPoint) -> None:
        """Handle context menu request on tree item."""
        folder_path = handle_context_menu(position, self._tree_view, self._model)
        if not folder_path:
            return
        
        menu = QMenu(self)
        remove_action = menu.addAction("Eliminar del árbol")
        remove_action.triggered.connect(
            lambda: self.focus_remove_requested.emit(folder_path)
        )
        
        menu.exec(self._tree_view.mapToGlobal(position))
    
    def add_focus_path(self, path: str) -> None:
        """
        Add Focus path to navigation history tree.
        
        Inserts path under its parent ONLY if parent exists in tree.
        Otherwise inserts as root node.
        Skips if path already exists in tree.
        
        Args:
            path: Folder path to add.
        """
        item = add_focus_path_to_model(self._model, self._path_to_item, path)
        if not item:
            return
        
        # Expand parent automatically to show new node
        parent_item = find_parent_item(self._model, self._path_to_item, os.path.normpath(path))
        if parent_item != self._model.invisibleRootItem():
            parent_index = self._model.indexFromItem(parent_item)
            if parent_index.isValid():
                self._tree_view.expand(parent_index)
    
    def remove_focus_path(self, path: str) -> None:
        """
        Remove Focus path from navigation history tree.
        
        Removes node and all its children (breadcrumb hierarchy).
        Does NOT delete folder from filesystem.
        
        Args:
            path: Folder path to remove.
        """
        remove_focus_path_from_model(self._model, self._path_to_item, path)
    
    def dragEnterEvent(self, event) -> None:
        """Handle drag enter on tree view."""
        handle_drag_enter(event)
    
    def dragMoveEvent(self, event) -> None:
        """Handle drag move over tree view."""
        handle_drag_move(event, self._tree_view, self._model)
    
    def dropEvent(self, event) -> None:
        """Handle file drop on tree node - move files to target folder."""
        # Get watcher from parent if available (MainWindow -> TabManager)
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
            target_path = self._get_drop_target_path(event)
            if target_path:
                for source_path in source_paths:
                    self.files_moved.emit(source_path, target_path)
            event.accept()
        else:
            event.ignore()
    
    def _get_drop_target_path(self, event) -> str:
        """Get target folder path from drop event."""
        return get_drop_target_path(event, self._tree_view, self._model)
    
    def _apply_styling(self) -> None:
        """Apply Arc Browser stylesheet to sidebar."""
        self.setStyleSheet(get_complete_stylesheet())
    
    def get_focus_tree_paths(self) -> list[str]:
        """
        Get all paths currently in the focus tree.
        
        Returns:
            List of folder paths in the tree.
        """
        return list(self._path_to_item.keys())
    
    def get_expanded_paths(self) -> list[str]:
        """
        Get all currently expanded node paths.
        
        Returns:
            List of expanded folder paths.
        """
        expanded_paths = []
        root = self._model.invisibleRootItem()
        
        def collect_expanded(item: QStandardItem, path: str) -> None:
            """Recursively collect expanded items."""
            if item is None:
                return
            
            item_path = path
            if item_path in self._path_to_item:
                index = self._model.indexFromItem(item)
                if index.isValid() and self._tree_view.isExpanded(index):
                    expanded_paths.append(item_path)
            
            # Check children
            for i in range(item.rowCount()):
                child = item.child(i)
                if child:
                    child_path = child.data(Qt.ItemDataRole.UserRole)
                    if child_path:
                        collect_expanded(child, child_path)
        
        # Start from root
        for i in range(root.rowCount()):
            item = root.child(i)
            if item:
                item_path = item.data(Qt.ItemDataRole.UserRole)
                if item_path:
                    collect_expanded(item, item_path)
        
        return expanded_paths
    
    def restore_tree(self, paths: list[str], expanded_paths: list[str]) -> None:
        """
        Restore tree state from saved paths and expanded nodes.
        
        Args:
            paths: List of folder paths to add to tree.
            expanded_paths: List of paths that should be expanded.
        """
        # Clear current tree
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["Folders"])
        self._path_to_item.clear()
        
        # Add all paths to tree
        for path in paths:
            self.add_focus_path(path)
        
        # Expand specified nodes
        expanded_set = set(expanded_paths)
        for path in expanded_set:
            if path in self._path_to_item:
                item = self._path_to_item[path]
                index = self._model.indexFromItem(item)
                if index.isValid():
                    self._tree_view.expand(index)
    
    def showEvent(self, event) -> None:
        """Asegurar que el botón sea visible cuando se muestra el widget."""
        super().showEvent(event)
        if hasattr(self, '_add_button'):
            self._add_button.setVisible(True)
            self._add_button.raise_()  # Traer al frente
            self._add_button.update()