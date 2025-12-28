"""
ReorderWorkspacesDialog - Dialog for reordering workspaces.

Follows official visual contract.
"""

from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)
from PySide6.QtGui import QPainter

from app.core.constants import (
    BUTTON_BG_DARK,
    BUTTON_BORDER_DARK,
    BUTTON_BG_DARK_HOVER,
    BUTTON_BORDER_DARK_HOVER,
    FILE_BOX_BUTTON_PRIMARY,
    FILE_BOX_BUTTON_PRIMARY_HOVER,
    FILE_BOX_BUTTON_PRIMARY_PRESSED,
    FILE_BOX_TEXT,
    FILE_BOX_LIST_BG,
    FILE_BOX_BORDER,
    FILE_BOX_HOVER_BG,
)
from app.ui.windows.base_frameless_dialog import BaseFramelessDialog

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class NoMarginItemDelegate(QStyledItemDelegate):
    """Delegate que elimina todos los márgenes de los items."""
    
    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(size.width(), size.height())
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        # Eliminar cualquier padding/margin del rectángulo de pintado
        # Asegurar que el texto se pinte desde el borde izquierdo
        option.rect.setLeft(option.rect.left())
        option.rect.setRight(option.rect.right())
        # Eliminar decoración de selección por defecto
        option.showDecorationSelected = False
        super().paint(painter, option, index)


