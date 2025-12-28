"""
RenameStateDialog - Dialog for renaming state labels.

Modal dialog with state selection and new name input.
Visual style: File Box elevated panel (following official visual contract).
"""

from typing import TYPE_CHECKING, Dict, Optional

from PySide6.QtCore import Qt, QPoint, QEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QWidget,
)

from app.ui.widgets.state_badge_widget import (
    STATE_CORRECTED,
    STATE_DELIVERED,
    STATE_LABELS,
    STATE_PENDING,
    STATE_REVIEW,
)

from app.ui.windows.error_dialog import ErrorDialog
from app.core.constants import (
    APP_HEADER_BG,
    APP_HEADER_BORDER,
    BUTTON_BG_DARK,
    BUTTON_BORDER_DARK,
    BUTTON_BG_DARK_HOVER,
    BUTTON_BORDER_DARK_HOVER,
    CENTRAL_AREA_BG,
    FILE_BOX_BORDER,
    FILE_BOX_BUTTON_PRIMARY,
    FILE_BOX_BUTTON_PRIMARY_HOVER,
    FILE_BOX_BUTTON_PRIMARY_PRESSED,
    FILE_BOX_HOVER_BG,
    FILE_BOX_LIST_BG,
    FILE_BOX_TEXT,
)

from app.core.logger import get_logger

if TYPE_CHECKING:
    from app.managers.state_label_manager import StateLabelManager

logger = get_logger(__name__)


