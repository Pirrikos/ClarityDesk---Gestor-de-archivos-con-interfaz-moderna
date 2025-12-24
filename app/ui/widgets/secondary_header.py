"""SecondaryHeader - Header secundario debajo del AppHeader.

Header visual igual al AppHeader con botón de renombrar.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPaintEvent
from PySide6.QtWidgets import QHBoxLayout, QWidget, QSizePolicy

from app.core.constants import DEBUG_LAYOUT


class SecondaryHeader(QWidget):
    """Header secundario con mismo estilo visual que AppHeader."""

    _HEADER_STYLESHEET = """
        QWidget#SecondaryHeader {
            background-color: #1A1D22;
            border-bottom: 1px solid #2A2E36;
        }
    """


    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SecondaryHeader")
        self.setStyleSheet(self._HEADER_STYLESHEET)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        self._setup_base_configuration()
        layout = self._create_main_layout()
        layout.addStretch(1)

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
    
    def paintEvent(self, event: QPaintEvent) -> None:
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

