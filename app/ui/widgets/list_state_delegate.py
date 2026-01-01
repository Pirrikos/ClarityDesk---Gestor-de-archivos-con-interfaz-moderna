from typing import Optional, Callable
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QWidget
from PySide6.QtCore import Qt, QRect, QSize

try:
    from app.ui.widgets.state_badge_widget import STATE_COLORS, STATE_LABELS
except ImportError:
    STATE_COLORS = {}
    STATE_LABELS = {}
from app.core.constants import CENTRAL_AREA_BG


# Rol de datos para estado (evitar colisión con otros UserRole)
STATE_ROLE = int(Qt.ItemDataRole.UserRole) + 1


class ListStateDelegate(QStyledItemDelegate):
    """Delegate que pinta la barra de estado con texto centrado."""

    def __init__(self, parent: Optional[QWidget] = None, get_label_callback: Optional[Callable[[str], str]] = None):
        super().__init__(parent)
        self._get_label_callback = get_label_callback

    def set_get_label_callback(self, callback: Optional[Callable[[str], str]]) -> None:
        self._get_label_callback = callback

    def paint(self, painter: QPainter, option, index) -> None:
        """Pintar barra de color y texto del estado (y tapar decoración por defecto)."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Tapar la decoración por defecto de Qt en la celda
        self._fill_background(painter, option.rect)

        # Obtener estado
        state = index.data(STATE_ROLE)

        # DEBUG: Log para diagnosticar por qué no se muestran estados
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        row = index.row()
        if row < 5:  # Solo primeras 5 filas para no saturar logs
            logger.debug(f"ListStateDelegate.paint - Row {row}: state='{state}', in STATE_COLORS={state in STATE_COLORS}")

        if state not in STATE_COLORS:
            painter.restore()
            return

        # Obtener color y texto
        bar_color, label_text = self._get_state_info(state)
        bar_rect = self._calculate_bar_geometry(option.rect)

        # Dibujar barra de estado
        self._draw_state_bar(painter, bar_rect, bar_color)

        # Dibujar texto de estado
        self._draw_state_text(painter, bar_rect, label_text)

        painter.restore()

    def _fill_background(self, painter: QPainter, rect: QRect):
        """Rellenar el fondo con el color de fondo central."""
        painter.fillRect(rect, CENTRAL_AREA_BG)

    def _get_state_info(self, state: str) -> tuple[QColor, str]:
        """Obtener el color de la barra y la etiqueta asociada al estado."""
        bar_color = STATE_COLORS.get(state, QColor(150, 150, 150))  # Color por defecto
        label_text = self._get_label_callback(state) if self._get_label_callback else STATE_LABELS.get(state, "")
        return bar_color, label_text

    def _calculate_bar_geometry(self, rect: QRect) -> QRect:
        """Calcular la geometría de la barra de estado (color y texto)."""
        full_h = rect.height()
        bar_h = max(16, int(full_h * 0.3))  # mínimo 16px para legibilidad
        bar_y = rect.top() + (full_h - bar_h) // 2
        margin_x = max(8, int(rect.width() * 0.1))
        return rect.adjusted(margin_x, bar_y - rect.top(), -margin_x, -(rect.bottom() - (bar_y + bar_h)))

    def _draw_state_bar(self, painter: QPainter, bar_rect: QRect, bar_color: QColor) -> None:
        """Dibujar la barra de estado redondeada."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_color)
        painter.drawRoundedRect(bar_rect, 4, 4)

    def _draw_state_text(self, painter: QPainter, bar_rect: QRect, label_text: str) -> None:
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(60, 60, 60))

        metrics = QFontMetrics(font)
        elided = metrics.elidedText(label_text, Qt.TextElideMode.ElideRight, max(0, bar_rect.width() - 8))
        text_width = metrics.horizontalAdvance(elided)
        text_height = metrics.height()

        text_x = bar_rect.left() + (bar_rect.width() - text_width) // 2
        text_y = bar_rect.top() + (bar_rect.height() + text_height) // 2 - metrics.descent()

        painter.drawText(text_x, text_y, elided)

    def sizeHint(self, option, index) -> QSize:
        """Tamaño preferido igual al alto de la fila (56px en la vista actual)."""
        return super().sizeHint(option, index)