class RenameStateDialog(QDialog):
    """Dialog for renaming a state label."""
    
    def __init__(self, state_label_manager: 'StateLabelManager', current_labels: Dict[str, str], parent=None):
        """
        Initialize rename state dialog.
        
        Args:
            state_label_manager: StateLabelManager instance.
            current_labels: Dictionary mapping state constants to current labels.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        # Configurar ventana frameless con fondo transparente
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        self._state_label_manager = state_label_manager
        self._current_labels = current_labels
        self._selected_state: Optional[str] = None
        self._drag_start: Optional[QPoint] = None
        self._header_widget: Optional[QWidget] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build dialog UI following official visual contract."""
        title_text = "Renombrar Etiqueta"
        self.setWindowTitle(title_text)
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        self.setModal(True)
        
        # 1. QDialog completamente transparente
        self.setStyleSheet("""
            QDialog {
                background-color: transparent;
            }
        """)
        
        # Layout principal completamente transparente
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Contenedor único con fondo y bordes redondeados
        main_container = QWidget()
        main_container.setStyleSheet(f"""
            QWidget {{
                background-color: {APP_HEADER_BG};
                border: 1px solid {APP_HEADER_BORDER};
                border-radius: 12px;
            }}
        """)
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 2. Header del diálogo con botón cerrar y arrastre
        self._header_widget = QWidget()
        self._header_widget.setFixedHeight(48)
        self._header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border-bottom: 1px solid {APP_HEADER_BORDER};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        header_layout = QHBoxLayout(self._header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(0)
        
        header_title_label = QLabel(title_text)
        header_title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)
        header_layout.addWidget(header_title_label)
        header_layout.addStretch()
        
        # Botón cerrar
        close_button = QPushButton("✕")
        close_button.setFixedSize(32, 28)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: {FILE_BOX_TEXT};
                font-size: 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
        close_button.clicked.connect(self.reject)
        header_layout.addWidget(close_button)
        
        container_layout.addWidget(self._header_widget)
        
        # 3. Panel interno con contenido
        content_panel = QWidget()
        content_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {CENTRAL_AREA_BG};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)
        
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)
        
        container_layout.addWidget(content_panel)
        
        # Añadir el contenedor principal al layout del diálogo
        main_layout.addWidget(main_container)
        
        # Warning message
        warning_label = QLabel(
            "Esta etiqueta se actualizará en todos los archivos que la usan."
        )
        warning_label.setStyleSheet(f"""
            QLabel {{
                color: #ff6b6b;
                font-size: 13px;
                padding: 8px;
                background-color: rgba(255, 107, 107, 0.1);
                border: 1px solid rgba(255, 107, 107, 0.3);
                border-radius: 6px;
            }}
        """)
        warning_label.setWordWrap(True)
        content_layout.addWidget(warning_label)
        
        # State selection
        state_label = QLabel("Etiqueta a renombrar:")
        state_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
            }}
        """)
        content_layout.addWidget(state_label)
        
        self._state_combo = QComboBox()
        self._state_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {FILE_BOX_LIST_BG};
                color: {FILE_BOX_TEXT};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QComboBox:hover {{
                border-color: {FILE_BOX_BUTTON_PRIMARY};
            }}
            QComboBox:focus {{
                border-color: {FILE_BOX_BUTTON_PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {FILE_BOX_LIST_BG};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
                selection-background-color: {FILE_BOX_HOVER_BG};
                color: {FILE_BOX_TEXT};
                padding: 4px;
            }}
        """)
        
        # Populate combo with states
        state_configs = [
            (STATE_PENDING, "🟡"),
            (STATE_DELIVERED, "🔵"),
            (STATE_CORRECTED, "✅"),
            (STATE_REVIEW, "🔴"),
        ]
        
        for state, emoji in state_configs:
            label = self._current_labels.get(state, STATE_LABELS.get(state, ""))
            self._state_combo.addItem(f"{emoji} {label}", state)
        
        self._state_combo.currentIndexChanged.connect(self._on_state_selected)
        content_layout.addWidget(self._state_combo)
        
        # New name input
        name_label = QLabel("Nuevo nombre:")
        name_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
            }}
        """)
        content_layout.addWidget(name_label)
        
        self._name_input = QLineEdit()
        self._name_input.setMaxLength(17)  # Límite máximo de 17 caracteres
        self._name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {FILE_BOX_LIST_BG};
                color: {FILE_BOX_TEXT};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border-color: {FILE_BOX_BUTTON_PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: #9AA0A6;
            }}
        """)
        self._name_input.setPlaceholderText("Ingresa el nuevo nombre...")
        self._name_input.returnPressed.connect(self._on_confirm)
        content_layout.addWidget(self._name_input)
        
        # Initialize with first state
        if self._state_combo.count() > 0:
            self._on_state_selected(0)
        
        # Buttons
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
        
        confirm_btn = QPushButton("Confirmar")
        confirm_btn.setStyleSheet(f"""
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
            QPushButton:disabled {{
                background-color: #3a3a3a;
                color: #666666;
            }}
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(confirm_btn)
        
        content_layout.addLayout(button_layout)
    
    def _on_state_selected(self, index: int) -> None:
        """Handle state selection change."""
        if index < 0:
            return
        
        self._selected_state = self._state_combo.itemData(index)
        if self._selected_state:
            current_label = self._current_labels.get(
                self._selected_state,
                STATE_LABELS.get(self._selected_state, "")
            )
            self._name_input.setText(current_label)
            self._name_input.selectAll()
            self._name_input.setFocus()
    
    def _on_confirm(self) -> None:
        """Handle confirm button click."""
        if not self._selected_state:
            return
        
        new_name = self._name_input.text().strip()
        if not new_name:
            error_dialog = ErrorDialog(
                parent=self,
                title="Nombre inválido",
                message="El nombre de la etiqueta no puede estar vacío.",
                is_warning=True
            )
            error_dialog.exec()
            return
        
        # Validate with manager
        success, error_msg = self._state_label_manager.rename_label(
            self._selected_state,
            new_name
        )
        
        if not success:
            error_dialog = ErrorDialog(
                parent=self,
                title="Error",
                message=error_msg or "No se pudo renombrar la etiqueta.",
                is_warning=False
            )
            error_dialog.exec()
            return
        
        self.accept()
    
    def get_selected_state(self) -> Optional[str]:
        """Get the selected state constant."""
        return self._selected_state
    
    def showEvent(self, event: QEvent) -> None:
        """Center dialog on screen when shown."""
        super().showEvent(event)
        screen = self.screen()
        if not screen:
            screen = QApplication.primaryScreen()
        
        if screen:
            screen_geometry = screen.availableGeometry()
            dialog_geometry = self.frameGeometry()
            self.move(
                screen_geometry.left() + (screen_geometry.width() - dialog_geometry.width()) // 2,
                screen_geometry.top() + (screen_geometry.height() - dialog_geometry.height()) // 2
            )
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._header_widget:
                header_pos = self._header_widget.mapFromGlobal(event.globalPos())
                if self._header_widget.rect().contains(header_pos):
                    child = self._header_widget.childAt(header_pos)
                    # No arrastrar si se hace clic en un botón
                    if isinstance(child, QPushButton):
                        super().mousePressEvent(event)
                        return
                    self._drag_start = event.globalPos()
                    event.accept()
                    return
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for window dragging."""
        if self._drag_start is not None:
            delta = event.globalPos() - self._drag_start
            self.move(self.pos() + delta)
            self._drag_start = event.globalPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

