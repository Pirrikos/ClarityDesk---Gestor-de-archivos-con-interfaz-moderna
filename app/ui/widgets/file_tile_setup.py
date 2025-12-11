"""
FileTileSetup - UI setup for FileTile.

Handles layout construction and widget initialization.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.file_tile_icon import add_icon_zone
from app.ui.widgets.state_badge_widget import StateBadgeWidget
from app.ui.widgets.text_elision import elide_middle_manual


def setup_ui(tile) -> None:
    """Build tile UI."""
    if tile._dock_style:
        tile.setFixedSize(70, 85)
    else:
        tile.setFixedSize(100, 158)
    tile.setAutoFillBackground(False)
    setup_layout(tile)
    tile.setMouseTracking(True)
    import os
    tile.setAcceptDrops(os.path.isdir(tile._file_path))


def setup_layout(tile) -> None:
    """Setup layout."""
    layout = QVBoxLayout(tile)
    if tile._dock_style:
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        container_widget = QWidget()
        container_widget.setFixedSize(70, 70)
        container_widget.setAutoFillBackground(False)
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(7, 7, 7, 7)
        container_layout.setSpacing(0)
        tile._container_widget = container_widget
        add_icon_zone(tile, container_layout, tile._icon_service)
        layout.addWidget(container_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        
        add_text_band(tile, layout)
    else:
        layout.setContentsMargins(1, 2, 1, 16)
        layout.setSpacing(4)
        add_icon_zone(tile, layout, tile._icon_service)
        layout.setSpacing(4)
        add_text_band(tile, layout)


def add_text_band(tile, layout: QVBoxLayout) -> None:
    """Add text label."""
    name_label = _create_name_label(tile)
    _configure_label_text(tile, name_label)
    
    layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignCenter)
    _add_state_badge_if_needed(tile, layout)


def _create_name_label(tile) -> QLabel:
    """Create and configure name label widget."""
    name_label = QLabel()
    name_label.setWordWrap(False)
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    if tile._dock_style:
        name_label.setFixedWidth(70)
        name_label.setMinimumWidth(70)
        name_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 10px;
            font-weight: 600;
            color: #ffffff;
            background-color: transparent;
            padding: 0px;
        """)
        _add_dock_text_shadow(name_label)
    else:
        name_label.setFixedWidth(96)
        name_label.setMinimumWidth(96)
        name_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #2d2d2d;
            background-color: transparent;
            padding: 0px;
        """)
    
    name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    return name_label


def _add_dock_text_shadow(name_label: QLabel) -> None:
    """Add shadow effect for dock style label."""
    text_shadow = QGraphicsDropShadowEffect(name_label)
    text_shadow.setBlurRadius(3)
    text_shadow.setXOffset(0)
    text_shadow.setYOffset(1)
    text_shadow.setColor(QColor(0, 0, 0, 180))
    name_label.setGraphicsEffect(text_shadow)


def _configure_label_text(tile, name_label: QLabel) -> None:
    """Configure label text with elision."""
    max_width = 68 if tile._dock_style else 94
    display_name = format_filename(tile._file_path)
    metrics = QFontMetrics(name_label.font())
    elided_text = elide_middle_manual(display_name, metrics, max_width)
    name_label.setText(elided_text)


def _add_state_badge_if_needed(tile, layout: QVBoxLayout) -> None:
    """Add state badge widget if not dock style."""
    if not tile._dock_style:
        icon_width = 96
        tile._state_badge = StateBadgeWidget(tile)
        tile._state_badge.setFixedWidth(icon_width)
        layout.addWidget(tile._state_badge, 0, Qt.AlignmentFlag.AlignHCenter)


def format_filename(file_path: str) -> str:
    """Format filename: remove extension, apply title case."""
    import os
    filename = os.path.basename(file_path)
    name_without_ext, _ = os.path.splitext(filename)
    return name_without_ext.title() if name_without_ext else ""

