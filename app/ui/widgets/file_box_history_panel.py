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
from app.services.file_box_icon_helper import LIST_ROW_ICON_SIZE
from app.ui.widgets.file_box_styles import (
    get_file_box_panel_stylesheet,
    get_file_box_header_stylesheet,
    get_file_box_body_stylesheet,
    get_file_box_list_stylesheet,
    get_file_box_close_button_stylesheet,
    get_file_box_label_stylesheet,
)
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
        self.setStyleSheet(get_file_box_panel_stylesheet("FileBoxHistoryPanel"))
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header_widget = QWidget()
        header_widget.setObjectName("FileBoxHistoryHeader")
        header_widget.setFixedHeight(44)
        header_widget.setStyleSheet(get_file_box_header_stylesheet("FileBoxHistoryHeader"))
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 0, 12, 0)
        header_layout.setSpacing(8)
        
        title_label = QLabel("Historial")
        title_label.setStyleSheet(get_file_box_label_stylesheet())
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(get_file_box_close_button_stylesheet())
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Cerrar")
        close_btn.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header_widget)
        
        body_widget = QWidget()
        body_widget.setObjectName("FileBoxHistoryBody")
        body_widget.setStyleSheet(get_file_box_body_stylesheet("FileBoxHistoryBody"))
        
        body_layout = QVBoxLayout(body_widget)
        body_layout.setSpacing(16)
        body_layout.setContentsMargins(16, 16, 16, 16)
        
        self._history_list = QListWidget()
        self._history_list.setIconSize(LIST_ROW_ICON_SIZE)
        self._history_list.setStyleSheet(get_file_box_list_stylesheet())
        self._history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        body_layout.addWidget(self._history_list, 1)
        
        layout.addWidget(body_widget, 1)
    
    def _load_history(self) -> None:
        try:
            from app.services.file_box_utils import populate_history_list
            
            recent_sessions = self._history_service.get_recent_sessions(limit=50)
            populate_history_list(self._history_list, recent_sessions, self._icon_service)
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}", exc_info=True)
    
    def _on_history_item_double_clicked(self, item: QListWidgetItem) -> None:
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path:
            open_folder_in_system_manager(folder_path, self)
    
    def refresh(self) -> None:
        self._load_history()

