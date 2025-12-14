"""
ViewToolbar - Toolbar with view toggle buttons.

Toolbar widget for switching between grid and list views.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from app.ui.widgets.toolbar_button_styles import get_view_button_style
from app.ui.widgets.toolbar_navigation_buttons import create_navigation_buttons
from app.ui.widgets.toolbar_state_buttons import create_state_buttons


class ViewToolbar(QWidget):
    """Toolbar with view toggle buttons and state quick actions."""

    # Signal emitted when state button is clicked
    state_button_clicked = Signal(str)  # Emits state constant or None
    # Signals for navigation
    navigation_back = Signal()
    navigation_forward = Signal()

    def __init__(self, parent=None):
        """Initialize toolbar."""
        super().__init__(parent)
        self._back_button: QPushButton = None
        self._forward_button: QPushButton = None
        self._grid_button: QPushButton = None
        self._list_button: QPushButton = None
        self._state_buttons: dict[str, QPushButton] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the toolbar UI."""
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #e5e5e7;
            }
        """)
        toolbar_layout = QHBoxLayout(self)
        toolbar_layout.setContentsMargins(20, 0, 20, 0)
        toolbar_layout.setSpacing(8)

        # Navigation buttons (Back/Forward)
        self._back_button, self._forward_button = create_navigation_buttons(self)
        self._back_button.clicked.connect(self.navigation_back.emit)
        self._forward_button.clicked.connect(self.navigation_forward.emit)
        toolbar_layout.addWidget(self._back_button)
        toolbar_layout.addWidget(self._forward_button)
        
        # Add spacing after navigation buttons
        toolbar_layout.addSpacing(8)

        # View toggle buttons (Grid/List)
        self._grid_button = QPushButton("Grid")
        self._grid_button.setCheckable(True)
        self._grid_button.setChecked(True)
        self._grid_button.setFixedHeight(32)
        self._grid_button.setStyleSheet(get_view_button_style(True))
        toolbar_layout.addWidget(self._grid_button)

        self._list_button = QPushButton("List")
        self._list_button.setCheckable(True)
        self._list_button.setFixedHeight(32)
        self._list_button.setStyleSheet(get_view_button_style(False))
        toolbar_layout.addWidget(self._list_button)

        toolbar_layout.addStretch()

        # State quick action buttons
        self._state_buttons = create_state_buttons(
            toolbar_layout,
            self.state_button_clicked.emit
        )

    def get_grid_button(self) -> QPushButton:
        """Get grid button widget."""
        return self._grid_button

    def get_list_button(self) -> QPushButton:
        """Get list button widget."""
        return self._list_button

    def set_nav_enabled(self, can_back: bool, can_forward: bool) -> None:
        """
        Update navigation buttons enabled state.
        
        Args:
            can_back: True if back navigation is possible.
            can_forward: True if forward navigation is possible.
        """
        if self._back_button:
            self._back_button.setEnabled(can_back)
        if self._forward_button:
            self._forward_button.setEnabled(can_forward)

    def update_button_styles(self, grid_checked: bool) -> None:
        """Update button styles based on checked state."""
        self._grid_button.setStyleSheet(get_view_button_style(grid_checked))
        self._list_button.setStyleSheet(get_view_button_style(not grid_checked))
