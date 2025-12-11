"""
Controller logic for FileTile.

Handles selection state and icon updates.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


def set_selected(tile, selected: bool) -> None:
    """Update tile selection state."""
    tile._is_selected = selected
    
    # For dock style, only update visual state (paint handles the rest)
    if tile._dock_style:
        tile.update()
        return
    
    # For non-dock style, apply old selection effects
    if tile._disable_hover:
        return
    
    if not tile._icon_shadow or not tile._icon_label:
        return
    
    try:
        if selected:
            tile._icon_shadow.setBlurRadius(18)
            tile._icon_shadow.setColor(QColor(0, 120, 255, 160))
            tile._icon_label.setFixedSize(100, 100)
            if not tile._icon_pixmap.isNull():
                scaled_pixmap = tile._icon_pixmap.scaled(
                    100, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                tile._icon_label.setPixmap(scaled_pixmap)
        else:
            tile._icon_shadow.setBlurRadius(10)
            tile._icon_shadow.setColor(QColor(0, 0, 0, 45))
            tile._icon_label.setFixedSize(96, 96)
            if not tile._icon_pixmap.isNull():
                tile._icon_label.setPixmap(tile._icon_pixmap)
    except RuntimeError:
        tile._icon_shadow = None
    
    tile._update_badge_position()
    tile.update()

