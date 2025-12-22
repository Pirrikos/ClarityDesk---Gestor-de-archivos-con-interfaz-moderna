import os
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidgetItem

from app.core.logger import get_logger
from app.models.file_box_session import FileBoxSession
from app.services.file_box_utils import format_date_spanish
from app.services.icon_service import IconService
from app.services.icon_render_service import IconRenderService

logger = get_logger(__name__)

LIST_ROW_ICON_SIZE = QSize(28, 28)


def get_file_box_icon(file_path: str, icon_service: IconService, icon_size: QSize = LIST_ROW_ICON_SIZE) -> Optional[QIcon]:
    try:
        render_service = IconRenderService(icon_service)
        pixmap = render_service.get_file_preview_list(file_path, icon_size)
        if pixmap and not pixmap.isNull():
            return QIcon(pixmap)
        
        icon = icon_service.get_file_icon(file_path, icon_size)
        if icon and not icon.isNull():
            return icon
        return None
    except Exception as e:
        logger.debug(f"Failed to get icon for {file_path}: {e}")
        return None


def create_history_list_item(
    file_path: str, 
    session: FileBoxSession, 
    icon_service: IconService
) -> QListWidgetItem:
    file_name = os.path.basename(file_path)
    icon = get_file_box_icon(file_path, icon_service)
    
    if icon and not icon.isNull():
        item = QListWidgetItem(icon, file_name)
    else:
        item = QListWidgetItem(file_name)
    
    item.setToolTip(f"{file_path}\nFecha: {format_date_spanish(session.timestamp)}")
    item.setData(Qt.ItemDataRole.UserRole, session.temp_folder_path)
    return item

