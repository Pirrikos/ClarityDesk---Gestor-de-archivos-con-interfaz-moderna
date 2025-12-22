import os
import platform
import subprocess
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QWidget

from app.core.logger import get_logger

logger = get_logger(__name__)


def open_folder_in_system_manager(folder_path: str, parent_widget: Optional[QWidget] = None) -> None:
    if not os.path.exists(folder_path):
        QMessageBox.information(
            parent_widget,
            "Carpeta no disponible",
            "La carpeta temporal ya no está disponible."
        )
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
        QMessageBox.warning(
            parent_widget,
            "Error",
            f"No se pudo abrir la carpeta:\n{folder_path}"
        )

