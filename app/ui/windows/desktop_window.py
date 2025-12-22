"""
DesktopWindow - Desktop Focus window with vertical layout.

Auto-start window showing Desktop Focus (top) and Trash Focus (bottom).
Opens automatically on app startup.
"""

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QUrl, QTimer, QPoint
from PySide6.QtGui import QDesktopServices, QPainter, QColor, QBrush, QPen, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from app.managers.tab_manager import TabManager
from app.services.desktop_path_helper import get_desktop_path
from app.services.icon_service import IconService
from app.services.trash_storage import TRASH_FOCUS_PATH
from app.ui.widgets.file_view_container import FileViewContainer


class DockBackgroundWidget(QWidget):
    """Widget with Apple Dock-style semi-transparent background."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._drag_start_position: Optional[QPoint] = None
        # Habilitar drops para que pasen a los widgets hijos
        self.setAcceptDrops(True)
    
    def paintEvent(self, event) -> None:
        """Paint Raycast-style background with rounded corners - gris muy oscuro translúcido."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Estilo Raycast: gris muy oscuro con baja opacidad para reducir ruido visual
        bg_color = QColor(20, 20, 20, 100)  # rgba(20, 20, 20, ~0.39) - baja opacidad
        
        # Borde muy sutil
        border_color = QColor(255, 255, 255, 15)  # Borde casi imperceptible
        
        # Draw rounded rectangle
        rect = self.rect().adjusted(8, 8, -8, -8)  # Margin for shadow effect
        radius = 18  # Apple uses ~16-20px radius
        
        # Draw background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, radius, radius)
        
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


