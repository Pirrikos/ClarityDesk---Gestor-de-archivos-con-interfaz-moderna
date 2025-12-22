from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QRadialGradient
from PySide6.QtWidgets import QWidget, QSizePolicy

from app.core.constants import DEBUG_LAYOUT

# Padding para cubrir el margen fantasma que Windows introduce en ventanas frameless
WINDOW_EDGE_PADDING = 8  # Píxeles - funciona bien en Windows 10/11 con DPI estándar y alto

class RaycastPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CentralWidget")
        self._radius = 12
        # Asegurar expansión completa en ambas direcciones
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Asegurar que el widget ocupe todo el espacio disponible sin márgenes
        self.setContentsMargins(0, 0, 0, 0)
        # Desactivar auto-fill background para control total del pintado
        self.setAutoFillBackground(False)

    def paintEvent(self, event):
        """
        RaycastPanel ya no pinta el fondo - MainWindow lo hace.
        
        Solución profesional: El fondo se pinta en la ventana raíz (MainWindow)
        para asegurar que cubra toda el área incluyendo el margen fantasma de Windows.
        RaycastPanel es transparente y solo contiene widgets hijos.
        """
        # En modo depuración, no pintar nada para que se vean los bordes
        if DEBUG_LAYOUT:
            return
        
        # RaycastPanel es transparente - el fondo se pinta en MainWindow
        # No pintar nada aquí para evitar duplicación
        pass
