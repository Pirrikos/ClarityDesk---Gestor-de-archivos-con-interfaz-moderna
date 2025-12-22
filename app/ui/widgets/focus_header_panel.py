"""
FocusHeaderPanel - Header panel with rename button.

Shows rename button that activates when 1+ files are selected.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


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
        
        # Breadcrumb simple: etiqueta de ruta actual con el nombre del tab
        self._path_label = QLabel("")
        self._path_label.setStyleSheet("""
            QLabel {
                color: #1f1f1f;
                /* font-size: establecido explícitamente */
            }
        """)
        layout.addWidget(self._path_label, 1)
        
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
                /* font-size: establecido explícitamente */
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
        layout.addWidget(self._rename_button, 0)
    
    def update_selection_count(self, count: int) -> None:
        """
        Update button state based on selection count.
        
        Args:
            count: Number of selected files.
        """
        self._rename_button.setEnabled(count >= 1)
    
    def update_path(self, path: str) -> None:
        """Actualizar texto de breadcrumb con la ruta actual."""
        self._path_label.setText(path or "")
