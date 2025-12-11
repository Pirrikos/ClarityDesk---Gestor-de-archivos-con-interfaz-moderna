"""
FileTileIcon - Icon handling for FileTile.

Handles icon loading, sizing, and hover animations.
"""

from PySide6.QtCore import QRect, QSize, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QLabel, QGraphicsDropShadowEffect

from app.services.icon_fallback_helper import safe_pixmap


def add_icon_zone(tile, layout, icon_service) -> None:
    """Add icon zone with shadow."""
    if tile._dock_style:
        icon_width = 48
        icon_height = 48
        pixmap = icon_service.get_file_preview(tile._file_path, QSize(48, 48))
    else:
        icon_width = 96
        icon_height = 96
        pixmap = icon_service.get_file_preview(tile._file_path, QSize(96, 96))
    
    # Para carpetas, no aplicar safe_pixmap
    import os
    if not os.path.isdir(tile._file_path):
        _, ext = os.path.splitext(tile._file_path)
        pixmap = safe_pixmap(pixmap, icon_width, ext)
    
    tile._icon_pixmap = pixmap
    
    tile._icon_label = QLabel()
    tile._icon_label.setFixedSize(icon_width, icon_height)
    tile._icon_label.setPixmap(pixmap)
    tile._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tile._icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    
    tile._icon_shadow = QGraphicsDropShadowEffect(tile._icon_label)
    if tile._dock_style:
        # Lighter shadow for dock style (matching FileStackTile)
        tile._icon_shadow.setBlurRadius(6)
        tile._icon_shadow.setColor(QColor(0, 0, 0, 25))
        tile._icon_shadow.setOffset(0, 2)
    else:
        # Stronger shadow for normal style
        tile._icon_shadow.setBlurRadius(10)
        tile._icon_shadow.setColor(QColor(0, 0, 0, 45))
        tile._icon_shadow.setOffset(0, 4)
    tile._icon_label.setGraphicsEffect(tile._icon_shadow)
    
    layout.addWidget(tile._icon_label, 0, Qt.AlignmentFlag.AlignHCenter)


def animate_icon_size(tile, target_size: int) -> None:
    """Animate icon size change."""
    if not tile._icon_label or tile._icon_pixmap.isNull():
        return
    
    if tile._hover_animation:
        tile._hover_animation.stop()
    
    start_size = tile._current_animated_size
    if start_size == target_size:
        return
    
    start_rect = tile._icon_label.geometry()
    end_rect = QRect(
        (tile.width() - target_size) // 2,
        start_rect.y() - (target_size - start_size) // 2,
        target_size,
        target_size
    )
    
    tile._hover_animation = QPropertyAnimation(tile._icon_label, b"geometry")
    tile._hover_animation.setDuration(200)
    tile._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    tile._hover_animation.setStartValue(start_rect)
    tile._hover_animation.setEndValue(end_rect)
    
    def update_during_animation(value):
        rect = value
        size = rect.width()
        tile._current_animated_size = size
        
        scaled = tile._icon_pixmap.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        tile._icon_label.setPixmap(scaled)
        
        if tile._icon_shadow:
            blur = int(10 + (size - tile._base_icon_size) * 0.3)
            tile._icon_shadow.setBlurRadius(blur)
    
    tile._hover_animation.valueChanged.connect(update_during_animation)
    tile._hover_animation.start()

