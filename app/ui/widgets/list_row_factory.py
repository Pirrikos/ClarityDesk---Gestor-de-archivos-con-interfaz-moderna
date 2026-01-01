"""
ListRowFactory - Factory functions for creating list view table cells.

Pure functions that create table items and widgets for list view rows.
"""

import os
from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QTableWidgetItem, QVBoxLayout, QWidget

from app.services.icon_service import IconService
from app.services.icon_render_service import IconRenderService
from app.ui.widgets.list_checkbox import CustomCheckBox
from app.ui.widgets.list_state_cell import ListStateCell
from app.ui.widgets.list_state_delegate import STATE_ROLE

LIST_ROW_ICON_SIZE = QSize(28, 28)
# Offset para alinear widget de estado con el título del header
# Compensa diferencia entre padding de items (20px) y header (10px)
STATE_CELL_LEFT_OFFSET = -30


def create_checkbox_cell(
    file_path: str,
    is_checked: bool,
    on_state_changed: Callable[[str, int], None],
    parent: Optional[QWidget] = None
) -> QWidget:
    checkbox = CustomCheckBox(parent)
    checkbox.setText("")
    checkbox.setChecked(is_checked)
    checkbox.setFixedSize(15, 56)  # Ancho mínimo: 11px indicador + 4px margen
    checkbox.stateChanged.connect(
        lambda state, path=file_path: on_state_changed(path, state)
    )
    # Envolver en contenedor centrado para alinearlo con el header
    return _create_centered_container(checkbox, parent)


def _create_centered_container(widget: QWidget, parent: Optional[QWidget] = None) -> QWidget:
    """Create a centered container widget for list view cells."""
    container = QWidget(parent)
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
    font: QFont,
    workspace_name: Optional[str] = None
) -> QTableWidgetItem:
    filename = os.path.basename(file_path)

    name, ext = os.path.splitext(filename)

    # Quitar extensión SOLO si es una extensión real
    if ext and len(ext) >= 2 and ext[1:].replace('_', '').isalnum():
        display_name = name
    else:
        display_name = filename

    # Si navegamos por estado y hay workspace_name, agregarlo al texto
    # El ListNameDelegate se encargará de renderizar con color gris
    if workspace_name:
        display_name = f"{display_name} (Workspace: {workspace_name})"

    name_item = QTableWidgetItem()
    name_item.setText(display_name)
    # Sorting usa el texto por defecto; ya es estable en "YYYY-MM-DD" y nombre
    name_item.setFont(font)
    icon = _get_file_icon(file_path, icon_service)
    if icon:
        name_item.setIcon(icon)
    return name_item


def _is_valid_pixmap(pixmap) -> bool:
    """Validar pixmap según R16: no nulo, no 0x0, válido visualmente."""
    if not pixmap or pixmap.isNull():
        return False
    if pixmap.width() <= 0 or pixmap.height() <= 0:
        return False
    # Verificar que tiene contenido visual (no completamente transparente)
    if pixmap.hasAlphaChannel():
        # Verificar que al menos algunos píxeles son visibles
        return True
    return True


def _get_file_icon(file_path: str, icon_service: IconService) -> Optional[QIcon]:
    """Obtener icono con validación estricta según R16."""
    render_service = IconRenderService(icon_service)
    pixmap = render_service.get_file_preview_list(file_path, LIST_ROW_ICON_SIZE)
    
    # R16: Validar pixmap antes de crear QIcon
    if _is_valid_pixmap(pixmap):
        return QIcon(pixmap)
    
    # Fallback inmediato si pixmap inválido
    folder_icon = icon_service.get_folder_icon(file_path, LIST_ROW_ICON_SIZE) if os.path.isdir(file_path) else icon_service.get_file_icon(file_path, LIST_ROW_ICON_SIZE)
    
    # Validar icono del fallback antes de retornar
    if folder_icon and not folder_icon.isNull():
        fallback_pixmap = folder_icon.pixmap(LIST_ROW_ICON_SIZE)
        if _is_valid_pixmap(fallback_pixmap):
            return folder_icon
    
    # Último fallback: icono genérico
    return None


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
    
    # Sorting por extensión usa el texto mostrado
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
    # Sorting por fecha usa el texto "YYYY-MM-DD HH:MM"
    date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    date_item.setFont(font)
    return date_item


def create_state_item(state: Optional[str], font: QFont) -> QTableWidgetItem:
    """Crear item de la columna Estado con datos para el delegate."""
    # DEBUG: Log para diagnosticar estados
    from app.core.logger import get_logger
    logger = get_logger(__name__)
    if state:
        logger.debug(f"create_state_item: state='{state}' (type={type(state).__name__})")

    item = QTableWidgetItem("")
    item.setData(STATE_ROLE, state)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFont(font)
    return item
