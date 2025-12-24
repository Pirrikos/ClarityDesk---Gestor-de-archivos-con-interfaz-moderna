"""AppHeader - Header simple y profesional estilo Finder.

Header compacto con navegación, vista, búsqueda y ajustes.
Completamente fijo - no personalizable.
"""

from typing import Optional

from PySide6.QtCore import Qt, QSize, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QMouseEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QLabel, QGraphicsDropShadowEffect, QPushButton, QApplication

from app.core.constants import DEBUG_LAYOUT
from app.services.icon_renderer import render_svg_icon


class ClickableIconLabel(QLabel):
    """Label clickeable para iconos del header."""
    
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Emitir señal cuando se hace clic."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class AppHeader(QWidget):
    """Header simple y profesional con controles esenciales."""

    show_desktop_requested = Signal()  # Emitido cuando se hace clic en el icono de escritorio

    _HEADER_STYLESHEET = """
        QWidget#AppHeader {
            background-color: #1A1D22;
            border-bottom: 1px solid #2A2E36;
        }
        QPushButton#CloseButton {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            color: rgba(255, 255, 255, 0.7);
            padding: 4px 8px;
            font-size: 16px;
            font-weight: 500;
        }
        QPushButton#CloseButton:hover {
            background-color: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.9);
        }
        QPushButton#CloseButton:pressed {
            background-color: rgba(255, 255, 255, 0.15);
        }
    """


    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("AppHeader")
        self.setStyleSheet(self._HEADER_STYLESHEET)
        self._desktop_icon_label: Optional[QLabel] = None
        self._settings_icon_label: Optional[QLabel] = None
        self._close_button: Optional[QPushButton] = None
        self._drag_start: Optional[QPoint] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._setup_base_configuration()
        layout = self._create_main_layout()
        self._add_dock_icons(layout)
        layout.addStretch(1)
        self._add_close_button(layout)

    def _setup_base_configuration(self) -> None:
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(False)

    def _create_main_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return layout

    def _add_dock_icons(self, layout: QHBoxLayout) -> None:
        """Agregar iconos del dock (escritorio y ajustes) a la izquierda del header."""
        icon_size = 32  # Tamaño ajustado al header de 48px
        
        # Icono de escritorio
        desktop_pixmap = render_svg_icon("escritorio.svg", QSize(icon_size, icon_size))
        if desktop_pixmap.isNull():
            desktop_pixmap = render_svg_icon("generic.svg", QSize(icon_size, icon_size))
        
        self._desktop_icon_label = ClickableIconLabel(self)
        self._desktop_icon_label.setFixedSize(icon_size, icon_size)
        self._desktop_icon_label.setPixmap(desktop_pixmap)
        self._desktop_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._desktop_icon_label.clicked.connect(self.show_desktop_requested.emit)
        
        # Sombra similar al dock
        desktop_shadow = QGraphicsDropShadowEffect(self._desktop_icon_label)
        desktop_shadow.setBlurRadius(4)
        desktop_shadow.setColor(QColor(0, 0, 0, 30))
        desktop_shadow.setOffset(0, 1)
        self._desktop_icon_label.setGraphicsEffect(desktop_shadow)
        
        layout.addWidget(self._desktop_icon_label, 0)
        
        # Icono de ajustes
        settings_pixmap = render_svg_icon("ajustes.svg", QSize(icon_size, icon_size))
        if settings_pixmap.isNull():
            settings_pixmap = render_svg_icon("generic.svg", QSize(icon_size, icon_size))
        
        self._settings_icon_label = QLabel(self)
        self._settings_icon_label.setFixedSize(icon_size, icon_size)
        self._settings_icon_label.setPixmap(settings_pixmap)
        self._settings_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._settings_icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Sombra similar al dock
        settings_shadow = QGraphicsDropShadowEffect(self._settings_icon_label)
        settings_shadow.setBlurRadius(4)
        settings_shadow.setColor(QColor(0, 0, 0, 30))
        settings_shadow.setOffset(0, 1)
        self._settings_icon_label.setGraphicsEffect(settings_shadow)
        
        layout.addWidget(self._settings_icon_label, 0)

    def _add_close_button(self, layout: QHBoxLayout) -> None:
        """Agregar botón de cerrar aplicación a la derecha del header."""
        self._close_button = QPushButton("✕", self)
        self._close_button.setObjectName("CloseButton")
        self._close_button.setFixedSize(32, 32)
        self._close_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_button.clicked.connect(self._on_close_clicked)
        layout.addWidget(self._close_button, 0)

    def _on_close_clicked(self) -> None:
        """Cerrar la aplicación cuando se hace clic en el botón de cerrar."""
        app = QApplication.instance()
        if app:
            app.quit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Iniciar arrastre de ventana si el clic no es en un widget hijo."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Verificar si el clic fue en un widget hijo (iconos clickeables)
            child = self.childAt(event.pos())
            
            # Verificar si el clic es en uno de los widgets interactivos (iconos o botón cerrar)
            is_on_interactive_widget = False
            if child:
                # Verificar si es el icono de escritorio o ajustes
                if child == self._desktop_icon_label or child == self._settings_icon_label:
                    is_on_interactive_widget = True
                # Verificar si es el botón de cerrar
                elif child == self._close_button or isinstance(child, QPushButton):
                    is_on_interactive_widget = True
                # Verificar si es un ClickableIconLabel (tipo del icono de escritorio)
                elif isinstance(child, ClickableIconLabel):
                    is_on_interactive_widget = True
                # Verificar si el widget hijo tiene WA_TransparentForMouseEvents pero está sobre un icono
                elif isinstance(child, QLabel):
                    # Verificar si está dentro del área de los iconos
                    icon_pos = event.pos()
                    if self._desktop_icon_label and self._desktop_icon_label.geometry().contains(icon_pos):
                        is_on_interactive_widget = True
                    elif self._settings_icon_label and self._settings_icon_label.geometry().contains(icon_pos):
                        is_on_interactive_widget = True
                # Verificar si está sobre el botón de cerrar
                elif self._close_button and self._close_button.geometry().contains(event.pos()):
                    is_on_interactive_widget = True
            
            if is_on_interactive_widget:
                # Si es un widget interactivo, dejar que maneje el evento
                super().mousePressEvent(event)
                return
            
            # Iniciar arrastre
            self._drag_start = event.globalPos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Mover la ventana mientras se arrastra."""
        if self._drag_start is not None:
            delta = event.globalPos() - self._drag_start
            win = self.window()
            if win:
                win.move(win.pos() + delta)
                self._drag_start = event.globalPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finalizar arrastre de ventana."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
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

