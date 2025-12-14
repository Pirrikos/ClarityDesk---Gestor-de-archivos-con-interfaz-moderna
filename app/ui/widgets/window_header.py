from typing import Optional

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel


class WindowHeader(QWidget):
    """Barra de título personalizada con botones de ventana y arrastre."""

    request_close = Signal()
    request_minimize = Signal()
    request_toggle_maximize = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drag_start: Optional[QPoint] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construir barra superior con estilo claro y botones."""
        self.setFixedHeight(40)
        # Estilo sobrio en blanco con borde inferior sutil
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #e5e5e7;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f0f0f3;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Botones estilo mac/win minimalistas
        self._btn_close = QPushButton("✕", self)
        self._btn_min = QPushButton("—", self)
        self._btn_max = QPushButton("◻", self)

        self._btn_close.setFixedHeight(28)
        self._btn_min.setFixedHeight(28)
        self._btn_max.setFixedHeight(28)

        self._btn_close.clicked.connect(self.request_close.emit)
        self._btn_min.clicked.connect(self.request_minimize.emit)
        self._btn_max.clicked.connect(self.request_toggle_maximize.emit)

        layout.addWidget(self._btn_close, 0)
        layout.addWidget(self._btn_min, 0)
        layout.addWidget(self._btn_max, 0)
        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:
        """Iniciar arrastre al pulsar en zona libre del header."""
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            # No arrastrar si se pulsa sobre botón o label
            if isinstance(child, QPushButton) or isinstance(child, QLabel):
                return
            self._drag_start = event.globalPos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Mover ventana mientras se arrastra el header."""
        if self._drag_start is not None:
            delta = event.globalPos() - self._drag_start
            win = self.window()
            if win:
                win.move(win.pos() + delta)
                self._drag_start = event.globalPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Finalizar arrastre al soltar."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