class ReorderWorkspacesDialog(BaseFramelessDialog):
    """Dialog for reordering workspaces."""
    
    def __init__(
        self,
        workspaces: List['Workspace'],
        parent=None
    ):
        """
        Initialize reorder workspaces dialog.
        
        Args:
            workspaces: List of Workspace instances to reorder.
            parent: Parent widget.
        """
        super().__init__("Reordenar Workspaces", parent)
        
        self._workspaces = workspaces.copy()
        self._reordered_workspaces: Optional[List['Workspace']] = None
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI following official visual contract."""
        content_layout = self.get_content_layout()
        content_layout.setSpacing(16)
        
        # Instrucciones
        instructions_label = QLabel("Arrastra los workspaces para reordenarlos o usa los botones ↑ ↓")
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet(f"""
            QLabel {{
                color: {FILE_BOX_TEXT};
                font-size: 13px;
                line-height: 1.4;
            }}
        """)
        content_layout.addWidget(instructions_label)
        
        # Lista de workspaces
        self._list_widget = QListWidget()
        self._list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list_widget.setSpacing(0)
        self._list_widget.setContentsMargins(0, 0, 0, 0)
        self._list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {FILE_BOX_LIST_BG};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
                color: {FILE_BOX_TEXT};
                font-size: 13px;
                padding: 0px;
                outline: none;
            }}
            QListWidget::viewport {{
                background-color: {FILE_BOX_LIST_BG};
                border: none;
                padding: 0px;
                margin: 0px;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 8px 12px;
                margin: 0px;
                outline: none;
            }}
            QListWidget::item:hover {{
                background-color: {FILE_BOX_HOVER_BG};
                border: none;
                outline: none;
            }}
            QListWidget::item:selected {{
                background-color: {FILE_BOX_HOVER_BG};
                border: none;
                outline: none;
                padding: 8px 12px;
                margin: 0px;
            }}
            QListWidget::item:selected:active {{
                background-color: {FILE_BOX_HOVER_BG};
                border: none;
                outline: none;
            }}
            QListWidget::item:selected:!active {{
                background-color: {FILE_BOX_HOVER_BG};
                border: none;
                outline: none;
            }}
        """)
        
        # Configurar viewport directamente para eliminar márgenes
        viewport = self._list_widget.viewport()
        if viewport:
            viewport.setContentsMargins(0, 0, 0, 0)
        
        # Usar delegate personalizado para eliminar márgenes
        self._list_widget.setItemDelegate(NoMarginItemDelegate(self._list_widget))
        
        # Agregar workspaces a la lista
        for workspace in self._workspaces:
            item = QListWidgetItem(workspace.name)
            item.setData(Qt.ItemDataRole.UserRole, workspace.id)
            # Eliminar cualquier padding/margin del item
            item.setSizeHint(item.sizeHint())
            self._list_widget.addItem(item)
        
        content_layout.addWidget(self._list_widget)
        
        # Botones de control
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        move_up_btn = QPushButton("↑ Subir")
        move_up_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_BG_DARK};
                border: 1px solid {BUTTON_BORDER_DARK};
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.88);
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_BG_DARK_HOVER};
                border-color: {BUTTON_BORDER_DARK_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {BUTTON_BG_DARK_HOVER};
                border-color: {BUTTON_BORDER_DARK_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {BUTTON_BG_DARK};
                border-color: {BUTTON_BORDER_DARK};
                color: rgba(255, 255, 255, 0.4);
            }}
        """)
        move_up_btn.clicked.connect(self._move_up)
        controls_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("↓ Bajar")
        move_down_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_BG_DARK};
                border: 1px solid {BUTTON_BORDER_DARK};
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.88);
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_BG_DARK_HOVER};
                border-color: {BUTTON_BORDER_DARK_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {BUTTON_BG_DARK_HOVER};
                border-color: {BUTTON_BORDER_DARK_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {BUTTON_BG_DARK};
                border-color: {BUTTON_BORDER_DARK};
                color: rgba(255, 255, 255, 0.4);
            }}
        """)
        move_down_btn.clicked.connect(self._move_down)
        controls_layout.addWidget(move_down_btn)
        
        controls_layout.addStretch()
        content_layout.addLayout(controls_layout)
        
        content_layout.addStretch()
        
        # Botones de acción
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.setSpacing(8)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_BG_DARK};
                border: 1px solid {BUTTON_BORDER_DARK};
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.88);
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_BG_DARK_HOVER};
                border-color: {BUTTON_BORDER_DARK_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {BUTTON_BG_DARK_HOVER};
                border-color: {BUTTON_BORDER_DARK_HOVER};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        accept_btn = QPushButton("Aceptar")
        accept_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {FILE_BOX_BUTTON_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {FILE_BOX_BUTTON_PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {FILE_BOX_BUTTON_PRIMARY_PRESSED};
            }}
        """)
        accept_btn.clicked.connect(self._on_accept)
        accept_btn.setDefault(True)
        button_layout.addWidget(accept_btn)
        
        content_layout.addLayout(button_layout)
        
        # Conectar cambios de selección para habilitar/deshabilitar botones
        self._list_widget.currentRowChanged.connect(lambda: self._update_button_states(move_up_btn, move_down_btn))
        self._list_widget.itemSelectionChanged.connect(lambda: self._update_button_states(move_up_btn, move_down_btn))
        self._update_button_states(move_up_btn, move_down_btn)
    
    def _update_button_states(self, move_up_btn: QPushButton, move_down_btn: QPushButton) -> None:
        """Update button enabled states based on selection."""
        current_row = self._list_widget.currentRow()
        move_up_btn.setEnabled(current_row > 0)
        move_down_btn.setEnabled(current_row >= 0 and current_row < self._list_widget.count() - 1)
    
    def _move_up(self) -> None:
        """Move selected item up."""
        current_row = self._list_widget.currentRow()
        if current_row > 0:
            item = self._list_widget.takeItem(current_row)
            self._list_widget.insertItem(current_row - 1, item)
            self._list_widget.setCurrentRow(current_row - 1)
    
    def _move_down(self) -> None:
        """Move selected item down."""
        current_row = self._list_widget.currentRow()
        if current_row < self._list_widget.count() - 1:
            item = self._list_widget.takeItem(current_row)
            self._list_widget.insertItem(current_row + 1, item)
            self._list_widget.setCurrentRow(current_row + 1)
    
    def _on_accept(self) -> None:
        """Handle accept button click - build reordered list."""
        reordered_workspaces = []
        workspace_dict = {ws.id: ws for ws in self._workspaces}
        
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            workspace_id = item.data(Qt.ItemDataRole.UserRole)
            if workspace_id in workspace_dict:
                reordered_workspaces.append(workspace_dict[workspace_id])
        
        self._reordered_workspaces = reordered_workspaces
        self.accept()
    
    def get_reordered_workspaces(self) -> Optional[List['Workspace']]:
        """
        Get reordered workspaces list.
        
        Returns:
            Reordered list of workspaces if accepted, None if cancelled.
        """
        return self._reordered_workspaces

