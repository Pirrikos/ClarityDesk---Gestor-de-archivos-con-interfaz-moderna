"""
EmailHistoryOnlyPanel - Panel showing only email history.

Similar to EmailSendPanel but shows only history section, no current files.
"""

import os
from typing import Optional

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.logger import get_logger
from app.services.email_history_service import EmailHistoryService
from app.services.icon_service import IconService
from app.services.icon_render_service import IconRenderService

logger = get_logger(__name__)

LIST_ROW_ICON_SIZE = QSize(28, 28)


class EmailHistoryOnlyPanel(QWidget):
    """Panel showing only email history, appears to the right of FileViewContainer."""
    
    # Signal emitted when close button is clicked
    close_requested = Signal()
    
    def __init__(
        self,
        history_service: EmailHistoryService,
        parent: Optional[QWidget] = None,
        icon_service: Optional[IconService] = None
    ):
        """
        Initialize email history only panel.
        
        Args:
            history_service: EmailHistoryService instance.
            parent: Parent widget.
            icon_service: IconService instance for file icons.
        """
        super().__init__(parent)
        self._history_service = history_service
        self._icon_service = icon_service or IconService()
        
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self) -> None:
        """Build the panel UI."""
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        
        # Set background color to match FileViewContainer
        # Usar objectName para evitar que afecte a QTableWidget hijos
        self.setObjectName("EmailHistoryOnlyPanel")
        self.setStyleSheet("""
            QWidget#EmailHistoryOnlyPanel {
                background-color: #1A1D22;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        title_label = QLabel("Historial de envíos")
        title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #e6edf3;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Close button (X)
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                border-radius: 4px;
                font-size: 20px;
                font-weight: 300;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #252A31;
                color: #e6edf3;
            }
            QPushButton:pressed {
                background-color: #2A2E36;
            }
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # History list
        self._history_list = QListWidget()
        self._history_list.setIconSize(LIST_ROW_ICON_SIZE)
        self._history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #2A2E36;
                border-radius: 8px;
                padding: 4px;
                background-color: #1A1D22;
                color: #e6edf3;
            }
            QListWidget::item {
                padding: 6px 8px;
                border: none;
                color: #e6edf3;
                height: 32px;
            }
            QListWidget::item::icon {
                padding-right: 8px;
            }
            QListWidget::item:hover {
                background-color: #252A31;
            }
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
        """)
        self._history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        layout.addWidget(self._history_list, 1)
    
    def _load_history(self) -> None:
        """Load and display email history."""
        try:
            # Get all recent sessions (more than in temporary history)
            recent_sessions = self._history_service.get_recent_sessions(limit=50)
            
            # Populate history list with files and icons
            self._history_list.clear()
            for session in recent_sessions:
                timestamp_str = session.timestamp.strftime("%d/%m/%Y --%H:%M")
                
                # Add file items with icons, name and timestamp
                for file_path in session.file_paths:
                    file_name = os.path.basename(file_path)
                    
                    # Get file icon
                    icon = self._get_file_icon(file_path)
                    if not icon or icon.isNull():
                        # Fallback: try to get icon directly from service
                        try:
                            icon = self._icon_service.get_file_icon(file_path, LIST_ROW_ICON_SIZE)
                        except Exception as e:
                            logger.debug(f"Failed to get fallback icon for {file_path}: {e}")
                            icon = None
                    
                    # Create item text with filename and timestamp
                    item_text = f"{file_name} - {timestamp_str}"
                    
                    # Create item with icon if available
                    if icon and not icon.isNull():
                        item = QListWidgetItem(icon, item_text)
                    else:
                        item = QListWidgetItem(item_text)
                    
                    item.setToolTip(f"{file_path}\nFecha: {timestamp_str}")
                    item.setData(Qt.ItemDataRole.UserRole, session.temp_folder_path)
                    self._history_list.addItem(item)
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}", exc_info=True)
    
    def _get_file_icon(self, file_path: str) -> Optional[QIcon]:
        """Get icon for file, similar to list view."""
        try:
            render_service = IconRenderService(self._icon_service)
            # get_file_preview_list expects QSize
            pixmap = render_service.get_file_preview_list(file_path, LIST_ROW_ICON_SIZE)
            if pixmap and not pixmap.isNull():
                return QIcon(pixmap)
            # Fallback to direct icon service
            icon = self._icon_service.get_file_icon(file_path, LIST_ROW_ICON_SIZE)
            if icon and not icon.isNull():
                return icon
            return None
        except Exception as e:
            logger.debug(f"Failed to get icon for {file_path}: {e}")
            return None
    
    def _on_history_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Open folder from history item."""
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path:
            self._open_folder(folder_path)
    
    def _open_folder(self, folder_path: str) -> None:
        """
        Open folder in system file manager.
        
        Shows honest message if folder no longer exists.
        """
        if not os.path.exists(folder_path):
            QMessageBox.information(
                self,
                "Carpeta no disponible",
                "La carpeta temporal ya no está disponible. Es posible que el sistema operativo la haya limpiado."
            )
            return
        try:
            # Open folder in system file manager
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)  # type: ignore[attr-defined]
            else:
                import subprocess
                import platform
                if platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', folder_path])
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            logger.error(f"Failed to open folder {folder_path}: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo abrir la carpeta:\n{folder_path}"
            )
    
    def refresh(self) -> None:
        """Refresh history display."""
        self._load_history()

