"""
FileTile - Tile widget for a single file in grid view.

Displays file icon and name, handles drag out and double-click.
"""

import os
from typing import Optional

from PySide6.QtCore import QPoint, QPropertyAnimation, QSize, Qt, QTimer, QEvent
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QEnterEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.services.icon_service import IconService
from app.ui.widgets.file_tile_anim import animate_enter, animate_exit
from app.ui.widgets.file_tile_controller import set_selected
from app.ui.widgets.file_tile_events import (
    mouse_press_event, mouse_move_event, mouse_release_event,
    mouse_double_click_event, drag_enter_event, drag_move_event, drop_event
)
from app.ui.widgets.file_tile_icon import animate_icon_size
from app.ui.widgets.file_tile_paint import paint_dock_style
from app.ui.widgets.file_tile_setup import setup_ui
from app.ui.widgets.file_tile_states import set_file_state
from app.ui.widgets.state_badge_widget import StateBadgeWidget


class FileTile(QWidget):
    """Internal tile widget for a single file."""

    def __init__(
        self,
        file_path: str,
        parent_view,
        icon_service: IconService,
        disable_hover: bool = False,
        dock_style: bool = False,
    ):
        """Initialize file tile."""
        super().__init__(parent_view)
        self._file_path = file_path
        self._parent_view = parent_view
        self._icon_service = icon_service
        self._icon_pixmap: Optional[QPixmap] = None
        self._drag_start_position: Optional[QPoint] = None
        self._is_selected: bool = False
        self._is_hovered: bool = False
        self._icon_label: Optional[QLabel] = None
        self._icon_shadow: Optional[QGraphicsDropShadowEffect] = None
        self._state_badge: Optional[StateBadgeWidget] = None
        self._hover_animation: Optional[QPropertyAnimation] = None
        self._base_icon_size = 96
        self._hover_icon_size = 120
        self._current_animated_size = 96
        self._disable_hover = disable_hover
        self._dock_style = dock_style
        setup_ui(self)

    def paintEvent(self, event) -> None:
        """Paint background - Dock style draws rounded rect container."""
        paint_dock_style(self, event)
        super().paintEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter for hover effect."""
        if self._disable_hover:
            super().enterEvent(event)
            return
        
        self._is_hovered = True
        if self._dock_style:
            # Dock style: just update for hover shadow
            self.update()
        else:
            # Normal style: animate icon size
            animate_icon_size(self, self._hover_icon_size)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Handle mouse leave."""
        if self._disable_hover:
            super().leaveEvent(event)
            return
        
        self._is_hovered = False
        if self._dock_style:
            # Dock style: just update to remove hover shadow
            self.update()
        else:
            # Normal style: animate icon size
            animate_icon_size(self, self._base_icon_size)
        super().leaveEvent(event)

    def resizeEvent(self, event) -> None:
        """Handle resize."""
        super().resizeEvent(event)
        self._update_badge_position()

    def showEvent(self, event) -> None:
        """Handle show."""
        super().showEvent(event)
        QTimer.singleShot(0, self._update_badge_position)

    def set_selected(self, selected: bool) -> None:
        """Update tile selection state."""
        set_selected(self, selected)

    def _get_selected_tiles(self):
        """Get selected tiles from parent view."""
        if self._parent_view and hasattr(self._parent_view, '_selected_tiles'):
            return self._parent_view._selected_tiles
        return None
    
    def _get_icon_service(self):
        """Get icon service from parent view."""
        if self._parent_view and hasattr(self._parent_view, '_icon_service'):
            return self._parent_view._icon_service
        return None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        mouse_press_event(self, event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for drag."""
        mouse_move_event(self, event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Reset drag start position."""
        mouse_release_event(self, event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Handle double-click to open file."""
        mouse_double_click_event(self, event)

    def contextMenuEvent(self, event) -> None:
        """Context menu disabled."""
        pass

    def get_file_path(self) -> str:
        """Get the file path for this tile."""
        return self._file_path

    def set_file_state(self, state: Optional[str]) -> None:
        """Update file state badge."""
        set_file_state(self, state)

    def _update_badge_position(self) -> None:
        """Update badge position."""
        pass
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter on folder tile."""
        drag_enter_event(self, event)
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move on folder tile."""
        drag_move_event(self, event)
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle file drop on folder tile."""
        drop_event(self, event)
    
    def animate_enter(self, delay_ms: int = 0, start_offset: int = 80) -> None:
        """Animate tile entrance Apple-style."""
        animate_enter(self, delay_ms, start_offset)
    
    def animate_exit(self, callback=None, end_offset: int = 60) -> None:
        """Animate tile exit Apple-style."""
        animate_exit(self, callback, end_offset)
