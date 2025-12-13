"""
DesktopWindow - Desktop Focus window with vertical layout.

Auto-start window showing Desktop Focus (top) and Trash Focus (bottom).
Opens automatically on app startup.
"""

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QUrl, QTimer, QPoint
from PySide6.QtGui import QDesktopServices, QPainter, QColor, QBrush, QPen, QMouseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
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
    
    def paintEvent(self, event) -> None:
        """Paint Apple Dock-style background with rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Apple Dock style: dark gray with ~65% opacity
        # macOS uses approximately rgba(30, 30, 30, 0.65) for dark mode dock
        bg_color = QColor(28, 28, 30, 165)  # ~65% opacity (165/255)
        
        # Subtle border like Apple Dock
        border_color = QColor(255, 255, 255, 25)  # Very subtle white border
        
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


class DesktopWindow(QMainWindow):
    """Desktop Focus window with vertical Desktop (top) and Trash (bottom) panels."""
    
    open_main_window = Signal()  # Emitted when user clicks to open main window
    
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
        
        # Position window at BOTTOM of screen, centered horizontally
        screen = self.screen().availableGeometry()
        window_height = 140  # Compact height for Dock (just icons)
        window_width = int(screen.width() * 0.6)  # 60% width
        window_x = (screen.width() - window_width) // 2  # Centered
        window_y = screen.height() - window_height - 10  # Bottom with small margin
        self.setGeometry(window_x, window_y, window_width, window_height)
        # Minimum size will be set dynamically based on stacks count
        # Only set minimum height, width will be adjusted by _adjust_window_width
        self.setMinimumHeight(120)
        # No max height limit - window expands as needed
        
        # Create dock background widget with Apple-style transparency
        central_widget = DockBackgroundWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        # Margins match the rounded background (8px outer + some inner padding)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(0)
        
        # Placeholder widget for Desktop Focus panel (will be replaced in initialize_after_show)
        self._desktop_placeholder = QWidget()
        self._desktop_placeholder.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        main_layout.addWidget(self._desktop_placeholder, 1)
        
        # NO footer - pure Dock style
        
        # Fully transparent window
        self.setStyleSheet("""
            QMainWindow {
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
        
        # Get parent widget for FileViewContainer
        central_widget = self.centralWidget()
        
        # Create Desktop Focus panel
        self._desktop_container = FileViewContainer(
            self._desktop_tab_manager,
            self._icon_service,
            None,
            central_widget  # Parent widget
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
        
        # Si es la primera expansión (altura base = 140px), aplicar inmediatamente
        # para evitar que los archivos se superpongan con el nombre del stack
        base_height = 140
        is_first_expansion = current_geometry.height() == base_height and expansion_height > 0
        
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
        base_height = 140
        
        target_height = base_height + expansion_height
        max_screen_height = screen.height() - 20
        target_height = min(target_height, max_screen_height)
        target_height = max(target_height, 120)
        
        target_y = screen.height() - target_height - 10
        return target_height, target_y
    
    def _apply_height_animation(self, current_geometry: QRect, target_height: int, target_y: int) -> None:
        """Apply smooth height animation to window."""
        if self._height_animation:
            self._height_animation.stop()
            self._height_animation = None
        
        current_height = current_geometry.height()
        current_y = current_geometry.y()
        
        self._height_animation = QPropertyAnimation(self, b"geometry", self)
        self._height_animation.setDuration(250)
        self._height_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._height_animation.setStartValue(QRect(
            current_geometry.x(), current_y,
            current_geometry.width(), current_height
        ))
        self._height_animation.setEndValue(QRect(
            current_geometry.x(), target_y,
            current_geometry.width(), target_height
        ))
        self._height_animation.start()
    
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
            return 400
        
        stack_width = 70
        spacing = 12
        margins = 72  # 32px (main_layout) + 40px (grid_layout)
        escritorio_width = 70
        ajustes_width = 70
        separator_width = 1  # Separador es muy delgado
        
        stacks_width = stacks_count * stack_width
        # Spacing: entre escritorio y ajustes, entre ajustes y separador, entre separador y primer stack, y entre stacks
        total_spacing = (stacks_count + 2) * spacing  # +2 por espacios entre escritorio-ajustes-separador-primer stack
        
        return escritorio_width + ajustes_width + separator_width + stacks_width + total_spacing + margins
        
        # Check if width needs to change
        if current_width == target_width:
            return
        
        # Apply smooth width animation
        self._apply_width_animation(current_geometry, target_width, new_x, current_height)
    
    def _apply_width_animation(self, current_geometry: QRect, target_width: int, new_x: int, current_height: int) -> None:
        """Apply smooth width animation to window."""
        if self._width_animation:
            self._width_animation.stop()
            self._width_animation = None
        
        current_width = current_geometry.width()
        current_x = current_geometry.x()
        current_y = current_geometry.y()
        
        self._width_animation = QPropertyAnimation(self, b"geometry", self)
        self._width_animation.setDuration(250)
        self._width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._width_animation.setStartValue(QRect(
            current_x, current_y,
            current_width, current_height
        ))
        self._width_animation.setEndValue(QRect(
            new_x, current_y,
            target_width, current_height
        ))
        self._width_animation.start()
    
    def _open_file(self, file_path: str) -> None:
        """Open file with default system application."""
        if os.path.exists(file_path):
            url = QUrl.fromLocalFile(file_path)
            QDesktopServices.openUrl(url)
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        super().closeEvent(event)
