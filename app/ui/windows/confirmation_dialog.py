"""
ConfirmationDialog - Custom confirmation dialog following visual contract.

Replaces QMessageBox for confirmations (delete, move to trash, etc.).
Visual style: File Box elevated panel.
"""

from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
)

from app.core.constants import (
    BUTTON_BG_DARK,
    BUTTON_BORDER_DARK,
    BUTTON_BG_DARK_HOVER,
    BUTTON_BORDER_DARK_HOVER,
    FILE_BOX_BUTTON_PRIMARY,
    FILE_BOX_BUTTON_PRIMARY_HOVER,
    FILE_BOX_BUTTON_PRIMARY_PRESSED,
    FILE_BOX_TEXT,
)
from app.ui.windows.base_frameless_dialog import BaseFramelessDialog


class ConfirmationDialog(BaseFramelessDialog):
    """Custom confirmation dialog following official visual contract."""
    
    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "Aceptar",
        cancel_text: str = "Cancelar",
        parent=None
    ):
        """
        Initialize confirmation dialog.
        
        Args:
            title: Dialog title.
            message: Message to display.
            confirm_text: Text for confirm button (default: "Aceptar").
            cancel_text: Text for cancel button (default: "Cancelar").
            parent: Parent widget.
        """
        super().__init__(title, parent)
        
        self._message = message
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._confirmed = False
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI following official visual contract."""
        content_layout = self.get_content_layout()
        content_layout.setSpacing(20)
        
        # Mensaje
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {FILE_BOX_TEXT};
                font-size: 14px;
                line-height: 1.4;
            }}
        """)
        content_layout.addWidget(message_label)
        
        content_layout.addStretch()
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.setSpacing(8)
        
        cancel_btn = QPushButton(self._cancel_text)
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
        
        confirm_btn = QPushButton(self._confirm_text)
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
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        confirm_btn.setDefault(True)
        button_layout.addWidget(confirm_btn)
        
        content_layout.addLayout(button_layout)
    
    def _on_confirm(self) -> None:
        """Handle confirm button click."""
        self._confirmed = True
        self.accept()
    
    def is_confirmed(self) -> bool:
        """
        Check if user confirmed.
        
        Returns:
            True if confirmed, False otherwise.
        """
        return self._confirmed
