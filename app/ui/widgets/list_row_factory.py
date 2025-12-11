"""
ListRowFactory - Factory functions for creating list view table cells.

Pure functions that create table items and widgets for list view rows.
"""

import os
from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QCheckBox, QTableWidgetItem, QVBoxLayout, QWidget

from app.services.icon_service import IconService
from app.ui.widgets.list_checkbox import CustomCheckBox
from app.ui.widgets.list_state_cell import ListStateCell


def create_checkbox_cell(
    file_path: str,
    is_checked: bool,
    on_state_changed: Callable[[str, int], None]
) -> QWidget:
    """
    Create checkbox widget container for column 0.
    
    Args:
        file_path: File path for this row.
        is_checked: Whether checkbox should be checked.
        on_state_changed: Callback for checkbox state changes.
    
    Returns:
        Container widget with checkbox.
    """
    checkbox = CustomCheckBox()
    checkbox.setText("")
    checkbox.setChecked(is_checked)
    checkbox.stateChanged.connect(
        lambda state, path=file_path: on_state_changed(path, state)
    )
    return _create_checkbox_container(checkbox)


def _create_checkbox_container(checkbox: QCheckBox) -> QWidget:
    """Create container widget for checkbox alignment."""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(checkbox)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    checkbox.setStyleSheet("""
        QCheckBox {
            padding: 0px;
            margin: 0px;
            margin-top: 5px;
        }
        QCheckBox::indicator {
            margin: 0px;
        }
    """)
    container.setMinimumSize(60, 56)
    container.setMaximumSize(60, 56)
    return container


def create_name_cell(
    file_path: str,
    icon_service: IconService,
    font: QFont
) -> QTableWidgetItem:
    """
    Create name item with icon for column 1.
    
    Args:
        file_path: Full path to file.
        icon_service: Service for getting file icons.
        font: Font to apply to item.
    
    Returns:
        Table widget item with filename and icon.
    """
    filename = os.path.basename(file_path)
    name_item = QTableWidgetItem(filename)
    name_item.setFont(font)
    icon = _get_file_icon(file_path, icon_service)
    if icon:
        name_item.setIcon(icon)
    return name_item


def _get_file_icon(file_path: str, icon_service: IconService) -> Optional[QIcon]:
    """Get file icon for list view."""
    pixmap = icon_service.get_file_preview_list(file_path, QSize(28, 28))
    if not pixmap.isNull():
        return QIcon(pixmap)
    return icon_service.get_file_icon(file_path, QSize(28, 28))


def create_extension_cell(file_path: str, font: QFont) -> QTableWidgetItem:
    """
    Create extension item for column 2.
    
    Args:
        file_path: Full path to file.
        font: Font to apply to item.
    
    Returns:
        Table widget item with file extension.
    """
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    ext_item = QTableWidgetItem(ext.upper() if ext else "")
    ext_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    ext_item.setFont(font)
    return ext_item


def create_date_cell(file_path: str, font: QFont) -> QTableWidgetItem:
    """
    Create modified date item for column 3.
    
    Args:
        file_path: Full path to file.
        font: Font to apply to item.
    
    Returns:
        Table widget item with modification date.
    """
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
    """
    Create state widget for column 4.
    
    Args:
        state: State constant or None if no state.
        font: Font (not used, kept for compatibility).
    
    Returns:
        Widget with colored bar and state text.
    """
    state_widget = ListStateCell(state)
    return state_widget

