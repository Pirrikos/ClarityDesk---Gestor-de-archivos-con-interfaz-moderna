"""
Setup helpers for FocusStackTile.

Handles UI setup: layout, icon zone, text band, and remove button.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.icon_service import IconService
from app.services.icon_renderer import render_svg_icon
from app.ui.widgets.text_elision import elide_middle_manual
from app.services.tab_utils import get_tab_display_name


def setup_tile_widget(widget: QWidget) -> None:
    """Setup basic widget properties - same as DesktopStackTile."""
    widget.setFixedSize(70, 85)
    widget.setAutoFillBackground(False)
    # Match DesktopStackTile exactly - no WA_OpaquePaintEvent, no stylesheet
    widget.setMouseTracking(True)
    widget.setAcceptDrops(True)


def create_container_widget(parent: QWidget) -> QWidget:
    """Create container widget for icon - same structure as DesktopStackTile."""
    container_widget = QWidget(parent)
    container_widget.setFixedSize(70, 70)
    container_widget.setAutoFillBackground(False)
    container_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    # Match DesktopStackTile exactly - no WA_OpaquePaintEvent, no stylesheet
    
    container_layout = QVBoxLayout(container_widget)
    container_layout.setContentsMargins(7, 7, 7, 7)
    container_layout.setSpacing(0)
    
    return container_widget


def add_icon_zone(
    layout: QVBoxLayout,
    folder_path: str,
    is_active: bool,
    icon_service: IconService
) -> tuple[QLabel, QGraphicsDropShadowEffect]:
    """Add icon zone with shadow."""
    icon_width = 48
    icon_height = 48
    
    pixmap = get_icon_pixmap(folder_path, is_active, icon_width, icon_height, icon_service)
    
    icon_label = QLabel()
    icon_label.setFixedSize(icon_width, icon_height)
    icon_label.setPixmap(pixmap)
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    # Match DesktopStackTile - no explicit setVisible/show needed
    
    icon_shadow = QGraphicsDropShadowEffect(icon_label)
    icon_shadow.setBlurRadius(6)
    icon_shadow.setColor(QColor(0, 0, 0, 25))
    icon_shadow.setOffset(0, 2)
    icon_label.setGraphicsEffect(icon_shadow)
    
    layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
    
    return icon_label, icon_shadow


def get_icon_pixmap(
    folder_path: str,
    is_active: bool,
    icon_width: int,
    icon_height: int,
    icon_service: IconService
) -> QPixmap:
    """Get icon pixmap - SVG if active, system icon otherwise."""
    from PySide6.QtCore import QSize
    
    size = QSize(icon_width, icon_height)
    
    if is_active:
        pixmap = render_svg_icon("folder icon.svg", size)
        if pixmap.isNull():
            folder_icon = icon_service.get_folder_icon(folder_path, size)
            pixmap = folder_icon.pixmap(size)
    else:
        folder_icon = icon_service.get_folder_icon(folder_path, size)
        pixmap = folder_icon.pixmap(size)
    
    if pixmap.isNull():
        pixmap = QPixmap(icon_width, icon_height)
        pixmap.fill(QColor(200, 200, 200))
    
    return pixmap


def add_text_band(layout: QVBoxLayout, folder_path: str) -> QLabel:
    """Add text label below icon."""
    name_label = QLabel()
    name_label.setWordWrap(False)
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
    name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    
    text_shadow = QGraphicsDropShadowEffect(name_label)
    text_shadow.setBlurRadius(3)
    text_shadow.setXOffset(0)
    text_shadow.setYOffset(1)
    text_shadow.setColor(QColor(0, 0, 0, 180))
    name_label.setGraphicsEffect(text_shadow)
    
    display_name = get_tab_display_name(folder_path)
    metrics = QFontMetrics(name_label.font())
    max_width = 68
    elided_text = elide_middle_manual(display_name, metrics, max_width)
    name_label.setText(elided_text)
    
    layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignHCenter)
    
    return name_label


def create_remove_button(parent: QWidget) -> QPushButton:
    """Create remove button (X) for tile."""
    remove_button = QPushButton("×", parent)
    remove_button.setFixedSize(18, 18)
    remove_button.setStyleSheet("""
        QPushButton {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(200, 200, 200, 0.8);
            border-radius: 9px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            font-weight: 600;
            color: rgb(100, 100, 100);
        }
        QPushButton:hover {
            background-color: rgba(255, 100, 100, 0.95);
            border-color: rgba(200, 50, 50, 1.0);
            color: rgb(255, 255, 255);
        }
    """)
    remove_button.setVisible(False)
    remove_button.raise_()
    return remove_button

