"""
ListStateDelegate - Delegate para renderizar la columna de estado en la vista de lista.

Reemplaza widgets incrustados por pintado con QStyledItemDelegate para evitar
desajustes al ordenar/navegar. Mantiene estética: barra redondeada y texto centrado.
"""

from typing import Optional, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QWidget

try:
    from app.ui.widgets.state_badge_widget import STATE_COLORS, STATE_LABELS
except ImportError:
    STATE_COLORS = {}
    STATE_LABELS = {}


# Rol de datos para estado (evitar colisión con otros UserRole)
STATE_ROLE = int(Qt.ItemDataRole.UserRole) + 1


class ListStateDelegate(QStyledItemDelegate):
    """Delegate que pinta la barra de estado con texto centrado."""

    def __init__(self, parent: Optional[QWidget] = None, get_label_callback: Optional[Callable[[str], str]] = None):
        super().__init__(parent)
        self._get_label_callback = get_label_callback

    def paint(self, painter: QPainter, option, index) -> None:
        """Pintar barra de color y texto del estado."""
        state = index.data(STATE_ROLE)
        if state is None or state not in STATE_COLORS:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Color y etiqueta
        bar_color = STATE_COLORS[state]
        if self._get_label_callback:
            label_text = self._get_label_callback(state)
        else:
            label_text = STATE_LABELS.get(state, "")

        rect = option.rect

        # Fondo barra redondeada
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_color)
        painter.drawRoundedRect(rect, 4, 4)

        # Texto en color oscuro para contraste
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(60, 60, 60))

        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(label_text)
        text_height = metrics.height()
        text_x = rect.left() + (rect.width() - text_width) // 2
        text_y = rect.top() + (rect.height() + text_height) // 2 - metrics.descent()
        painter.drawText(text_x, text_y, label_text)

        painter.restore()

    def sizeHint(self, option, index):
        """Tamaño preferido igual al alto de la fila (56px en la vista actual)."""
        return super().sizeHint(option, index)

