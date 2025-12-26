"""
PathFooterWidget - Simple footer widget that displays file path.

Shows the full path of the selected file.
Non-interactive, no logic, just displays text.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget


class PathFooterWidget(QWidget):
    """Simple footer widget that displays a file path."""
    
    def __init__(self, parent=None):
        """Initialize footer widget."""
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI layout and styling."""
        from PySide6.QtWidgets import QHBoxLayout
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(0)
        
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._label.setText("")
        self._label.setStyleSheet("""
            QLabel {
                color: rgba(150, 150, 150, 1.0);
                font-size: 11px;
                background-color: transparent;
                border: none;
            }
        """)
        
        layout.addWidget(self._label)
    
    def set_text(self, text: str) -> None:
        """
        Set the text to display in the footer.
        
        Args:
            text: Text to display (file path). Empty string to clear.
        """
        if text:
            self._label.setText(text)
            self._label.setVisible(True)
        else:
            self._label.setText("")
            self._label.setVisible(False)

