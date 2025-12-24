"""
ListRowFactory - Factory functions for creating list view table cells.

Pure functions that create table items and widgets for list view rows.
"""

import os
from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QTableWidgetItem, QVBoxLayout, QWidget

from app.services.icon_service import IconService
from app.services.icon_render_service import IconRenderService
from app.ui.widgets.list_checkbox import CustomCheckBox
from app.ui.widgets.list_state_cell import ListStateCell

LIST_ROW_ICON_SIZE = QSize(28, 28)


def create_checkbox_cell(
    file_path: str,
    is_checked: bool,
    on_state_changed: Callable[[str, int], None]
) -> QWidget:
    checkbox = CustomCheckBox()
    checkbox.setText("")
    checkbox.setChecked(is_checked)
    checkbox.setFixedSize(59, 56)  # 15px + 44px de margen izquierdo
    checkbox.stateChanged.connect(
        lambda state, path=file_path: on_state_changed(path, state)
    )
    return checkbox


def _create_centered_container(widget: QWidget) -> QWidget:
    """Create a centered container widget for list view cells."""
    container = QWidget()
    container.setStyleSheet("QWidget { background-color: transparent; border: none; }")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(widget)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return container


def create_name_cell(
    file_path: str,
    icon_service: IconService,
    font: QFont
) -> QTableWidgetItem:
    filename = os.path.basename(file_path)
    name_item = QTableWidgetItem(filename)
    name_item.setFont(font)
    icon = _get_file_icon(file_path, icon_service)
    if icon:
        name_item.setIcon(icon)
    return name_item


def _get_file_icon(file_path: str, icon_service: IconService) -> Optional[QIcon]:
    render_service = IconRenderService(icon_service)
    pixmap = render_service.get_file_preview_list(file_path, LIST_ROW_ICON_SIZE)
    if not pixmap.isNull():
        return QIcon(pixmap)
    return icon_service.get_file_icon(file_path, LIST_ROW_ICON_SIZE)


def create_extension_cell(file_path: str, font: QFont) -> QTableWidgetItem:
    """Create extension cell, handling folders and files with dots in name."""
    filename = os.path.basename(file_path)
    
    # Si es una carpeta, no tiene extensión
    if os.path.isdir(file_path):
        ext_item = QTableWidgetItem("")
    else:
        # Para archivos, detectar solo extensiones reales (ej: .pdf, .txt)
        # No confundir puntos en el nombre (ej: "1. PLATON") con extensiones
        _, ext = os.path.splitext(filename)
        # Solo considerar extensión si tiene formato válido (al menos 2 chars, alfanumérica)
        if ext and len(ext) >= 2 and ext[1:].replace('_', '').isalnum():
            ext_item = QTableWidgetItem(ext.upper())
        else:
            ext_item = QTableWidgetItem("")
    
    ext_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    ext_item.setFont(font)
    return ext_item


def create_date_cell(file_path: str, font: QFont) -> QTableWidgetItem:
    try:
        mtime = os.path.getmtime(file_path)
        dt = datetime.fromtimestamp(mtime)
        date_str = dt.strftime("%Y-%m-%d %H:%M")
        date_item = QTableWidgetItem(date_str)
    except (OSError, ValueError):
        date_item = QTableWidgetItem("")
    date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    date_item.setFont(font)
    return date_item


def create_state_cell(state: Optional[str], font: QFont) -> QWidget:
    """Create state cell widget centered vertically in the row."""
    state_widget = ListStateCell(state)
    return _create_centered_container(state_widget)

