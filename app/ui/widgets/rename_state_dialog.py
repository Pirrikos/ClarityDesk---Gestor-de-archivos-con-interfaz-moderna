"""
RenameStateDialog - Dialog for renaming state labels.

Modal dialog with state selection and new name input.
"""

from typing import TYPE_CHECKING, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QComboBox,
)

from app.ui.widgets.state_badge_widget import (
    STATE_CORRECTED,
    STATE_DELIVERED,
    STATE_LABELS,
    STATE_PENDING,
    STATE_REVIEW,
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
        self._state_label_manager = state_label_manager
        self._current_labels = current_labels
        self._selected_state: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build dialog UI."""
        self.setWindowTitle("Renombrar Etiqueta")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Renombrar Etiqueta de Estado")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #1f1f1f;
            }
        """)
        layout.addWidget(title_label)
        
        # Warning message
        warning_label = QLabel(
            "Esta etiqueta se actualizará en todos los archivos que la usan."
        )
        warning_label.setStyleSheet("""
            QLabel {
                color: #d13438;
                font-size: 13px;
                padding: 8px;
                background-color: #fff4e5;
                border-radius: 4px;
            }
        """)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # State selection
        state_label = QLabel("Etiqueta a renombrar:")
        state_label.setStyleSheet("font-weight: 500;")
        layout.addWidget(state_label)
        
        self._state_combo = QComboBox()
        self._state_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #d1d1d1;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QComboBox:hover {
                border-color: #0078d4;
            }
            QComboBox:focus {
                border-color: #0078d4;
                outline: none;
            }
            QComboBox QAbstractItemView {
                background-color: #f5f5f5;
                border: 1px solid #d1d1d1;
                border-radius: 4px;
                selection-background-color: #e0e0e0;
                color: #1f1f1f;
            }
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
        layout.addWidget(self._state_combo)
        
        # New name input
        name_label = QLabel("Nuevo nombre:")
        name_label.setStyleSheet("font-weight: 500;")
        layout.addWidget(name_label)
        
        self._name_input = QLineEdit()
        self._name_input.setMaxLength(17)  # Límite máximo de 17 caracteres
        self._name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d1d1d1;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #0078d4;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                outline: none;
            }
        """)
        self._name_input.setPlaceholderText("Ingresa el nuevo nombre...")
        self._name_input.returnPressed.connect(self._on_confirm)
        layout.addWidget(self._name_input)
        
        # Initialize with first state
        if self._state_combo.count() > 0:
            self._on_state_selected(0)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #d1d1d1;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("Confirmar")
        confirm_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: #0078d4;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #e5e5e7;
                color: #8e8e93;
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(confirm_btn)
        
        layout.addLayout(button_layout)
    
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
            QMessageBox.warning(
                self,
                "Nombre inválido",
                "El nombre de la etiqueta no puede estar vacío."
            )
            return
        
        # Validate with manager
        success, error_msg = self._state_label_manager.rename_label(
            self._selected_state,
            new_name
        )
        
        if not success:
            QMessageBox.warning(self, "Error", error_msg or "No se pudo renombrar la etiqueta.")
            return
        
        self.accept()
    
    def get_selected_state(self) -> Optional[str]:
        """Get the selected state constant."""
        return self._selected_state

