from typing import Optional

from PySide6.QtCore import Qt
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
from app.models.file_box_session import FileBoxSession
from app.services.file_box_history_service import FileBoxHistoryService
from app.ui.utils.file_box_ui_utils import open_folder_in_system_manager

logger = get_logger(__name__)


class FileBoxHistoryPanelSidebar(QWidget):
    """Collapsible panel showing persistent file box history."""
    
    def __init__(
        self,
        history_service: FileBoxHistoryService,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._history_service = history_service
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self) -> None:
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Historial")
        title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                color: #8e8e93;
            }
            QPushButton:hover {
                background-color: #e5e5e7;
                color: #000000;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        self._history_list = QListWidget()
        self._history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e5e7;
                border-radius: 8px;
                padding: 4px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)
        self._history_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._history_list, 1)
        
        self._empty_label = QLabel("No hay historial")
        self._empty_label.setStyleSheet("color: #8e8e93; padding: 20px;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)
    
    def _load_history(self) -> None:
        try:
            sessions = self._history_service.get_recent_sessions(limit=50)
            
            self._history_list.clear()
            
            if not sessions:
                self._empty_label.show()
                return
            
            self._empty_label.hide()
            
            for session in sessions:
                timestamp_str = session.timestamp.strftime("%Y-%m-%d %H:%M")
                text = f"{timestamp_str}\n{session.file_count} archivo(s)"
                
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, session)
                item.setToolTip(f"Carpeta: {session.temp_folder_path}")
                self._history_list.addItem(item)
            
        except Exception as e:
            logger.error(f"Failed to load file box history: {e}", exc_info=True)
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        session = item.data(Qt.ItemDataRole.UserRole)
        if session and isinstance(session, FileBoxSession):
            open_folder_in_system_manager(session.temp_folder_path, self)
    
    def refresh(self) -> None:
        self._load_history()
    
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._load_history()

