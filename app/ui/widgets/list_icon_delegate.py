"""
ListIconDelegate - Professional delegate for list view rendering.

Controls all drawing to prevent Qt's default selection borders.
"""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem, QStyledItemDelegate, QTableWidget

from app.core.constants import (
    SELECTION_BORDER_COLOR,
    SELECTION_BG_COLOR,
    CENTRAL_AREA_BG,
    CENTRAL_AREA_BG_LIGHT,
)


class ListViewDelegate(QStyledItemDelegate):
    """
    Unified delegate for all list view columns.

    Completely controls item rendering to prevent default Qt selection borders.
    """

    # ─────────────────────────────────────────────────────────────
    # Layout / geometry
    # ─────────────────────────────────────────────────────────────
    MARGIN_LEFT = 14
    ICON_SIZE_SELECTED = QSize(30, 30)
    ICON_SIZE_NORMAL = QSize(28, 28)
    ICON_OFFSET_X = 2
    TEXT_OFFSET_X = 32
    CONTAINER_MARGIN = 2
    CONTAINER_RADIUS = 8
    HOVER_RADIUS = 8

    # ─────────────────────────────────────────────────────────────
    # Colors
    # ─────────────────────────────────────────────────────────────
    TEXT_COLOR = QColor(232, 232, 232)
    HOVER_BG_COLOR = QColor(255, 255, 255, 20)
    CONTAINER_BG_COLOR = QColor(190, 190, 190)
    CONTAINER_BORDER_COLOR = QColor(160, 160, 160)

    # ─────────────────────────────────────────────────────────────
    # Constants
    # ─────────────────────────────────────────────────────────────
    ROW_HEIGHT = 56  # Debe coincidir con vheader.setDefaultSectionSize(56)

    def __init__(self, parent=None, column_index: int = 1):
        super().__init__(parent)
        self._column_index = column_index
        self._is_widget_column = column_index in (0, 4)  # checkbox / state
        self._is_name_column = column_index == 1
        self._table_widget = parent if isinstance(parent, QTableWidget) else None

    # ─────────────────────────────────────────────────────────────
    # Size hint - CRÍTICO para que Qt pinte toda la fila
    # ─────────────────────────────────────────────────────────────
    def sizeHint(self, option, index) -> QSize:
        """Return fixed size hint to ensure full row is painted."""
        return QSize(option.rect.width(), self.ROW_HEIGHT)

    # ─────────────────────────────────────────────────────────────
    # Hover tracking
    # ─────────────────────────────────────────────────────────────
    def _get_hovered_row(self) -> int:
        if not self._table_widget:
            return -1
        try:
            return getattr(self._table_widget, "_hovered_row", -1)
        except (AttributeError, RuntimeError):
            return -1

    # ─────────────────────────────────────────────────────────────
    # Paint
    # ─────────────────────────────────────────────────────────────
    def paint(self, painter: QPainter, option, index) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        # Disable Qt default selection visuals
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        opt.state &= ~QStyle.StateFlag.State_KeyboardFocusChange
        opt.showDecorationSelected = False
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        current_row = index.row()
        is_hovered = current_row == self._get_hovered_row()

        base_color = self._get_theme_color()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # ───── Background handling ─────
        if self._is_widget_column:
            # Checkbox / state columns: NEVER paint hover/selection full-row
            painter.fillRect(opt.rect, base_color)

        elif self._is_name_column and is_hovered and not is_selected:
            # Hover background (rounded), excluding checkbox column
            full_row_rect = self._calculate_full_row_rect(current_row)

            if full_row_rect.isValid():
                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                painter.setBrush(QBrush(self.HOVER_BG_COLOR))
                painter.setPen(Qt.PenStyle.NoPen)

                painter.drawRoundedRect(
                    full_row_rect.adjusted(1, 1, -1, -1),
                    self.HOVER_RADIUS,
                    self.HOVER_RADIUS,
                )

                painter.restore()
            else:
                painter.fillRect(opt.rect, self.HOVER_BG_COLOR)

        elif not self._is_name_column:
            if not is_hovered or is_selected:
                painter.fillRect(opt.rect, base_color)

        else:
            painter.fillRect(opt.rect, base_color)

        # Widget columns stop here
        if self._is_widget_column:
            return

        # ───── Content ─────
        if self._is_name_column:
            self._draw_icon_container(painter, opt, is_selected)
            self._draw_name_column(painter, opt, index, is_selected)
        else:
            self._draw_text_column(painter, opt, index)

    # ─────────────────────────────────────────────────────────────
    # Icon + container
    # ─────────────────────────────────────────────────────────────
    def _calculate_icon_position(self, option, is_selected: bool) -> QRect:
        icon_size = self.ICON_SIZE_SELECTED if is_selected else self.ICON_SIZE_NORMAL
        x = option.rect.left() + self.MARGIN_LEFT + self.ICON_OFFSET_X
        y = option.rect.top() + (option.rect.height() - icon_size.height()) // 2
        return QRect(x, y, icon_size.width(), icon_size.height())

    def _draw_icon_container(self, painter: QPainter, option, is_selected: bool) -> None:
        icon_rect = self._calculate_icon_position(option, is_selected)

        container_rect = QRect(
            icon_rect.left() - self.CONTAINER_MARGIN,
            icon_rect.top() - self.CONTAINER_MARGIN,
            icon_rect.width() + self.CONTAINER_MARGIN * 2,
            icon_rect.height() + self.CONTAINER_MARGIN * 2,
        )

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        bg = self.CONTAINER_BG_COLOR
        border = self.CONTAINER_BORDER_COLOR
        width = 1

        if is_selected:
            bg = SELECTION_BG_COLOR
            border = SELECTION_BORDER_COLOR
            width = 2

        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, width))
        painter.drawRoundedRect(container_rect, self.CONTAINER_RADIUS, self.CONTAINER_RADIUS)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    # ─────────────────────────────────────────────────────────────
    # Text drawing
    # ─────────────────────────────────────────────────────────────
    def _draw_name_column(self, painter: QPainter, option, index, is_selected: bool) -> None:
        text = index.data(Qt.ItemDataRole.DisplayRole)
        icon = index.data(Qt.ItemDataRole.DecorationRole)

        icon_size = self.ICON_SIZE_SELECTED if is_selected else self.ICON_SIZE_NORMAL

        if icon and isinstance(icon, QIcon):
            pixmap = icon.pixmap(icon_size)
            if not pixmap.isNull():
                painter.drawPixmap(self._calculate_icon_position(option, is_selected), pixmap)

        if text:
            text_x = option.rect.left() + self.MARGIN_LEFT + icon_size.width() + self.TEXT_OFFSET_X
            text_rect = QRect(
                text_x,
                option.rect.top(),
                option.rect.right() - text_x - 4,
                option.rect.height(),
            )
            painter.setPen(self.TEXT_COLOR)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(text),
            )

    def _draw_text_column(self, painter: QPainter, option, index) -> None:
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return

        painter.setPen(self.TEXT_COLOR)

        alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        if self._column_index in (2, 3):
            alignment = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter

        painter.drawText(option.rect, alignment, str(text))

    # ─────────────────────────────────────────────────────────────
    # Theme + geometry helpers
    # ─────────────────────────────────────────────────────────────
    def _get_theme_color(self) -> QColor:
        try:
            from app.managers import app_settings as app_settings_module

            if app_settings_module.app_settings is not None:
                theme = app_settings_module.app_settings.central_area_color
                return QColor(
                    CENTRAL_AREA_BG_LIGHT if theme == "light" else CENTRAL_AREA_BG
                )
        except Exception:
            pass

        return QColor(CENTRAL_AREA_BG)

    def _calculate_full_row_rect(self, row: int) -> QRect:
        if not self._table_widget:
            return QRect()

        model = self._table_widget.model()
        if not model:
            return QRect()

        first_col = 0  # Incluir checkbox para cubrir barras verticales
        first_index = model.index(row, first_col)
        if not first_index.isValid():
            return QRect()

        first_rect = self._table_widget.visualRect(first_index)
        if not first_rect.isValid():
            return QRect()
        # Hover termina en columna 3 (Fecha), SIN incluir columna 4 (Estado)
        last_col = 3
        last_index = model.index(row, last_col)

        if not last_index.isValid():
            return first_rect

        last_rect = self._table_widget.visualRect(last_index)

        if not last_rect.isValid():
            return first_rect

        # Calculate the full row rectangle from column 1 to end of column 3
        row_left = first_rect.left()
        row_top = first_rect.top()
        row_width = last_rect.right() - row_left
        row_height = first_rect.height()

        return QRect(row_left, row_top, row_width, row_height)
