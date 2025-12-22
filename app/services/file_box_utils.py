from collections import defaultdict
from datetime import datetime

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QBrush
from PySide6.QtWidgets import QListWidgetItem

from app.models.file_box_session import FileBoxSession

SPANISH_DAYS = [
    "LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"
]

SPANISH_MONTHS = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def format_date_spanish(dt: datetime) -> str:
    """Format date as 'MARTES, 12 de Febrero 2024'."""
    day_name = SPANISH_DAYS[dt.weekday()]
    day = dt.day
    month_name = SPANISH_MONTHS[dt.month - 1]
    year = dt.year
    return f"{day_name}, {day} de {month_name} {year}"


def group_sessions_by_date(sessions: list[FileBoxSession]) -> dict[str, list[FileBoxSession]]:
    grouped = defaultdict(list)
    for session in sessions:
        date_key = session.timestamp.date().isoformat()
        grouped[date_key].append(session)
    return grouped


def create_date_header_item(date: datetime, font_size: int = 13) -> QListWidgetItem:
    date_text = format_date_spanish(date)
    header_item = QListWidgetItem(date_text)
    header_item.setFlags(Qt.ItemFlag.NoItemFlags)
    header_item.setData(Qt.ItemDataRole.UserRole + 1, "header")
    header_font = QFont()
    header_font.setWeight(QFont.Weight.DemiBold)
    header_font.setPointSize(font_size)
    header_item.setFont(header_font)
    header_item.setForeground(QBrush(QColor("rgba(255, 255, 255, 0.7)")))
    header_item.setSizeHint(QSize(0, 40))
    return header_item


FILE_BOX_SCROLLBAR_STYLES = """
    QScrollBar:vertical {
        background-color: transparent;
        width: 12px;
        margin: 0px;
        border: none;
    }
    QScrollBar::handle:vertical {
        background-color: rgba(255, 255, 255, 0.12);
        border-radius: 6px;
        min-height: 40px;
        margin: 2px 2px 2px 4px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: rgba(255, 255, 255, 0.22);
    }
    QScrollBar::handle:vertical:pressed {
        background-color: rgba(255, 255, 255, 0.30);
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
        border: none;
    }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QScrollBar:horizontal {
        background-color: transparent;
        height: 12px;
        margin: 0px;
        border: none;
    }
    QScrollBar::handle:horizontal {
        background-color: rgba(255, 255, 255, 0.12);
        border-radius: 6px;
        min-width: 40px;
        margin: 4px 2px 2px 2px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: rgba(255, 255, 255, 0.22);
    }
    QScrollBar::handle:horizontal:pressed {
        background-color: rgba(255, 255, 255, 0.30);
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
        border: none;
    }
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: transparent;
    }
"""