class DesktopWindow(QWidget):
    """Desktop Focus window with vertical Desktop (top) and Trash (bottom) panels."""
    
    open_main_window = Signal()  # Emitted when user clicks to open main window
    
    # Dock layout constants
    STACK_TILE_WIDTH = 70
    DESKTOP_TILE_WIDTH = 70
    SETTINGS_TILE_WIDTH = 70
    SEPARATOR_WIDTH = 1
    STACK_SPACING = 12
    BASE_WINDOW_HEIGHT = 140
    MIN_WINDOW_HEIGHT = 120
    ANIMATION_DURATION_MS = 250
    DEFAULT_WINDOW_WIDTH = 400
    
    # Layout margins
    MAIN_LAYOUT_MARGIN = 16
    CENTRAL_LAYOUT_MARGIN = 16
    GRID_LAYOUT_LEFT_MARGIN = 20
    GRID_LAYOUT_RIGHT_MARGIN = 12  # Simétrico con spacing después del separador
    
    # Screen positioning
    WINDOW_BOTTOM_MARGIN = 10
    WINDOW_MAX_HEIGHT_MARGIN = 20
    INITIAL_WINDOW_WIDTH_RATIO = 0.6
    
    def __init__(self, parent=None):
        """Initialize DesktopWindow with Desktop and Trash Focus."""
        super().__init__(parent)
        
        # Initialize managers and services as None - will be created in initialize_after_show()
        self._desktop_tab_manager: Optional[TabManager] = None
        self._trash_tab_manager: Optional[TabManager] = None
        self._icon_service: Optional[IconService] = None
        self._desktop_container: Optional[FileViewContainer] = None
        
        # Placeholder widget for desktop container (will be replaced after init)
        self._desktop_placeholder: Optional[QWidget] = None
        self._height_animation: Optional[QPropertyAnimation] = None
        self._width_animation: Optional[QPropertyAnimation] = None
        
        # Setup UI structure only (no heavy initialization)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build Dock-style layout - exactly like macOS Dock."""
        self.setWindowTitle("ClarityDesk - Dock")
        
        # Set window flags: frameless, always on top, stay on desktop
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Don't show in taskbar
        )
        # Enable full transparency and prevent border flashing
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_PaintOnScreen, False)  # Prevent flicker
        # Disable window frame painting to prevent border flash
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        # Habilitar drops en la ventana principal
        self.setAcceptDrops(True)
        
        # Position window at BOTTOM of screen, centered horizontally
        screen = self.screen().availableGeometry()
        window_height = self.BASE_WINDOW_HEIGHT
        window_width = int(screen.width() * self.INITIAL_WINDOW_WIDTH_RATIO)
        window_x = (screen.width() - window_width) // 2
        window_y = screen.height() - window_height - self.WINDOW_BOTTOM_MARGIN
        self.setGeometry(window_x, window_y, window_width, window_height)
        # Minimum size will be set dynamically based on stacks count
        # Only set minimum height, width will be adjusted by _adjust_window_width
        self.setMinimumHeight(self.MIN_WINDOW_HEIGHT)
        # No max height limit - window expands as needed
        
        # Create dock background widget with Apple-style transparency
        self._central_widget = DockBackgroundWidget()
        
        # Layout raíz directamente en la ventana
        main_layout = QVBoxLayout(self)
        # Margins match the rounded background (8px outer + some inner padding)
        main_layout.setContentsMargins(self.MAIN_LAYOUT_MARGIN, 14, self.MAIN_LAYOUT_MARGIN, 14)
        main_layout.setSpacing(0)
        
        # Añadir central_widget al layout raíz
        main_layout.addWidget(self._central_widget, 1)
        
        # Layout interno del central_widget (DockBackgroundWidget mantiene su layout interno)
        central_internal_layout = QVBoxLayout(self._central_widget)
        central_internal_layout.setContentsMargins(self.CENTRAL_LAYOUT_MARGIN, 14, self.CENTRAL_LAYOUT_MARGIN, 14)
        central_internal_layout.setSpacing(0)
        
        # Placeholder widget for Desktop Focus panel (will be replaced in initialize_after_show)
        self._desktop_placeholder = QWidget()
        self._desktop_placeholder.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        central_internal_layout.addWidget(self._desktop_placeholder, 1)
        
        # NO footer - pure Dock style
        
        # Fully transparent window
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
    
    def initialize_after_show(self) -> None:
        """
        Initialize heavy components after window is shown.
        
        This method is called via QTimer.singleShot(0, ...) after show()
        to ensure the window appears immediately without blocking.
        """
        # Create TabManager instances for Desktop and Trash using separate storage to avoid collision
        from pathlib import Path as PathLib
        dock_storage = PathLib(__file__).parent.parent.parent / 'storage' / 'dock_tabs.json'
        trash_storage = PathLib(__file__).parent.parent.parent / 'storage' / 'trash_tabs.json'
        self._desktop_tab_manager = TabManager(str(dock_storage))
        self._trash_tab_manager = TabManager(str(trash_storage))
        
        # Set Desktop and Trash as active tabs
        desktop_path = get_desktop_path()
        self._desktop_tab_manager.add_tab(desktop_path)
        self._trash_tab_manager.add_tab(TRASH_FOCUS_PATH)
        
        # Create IconService
        self._icon_service = IconService()
        
        # Get parent widget for FileViewContainer (usar referencia directa)
        central_widget = self._central_widget
        
        # Create Desktop Focus panel
        self._desktop_container = FileViewContainer(
            self._desktop_tab_manager,
            self._icon_service,
            None,
            central_widget,  # Parent widget
            is_desktop=True  # Flag explícito: este es DesktopWindow
        )
        
        # Connect expansion height changes to adjust window size
        self._desktop_container.expansion_height_changed.connect(self._adjust_window_height)
        
        # Connect stacks count changes to adjust window width
        self._desktop_container.stacks_count_changed.connect(self._adjust_window_width)
        
        # Connect open_file signal to open files with default application
        self._desktop_container.open_file.connect(self._open_file)
        
        # Get initial stacks count and adjust width
        use_stacks = True  # DesktopWindow always uses stacks
        initial_items = self._desktop_tab_manager.get_files(use_stacks=use_stacks)
        if initial_items and hasattr(initial_items[0], 'files'):  # FileStack objects
            initial_stacks_count = len(initial_items)
        else:
            initial_stacks_count = 0  # No stacks initially
        self._adjust_window_width(initial_stacks_count)
        
        # Replace placeholder with container directly (each stack has its own Dock-style container)
        layout = central_widget.layout()
        if layout and self._desktop_placeholder:
            # Get placeholder index
            placeholder_index = layout.indexOf(self._desktop_placeholder)
            
            # Remove placeholder
            layout.removeWidget(self._desktop_placeholder)
            self._desktop_placeholder.setParent(None)
            self._desktop_placeholder = None
            
            # Insert container at the same position
            layout.insertWidget(placeholder_index, self._desktop_container, 1)
    
    def _adjust_window_height(self, expansion_height: int) -> None:
        """Adjust window height based on stack expansion."""
        target_height, target_y = self._calculate_target_geometry(expansion_height)
        current_geometry = self.geometry()
        
        if current_geometry.height() == target_height:
            return
        
        # Si es la primera expansión (altura base), aplicar inmediatamente
        # para evitar que los archivos se superpongan con el nombre del stack
        is_first_expansion = current_geometry.height() == self.BASE_WINDOW_HEIGHT and expansion_height > 0
        
        if is_first_expansion:
            # Aplicar altura inmediatamente sin animación
            self.setGeometry(
                current_geometry.x(), target_y,
                current_geometry.width(), target_height
            )
        else:
            # Usar animación para cambios entre stacks
            self._apply_height_animation(current_geometry, target_height, target_y)
    
    def _calculate_target_geometry(self, expansion_height: int) -> tuple[int, int]:
        """Calculate target height and Y position for window."""
        screen = self.screen().availableGeometry()
        
        target_height = self.BASE_WINDOW_HEIGHT + expansion_height
        max_screen_height = screen.height() - self.WINDOW_MAX_HEIGHT_MARGIN
        target_height = min(target_height, max_screen_height)
        target_height = max(target_height, self.MIN_WINDOW_HEIGHT)
        
        target_y = screen.height() - target_height - self.WINDOW_BOTTOM_MARGIN
        return target_height, target_y
    
    def _apply_geometry_animation(
        self,
        current_geometry: QRect,
        target_geometry: QRect,
        animation_attr: str
    ) -> None:
        """Apply smooth geometry animation to window."""
        # Detener animación anterior si existe
        current_animation = getattr(self, animation_attr, None)
        if current_animation:
            current_animation.stop()
            setattr(self, animation_attr, None)
        
        # Crear nueva animación
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(self.ANIMATION_DURATION_MS)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.setStartValue(current_geometry)
        animation.setEndValue(target_geometry)
        animation.start()
        
        setattr(self, animation_attr, animation)
    
    def _apply_height_animation(self, current_geometry: QRect, target_height: int, target_y: int) -> None:
        """Apply smooth height animation to window."""
        target_geometry = QRect(
            current_geometry.x(), target_y,
            current_geometry.width(), target_height
        )
        self._apply_geometry_animation(current_geometry, target_geometry, '_height_animation')
    
    def _adjust_window_width(self, stacks_count: int) -> None:
        """Adjust window width based on number of stacks."""
        target_width = self._calculate_target_width(stacks_count)
        current_geometry = self.geometry()
        
        if current_geometry.width() == target_width:
            return
        
        screen = self.screen().availableGeometry()
        new_x = (screen.width() - target_width) // 2
        current_height = current_geometry.height()
        
        self._apply_width_animation(current_geometry, target_width, new_x, current_height)
    
    def _calculate_target_width(self, stacks_count: int) -> int:
        """Calculate target width for dock window based on stacks count."""
        if stacks_count == 0:
            return self.DEFAULT_WINDOW_WIDTH
        
        # Márgenes: main_layout + central_internal_layout + grid_layout
        layout_margins = (self.MAIN_LAYOUT_MARGIN * 2) + (self.CENTRAL_LAYOUT_MARGIN * 2)
        grid_margins = self.GRID_LAYOUT_LEFT_MARGIN + self.GRID_LAYOUT_RIGHT_MARGIN
        total_margins = layout_margins + grid_margins
        
        stacks_width = stacks_count * self.STACK_TILE_WIDTH
        # Spacing: entre escritorio-ajustes, ajustes-separador, separador-primer stack, entre stacks
        # A la izquierda: después del separador hay spacing antes del primer stack
        # A la derecha: el margin derecho del grid proporciona el espacio simétrico
        # Total spacing: 3 espacios fijos + (stacks_count - 1) entre stacks = stacks_count + 2
        total_spacing = (stacks_count + 2) * self.STACK_SPACING
        
        return (self.DESKTOP_TILE_WIDTH + self.SETTINGS_TILE_WIDTH + self.SEPARATOR_WIDTH + 
                stacks_width + total_spacing + total_margins)
    
    def _apply_width_animation(self, current_geometry: QRect, target_width: int, new_x: int, current_height: int) -> None:
        """Apply smooth width animation to window."""
        target_geometry = QRect(
            new_x, current_geometry.y(),
            target_width, current_height
        )
        self._apply_geometry_animation(current_geometry, target_geometry, '_width_animation')
    
    def _open_file(self, file_path: str) -> None:
        """Open file with default system application."""
        if os.path.exists(file_path):
            url = QUrl.fromLocalFile(file_path)
            QDesktopServices.openUrl(url)
    
    def _handle_drag_event(self, event: QDragEnterEvent | QDragMoveEvent | QDropEvent) -> bool:
        """Handle common drag event logic and propagate to FileViewContainer."""
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            event.ignore()
            return False
        
        # Aceptar el evento primero para que Windows sepa que esta ventana acepta drops
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        
        # Propagar al FileViewContainer si existe
        if self._desktop_container:
            if isinstance(event, QDragEnterEvent):
                self._desktop_container.dragEnterEvent(event)
            elif isinstance(event, QDragMoveEvent):
                self._desktop_container.dragMoveEvent(event)
            else:  # QDropEvent
                self._desktop_container.dropEvent(event)
            return True
        
        return False
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Capture drag enter events and propagate to FileViewContainer."""
        self._handle_drag_event(event)
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Capture drag move events and propagate to FileViewContainer."""
        self._handle_drag_event(event)
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Capture drop events and propagate to FileViewContainer."""
        if not self._handle_drag_event(event):
            event.ignore()
    
    
