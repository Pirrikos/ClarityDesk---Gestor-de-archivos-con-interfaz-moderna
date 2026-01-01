"""
ListNameDelegate - Delegate personalizado para renderizar la columna de nombre con información de workspace.

Extiende ListViewDelegate para mantener toda la funcionalidad visual (iconos, contenedores, hover)
y agrega renderizado de workspace en gris sutil (#6B6B6B).
"""

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QWidget

from app.ui.widgets.list_icon_delegate import ListViewDelegate


class ListNameDelegate(ListViewDelegate):
    """Delegate para renderizar la celda de nombre con texto de workspace en gris."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent, column_index=1)
        self._workspace_color = QColor("#6B6B6B")  # Subtle gray matching "Estados" sidebar

    def _draw_name_column(self, painter: QPainter, option, index, is_selected: bool) -> None:
        """Override to add workspace text in gray color."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        icon = index.data(Qt.ItemDataRole.DecorationRole)

        icon_size = self.ICON_SIZE_SELECTED if is_selected else self.ICON_SIZE_NORMAL

        # Draw icon (same as parent)
        if icon and isinstance(icon, QIcon):
            pixmap = icon.pixmap(icon_size)
            if not pixmap.isNull():
                painter.drawPixmap(self._calculate_icon_position(option, is_selected), pixmap)

        # Draw text with workspace in gray
        if text:
            text_x = option.rect.left() + self.MARGIN_LEFT + icon_size.width() + self.TEXT_OFFSET_X
            text_rect = QRect(
                text_x,
                option.rect.top(),
                option.rect.right() - text_x - 4,
                option.rect.height(),
            )

            # Check if text contains workspace info
            workspace_start = text.find(" (Workspace: ")

            if workspace_start == -1:
                # No workspace info, render normally
                painter.setPen(self.TEXT_COLOR)
                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    str(text),
                )
            else:
                # Split text into filename and workspace parts
                filename = text[:workspace_start]
                workspace_info = text[workspace_start:]

                fm = painter.fontMetrics()
                filename_width = fm.horizontalAdvance(filename)

                # Draw filename in default color
                painter.setPen(self.TEXT_COLOR)
                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    filename,
                )

                # Draw workspace info in gray
                workspace_rect = QRect(
                    text_x + filename_width,
                    text_rect.top(),
                    text_rect.width() - filename_width,
                    text_rect.height(),
                )
                painter.setPen(self._workspace_color)
                painter.drawText(
                    workspace_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    workspace_info,
                )
