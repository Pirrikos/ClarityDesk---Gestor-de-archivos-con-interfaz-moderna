"""
StateBadgeWidget - Horizontal bar overlay for file state indicators.

Displays a colored horizontal bar with state text positioned above file icons.
Animates state changes with opacity transitions.
"""

from typing import Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QSize
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


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

# State colors (Windows Fluent Design palette)
STATE_COLORS = {
    STATE_PENDING: QColor(255, 184, 0),      # #FFB800 - Amarillo
    STATE_DELIVERED: QColor(0, 120, 212),    # #0078D4 - Azul
    STATE_CORRECTED: QColor(16, 124, 16),    # #107C10 - Verde
    STATE_REVIEW: QColor(209, 52, 56),       # #D13438 - Rojo
}


class StateBadgeWidget(QWidget):
    """Horizontal bar widget for displaying file state indicators."""

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize state badge widget."""
        super().__init__(parent)
        self._state: Optional[str] = None
        self._bar_height = 20  # Height of horizontal bar
        self._animation_duration = 200  # ms
        
        # Setup widget properties - width will be set by parent
        self.setFixedHeight(self._bar_height)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Animation effects
        self._opacity_effect: Optional[QGraphicsOpacityEffect] = None
        self._opacity_animation: Optional[QPropertyAnimation] = None
        
        self._setup_animations()

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
        self.show()
        
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
        label_text = STATE_LABELS.get(self._state, "")
        
        rect = self.rect()
        
        # Draw colored bar background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_color)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Draw white text
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        
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

