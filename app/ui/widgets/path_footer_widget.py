"""
PathFooterWidget - Footer widget that displays file path with button to open containing folder.

Shows the full path of the selected file and a button to open the containing folder.
"""

from PySide6.QtCore import Qt, QElapsedTimer
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from app.services.file_open_service import open_containing_folder
from app.core.constants import DEBUG_LAYOUT, CENTRAL_AREA_BG
from app.core.logger import get_logger

logger = get_logger(__name__)


class PathFooterWidget(QWidget):
    """Footer widget that displays a file path with button to open containing folder."""
    
    def __init__(self, parent=None):
        """Initialize footer widget."""
        super().__init__(parent)
        self._current_path: str = ""
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI layout and styling."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 6)
        layout.setSpacing(8)
        
        self._open_folder_button = QPushButton("Abrir carpeta contenedora", self)
        self._open_folder_button.setStyleSheet("""
            QPushButton {
                color: rgba(100, 100, 100, 1.0);
                font-size: 11px;
                background-color: transparent;
                border: 1px solid rgba(150, 150, 150, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: rgba(150, 150, 150, 0.1);
                border-color: rgba(150, 150, 150, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(150, 150, 150, 0.2);
            }
        """)
        self._open_folder_button.clicked.connect(self._on_open_folder_clicked)
        self._open_folder_button.setVisible(False)
        self._open_folder_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        layout.addWidget(self._open_folder_button, 0, Qt.AlignmentFlag.AlignTop)
        
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._label.setWordWrap(True)
        self._label.setText("")
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._label.setStyleSheet("""
            QLabel {
                color: rgba(150, 150, 150, 1.0);
                font-size: 11px;
                background-color: transparent;
                border: none;
            }
        """)
        
        layout.addWidget(self._label, 1)

    def paintEvent(self, event) -> None:
        """Pintar fondo sólido de refuerzo con instrumentación."""
        if not hasattr(self, '_paint_count_debug'): self._paint_count_debug = 0
        self._paint_count_debug += 1
        t = QElapsedTimer()
        t.start()

        from app.core.constants import CENTRAL_AREA_BG
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(CENTRAL_AREA_BG))
        painter.end()

        elapsed = t.nsecsElapsed() / 1000000.0
        if DEBUG_LAYOUT:
            logger.info(f"🎨 [Footer] Paint #{self._paint_count_debug} | dur={elapsed:.2f}ms")

    def _on_open_folder_clicked(self) -> None:
        """Handle click on open folder button."""
        if self._current_path:
            open_containing_folder(self._current_path)
    
    def set_text(self, text: str) -> None:
        """Set the text to display in the footer (file path). Empty string to clear."""
        self._current_path = text
        if text:
            self._label.setText(text)
            self._label.setVisible(True)
            self._open_folder_button.setVisible(True)
        else:
            self._label.setText("")
            self._label.setVisible(False)
            self._open_folder_button.setVisible(False)
