"""AppHeader - Header simple y profesional estilo Finder.

Header compacto con navegación, vista, búsqueda y ajustes.
Completamente fijo - no personalizable.
"""

from typing import Optional

from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer, QEvent, QRect
from PySide6.QtGui import QPainter, QColor, QMouseEvent, QIcon, QPixmap, QScreen, QPainterPath
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QLabel, QGraphicsDropShadowEffect, QPushButton, QApplication, QFrame

from app.core.constants import DEBUG_LAYOUT, ROUNDED_BG_RADIUS, SEPARATOR_LINE_COLOR
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
    show_settings_requested = Signal()  # Emitido cuando se hace clic en el icono de ajustes

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
        self._maximize_button: Optional[QPushButton] = None
        self._three_quarter_button: Optional[QPushButton] = None
        self._original_size_button: Optional[QPushButton] = None
        self._original_geometry: Optional[QRect] = None
        self._setup_window_size_buttons()  # Crear botones antes de agregarlos al layout
        self._setup_ui()
        self._setup_window_state_listener()

    def _setup_ui(self) -> None:
        self._setup_base_configuration()
        layout = self._create_main_layout()
        self._add_dock_icons(layout)
        self._add_window_size_buttons(layout)
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
        
        # Icono de ajustes (clickeable)
        settings_pixmap = render_svg_icon("ajustes.svg", QSize(icon_size, icon_size))
        if settings_pixmap.isNull():
            settings_pixmap = render_svg_icon("generic.svg", QSize(icon_size, icon_size))
        
        self._settings_icon_label = ClickableIconLabel(self)
        self._settings_icon_label.setFixedSize(icon_size, icon_size)
        self._settings_icon_label.setPixmap(settings_pixmap)
        self._settings_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._settings_icon_label.clicked.connect(self.show_settings_requested.emit)
        
        # Sombra similar al dock
        settings_shadow = QGraphicsDropShadowEffect(self._settings_icon_label)
        settings_shadow.setBlurRadius(4)
        settings_shadow.setColor(QColor(0, 0, 0, 30))
        settings_shadow.setOffset(0, 1)
        self._settings_icon_label.setGraphicsEffect(settings_shadow)
        
        layout.addWidget(self._settings_icon_label, 0)
    
    def _add_window_size_buttons(self, layout: QHBoxLayout) -> None:
        """Agregar separador y botones de tamaño de ventana después de los iconos."""
        # Separador
        separator = self._create_separator()
        layout.addWidget(separator, 0)
        
        # Botones de tamaño de ventana
        if self._maximize_button:
            layout.addWidget(self._maximize_button, 0)
        if self._three_quarter_button:
            layout.addWidget(self._three_quarter_button, 0)
        if self._original_size_button:
            layout.addWidget(self._original_size_button, 0)
        
        # Espacio después de los botones
        if self._maximize_button or self._three_quarter_button or self._original_size_button:
            layout.addSpacing(8)

    def _create_separator(self) -> QFrame:
        """Create a vertical separator line."""
        separator = QFrame(self)
        separator.setObjectName("AppHeaderSeparator")
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedWidth(1)
        separator.setFixedHeight(24)
        separator.setStyleSheet(f"""
            QFrame#AppHeaderSeparator {{
                background-color: {SEPARATOR_LINE_COLOR};
                border: none;
            }}
        """)
        return separator

    def _setup_window_size_buttons(self) -> None:
        """Create and configure window size buttons."""
        self._setup_maximize_button()
        self._setup_three_quarter_button()
        self._setup_original_size_button()
    
    def _create_dots_icon(self, dot_count: int) -> QIcon:
        """Crear icono minimalista con puntos blancos."""
        size = QSize(16, 16)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        
        center_y = size.height() // 2
        
        if dot_count == 1:
            painter.drawEllipse(6, center_y - 2, 4, 4)
        elif dot_count == 2:
            painter.drawEllipse(4, center_y - 2, 4, 4)
            painter.drawEllipse(8, center_y - 2, 4, 4)
        elif dot_count == 3:
            painter.drawEllipse(2, center_y - 2, 4, 4)
            painter.drawEllipse(6, center_y - 2, 4, 4)
            painter.drawEllipse(10, center_y - 2, 4, 4)
        
        painter.end()
        return QIcon(pixmap)
    
    def _setup_maximize_button(self) -> None:
        """Create and configure maximize button."""
        self._maximize_button = QPushButton(self)
        self._maximize_button.setObjectName("MaximizeButton")
        self._maximize_button.setFixedSize(32, 32)
        self._maximize_button.setToolTip("Maximizar ventana")
        self._maximize_button.setIcon(self._create_dots_icon(3))
        self._maximize_button.setIconSize(QSize(16, 16))
        self._maximize_button.setStyleSheet("""
            QPushButton#MaximizeButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }
            QPushButton#MaximizeButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#MaximizeButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self._maximize_button.clicked.connect(self._on_maximize_clicked)
        self._update_maximize_button_state()
    
    def _setup_three_quarter_button(self) -> None:
        """Create and configure 3/4 screen size button."""
        self._three_quarter_button = QPushButton(self)
        self._three_quarter_button.setObjectName("ThreeQuarterButton")
        self._three_quarter_button.setFixedSize(32, 32)
        self._three_quarter_button.setToolTip("Ventana a 3/4 del escritorio")
        self._three_quarter_button.setIcon(self._create_dots_icon(2))
        self._three_quarter_button.setIconSize(QSize(16, 16))
        self._three_quarter_button.setStyleSheet("""
            QPushButton#ThreeQuarterButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }
            QPushButton#ThreeQuarterButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#ThreeQuarterButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self._three_quarter_button.clicked.connect(self._on_three_quarter_clicked)
    
    def _setup_original_size_button(self) -> None:
        """Create and configure original size button."""
        self._original_size_button = QPushButton(self)
        self._original_size_button.setObjectName("OriginalSizeButton")
        self._original_size_button.setFixedSize(32, 32)
        self._original_size_button.setToolTip("Tamaño original")
        self._original_size_button.setIcon(self._create_dots_icon(1))
        self._original_size_button.setIconSize(QSize(16, 16))
        self._original_size_button.setStyleSheet("""
            QPushButton#OriginalSizeButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }
            QPushButton#OriginalSizeButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#OriginalSizeButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self._original_size_button.clicked.connect(self._on_original_size_clicked)
    
    def _setup_window_state_listener(self) -> None:
        """Setup listener for window state changes to update maximize button."""
        window = self.window()
        if window:
            window.installEventFilter(self)
    
    def eventFilter(self, obj, event) -> bool:
        """Filter window events to detect state changes and capture initial size."""
        window = self.window()
        if obj == window:
            if event.type() == QEvent.Type.WindowStateChange:
                QTimer.singleShot(50, self._update_maximize_button_state)
            elif event.type() == QEvent.Type.Show and not self._original_geometry:
                QTimer.singleShot(100, self._capture_initial_size)
        return super().eventFilter(obj, event)
    
    def _on_maximize_clicked(self) -> None:
        """Handle maximize button click - maximize or restore window."""
        window = self.window()
        if window:
            if window.isMaximized():
                window.showNormal()
            else:
                window.showMaximized()
            QTimer.singleShot(100, self._update_maximize_button_state)
    
    def _update_maximize_button_state(self) -> None:
        """Update maximize button icon and tooltip based on window state."""
        if not self._maximize_button:
            return
        window = self.window()
        if window and window.isMaximized():
            self._maximize_button.setToolTip("Restaurar ventana")
            self._maximize_button.setIcon(self._create_dots_icon(2))
        else:
            self._maximize_button.setToolTip("Maximizar ventana")
            self._maximize_button.setIcon(self._create_dots_icon(3))
    
    def _on_three_quarter_clicked(self) -> None:
        """Handle 3/4 screen size button click - resize window to 3/4 of desktop."""
        window = self.window()
        if not window:
            return
        
        screen = QApplication.primaryScreen()
        if not screen:
            return
        
        screen_geometry = screen.availableGeometry()
        
        width = int(screen_geometry.width() * 0.75)
        height = int(screen_geometry.height() * 0.75)
        
        x = screen_geometry.x() + (screen_geometry.width() - width) // 2
        y = screen_geometry.y() + (screen_geometry.height() - height) // 2
        
        if window.isMaximized():
            window.showNormal()
            QTimer.singleShot(50, lambda: window.setGeometry(QRect(x, y, width, height)))
        else:
            window.setGeometry(QRect(x, y, width, height))
    
    def _capture_initial_size(self) -> None:
        """Capture initial window size when first shown."""
        if self._original_geometry:
            return
        
        window = self.window()
        if not window or not window.isVisible():
            return
        
        self._original_geometry = window.geometry()
    
    def _on_original_size_clicked(self) -> None:
        """Handle original size button click - restore window to initial size."""
        window = self.window()
        if not window:
            return
        
        if not self._original_geometry:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                default_width = min(1200, int(screen_geometry.width() * 0.7))
                default_height = min(800, int(screen_geometry.height() * 0.7))
                x = screen_geometry.x() + (screen_geometry.width() - default_width) // 2
                y = screen_geometry.y() + (screen_geometry.height() - default_height) // 2
                self._original_geometry = QRect(x, y, default_width, default_height)
            else:
                self._original_geometry = QRect(100, 100, 1200, 800)
        
        if window.isMaximized():
            window.showNormal()
            QTimer.singleShot(50, lambda: window.setGeometry(self._original_geometry))
        else:
            window.setGeometry(self._original_geometry)

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
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        radius = ROUNDED_BG_RADIUS
        
        # Crear path con esquinas redondeadas solo superiores (sin redondeo inferior para juntar con SecondaryHeader)
        path = QPainterPath()
        path.moveTo(rect.left() + radius, rect.top())
        path.lineTo(rect.right() - radius, rect.top())
        path.arcTo(rect.right() - 2 * radius, rect.top(), 2 * radius, 2 * radius, 90, -90)
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + radius)
        path.arcTo(rect.left(), rect.top(), 2 * radius, 2 * radius, 180, -90)
        path.closeSubpath()
        
        p.fillPath(path, QColor("#1A1D22"))
        
        p.end()
        super().paintEvent(event)

