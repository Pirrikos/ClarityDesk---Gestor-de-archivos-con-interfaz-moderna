"""
ResizeEdgeOverlay - Área invisible para captura de eventos de redimensionamiento.

Widget transparente que se superpone a los bordes de la ventana para capturar
eventos de mouse y delegarlos a MainWindow para redimensionamiento, sin interferir
con la funcionalidad de otros widgets.
"""

from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QRegion

from app.core.constants import RESIZE_EDGE_DETECTION_MARGIN, DEBUG_LAYOUT
from app.core.logger import get_logger

logger = get_logger(__name__)


class ResizeEdgeOverlay(QWidget):
    """
    Widget transparente que captura eventos de mouse en los bordes de la ventana.

    Este widget se superpone a toda la ventana pero solo captura eventos en las
    áreas de borde definidas por RESIZE_EDGE_DETECTION_MARGIN. El resto del área
    es transparente para eventos, permitiendo que los widgets subyacentes funcionen
    normalmente.
    """

    def __init__(self, parent=None):
        """
        Initialize ResizeEdgeOverlay.

        Args:
            parent: Parent widget (MainWindow).
        """
        super().__init__(parent)

        # Configurar como overlay transparente
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        # Hacer que el widget se superponga a todos los demás (Z-order superior)
        self.raise_()

        # Habilitar mouse tracking para cambiar cursor
        self.setMouseTracking(True)

    def resizeEvent(self, event):
        """
        Actualizar la máscara cuando el widget cambia de tamaño.

        La máscara define las áreas "clickeables" del widget, limitándolas
        solo a los bordes. El resto del widget es transparente para eventos.
        """
        if DEBUG_LAYOUT:
            try:
                logger.debug("🧩 ResizeEdgeOverlay.resizeEvent")
            except Exception:
                pass
        super().resizeEvent(event)
        self._update_mask()

    def _update_mask(self):
        """
        Crear una máscara que define solo las áreas de borde como clickeables.

        La máscara es una región que incluye solo los bordes de la ventana
        (superior, inferior, izquierdo, derecho) con un grosor de
        RESIZE_EDGE_DETECTION_MARGIN píxeles.
        """
        margin = RESIZE_EDGE_DETECTION_MARGIN
        rect = self.rect()

        # Crear regiones para cada borde
        top_region = QRegion(QRect(0, 0, rect.width(), margin))
        bottom_region = QRegion(QRect(0, rect.height() - margin, rect.width(), margin))
        left_region = QRegion(QRect(0, 0, margin, rect.height()))
        right_region = QRegion(QRect(rect.width() - margin, 0, margin, rect.height()))

        # Combinar todas las regiones
        edge_region = top_region.united(bottom_region).united(left_region).united(right_region)

        # Aplicar la máscara
        self.setMask(edge_region)
        if DEBUG_LAYOUT:
            try:
                logger.debug("🧩 ResizeEdgeOverlay.mask updated")
            except Exception:
                pass

    def mousePressEvent(self, event):
        """
        Capturar eventos de mouse en los bordes y delegar a MainWindow.

        Este método solo se ejecuta cuando el mouse hace click en las áreas
        definidas por la máscara (bordes). Los clicks en otras áreas pasan
        directamente a los widgets subyacentes.
        """
        # Obtener MainWindow
        main_window = self.window()
        if not main_window or not hasattr(main_window, '_detect_resize_edges'):
            super().mousePressEvent(event)
            return

        # Solo manejar botón izquierdo
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPos()

            # Detectar bordes usando el método de MainWindow
            edges = main_window._detect_resize_edges(global_pos)

            if edges and main_window.windowHandle():
                # Iniciar resize
                main_window._is_resizing = True
                main_window.windowHandle().startSystemResize(edges)
                event.accept()
                return

        # Si no se manejó el evento, ignorarlo para que pase a través
        event.ignore()

    def paintEvent(self, event):
        """
        No pintar nada - el widget es completamente transparente.

        Solo existe para capturar eventos de mouse en los bordes.
        """
        # No pintar nada - completamente transparente
        pass
