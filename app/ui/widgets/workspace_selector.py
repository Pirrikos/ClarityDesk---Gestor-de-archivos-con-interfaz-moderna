"""
WorkspaceSelector - Workspace selection widget.

Vertical list widget for selecting and managing workspaces.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QMessageBox
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class WorkspaceSelector(QWidget):
    """Vertical list widget for workspace selection."""
    
    workspace_selected = Signal(str)  # Emitted when workspace is selected (workspace_id)
    workspace_create_requested = Signal()  # Emitted when + button is clicked
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize WorkspaceSelector.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setObjectName("WorkspaceSelector")
        self.setMinimumWidth(120)
        self.setMaximumWidth(180)
        self._workspace_manager = None
        self._setup_ui()
        self._apply_styling()
    
    def set_workspace_manager(self, workspace_manager) -> None:
        """
        Set WorkspaceManager instance.
        
        Args:
            workspace_manager: WorkspaceManager instance.
        """
        self._workspace_manager = workspace_manager
        self._refresh_workspaces()
        
        if workspace_manager:
            workspace_manager.workspace_created.connect(self._refresh_workspaces)
            workspace_manager.workspace_deleted.connect(self._refresh_workspaces)
            workspace_manager.workspace_changed.connect(self._on_workspace_changed)
    
    def _setup_ui(self) -> None:
        """Build UI layout with + button and list."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add button at top
        self._add_button = QPushButton("+")
        self._add_button.setObjectName("WorkspaceAddButton")
        self._add_button.setFixedHeight(52)
        self._add_button.setMinimumWidth(100)
        self._add_button.setMaximumWidth(180)
        self._add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(self._add_button)
        
        # List widget
        self._list_widget = QListWidget(self)
        self._list_widget.setObjectName("WorkspaceList")
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._list_widget, 1)
    
    def _apply_styling(self) -> None:
        """Apply stylesheet to widget."""
        self.setStyleSheet("""
            QWidget#WorkspaceSelector {
                background-color: rgba(0, 0, 0, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }
            QPushButton#WorkspaceAddButton {
                background-color: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.7);
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton#WorkspaceAddButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.9);
            }
            QPushButton#WorkspaceAddButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QListWidget#WorkspaceList {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget#WorkspaceList::item {
                color: rgba(255, 255, 255, 0.6);
                padding: 8px 12px;
                border: none;
                min-height: 32px;
            }
            QListWidget#WorkspaceList::item:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.8);
            }
            QListWidget#WorkspaceList::item:selected {
                background-color: rgba(255, 255, 255, 0.15);
                color: rgba(255, 255, 255, 0.9);
            }
        """)
    
    def _refresh_workspaces(self) -> None:
        """Refresh workspace list from manager."""
        if not self._workspace_manager:
            return
        
        self._list_widget.clear()
        workspaces = self._workspace_manager.get_workspaces()
        active_id = self._workspace_manager.get_active_workspace_id()
        
        for workspace in workspaces:
            item = QListWidgetItem(workspace.name)
            item.setData(Qt.ItemDataRole.UserRole, workspace.id)
            self._list_widget.addItem(item)
            
            if workspace.id == active_id:
                self._list_widget.setCurrentItem(item)
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle workspace item click."""
        workspace_id = item.data(Qt.ItemDataRole.UserRole)
        if workspace_id:
            self.workspace_selected.emit(workspace_id)
    
    def _on_add_clicked(self) -> None:
        """Handle + button click - create new workspace."""
        if not self._workspace_manager:
            return
        
        name, ok = QInputDialog.getText(
            self,
            "Nuevo Workspace",
            "Nombre del workspace:",
            text=""
        )
        
        if ok and name.strip():
            workspace = self._workspace_manager.create_workspace(name.strip())
            self._refresh_workspaces()
            # Auto-select newly created workspace
            self.workspace_selected.emit(workspace.id)
    
    def _on_context_menu(self, position) -> None:
        """Handle context menu for workspace item."""
        item = self._list_widget.itemAt(position)
        if not item:
            return
        
        workspace_id = item.data(Qt.ItemDataRole.UserRole)
        if not workspace_id or not self._workspace_manager:
            return
        
        workspace = self._workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return
        
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        delete_action = menu.addAction("Eliminar")
        delete_action.triggered.connect(lambda: self._delete_workspace(workspace_id, workspace.name))
        
        menu.exec(self._list_widget.mapToGlobal(position))
    
    def _delete_workspace(self, workspace_id: str, workspace_name: str) -> None:
        """Delete workspace after confirmation."""
        reply = QMessageBox.question(
            self,
            "Eliminar Workspace",
            f"¿Eliminar workspace '{workspace_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._workspace_manager:
                self._workspace_manager.delete_workspace(workspace_id)
    
    def _on_workspace_changed(self, workspace_id: str) -> None:
        """Handle workspace change from manager."""
        self._refresh_workspaces()

