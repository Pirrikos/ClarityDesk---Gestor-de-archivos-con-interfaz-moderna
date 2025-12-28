"""
DockBackgroundWidget - Widget with Apple Dock-style semi-transparent background.
"""

from typing import Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QWidget


class DockBackgroundWidget(QWidget):
    """Widget with Apple Dock-style semi-transparent background."""
    
    # Background styling constants
    BG_COLOR_R = 20
    BG_COLOR_G = 20
    BG_COLOR_B = 20
    BG_COLOR_ALPHA = 100  # rgba(20, 20, 20, ~0.39) - baja opacidad
    BORDER_COLOR_R = 255
    BORDER_COLOR_G = 255
    BORDER_COLOR_B = 255
    BORDER_COLOR_ALPHA = 15  # Borde casi imperceptible
    SHADOW_MARGIN = 8  # Margin for shadow effect
    CORNER_RADIUS = 18  # Apple uses ~16-20px radius
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._drag_start_position: Optional[QPoint] = None
        # Habilitar drops para que pasen a los widgets hijos
        self.setAcceptDrops(True)
        # Habilitar mouse tracking para recibir eventos de movimiento
        self.setMouseTracking(True)
        
        # Subscribe to AppSettings opacity changes
        self._background_opacity: float = 1.0
        # Import module to get updated reference
        from app.managers import app_settings as app_settings_module
        if app_settings_module.app_settings is not None:
            self._background_opacity = app_settings_module.app_settings.dock_background_opacity
            app_settings_module.app_settings.dock_background_opacity_changed.connect(self._on_opacity_changed)
    
    def _on_opacity_changed(self, opacity: float) -> None:
        """Handle opacity change from AppSettings."""
        self._background_opacity = opacity
        self.update()
    
    def paintEvent(self, event) -> None:
        """Paint Raycast-style background with rounded corners - gris muy oscuro translúcido."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calcular alpha dinámico basado en opacidad de AppSettings
        alpha = int(self.BG_COLOR_ALPHA * self._background_opacity)
        bg_color = QColor(self.BG_COLOR_R, self.BG_COLOR_G, self.BG_COLOR_B, alpha)
        
        # Borde muy sutil con opacidad dinámica
        border_alpha = int(self.BORDER_COLOR_ALPHA * self._background_opacity)
        border_color = QColor(self.BORDER_COLOR_R, self.BORDER_COLOR_G, self.BORDER_COLOR_B, border_alpha)
        
        # Draw rounded rectangle
        rect = self.rect().adjusted(self.SHADOW_MARGIN, self.SHADOW_MARGIN, -self.SHADOW_MARGIN, -self.SHADOW_MARGIN)
        
        # Draw background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        
        painter.end()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - start window dragging if clicking on background."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on a child widget (icon/tile)
            child_widget = self.childAt(event.pos())
            
            # Check if the widget or any of its parents is a tile
            is_tile = False
            widget = child_widget
            while widget is not None and widget != self:
                widget_type = type(widget).__name__
                # Check if it's a tile widget (FileStackTile, DesktopStackTile, FileTile, etc.)
                if 'Tile' in widget_type or 'StackTile' in widget_type:
                    is_tile = True
                    break
                widget = widget.parent()
            
            if not is_tile:
                # Click is on background (not on a tile), start dragging
                self._drag_start_position = event.globalPos()
                event.accept()
            else:
                # Click is on a tile, let it handle the event
                event.ignore()
        else:
            event.ignore()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move - drag window if dragging started."""
        if self._drag_start_position is not None:
            # Calculate movement delta
            delta = event.globalPos() - self._drag_start_position
            # Move the window
            main_window = self.window()
            if main_window:
                new_pos = main_window.pos() + delta
                main_window.move(new_pos)
                self._drag_start_position = event.globalPos()
            event.accept()
        else:
            event.ignore()
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release - stop dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = None
            event.accept()
        else:
            event.ignore()
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Propagate drag enter to child widgets (FileViewContainer)."""
        # Buscar el FileViewContainer hijo y propagar el evento
        for child in self.findChildren(QWidget):
            if hasattr(child, 'dragEnterEvent') and hasattr(child, '_is_desktop'):
                if getattr(child, '_is_desktop', False):
                    child.dragEnterEvent(event)
                    return
        event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Propagate drag move to child widgets (FileViewContainer)."""
        # Buscar el FileViewContainer hijo y propagar el evento
        for child in self.findChildren(QWidget):
            if hasattr(child, 'dragMoveEvent') and hasattr(child, '_is_desktop'):
                if getattr(child, '_is_desktop', False):
                    child.dragMoveEvent(event)
                    return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Propagate drop to child widgets (FileViewContainer)."""
        # Buscar el FileViewContainer hijo y propagar el evento
        for child in self.findChildren(QWidget):
            if hasattr(child, 'dropEvent') and hasattr(child, '_is_desktop'):
                if getattr(child, '_is_desktop', False):
                    child.dropEvent(event)
                    return
        event.ignore()

