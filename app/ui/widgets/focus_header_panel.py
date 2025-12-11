"""
FocusHeaderPanel - Header panel with rename button.

Shows rename button that activates when 1+ files are selected.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class FocusHeaderPanel(QWidget):
    """Header panel with rename button for bulk operations."""
    
    rename_clicked = Signal()  # Emitted when rename button is clicked
    
    def __init__(self, parent=None):
        """Initialize focus header panel."""
        super().__init__(parent)
        self._rename_button: QPushButton = None
        self._setup_ui()
        self.update_selection_count(0)
    
    def _setup_ui(self) -> None:
        """Build the panel UI."""
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #e5e5e7;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(8)
        layout.addStretch()
        
        self._rename_button = QPushButton("📝 Renombrar")
        self._rename_button.setFixedHeight(36)
        self._rename_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
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
        self._rename_button.clicked.connect(self.rename_clicked.emit)
        layout.addWidget(self._rename_button)
    
    def update_selection_count(self, count: int) -> None:
        """
        Update button state based on selection count.
        
        Args:
            count: Number of selected files.
        """
        self._rename_button.setEnabled(count >= 1)

