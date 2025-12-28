import os
import platform
import subprocess
from typing import Optional

from PySide6.QtWidgets import QWidget

from app.core.logger import get_logger
from app.ui.windows.error_dialog import ErrorDialog

logger = get_logger(__name__)


def open_folder_in_system_manager(folder_path: str, parent_widget: Optional[QWidget] = None) -> None:
    if not os.path.exists(folder_path):
        error_dialog = ErrorDialog(
            parent=parent_widget,
            title="Carpeta no disponible",
            message="La carpeta temporal ya no está disponible.",
            is_warning=True
        )
        error_dialog.exec()
        return
    
    try:
        if os.name == 'nt':
            os.startfile(folder_path)  # type: ignore[attr-defined]
        elif platform.system() == 'Darwin':
            subprocess.run(['open', folder_path])
        else:
            subprocess.run(['xdg-open', folder_path])
    except Exception as e:
        logger.error(f"Failed to open folder {folder_path}: {e}")
        error_dialog = ErrorDialog(
            parent=parent_widget,
            title="Error",
            message=f"No se pudo abrir la carpeta:\n{folder_path}",
            is_warning=True
        )
        error_dialog.exec()

