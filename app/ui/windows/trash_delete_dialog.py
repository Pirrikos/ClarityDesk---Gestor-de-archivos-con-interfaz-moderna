"""
TrashDeleteDialog - Confirmation dialog for permanent deletion.

Shows confirmation dialog with checkbox for permanent deletion from trash.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)


class TrashDeleteDialog(QDialog):
    """Dialog for confirming permanent deletion from trash."""
    
    def __init__(self, file_name: str, parent=None):
        """
        Initialize delete confirmation dialog.
        
        Args:
            file_name: Name of file to delete.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._file_name = file_name
        self._confirmed = False
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI."""
        self.setWindowTitle("Eliminar permanentemente")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Warning message
        warning_label = QLabel(
            f"¿Estás seguro de que quieres eliminar permanentemente '{self._file_name}'?\n\n"
            "Esta acción no se puede deshacer."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #1d1d1f;
            }
        """)
        layout.addWidget(warning_label)
        
        # Confirmation checkbox
        self._confirm_checkbox = QCheckBox("Sí, eliminar permanentemente")
        self._confirm_checkbox.setStyleSheet("""
            QCheckBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                color: #1d1d1f;
            }
        """)
        layout.addWidget(self._confirm_checkbox)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Eliminar")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        # Disable OK button until checkbox is checked
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setEnabled(False)
        self._confirm_checkbox.stateChanged.connect(
            lambda state: ok_button.setEnabled(state == Qt.CheckState.Checked.value)
        )
        
        layout.addWidget(button_box)
    
    def _on_accept(self) -> None:
        """Handle accept button click."""
        if self._confirm_checkbox.isChecked():
            self._confirmed = True
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Confirmación requerida",
                "Debes marcar la casilla para confirmar la eliminación permanente."
            )
    
    def is_confirmed(self) -> bool:
        """
        Check if deletion was confirmed.
        
        Returns:
            True if confirmed, False otherwise.
        """
        return self._confirmed

