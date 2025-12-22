from typing import Optional

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy


class WindowHeader(QWidget):
    """Barra de título personalizada con botones de ventana y arrastre."""

    request_close = Signal()
    request_minimize = Signal()
    request_toggle_maximize = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drag_start: Optional[QPoint] = None
        # Establecer color de fondo inmediatamente para evitar flash marrón
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F5F7;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        self._setup_ui()
    

    def _setup_ui(self) -> None:
        self.setFixedHeight(40)
        # Agregar estilos de botones a los estilos existentes
        current_styles = self.styleSheet()
        button_styles = """
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 4px 6px;
                /* font-size: establecido explícitamente */
            }
            QPushButton:hover {
                background-color: #f0f0f3;
            }
        """
        self.setStyleSheet(current_styles + button_styles)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self._btn_close = QPushButton("✕", self)
        self._btn_min = QPushButton("—", self)
        self._btn_max = QPushButton("◻", self)

        self._btn_close.setFixedSize(32, 28)
        self._btn_min.setFixedSize(32, 28)
        self._btn_max.setFixedSize(32, 28)
        
        self._btn_close.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._btn_min.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._btn_max.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._btn_close.clicked.connect(self.request_close.emit)
        self._btn_min.clicked.connect(self.request_minimize.emit)
        self._btn_max.clicked.connect(self.request_toggle_maximize.emit)

        layout.addWidget(self._btn_close, 0)
        layout.addWidget(self._btn_min, 0)
        layout.addWidget(self._btn_max, 0)
        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                win = self.window()
                wh = win.windowHandle() if win else None
                if wh:
                    geo = win.frameGeometry()
                    margin = 6
                    gp = event.globalPos()
                    edges = Qt.Edges()
                    if abs(gp.y() - geo.top()) <= margin:
                        edges |= Qt.Edge.TopEdge
                        if abs(gp.x() - geo.left()) <= margin:
                            edges |= Qt.Edge.LeftEdge
                        elif abs(gp.x() - geo.right()) <= margin:
                            edges |= Qt.Edge.RightEdge
                    if edges:
                        wh.startSystemResize(edges)
                        event.accept()
                        return
            except Exception:
                pass

            child = self.childAt(event.pos())
            if isinstance(child, QPushButton) or isinstance(child, QLabel):
                return
            self._drag_start = event.globalPos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
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
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
