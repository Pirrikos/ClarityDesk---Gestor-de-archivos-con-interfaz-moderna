"""
DesktopStackTile - Tile widget for the desktop icon.

Displays escritorio.svg icon as a stack tile, always positioned at the leftmost position.
"""

from typing import Optional

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap
)
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.services.icon_renderer import render_svg_icon
from app.ui.widgets.text_elision import elide_middle_manual


class DesktopStackTile(QWidget):
    """Tile widget for the desktop icon."""
    
    clicked = Signal()  # Emitted when tile is clicked

    def __init__(
        self,
        parent_view,
    ):
        """Initialize desktop stack tile."""
        super().__init__(parent_view)
        self._parent_view = parent_view
        self._icon_pixmap: Optional[QPixmap] = None
        self._is_hovered: bool = False
        self._icon_label: Optional[QLabel] = None
        self._icon_shadow: Optional[QGraphicsDropShadowEffect] = None
        self._drag_start_position: Optional[QPoint] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build tile UI."""
        # Tamaño: contenedor 70x70 + texto debajo (igual que FileStackTile)
        self.setFixedSize(70, 85)
        self.setAutoFillBackground(False)
        self._setup_layout()
        self.setMouseTracking(True)

    def _setup_layout(self) -> None:
        """Setup layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Container widget for icon (70x70)
        container_widget = QWidget()
        container_widget.setFixedSize(70, 70)
        container_widget.setAutoFillBackground(False)
        container_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(7, 7, 7, 7)
        container_layout.setSpacing(0)
        self._container_widget = container_widget
        self._add_icon_zone(container_layout)
        layout.addWidget(container_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # Text label below container
        self._add_text_band(layout)
    
    def paintEvent(self, event) -> None:
        """Paint the dock app container background with rounded corners - Apple white style."""
        if not hasattr(self, '_container_widget'):
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get container widget rect (only draw on container area, not text area)
        container_rect = self._container_widget.geometry()
        rect = container_rect.adjusted(2, 2, -2, -2)
        
        # Fondo blanco translúcido sutil - estilo Raycast
        bg_color = QColor(255, 255, 255, 15)  # rgba(255, 255, 255, 0.06)
        border_color = QColor(255, 255, 255, 20)  # rgba(255, 255, 255, 0.08)
        
        # Draw rounded rectangle background only on container area
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, 14, 14)
        
        painter.end()
    
    def _add_icon_zone(self, layout: QVBoxLayout) -> None:
        """Add icon zone with shadow."""
        icon_width = 48
        icon_height = 48
        
        # Cargar el SVG escritorio.svg
        pixmap = render_svg_icon("escritorio.svg", QSize(icon_width, icon_height))
        
        # Si falla, usar un icono genérico
        if pixmap.isNull():
            pixmap = render_svg_icon("generic.svg", QSize(icon_width, icon_height))
        
        self._icon_pixmap = pixmap
        
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(icon_width, icon_height)
        self._icon_label.setPixmap(pixmap)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Lighter shadow for icon inside dock container
        self._icon_shadow = QGraphicsDropShadowEffect(self._icon_label)
        self._icon_shadow.setBlurRadius(6)
        self._icon_shadow.setColor(QColor(0, 0, 0, 25))
        self._icon_shadow.setOffset(0, 2)
        self._icon_label.setGraphicsEffect(self._icon_shadow)
        
        layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignHCenter)

    def _add_text_band(self, layout: QVBoxLayout) -> None:
        """Add text label below icon."""
        name_label = QLabel()
        name_label.setWordWrap(False)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFixedWidth(70)
        name_label.setMinimumWidth(70)
        name_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 10px;
            font-weight: 600;
            color: #ffffff;
            background-color: transparent;
            padding: 0px;
        """)
        name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Add text shadow for better visibility
        text_shadow = QGraphicsDropShadowEffect(name_label)
        text_shadow.setBlurRadius(3)
        text_shadow.setXOffset(0)
        text_shadow.setYOffset(1)
        text_shadow.setColor(QColor(0, 0, 0, 180))
        name_label.setGraphicsEffect(text_shadow)
        
        display_name = "Escritorio"
        metrics = name_label.fontMetrics()
        max_width = 68
        elided_text = elide_middle_manual(display_name, metrics, max_width)
        name_label.setText(elided_text)
        
        layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignHCenter)

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter - enhance dock app container on hover."""
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave - restore dock app container style."""
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release - emit clicked signal if it was a click (not drag)."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_start_position:
                distance = (event.pos() - self._drag_start_position).manhattanLength()
                if distance < 5:  # Click threshold (not a drag)
                    self.clicked.emit()
            self._drag_start_position = None
        super().mouseReleaseEvent(event)

