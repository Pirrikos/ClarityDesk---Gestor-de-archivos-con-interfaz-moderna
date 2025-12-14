"""
FileTileSetup - UI setup for FileTile.

Handles layout construction and widget initialization.
"""

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)

from app.ui.widgets.file_tile_icon import add_icon_zone
from app.ui.widgets.file_tile_utils import format_filename, is_grid_view
from app.ui.widgets.state_badge_widget import StateBadgeWidget
from app.ui.widgets.text_elision import elide_middle_manual

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def setup_ui(tile: 'FileTile') -> None:
    """Build tile UI."""
    tile.setFixedSize(70, 85)
    tile.setAutoFillBackground(False)
    setup_layout(tile)
    tile.setMouseTracking(True)
    tile.setAcceptDrops(os.path.isdir(tile._file_path))


def setup_layout(tile: 'FileTile') -> None:
    """Setup layout - mismo layout para Dock y Grid."""
    layout = QVBoxLayout(tile)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    
    container_widget = QWidget()
    container_widget.setFixedSize(70, 64)
    container_widget.setAutoFillBackground(False)
    container_layout = QVBoxLayout(container_widget)
    container_layout.setContentsMargins(7, 7, 7, 7)
    container_layout.setSpacing(0)
    tile._container_widget = container_widget
    add_icon_zone(tile, container_layout, tile._icon_service)
    layout.addWidget(container_widget, 0, Qt.AlignmentFlag.AlignHCenter)
    
    add_text_band(tile, layout)
    
    layout.setStretchFactor(container_widget, 0)


def add_text_band(tile: 'FileTile', layout: QVBoxLayout) -> None:
    """Add text label - mismo estilo para Dock y Grid."""
    is_grid = is_grid_view(tile)
    is_list_view = not is_grid and not tile._dock_style
    
    name_label = _create_and_configure_name_label(tile)
    
    if is_list_view:
        bottom_band = _create_bottom_band_with_badge(tile, name_label)
        layout.addWidget(bottom_band, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.setStretchFactor(bottom_band, 0)
    else:
        layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignCenter)


def _create_bottom_band_with_badge(tile: 'FileTile', name_label: QLabel) -> QWidget:
    """Create bottom band widget with name label and state badge for ListView."""
    bottom_band = QWidget()
    bottom_band.setFixedWidth(96)
    bottom_band.setFixedHeight(56)
    bottom_band.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    band_layout = QVBoxLayout(bottom_band)
    band_layout.setContentsMargins(0, 0, 0, 0)
    band_layout.setSpacing(4)
    
    band_layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignHCenter)
    _add_state_badge_to_band(tile, band_layout, bottom_band)
    
    return bottom_band


def _create_and_configure_name_label(tile: 'FileTile') -> QLabel:
    """Create and configure name label widget - mismo estilo para Dock y Grid."""
    name_label = QLabel()
    name_label.setWordWrap(True)
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
    
    name_label.setFixedWidth(70)
    name_label.setMinimumWidth(70)
    name_label.setMinimumHeight(12)
    name_label.setMaximumHeight(15)
    name_label.setSizePolicy(
        QSizePolicy.Policy.Fixed,
        QSizePolicy.Policy.Fixed
    )
    name_label.setScaledContents(False)
    name_label.setStyleSheet("""
        QLabel {
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
            font-weight: 600;
            color: #E8E8E8;
            background-color: transparent;
            padding: 0px;
            line-height: 1.2;
        }
    """)
    _add_dock_text_shadow(name_label)
    
    name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    
    display_name = format_filename(tile._file_path)
    label_width = name_label.width() or name_label.fixedWidth() or 70
    max_width = label_width - 2
    metrics = QFontMetrics(name_label.font())
    text_width = metrics.horizontalAdvance(display_name)
    
    if text_width <= max_width:
        name_label.setText(display_name)
    else:
        elided_text = elide_middle_manual(display_name, metrics, max_width)
        name_label.setText(elided_text)
    
    tile._name_label = name_label
    return name_label


def _add_dock_text_shadow(name_label: QLabel) -> None:
    """Add shadow effect for dock style label."""
    text_shadow = QGraphicsDropShadowEffect(name_label)
    text_shadow.setBlurRadius(3)
    text_shadow.setXOffset(0)
    text_shadow.setYOffset(1)
    text_shadow.setColor(QColor(0, 0, 0, 180))
    name_label.setGraphicsEffect(text_shadow)


def _add_state_badge_to_band(tile: 'FileTile', band_layout: QVBoxLayout, band_widget: QWidget) -> None:
    """Add state badge widget to bottom band (for ListView)."""
    tile._state_badge = StateBadgeWidget(band_widget)
    tile._state_badge.setFixedWidth(96)
    tile._state_badge.setFixedHeight(20)
    band_layout.addWidget(tile._state_badge, 0, Qt.AlignmentFlag.AlignHCenter)



