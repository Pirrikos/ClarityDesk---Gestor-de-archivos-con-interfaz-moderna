"""
FileTile - Tile widget for a single file in grid view.

Displays file icon and name, handles drag out and double-click.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QWidget,
)

from app.services.icon_service import IconService
from app.ui.widgets.file_tile_anim import animate_enter, animate_exit
from app.ui.widgets.file_tile_controller import set_selected
from app.ui.widgets.file_tile_events import (
    mouse_press_event, mouse_move_event, mouse_release_event,
    mouse_double_click_event, drag_enter_event, drag_move_event, drop_event
)
from app.ui.widgets.file_tile_paint import paint_dock_style
from app.ui.widgets.file_tile_setup import setup_ui
from app.ui.widgets.file_tile_states import set_file_state
from app.ui.widgets.state_badge_widget import StateBadgeWidget

if TYPE_CHECKING:
    from app.ui.widgets.file_grid_view import FileGridView


class FileTile(QWidget):
    """Internal tile widget for a single file."""

    def __init__(
        self,
        file_path: str,
        parent_view: 'FileGridView',
        icon_service: IconService,
        dock_style: bool = False,
        initial_state: Optional[str] = None,
    ):
        """Initialize file tile."""
        super().__init__(parent_view)
        self._file_path = file_path
        self._parent_view = parent_view
        self._icon_service = icon_service
        self._icon_pixmap: Optional[QPixmap] = None
        self._drag_start_position: Optional[QPoint] = None
        self._is_selected: bool = False
        self._icon_label: Optional[QLabel] = None
        self._icon_shadow: Optional[QGraphicsDropShadowEffect] = None
        self._state_badge: Optional[StateBadgeWidget] = None
        self._file_state: Optional[str] = initial_state
        self._dock_style = dock_style
        setup_ui(self)

    def paintEvent(self, event) -> None:
        """Paint background - Dock style draws rounded rect container."""
        paint_dock_style(self, event)
        super().paintEvent(event)

    def set_selected(self, selected: bool) -> None:
        """Update tile selection state."""
        set_selected(self, selected)

    def _get_selected_tiles(self):
        """Get selected tiles from parent view."""
        return getattr(self._parent_view, '_selected_tiles', None) if self._parent_view else None
    
    def _get_icon_service(self):
        """Get icon service from parent view."""
        return getattr(self._parent_view, '_icon_service', None) if self._parent_view else None

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

    def get_file_path(self) -> str:
        """Get the file path for this tile."""
        return self._file_path

    def set_file_state(self, state: Optional[str]) -> None:
        """Update file state badge."""
        set_file_state(self, state)
    
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
    
    def sizeHint(self) -> QSize:
        """Return preferred size - mismo tamaño para Dock y Grid."""
        return QSize(70, 85)
    
    def minimumSizeHint(self) -> QSize:
        """Return minimum size - mismo tamaño para Dock y Grid."""
        return self.sizeHint()
