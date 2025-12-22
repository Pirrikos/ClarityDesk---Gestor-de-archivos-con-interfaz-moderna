from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.logger import get_logger
from app.services.file_box_history_service import FileBoxHistoryService
from app.services.file_box_icon_helper import LIST_ROW_ICON_SIZE, create_history_list_item
from app.services.file_box_utils import FILE_BOX_SCROLLBAR_STYLES, create_date_header_item, group_sessions_by_date
from app.services.icon_service import IconService
from app.ui.utils.file_box_ui_utils import open_folder_in_system_manager

logger = get_logger(__name__)


class FileBoxHistoryPanel(QWidget):
    """Panel showing only file box history, appears to the right of FileViewContainer."""
    
    close_requested = Signal()
    
    def __init__(
        self,
        history_service: FileBoxHistoryService,
        parent: Optional[QWidget] = None,
        icon_service: Optional[IconService] = None
    ):
        super().__init__(parent)
        self._history_service = history_service
        self._icon_service = icon_service or IconService()
        
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self) -> None:
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        
        self.setObjectName("FileBoxHistoryPanel")
        self.setStyleSheet("""
            QWidget#FileBoxHistoryPanel {
                background-color: #1A1D22;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        title_label = QLabel("Historial")
        title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #e6edf3;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
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
            """ + FILE_BOX_SCROLLBAR_STYLES + """
        """)
        self._history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        layout.addWidget(self._history_list, 1)
    
    def _load_history(self) -> None:
        try:
            recent_sessions = self._history_service.get_recent_sessions(limit=50)
            
            grouped_sessions = group_sessions_by_date(recent_sessions)
            sorted_dates = sorted(grouped_sessions.keys(), reverse=True)
            
            self._history_list.clear()
            for date_key in sorted_dates:
                sessions_for_date = grouped_sessions[date_key]
                
                first_session = sessions_for_date[0]
                header_item = create_date_header_item(first_session.timestamp)
                self._history_list.addItem(header_item)
                
                for session in sessions_for_date:
                    for file_path in session.file_paths:
                        item = create_history_list_item(file_path, session, self._icon_service)
                        self._history_list.addItem(item)
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}", exc_info=True)
    
    def _on_history_item_double_clicked(self, item: QListWidgetItem) -> None:
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path:
            open_folder_in_system_manager(folder_path, self)
    
    def refresh(self) -> None:
        self._load_history()

