"""
FileTile - Tile widget for a single file in grid view.

Displays file icon and name, handles drag out and double-click.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QEnterEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QWidget,
)

from app.core.logger import get_logger
from app.services.icon_service import IconService
from app.ui.widgets.file_tile_anim import animate_enter, animate_exit
from app.ui.widgets.file_tile_controller import set_selected

logger = get_logger(__name__)
from app.ui.widgets.file_tile_events import (
    mouse_press_event, mouse_move_event, mouse_release_event,
    mouse_double_click_event, drag_enter_event, drag_move_event, drop_event
)
from app.ui.widgets.file_tile_paint import paint_dock_style, _paint_hover_overlay
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
        get_label_callback: Optional = None
    ):
        """
        Initialize file tile.
        
        Args:
            file_path: Full path to the file.
            parent_view: Parent FileGridView instance.
            icon_service: IconService instance.
            dock_style: If True, use dock style.
            initial_state: Optional initial file state.
            get_label_callback: Optional callback to get state labels.
        """
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
        self._is_hovered: bool = False  # Estado de hover para efecto tipo Finder
        self._get_label_callback = get_label_callback
        setup_ui(self)

    def paintEvent(self, event) -> None:
        # Pintar fondo del contenedor primero
        paint_dock_style(self, event)
        # Luego pintar widgets hijos encima
        super().paintEvent(event)
        # Finalmente pintar hover encima de TODO (incluyendo widgets hijos)
        _paint_hover_overlay(self, event)

    def set_selected(self, selected: bool) -> None:
        set_selected(self, selected)

    def _get_selected_tiles(self):
        return getattr(self._parent_view, '_selected_tiles', None) if self._parent_view else None
    
    def _get_icon_service(self):
        return getattr(self._parent_view, '_icon_service', None) if self._parent_view else None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        mouse_press_event(self, event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        mouse_move_event(self, event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        mouse_release_event(self, event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        mouse_double_click_event(self, event)
    
    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter - activate hover effect."""
        self._is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave - deactivate hover effect."""
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def get_file_path(self) -> str:
        return self._file_path

    def set_file_state(self, state: Optional[str]) -> None:
        set_file_state(self, state)
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        drag_enter_event(self, event)
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        drag_move_event(self, event)
    
    def dropEvent(self, event: QDropEvent) -> None:
        drop_event(self, event)
    
    def animate_enter(self, delay_ms: int = 0, start_offset: int = 80) -> None:
        animate_enter(self, delay_ms, start_offset)
    
    def animate_exit(self, callback=None, end_offset: int = 60) -> None:
        animate_exit(self, callback, end_offset)
    
    def sizeHint(self) -> QSize:
        from app.ui.widgets.file_tile_utils import is_grid_view
        is_grid = is_grid_view(self)
        tile_height = 98 if is_grid else 85
        return QSize(70, tile_height)
    
    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()
