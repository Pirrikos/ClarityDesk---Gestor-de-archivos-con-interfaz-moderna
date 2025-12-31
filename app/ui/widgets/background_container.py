"""
BackgroundContainer - Widget contenedor para la pintura de fondo.

Maneja la pintura del fondo con esquinas redondeadas de forma optimizada,
evitando repintar toda la ventana raíz durante el redimensionado.
"""

from PySide6.QtCore import Qt, QTimer, QElapsedTimer
from PySide6.QtGui import QPainter, QColor, QPainterPath
from PySide6.QtWidgets import QWidget

from app.core.constants import DEBUG_LAYOUT, SIDEBAR_BG
from app.core.logger import get_logger

logger = get_logger(__name__)


class BackgroundContainer(QWidget):
    """Widget contenedor que maneja la pintura del fondo con esquinas redondeadas."""

    def __init__(self, parent=None):
        """
        Initialize BackgroundContainer.

        Args:
            parent: Parent widget (MainWindow).
        """
        super().__init__(parent)

        # Configuración para optimizar el rendimiento y ELIMINAR PARPADEO
        # WA_OpaquePaintEvent=True activa doble buffer automático en Qt
        # Esto evita el parpadeo durante el redimensionamiento
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)

        # NO usar WA_TransparentForMouseEvents porque rompería la interacción con widgets hijos
        self.setMouseTracking(False)

        # Color de fondo (sidebar color por defecto)
        self._bg_color = SIDEBAR_BG
        self._corner_radius = 12

    def set_background_color(self, color: str) -> None:
        """
        Set background color and trigger repaint.

        Args:
            color: Hex color string (e.g., "#1A1D22").
        """
        if self._bg_color != color:
            self._bg_color = color
            self.update()

    def set_corner_radius(self, radius: int) -> None:
        """
        Set corner radius and trigger repaint.

        Args:
            radius: Corner radius in pixels.
        """
        if self._corner_radius != radius:
            self._corner_radius = radius
            self.update()

    def paintEvent(self, event):
        """
        Pintar el fondo con esquinas redondeadas de forma optimizada.
        """
        if DEBUG_LAYOUT:
            super().paintEvent(event)
            return

        if not hasattr(self, '_paint_count_debug'): self._paint_count_debug = 0
        self._paint_count_debug += 1
        t = QElapsedTimer()
        t.start()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        rect = self.rect()
        bg_color = QColor(self._bg_color)

        # REFUERZO: Pintar fondo sólido base antes del redondeado
        painter.fillRect(rect, bg_color)

        # Usar QPainterPath para el redondeado - esta es la forma canónica
        path = QPainterPath()
        path.addRoundedRect(rect, self._corner_radius, self._corner_radius)
        painter.fillPath(path, bg_color)

        painter.end()

        elapsed = t.nsecsElapsed() / 1000000.0
        if DEBUG_LAYOUT:
            logger.info(f"🎨 [Background] Paint #{self._paint_count_debug} | dur={elapsed:.2f}ms")

    def resizeEvent(self, event):
        """Manejar redimensionado."""
        super().resizeEvent(event)
        # update() es asíncrono y eficiente
        self.update()
