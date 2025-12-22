"""
WorkspaceSelector - Workspace selection widget.

Horizontal compact bar for selecting and managing workspaces.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
    QInputDialog,
    QMessageBox,
    QMenu
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class WorkspaceSelector(QWidget):
    """Horizontal compact bar for workspace selection."""
    
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
        self._workspace_manager = None
        self._workspace_button = None
        self._add_button = None
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
        """Build UI layout as horizontal compact bar."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Workspace selector button (shows active workspace + dropdown indicator)
        self._workspace_button = QPushButton()
        self._workspace_button.setObjectName("WorkspaceButton")
        self._workspace_button.setFixedHeight(32)
        self._workspace_button.clicked.connect(self._on_workspace_button_clicked)
        layout.addWidget(self._workspace_button, 0)
        
        # Add button (compact, horizontal)
        self._add_button = QPushButton("+")
        self._add_button.setObjectName("WorkspaceAddButton")
        self._add_button.setFixedSize(32, 32)
        self._add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(self._add_button, 0)
        
        # Set fixed height for the entire widget
        self.setFixedHeight(48)
    
    def _apply_styling(self) -> None:
        """Apply stylesheet to widget."""
        self.setStyleSheet("""
            QWidget#WorkspaceSelector {
                background-color: rgba(0, 0, 0, 0.2);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton#WorkspaceButton {
                /* Un poco más claro que el fondo para destacar el desplegable */
                background-color: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                /* font-size: establecido explícitamente */
                padding: 6px 12px;
                text-align: left;
            }
            QPushButton#WorkspaceButton:hover {
                background-color: rgba(255, 255, 255, 0.16);
                border-color: rgba(255, 255, 255, 0.22);
            }
            QPushButton#WorkspaceButton:pressed {
                background-color: rgba(255, 255, 255, 0.20);
            }
            QPushButton#WorkspaceAddButton {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.7);
                /* font-size: establecido explícitamente */
                font-weight: bold;
            }
            QPushButton#WorkspaceAddButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-color: rgba(255, 255, 255, 0.2);
                color: rgba(255, 255, 255, 0.9);
            }
            QPushButton#WorkspaceAddButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
    
    def _refresh_workspaces(self) -> None:
        """Refresh workspace button text from manager."""
        if not self._workspace_manager or not self._workspace_button:
            return
        
        active_id = self._workspace_manager.get_active_workspace_id()
        if active_id:
            active_workspace = self._workspace_manager.get_workspace(active_id)
            if active_workspace:
                # Mostrar nombre del workspace + indicador de dropdown (▼)
                self._workspace_button.setText(f"{active_workspace.name} ▼")
            else:
                self._workspace_button.setText("Sin workspace ▼")
        else:
            self._workspace_button.setText("Sin workspace ▼")
    
    def _on_workspace_button_clicked(self) -> None:
        """Handle workspace button click - show dropdown menu."""
        if not self._workspace_manager:
            return
        
        workspaces = self._workspace_manager.get_workspaces()
        active_id = self._workspace_manager.get_active_workspace_id()
        
        menu = QMenu(self)
        # Estilo del menú desplegable: fondo oscuro claro, borde oscuro y esquinas redondeadas
        menu.setStyleSheet("""
            QMenu {
                background-color: #1A1D22;
                border: 1px solid #2A2E36;
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.92);
                padding: 8px 8px;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #20242A;
                color: rgba(255, 255, 255, 0.98);
            }
            QMenu::separator {
                height: 1px;
                background: #2A2E36;
                margin: 6px 8px;
            }
            /* Indicador circular pequeño a la izquierda, sin desplazar el texto entre items */
            QMenu::indicator {
                width: 8px; height: 8px;
                border-radius: 4px;
                margin: 0 6px 0 0;
                background-color: transparent;
                border: none;
            }
            QMenu::indicator:checked {
                background-color: #3D7BFF;
                border: 1px solid #2F61CC;
            }
            QMenu::indicator:unchecked {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Añadir cada workspace al menú con indicador circular del activo
        for workspace in workspaces:
            is_active = workspace.id == active_id
            action = menu.addAction(workspace.name)
            action.setCheckable(True)  # todos checkables para reservar espacio del indicador
            action.setChecked(is_active)
            action.triggered.connect(lambda checked, ws_id=workspace.id: self._on_menu_item_selected(ws_id))
        
        # Separador
        menu.addSeparator()
        
        # Opción para crear nuevo workspace
        create_action = menu.addAction("+ Nuevo workspace")
        create_action.triggered.connect(self._on_add_clicked)
        
        # Mostrar menú centrado bajo el botón del workspace
        button_rect = self._workspace_button.geometry()
        menu_size = menu.sizeHint()
        x_local = int(button_rect.left() + (button_rect.width() - menu_size.width()) / 2)
        y_local = button_rect.bottom()
        menu_pos = self._workspace_button.mapToGlobal(QPoint(x_local, y_local))
        menu.exec(menu_pos)
    
    def _on_menu_item_selected(self, workspace_id: str) -> None:
        """Handle workspace selection from menu."""
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
