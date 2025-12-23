"""SecondaryHeader - Header secundario debajo del AppHeader.

Header visual igual al AppHeader con botón de renombrar.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget, QSizePolicy

from app.core.constants import DEBUG_LAYOUT


class SecondaryHeader(QWidget):
    """Header secundario con mismo estilo visual que AppHeader."""

    rename_clicked = Signal()  # Emitted when rename button is clicked

    _HEADER_STYLESHEET = """
        QWidget#SecondaryHeader {
            background-color: #1A1D22;
            border-bottom: 1px solid #2A2E36;
        }
    """

    _RENAME_BUTTON_STYLESHEET = """
        QPushButton {
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 8px;
            color: rgba(0, 0, 0, 0.85);
            /* font-size: establecido explícitamente */
            font-weight: 500;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.95);
            border-color: rgba(0, 0, 0, 0.2);
            color: rgba(0, 0, 0, 0.95);
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 1.0);
        }
        QPushButton:disabled {
            background-color: rgba(255, 255, 255, 0.3);
            color: rgba(0, 0, 0, 0.4);
        }
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SecondaryHeader")
        self.setStyleSheet(self._HEADER_STYLESHEET)
        self._rename_button: Optional[QPushButton] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        self._setup_base_configuration()
        layout = self._create_main_layout()
        self._setup_rename_button(layout)

    def _setup_base_configuration(self) -> None:
        """Configure base header properties."""
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(False)

    def _create_main_layout(self) -> QHBoxLayout:
        """Create main horizontal layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return layout

    def _setup_rename_button(self, layout: QHBoxLayout) -> None:
        """Setup rename button."""
        layout.addStretch(1)
        
        self._rename_button = QPushButton("📝 Renombrar", self)
        self._rename_button.setFixedHeight(36)
        self._rename_button.setStyleSheet(self._RENAME_BUTTON_STYLESHEET)
        self._rename_button.clicked.connect(self.rename_clicked.emit)
        self._rename_button.setEnabled(False)  # Inicialmente deshabilitado
        layout.addWidget(self._rename_button, 0)

    def update_selection_count(self, count: int) -> None:
        """
        Update button state based on selection count.
        
        Args:
            count: Number of selected files.
        """
        if self._rename_button:
            self._rename_button.setEnabled(count >= 1)

    def paintEvent(self, event):
        """Paint header background and border."""
        if DEBUG_LAYOUT:
            super().paintEvent(event)
            return
        
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        p.fillRect(rect, QColor("#1A1D22"))
        # Línea inferior acorde al estilo del AppHeader
        p.setPen(QColor("#2A2E36"))
        p.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        p.end()
        super().paintEvent(event)

