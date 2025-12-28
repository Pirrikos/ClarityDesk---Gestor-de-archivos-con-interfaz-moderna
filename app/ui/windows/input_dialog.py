"""
InputDialog - Custom input dialog following visual contract.

Replaces QInputDialog for text input (create folder, create file, etc.).
Visual style: File Box elevated panel.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
)

from app.core.constants import (
    BUTTON_BG_DARK,
    BUTTON_BORDER_DARK,
    BUTTON_BG_DARK_HOVER,
    BUTTON_BORDER_DARK_HOVER,
    FILE_BOX_BORDER,
    FILE_BOX_BUTTON_PRIMARY,
    FILE_BOX_BUTTON_PRIMARY_HOVER,
    FILE_BOX_BUTTON_PRIMARY_PRESSED,
    FILE_BOX_LIST_BG,
    FILE_BOX_TEXT,
)
from app.ui.windows.base_frameless_dialog import BaseFramelessDialog


class InputDialog(BaseFramelessDialog):
    """Custom input dialog following official visual contract."""
    
    def __init__(
        self,
        title: str,
        label: str,
        text: str = "",
        parent=None
    ):
        """
        Initialize input dialog.
        
        Args:
            title: Dialog title.
            label: Label text for input field.
            text: Initial text value (default: empty).
            parent: Parent widget.
        """
        super().__init__(title, parent)
        
        self._label = label
        self._initial_text = text
        self._input_field: Optional[QLineEdit] = None
        self._result_text: Optional[str] = None
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI following official visual contract."""
        content_layout = self.get_content_layout()
        content_layout.setSpacing(16)
        
        # Label
        label_widget = QLabel(self._label)
        label_widget.setStyleSheet(f"""
            QLabel {{
                color: {FILE_BOX_TEXT};
                font-size: 13px;
                font-weight: 500;
            }}
        """)
        content_layout.addWidget(label_widget)
        
        # Input field
        self._input_field = QLineEdit()
        self._input_field.setText(self._initial_text)
        self._input_field.selectAll()  # Seleccionar todo el texto inicial
        self._input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {FILE_BOX_LIST_BG};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
                color: {FILE_BOX_TEXT};
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {FILE_BOX_BUTTON_PRIMARY};
            }}
        """)
        self._input_field.returnPressed.connect(self._on_accept)
        content_layout.addWidget(self._input_field)
        
        content_layout.addStretch()
        
        # Botones
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
        
        # Focus en el input field
        self._input_field.setFocus()
    
    def _on_accept(self) -> None:
        """Handle accept button click."""
        text = self._input_field.text().strip()
        if text:
            self._result_text = text
            self.accept()
    
    def get_text(self) -> Optional[str]:
        """
        Get entered text.
        
        Returns:
            Entered text if accepted, None if cancelled.
        """
        return self._result_text
