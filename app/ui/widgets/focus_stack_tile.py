"""
FocusStackTile - Tile widget for a Focus (workspace).

Displays Focus icon, name, and active highlight.
Handles click to switch Focus and drag & drop with hover overlay.
"""

from typing import Optional

from PySide6.QtCore import QPoint, Qt, Signal, QTimer
from PySide6.QtGui import QEnterEvent, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from app.services.icon_service import IconService
from app.ui.widgets.focus_stack_tile_setup import (
    setup_tile_widget,
    create_container_widget,
    add_icon_zone,
    get_icon_pixmap,
    add_text_band,
    create_remove_button
)
from app.ui.widgets.focus_stack_tile_paint import paint_tile_background
from app.ui.widgets.focus_stack_tile_events import (
    handle_mouse_press,
    handle_mouse_release,
    update_remove_button_position,
    hide_remove_button_if_not_hovered
)
from app.ui.widgets.focus_stack_tile_drag import (
    handle_drag_enter,
    handle_drag_leave,
    handle_drag_move,
    handle_drop
)


class FocusStackTile(QWidget):
    """Tile widget for a Focus (workspace)."""

    focus_clicked = Signal(str)  # Emitted when tile is clicked (folder_path)
    overlay_requested = Signal(str, QPoint)  # Emitted when hover > 600ms (folder_path, global_pos)
    focus_remove_requested = Signal(str)  # Emitted when remove button is clicked (folder_path)

    def __init__(
        self,
        folder_path: str,
        is_active: bool,
        parent_view,
        icon_service: IconService,
    ):
        """Initialize Focus stack tile."""
        super().__init__(parent_view)
        self._folder_path = folder_path
        self._is_active = is_active
        self._parent_view = parent_view
        self._icon_service = icon_service
        self._icon_pixmap: Optional[QPixmap] = None
        self._drag_start_position: Optional[QPoint] = None
        self._is_hovered: bool = False
        self._icon_label: Optional[QLabel] = None
        self._icon_shadow: Optional[QGraphicsDropShadowEffect] = None
        self._hover_timer: Optional[QTimer] = None
        self._is_dragging_over: bool = False
        self._remove_button: Optional[QPushButton] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build tile UI."""
        setup_tile_widget(self)
        self._setup_layout()
        self.update()

    def _setup_layout(self) -> None:
        """Setup layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._container_widget = create_container_widget(self)
        self._icon_label, self._icon_shadow = add_icon_zone(
            self._container_widget.layout(), self._folder_path,
            self._is_active, self._icon_service
        )
        self._icon_pixmap = self._icon_label.pixmap()
        layout.addWidget(self._container_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        self._remove_button = create_remove_button(self)
        self._remove_button.clicked.connect(self._on_remove_button_clicked)
        add_text_band(layout, self._folder_path)
    
    def paintEvent(self, event) -> None:
        """Paint the dock container background with rounded corners."""
        if not hasattr(self, '_container_widget') or not self._container_widget:
            super().paintEvent(event)
            return
        
        painter = QPainter(self)
        container_rect = self._container_widget.geometry()
        paint_tile_background(
            painter,
            container_rect,
            self._is_active,
            self._is_hovered,
            self._is_dragging_over
        )
        painter.end()
    

    def resizeEvent(self, event) -> None:
        """Handle resize - update remove button position."""
        super().resizeEvent(event)
        update_remove_button_position(self._remove_button, self._container_widget)
    
    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter - update hover state and show remove button."""
        self._is_hovered = True
        if self._remove_button:
            update_remove_button_position(self._remove_button, self._container_widget)
            self._remove_button.setVisible(True)
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave - reset hover state and hide remove button."""
        self._is_hovered = False
        self._is_dragging_over = False
        if self._remove_button:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(200, lambda: hide_remove_button_if_not_hovered(
                self._remove_button, self._is_hovered
            ))
        self.update()
        
        if self._hover_timer:
            self._hover_timer.stop()
        
        super().leaveEvent(event)
    
    def _on_remove_button_clicked(self) -> None:
        """Handle remove button click - emit signal."""
        self.focus_remove_requested.emit(self._folder_path)

    def _on_hover_timeout(self) -> None:
        """Handle hover timeout - emit overlay request if dragging."""
        if self._is_dragging_over:
            pos = self._container_widget.geometry().center()
            self.overlay_requested.emit(self._folder_path, self.mapToGlobal(pos))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        self._drag_start_position = handle_mouse_press(event, self._drag_start_position)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release - emit clicked signal if it was a click."""
        self._drag_start_position = handle_mouse_release(
            event,
            self._drag_start_position,
            self._folder_path,
            self.focus_clicked
        )
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter - accept if dragging files and start hover timer."""
        handle_drag_enter(event, self._hover_timer, self)

    def dragLeaveEvent(self, event) -> None:
        """Handle drag leave - reset state."""
        handle_drag_leave(self)
        super().dragLeaveEvent(event)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move - keep accepting."""
        handle_drag_move(event)

    def dropEvent(self, event) -> None:
        """Handle drop - emit signal for file move to Focus root."""
        handle_drop(event, self._folder_path, self)

    def set_active(self, is_active: bool) -> None:
        """Set active state and update icon accordingly."""
        if self._is_active == is_active:
            return
        self._is_active = is_active
        if self._icon_label:
            new_pixmap = get_icon_pixmap(
                self._folder_path, self._is_active, 48, 48, self._icon_service
            )
            self._icon_pixmap = new_pixmap
            self._icon_label.setPixmap(new_pixmap)
        self.update()

    def get_folder_path(self) -> str:
        """Get folder path for this Focus."""
        return self._folder_path

