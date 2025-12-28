"""
TrashDeleteDialog - Confirmation dialog for permanent deletion.

Shows confirmation dialog with checkbox for permanent deletion from trash.
Visual style: File Box elevated panel (following official visual contract).
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QHBoxLayout,
)

from app.core.constants import (
    BUTTON_BG_DARK,
    BUTTON_BORDER_DARK,
    BUTTON_BG_DARK_HOVER,
    BUTTON_BORDER_DARK_HOVER,
    CHECKBOX_BORDER,
    CHECKBOX_BORDER_HOVER,
    CHECKBOX_BG_CHECKED,
    CHECKBOX_BG_CHECKED_HOVER,
    FILE_BOX_BUTTON_PRIMARY,
    FILE_BOX_BUTTON_PRIMARY_HOVER,
    FILE_BOX_BUTTON_PRIMARY_PRESSED,
    FILE_BOX_LIST_BG,
    FILE_BOX_TEXT,
)
from app.ui.windows.base_frameless_dialog import BaseFramelessDialog
from app.ui.windows.error_dialog import ErrorDialog


class TrashDeleteDialog(BaseFramelessDialog):
    """Dialog for confirming permanent deletion from trash."""
    
    def __init__(self, file_name: str, parent=None):
        """
        Initialize delete confirmation dialog.
        
        Args:
            file_name: Name of file to delete.
            parent: Parent widget.
        """
        super().__init__("Eliminar permanentemente", parent)
        
        self._file_name = file_name
        self._confirmed = False
        self._ok_button: Optional[QPushButton] = None
        
        self.setMinimumWidth(450)
        self.setMinimumHeight(300)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI following official visual contract."""
        content_layout = self.get_content_layout()
        content_layout.setSpacing(16)
        
        # Warning message
        warning_label = QLabel(
            f"¿Estás seguro de que quieres eliminar permanentemente '{self._file_name}'?\n\n"
            "Esta acción no se puede deshacer."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(f"""
            QLabel {{
                color: #ff6b6b;
                font-size: 14px;
                padding: 12px;
                background-color: rgba(255, 107, 107, 0.1);
                border: 1px solid rgba(255, 107, 107, 0.3);
                border-radius: 6px;
            }}
        """)
        content_layout.addWidget(warning_label)
        
        # Confirmation checkbox
        self._confirm_checkbox = QCheckBox("Sí, eliminar permanentemente")
        self._confirm_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {FILE_BOX_TEXT};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {CHECKBOX_BORDER};
                border-radius: 4px;
                background-color: {FILE_BOX_LIST_BG};
            }}
            QCheckBox::indicator:hover {{
                border-color: {CHECKBOX_BORDER_HOVER};
            }}
            QCheckBox::indicator:checked {{
                background-color: {CHECKBOX_BG_CHECKED};
                border-color: {CHECKBOX_BG_CHECKED};
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {CHECKBOX_BG_CHECKED_HOVER};
                border-color: {CHECKBOX_BG_CHECKED_HOVER};
            }}
        """)
        self._confirm_checkbox.stateChanged.connect(self._on_checkbox_changed)
        content_layout.addWidget(self._confirm_checkbox)
        
        content_layout.addStretch()
        
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
        
        self._ok_button = QPushButton("Eliminar")
        self._ok_button.setEnabled(False)  # Deshabilitado hasta que se marque el checkbox
        self._ok_button.setStyleSheet(f"""
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
        self._ok_button.clicked.connect(self._on_accept)
        button_layout.addWidget(self._ok_button)
        
        content_layout.addLayout(button_layout)
    
    def _on_checkbox_changed(self, state: int) -> None:
        """Handle checkbox state change - enable/disable OK button."""
        if self._ok_button:
            self._ok_button.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _on_accept(self) -> None:
        """Handle accept button click."""
        if self._confirm_checkbox.isChecked():
            self._confirmed = True
            self.accept()
        else:
            error_dialog = ErrorDialog(
                parent=self,
                title="Confirmación requerida",
                message="Debes marcar la casilla para confirmar la eliminación permanente.",
                is_warning=True
            )
            error_dialog.exec()
    
    def is_confirmed(self) -> bool:
        """
        Check if deletion was confirmed.
        
        Returns:
            True if confirmed, False otherwise.
        """
        return self._confirmed
