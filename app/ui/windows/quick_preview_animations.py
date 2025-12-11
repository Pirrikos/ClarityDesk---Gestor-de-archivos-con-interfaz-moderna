"""
Quick Preview Animations - UI animations for preview window.

Handles entrance and crossfade animations.
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, QTimer, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget


class QuickPreviewAnimations:
    """Manages animations for the preview window."""
    
    @staticmethod
    def apply_crossfade(image_label: QLabel, new_pixmap: QPixmap) -> None:
        """
        Apply crossfade animation when changing images.
        
        Args:
            image_label: Label displaying the image.
            new_pixmap: The new pixmap to display.
        """
        existing_effect = image_label.graphicsEffect()
        if existing_effect:
            image_label.setGraphicsEffect(None)
        
        opacity_effect = QGraphicsOpacityEffect(image_label)
        image_label.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(1.0)
        
        fade_out = QPropertyAnimation(opacity_effect, b"opacity", image_label)
        fade_out.setDuration(60)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        fade_in = QPropertyAnimation(opacity_effect, b"opacity", image_label)
        fade_in.setDuration(60)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        def change_image():
            image_label.setPixmap(new_pixmap)
            fade_in.start()
        
        fade_out.finished.connect(change_image)
        fade_out.start()
        
        def cleanup():
            image_label.setGraphicsEffect(None)
        
        fade_in.finished.connect(cleanup)
    
    @staticmethod
    def animate_entrance(window: QWidget) -> None:
        """Animate window entrance with fade and scale."""
        opacity_effect = QGraphicsOpacityEffect(window)
        window.setGraphicsEffect(opacity_effect)
        
        initial_geo = window.geometry()
        center_x = initial_geo.x() + initial_geo.width() // 2
        center_y = initial_geo.y() + initial_geo.height() // 2
        initial_width = int(initial_geo.width() * 0.96)
        initial_height = int(initial_geo.height() * 0.96)
        initial_rect = QRect(
            center_x - initial_width // 2,
            center_y - initial_height // 2,
            initial_width,
            initial_height
        )
        
        window.setGeometry(initial_rect)
        opacity_effect.setOpacity(0.0)
        
        opacity_anim = QPropertyAnimation(opacity_effect, b"opacity", window)
        opacity_anim.setDuration(120)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        geometry_anim = QPropertyAnimation(window, b"geometry", window)
        geometry_anim.setDuration(120)
        geometry_anim.setStartValue(initial_rect)
        geometry_anim.setEndValue(initial_geo)
        geometry_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        opacity_anim.start()
        geometry_anim.start()
        
        QTimer.singleShot(120, lambda: window.setGraphicsEffect(None))

