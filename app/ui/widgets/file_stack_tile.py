"""
FileStackTile - Tile widget for a file stack (grouped files).

Displays stack icon with count badge, handles click to expand and drag to move all files.
"""

import os
from typing import Optional

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal, QTimer
from PySide6.QtGui import QBrush, QColor, QEnterEvent, QFontMetrics, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.models.file_stack import FileStack
from app.services.icon_service import IconService
from app.services.icon_fallback_helper import get_default_icon, safe_pixmap
from app.ui.widgets.badge_overlay_widget import BadgeOverlayWidget
from app.ui.widgets.text_elision import elide_middle_manual
from app.ui.widgets.tile_drag_handler import handle_tile_drag


class FileStackTile(QWidget):
    """Tile widget for a file stack."""

    stack_clicked = Signal(FileStack)
    open_file = Signal(str)
    
    def __init__(
        self,
        file_stack: FileStack,
        parent_view,
        icon_service: IconService,
    ):
        """Initialize file stack tile."""
        super().__init__(parent_view)
        self._file_stack = file_stack
        self._parent_view = parent_view
        self._icon_service = icon_service
        self._icon_pixmap: Optional[QPixmap] = None
        self._drag_start_position: Optional[QPoint] = None
        self._is_selected: bool = False
        self._is_hovered: bool = False
        self._icon_label: Optional[QLabel] = None
        self._icon_shadow: Optional[QGraphicsDropShadowEffect] = None
        self._badge_overlay: Optional[BadgeOverlayWidget] = None
        self._last_count = file_stack.get_count()  # Track count to detect changes
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build tile UI."""
        # Tamaño: contenedor 70x70 + texto debajo
        self.setFixedSize(70, 85)  # Height for container + text below
        self.setAutoFillBackground(False)  # We'll paint the background ourselves
        self._setup_layout()
        self.setMouseTracking(True)
        self.setAcceptDrops(False)

    def _setup_layout(self) -> None:
        """Setup layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Container widget for icon (70x70)
        container_widget = QWidget()
        container_widget.setFixedSize(70, 70)
        container_widget.setAutoFillBackground(False)
        # Make container transparent to mouse events so clicks pass through to parent
        container_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(7, 7, 7, 7)
        container_layout.setSpacing(0)
        self._container_widget = container_widget  # Store reference for paintEvent
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
        
        # Apple white style: bright white background
        if self._is_hovered:
            # Slightly brighter on hover
            bg_color = QColor(255, 255, 255, 255)
            border_color = QColor(220, 220, 220, 200)
        else:
            # Pure white like macOS Dock
            bg_color = QColor(255, 255, 255, 250)
            border_color = QColor(200, 200, 200, 150)
        
        # Draw rounded rectangle background only on container area
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, 14, 14)
        
        painter.end()
    
    def _add_icon_zone(self, layout: QVBoxLayout) -> None:
        """Add icon zone with shadow and count badge."""
        # Icono compacto para el Dock
        icon_width = 48
        icon_height = 48
        
        first_file = self._file_stack.files[0] if self._file_stack.files else None
        is_folder_stack = self._file_stack.stack_type == 'folder'
        
        if first_file:
            pixmap = self._icon_service.get_file_preview(first_file, QSize(48, 48))
            
            if is_folder_stack:
                # Para carpetas: verificar si el pixmap tiene contenido visible
                needs_fallback = not pixmap or pixmap.isNull() or self._is_pixmap_empty(pixmap)
                if needs_fallback:
                    # Usar icono de carpeta del sistema
                    folder_icon = self._icon_service.get_folder_icon(first_file, QSize(icon_width, icon_height))
                    pixmap = folder_icon.pixmap(QSize(icon_width, icon_height))
            else:
                # Para archivos: aplicar fallback a SVG por extensión
                _, ext = os.path.splitext(first_file)
                pixmap = safe_pixmap(pixmap, icon_width, ext)
        else:
            pixmap = get_default_icon(icon_width)
        
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
        
        self._setup_badge_overlay()

    def _setup_badge_overlay(self) -> None:
        """Setup floating badge overlay widget."""
        # Clean up any existing badge first to avoid duplicates
        if self._badge_overlay:
            try:
                # Verify badge still exists and is valid
                if hasattr(self._badge_overlay, 'parent') and self._badge_overlay.parent():
                    # Badge exists and is valid, just update it
                    self.update_badge_count()
                    return
                else:
                    # Badge is orphaned, clean it up
                    self._cleanup_badge()
            except (RuntimeError, AttributeError):
                # Badge was deleted, clean up reference
                self._badge_overlay = None
        
        # Get parent visual (GridContentWidget) for badge overlay
        parent_visual = None
        if hasattr(self._parent_view, '_content_widget'):
            parent_visual = self._parent_view._content_widget
        else:
            # Fallback to parent_view if content_widget not available
            parent_visual = self._parent_view
        
        if parent_visual:
            self._badge_overlay = BadgeOverlayWidget(parent_visual)
            count = self._file_stack.get_count()
            self._badge_overlay.set_count(count)
            self._update_badge_position()
    
    def _update_badge_position(self) -> None:
        """Update badge position relative to tile's top-right corner."""
        if not self._badge_overlay:
            return
        
        # Verify badge is still valid
        try:
            if not hasattr(self._badge_overlay, 'parent') or not self._badge_overlay.parent():
                # Badge is orphaned, clean it up
                self._badge_overlay = None
                return
        except (RuntimeError, AttributeError):
            # Badge was deleted, clean up reference
            self._badge_overlay = None
            return
        
        if not self.isVisible():
            try:
                self._badge_overlay.hide()
            except (RuntimeError, AttributeError):
                self._badge_overlay = None
            return
        
        try:
            # Get tile's top-right corner in global coordinates
            tile_rect = self.rect()
            tile_top_right = tile_rect.topRight()
            tile_top_right_global = self.mapToGlobal(tile_top_right)
            
            # Convert to parent visual coordinates
            parent_visual = self._badge_overlay.parent()
            if not parent_visual:
                return
            
            parent_pos = parent_visual.mapFromGlobal(tile_top_right_global)
            
            # Position badge at top-right corner, slightly offset outward
            badge_width = self._badge_overlay.width()
            badge_height = self._badge_overlay.height()
            
            # Offset badge to float above the corner
            badge_x = parent_pos.x() - (badge_width // 2) - 2
            badge_y = parent_pos.y() - (badge_height // 2) - 2
            
            self._badge_overlay.move(int(badge_x), int(badge_y))
            self._badge_overlay.raise_()
            self._badge_overlay.show()
        except (RuntimeError, AttributeError):
            # Widget was deleted or invalid, clean up reference
            self._badge_overlay = None

    def _add_text_band(self, layout: QVBoxLayout) -> None:
        """Add text label below icon - bright white text with shadow for Dock visibility."""
        name_label = QLabel()
        name_label.setWordWrap(False)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFixedWidth(70)  # Match container width
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
        
        # Add text shadow for better visibility and depth
        text_shadow = QGraphicsDropShadowEffect(name_label)
        text_shadow.setBlurRadius(3)
        text_shadow.setXOffset(0)
        text_shadow.setYOffset(1)
        text_shadow.setColor(QColor(0, 0, 0, 180))
        name_label.setGraphicsEffect(text_shadow)
        
        display_name = self._file_stack.get_display_name()
        metrics = QFontMetrics(name_label.font())
        max_width = 68
        elided_text = elide_middle_manual(display_name, metrics, max_width)
        name_label.setText(elided_text)
        
        layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignHCenter)

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter - enhance dock app container on hover."""
        self._is_hovered = True
        self.update()  # Trigger repaint with hover state
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave - restore dock app container style."""
        self._is_hovered = False
        self.update()  # Trigger repaint without hover state
        super().leaveEvent(event)

    def moveEvent(self, event) -> None:
        """Handle move - update badge position."""
        super().moveEvent(event)
        # Use QTimer to ensure position is updated after layout completes
        QTimer.singleShot(0, self._update_badge_position)
    
    def resizeEvent(self, event) -> None:
        """Handle resize - update badge position."""
        super().resizeEvent(event)
        # Use QTimer to ensure position is updated after layout completes
        QTimer.singleShot(0, self._update_badge_position)

    def showEvent(self, event) -> None:
        """Handle show - update badge position and count."""
        super().showEvent(event)
        # Update badge count in case stack changed
        self.update_badge_count()
        QTimer.singleShot(0, self._update_badge_position)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            # If drag was in progress, cancel it immediately
            if self._drag_start_position:
                distance = (event.pos() - self._drag_start_position).manhattanLength()
                if distance < 5:
                    self.stack_clicked.emit(self._file_stack)
                # Immediately clear drag state and force visual update
                self._drag_start_position = None
                self.repaint()  # Immediate repaint, no delay
            else:
                self._drag_start_position = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move - drag all files in stack."""
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._drag_start_position is None:
            return
        
        if handle_tile_drag(
            self._file_stack.files[0],
            self._icon_pixmap,
            self._parent_view,
            self._drag_start_position,
            event.pos(),
            selected_tiles=None,
            icon_service=self._icon_service,
            all_files=self._file_stack.files
        ):
            self._drag_start_position = None

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Handle double-click."""
        # Prevent single-click from firing after double-click
        self._drag_start_position = None
        if self._file_stack.files:
            self.open_file.emit(self._file_stack.files[0])
        event.accept()
        super().mouseDoubleClickEvent(event)

    def get_file_stack(self) -> FileStack:
        """Get the file stack."""
        return self._file_stack

    def get_all_file_paths(self) -> list[str]:
        """Get all file paths in stack."""
        return self._file_stack.files.copy()
    
    def closeEvent(self, event) -> None:
        """Handle close - cleanup badge overlay."""
        self._cleanup_badge()
        super().closeEvent(event)
    
    def _cleanup_badge(self) -> None:
        """Clean up badge overlay widget."""
        if self._badge_overlay:
            try:
                self._badge_overlay.hide()
                self._badge_overlay.setParent(None)
                self._badge_overlay.deleteLater()
            except (RuntimeError, AttributeError):
                pass
            finally:
                self._badge_overlay = None
    
    def update_badge_count(self) -> None:
        """Update badge count from file stack."""
        count = self._file_stack.get_count()
        
        # Only update if count changed or badge doesn't exist
        if count != self._last_count or not self._badge_overlay:
            self._last_count = count
            
            if self._badge_overlay:
                self._badge_overlay.set_count(count)
                self._update_badge_position()
            else:
                # If badge doesn't exist yet, create it
                self._setup_badge_overlay()
    
    def hideEvent(self, event) -> None:
        """Handle hide - hide badge overlay."""
        if self._badge_overlay:
            try:
                self._badge_overlay.hide()
            except (RuntimeError, AttributeError):
                # Badge was deleted, clean up reference
                self._badge_overlay = None
        super().hideEvent(event)
    
    def _is_pixmap_empty(self, pixmap: QPixmap) -> bool:
        """Check if pixmap is visually empty (transparent or no content)."""
        if not pixmap or pixmap.isNull():
            return True
        
        image = pixmap.toImage()
        if image.isNull():
            return True
        
        width = image.width()
        height = image.height()
        
        if width == 0 or height == 0:
            return True
        
        # Sample center and corners
        check_points = [
            (width // 2, height // 2),
            (width // 4, height // 4),
            (3 * width // 4, 3 * height // 4),
        ]
        
        for x, y in check_points:
            if 0 <= x < width and 0 <= y < height:
                color = image.pixelColor(x, y)
                if color.alpha() > 50:
                    return False
        
        return True
