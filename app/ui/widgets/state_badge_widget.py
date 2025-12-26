"""
StateBadgeWidget - Horizontal bar overlay for file state indicators.

Displays a colored horizontal bar with state text positioned above file icons.
Animates state changes with opacity transitions.
"""

from typing import Callable, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QSize
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from app.ui.utils.font_manager import FontManager


# State constants
STATE_PENDING = "pending"      # 🟡 PENDIENTE
STATE_DELIVERED = "delivered"   # 🔵 ENTREGADO
STATE_CORRECTED = "corrected"   # ✅ CORREGIDO
STATE_REVIEW = "review"         # 🔴 REVISAR

# State labels
STATE_LABELS = {
    STATE_PENDING: "PENDIENTE",
    STATE_DELIVERED: "ENTREGADO",
    STATE_CORRECTED: "CORREGIDO",
    STATE_REVIEW: "REVISAR",
}

# State colors (Windows Fluent Design palette - versión tenue)
STATE_COLORS = {
    STATE_PENDING: QColor(255, 220, 120),    # Amarillo más tenue
    STATE_DELIVERED: QColor(120, 180, 240),  # Azul más tenue
    STATE_CORRECTED: QColor(120, 200, 120),   # Verde más tenue
    STATE_REVIEW: QColor(240, 140, 140),     # Rojo más tenue
}


class StateBadgeWidget(QWidget):
    """Horizontal bar widget for displaying file state indicators."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        get_label_callback: Optional[Callable[[str], str]] = None
    ):
        """
        Initialize state badge widget.
        
        Args:
            parent: Parent widget.
            get_label_callback: Optional callback to get label text for a state.
                              If None, uses STATE_LABELS dict.
        """
        super().__init__(parent)
        self._state: Optional[str] = None
        self._bar_height = 20  # Height of horizontal bar
        self._animation_duration = 200  # ms
        self._get_label_callback = get_label_callback
        
        # Setup widget properties - width will be set by parent
        self.setFixedHeight(self._bar_height)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Animation effects
        self._opacity_effect: Optional[QGraphicsOpacityEffect] = None
        self._opacity_animation: Optional[QPropertyAnimation] = None
        
        self._setup_animations()
    
    def set_get_label_callback(self, callback: Optional[Callable[[str], str]]) -> None:
        """Set callback to get label text. Updates display if state is set."""
        self._get_label_callback = callback
        if self._state:
            self.update()

    def _setup_animations(self) -> None:
        """Setup animation effects for state changes."""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)  # Start transparent (no state)

    def set_state(self, state: Optional[str]) -> None:
        """
        Update badge state and animate the change.
        
        Args:
            state: One of STATE_* constants or None to hide badge (transparent but keeps space).
        """
        if state == self._state:
            return
        
        self._state = state
        
        if state is None:
            # Hide badge visually but keep space
            self._animate_hide()
        else:
            # Show badge with animation
            self._animate_show()
        
        self.update()

    def get_state(self) -> Optional[str]:
        """Get current badge state."""
        return self._state

    def _animate_show(self) -> None:
        """Animate badge appearance with opacity."""
        if not self._opacity_effect:
            return
        
        # Reset opacity
        self._opacity_effect.setOpacity(0.0)
        self.setVisible(True)
        
        # Opacity animation
        self._opacity_animation = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._opacity_animation.setDuration(150)
        self._opacity_animation.setStartValue(0.0)
        self._opacity_animation.setEndValue(1.0)
        self._opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animation
        self._opacity_animation.start()

    def _animate_hide(self) -> None:
        """Animate badge disappearance (keep widget visible but transparent to reserve space)."""
        if not self._opacity_effect:
            self._opacity_effect.setOpacity(0.0)
            return
        
        self._opacity_animation = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._opacity_animation.setDuration(150)
        self._opacity_animation.setStartValue(1.0)
        self._opacity_animation.setEndValue(0.0)
        self._opacity_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self._opacity_animation.start()
        # Don't hide widget - keep space reserved so title doesn't move

    def paintEvent(self, event) -> None:
        """Draw horizontal bar with state text."""
        if self._state is None or self._state not in STATE_COLORS:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get state color and label
        bar_color = STATE_COLORS[self._state]
        if self._get_label_callback:
            label_text = self._get_label_callback(self._state)
        else:
            label_text = STATE_LABELS.get(self._state, "")
        
        rect = self.rect()
        
        # Draw colored bar background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_color)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Draw text with appropriate color for contrast (darker for lighter backgrounds)
        font = FontManager.create_font("Segoe UI", FontManager.SIZE_SMALL, QFont.Weight.Bold)
        painter.setFont(font)
        # Use darker text color for better contrast with lighter backgrounds
        painter.setPen(QColor(60, 60, 60))
        
        # Center text horizontally and vertically
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(label_text)
        text_height = metrics.height()
        text_x = (rect.width() - text_width) // 2
        text_y = (rect.height() + text_height) // 2 - metrics.descent()
        
        painter.drawText(text_x, text_y, label_text)
        
        painter.end()

    def sizeHint(self) -> QSize:
        """Return preferred widget size."""
        return QSize(96, self._bar_height)  # Width matches icon width

