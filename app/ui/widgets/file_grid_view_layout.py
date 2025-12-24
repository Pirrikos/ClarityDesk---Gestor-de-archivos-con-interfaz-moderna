"""
Layout helpers for FileGridView.

Handles grid layout setup.
"""

from PySide6.QtWidgets import QGridLayout

GRID_SPACING = 20
GRID_MARGINS = (4, 8, 24, 24)


def setup_grid_layout(content_widget) -> QGridLayout:
    """Setup grid layout para el contenido sin panel dock."""
    grid_layout = QGridLayout(content_widget)
    grid_layout.setSpacing(GRID_SPACING)
    grid_layout.setContentsMargins(*GRID_MARGINS)
    grid_layout.setColumnStretch(0, 1)
    return grid_layout
