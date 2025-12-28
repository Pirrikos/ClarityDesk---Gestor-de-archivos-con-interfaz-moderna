"""
ErrorDialog - Custom error/warning dialog following visual contract.

Replaces QMessageBox for errors and warnings.
Visual style: File Box elevated panel.
"""

from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
)

from app.core.constants import (
    FILE_BOX_BUTTON_PRIMARY,
    FILE_BOX_BUTTON_PRIMARY_HOVER,
    FILE_BOX_BUTTON_PRIMARY_PRESSED,
)
from app.ui.windows.base_frameless_dialog import BaseFramelessDialog


class ErrorDialog(BaseFramelessDialog):
    """Custom error/warning dialog following official visual contract."""
    
    def __init__(
        self,
        title: str,
        message: str,
        is_warning: bool = False,
        parent=None
    ):
        """
        Initialize error/warning dialog.
        
        Args:
            title: Dialog title.
            message: Error/warning message to display.
            is_warning: True for warning (yellow), False for error (red).
            parent: Parent widget.
        """
        super().__init__(title, parent)
        
        self._message = message
        self._is_warning = is_warning
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI following official visual contract."""
        content_layout = self.get_content_layout()
        content_layout.setSpacing(20)
        
        # Mensaje con estilo según tipo
        if self._is_warning:
            message_style = f"""
                QLabel {{
                    color: #ffa500;
                    font-size: 14px;
                    line-height: 1.4;
                    padding: 12px;
                    background-color: rgba(255, 165, 0, 0.1);
                    border: 1px solid rgba(255, 165, 0, 0.3);
                    border-radius: 6px;
                }}
            """
        else:
            message_style = f"""
                QLabel {{
                    color: #ff6b6b;
                    font-size: 14px;
                    line-height: 1.4;
                    padding: 12px;
                    background-color: rgba(255, 107, 107, 0.1);
                    border: 1px solid rgba(255, 107, 107, 0.3);
                    border-radius: 6px;
                }}
            """
        
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(message_style)
        content_layout.addWidget(message_label)
        
        content_layout.addStretch()
        
        # Botón OK
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("Aceptar")
        ok_btn.setStyleSheet(f"""
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
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        content_layout.addLayout(button_layout)
