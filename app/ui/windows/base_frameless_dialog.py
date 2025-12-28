"""
BaseFramelessDialog - Base class for frameless dialogs following visual contract.

Provides common functionality for frameless dialogs with:
- Transparent window with rounded container
- Draggable header with close button
- Auto-centering on screen
- Consistent visual styling
"""

from typing import Optional

from PySide6.QtCore import Qt, QPoint, QEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import (
    APP_HEADER_BG,
    APP_HEADER_BORDER,
    CENTRAL_AREA_BG,
    FILE_BOX_TEXT,
)


class BaseFramelessDialog(QDialog):
    """Base class for frameless dialogs following official visual contract."""
    
    def __init__(self, title: str, parent=None, modal: bool = True):
        """
        Initialize base frameless dialog.
        
        Args:
            title: Dialog title.
            parent: Parent widget.
            modal: Whether dialog should be modal (default: True).
        """
        super().__init__(parent)
        
        self._title = title
        self._drag_start: Optional[QPoint] = None
        self._header_widget: Optional[QWidget] = None
        self._main_container: Optional[QWidget] = None
        self._content_panel: Optional[QWidget] = None
        
        self._setup_frameless_window(modal)
    
    def _setup_frameless_window(self, modal: bool = True) -> None:
        """
        Setup frameless window attributes and base structure.
        
        Args:
            modal: Whether dialog should be modal.
        """
        # Configurar ventana frameless con fondo transparente
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        self.setWindowTitle(self._title)
        self.setModal(modal)
        
        # QDialog completamente transparente
        self.setStyleSheet("""
            QDialog {
                background-color: transparent;
            }
        """)
        
        # Layout principal completamente transparente
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Contenedor único con fondo y bordes redondeados
        self._main_container = QWidget()
        self._main_container.setStyleSheet(f"""
            QWidget {{
                background-color: {APP_HEADER_BG};
                border: 1px solid {APP_HEADER_BORDER};
                border-radius: 12px;
            }}
        """)
        container_layout = QVBoxLayout(self._main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Crear header
        self._header_widget = self._create_header(container_layout)
        
        # Crear panel de contenido
        self._content_panel = self._create_content_panel(container_layout)
        
        # Añadir el contenedor principal al layout del diálogo
        main_layout.addWidget(self._main_container)
    
    def _create_header(self, container_layout: QVBoxLayout) -> QWidget:
        """
        Create header with title and close button.
        
        Args:
            container_layout: Layout to add header to.
            
        Returns:
            Header widget.
        """
        header_widget = QWidget()
        header_widget.setFixedHeight(48)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border-bottom: 1px solid {APP_HEADER_BORDER};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(0)
        
        header_title_label = QLabel(self._title)
        header_title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)
        header_layout.addWidget(header_title_label)
        header_layout.addStretch()
        
        # Botón cerrar
        close_button = QPushButton("✕")
        close_button.setFixedSize(32, 28)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: {FILE_BOX_TEXT};
                font-size: 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
        close_button.clicked.connect(self.reject)
        header_layout.addWidget(close_button)
        
        container_layout.addWidget(header_widget)
        return header_widget
    
    def _create_content_panel(self, container_layout: QVBoxLayout) -> QWidget:
        """
        Create content panel with rounded bottom corners.
        
        Args:
            container_layout: Layout to add content panel to.
            
        Returns:
            Content panel widget.
        """
        content_panel = QWidget()
        content_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {CENTRAL_AREA_BG};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)
        
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        container_layout.addWidget(content_panel)
        return content_panel
    
    def get_content_layout(self) -> QVBoxLayout:
        """
        Get content layout for adding custom content.
        
        Returns:
            Content panel's layout.
        """
        return self._content_panel.layout()
    
    def showEvent(self, event: QEvent) -> None:
        """Position dialog centered on screen when shown."""
        super().showEvent(event)
        screen = self.screen()
        if not screen:
            screen = QApplication.primaryScreen()
        
        if screen:
            screen_geometry = screen.availableGeometry()
            dialog_geometry = self.frameGeometry()
            # Centrar completamente en la pantalla (horizontal y vertical)
            x = screen_geometry.left() + (screen_geometry.width() - dialog_geometry.width()) // 2
            y = screen_geometry.top() + (screen_geometry.height() - dialog_geometry.height()) // 2
            self.move(x, y)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._header_widget:
                header_pos = self._header_widget.mapFromGlobal(event.globalPos())
                if self._header_widget.rect().contains(header_pos):
                    child = self._header_widget.childAt(header_pos)
                    # No arrastrar si se hace clic en un botón
                    if isinstance(child, QPushButton):
                        super().mousePressEvent(event)
                        return
                    self._drag_start = event.globalPos()
                    event.accept()
                    return
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for window dragging."""
        if self._drag_start is not None:
            delta = event.globalPos() - self._drag_start
            self.move(self.pos() + delta)
            self._drag_start = event.globalPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

