import os
from typing import Optional

from PySide6.QtCore import Qt, QMimeData, QUrl, QPoint, QSize, Signal
from PySide6.QtGui import QDrag
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
from app.services.file_box_icon_helper import LIST_ROW_ICON_SIZE, create_history_list_item, get_file_box_icon
from app.services.file_box_utils import FILE_BOX_SCROLLBAR_STYLES, create_date_header_item, format_date_spanish, group_sessions_by_date
from app.services.icon_service import IconService
from app.ui.utils.file_box_ui_utils import open_folder_in_system_manager
from app.ui.widgets.drag_preview_helper import create_multi_file_preview

logger = get_logger(__name__)


class FileBoxFileListWidget(QListWidget):
    """QListWidget with custom drag handling for file box files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_handler = None
    
    def set_drag_handler(self, handler):
        self._drag_handler = handler
    
    def startDrag(self, supported_actions: Qt.DropActions) -> None:
        if self._drag_handler:
            self._drag_handler(supported_actions)
        else:
            super().startDrag(supported_actions)


class FileBoxPanel(QWidget):
    """Integrated panel for file box (files in use), appears to the right of FileViewContainer."""
    
    close_requested = Signal()
    
    def __init__(
        self,
        current_session: FileBoxSession,
        history_service: FileBoxHistoryService,
        parent: Optional[QWidget] = None,
        icon_service: Optional[IconService] = None
    ):
        super().__init__(parent)
        self._current_session = current_session
        self._history_service = history_service
        self._icon_service = icon_service or IconService()
        
        self._setup_ui()
        self._load_temporary_history()
    
    def _setup_ui(self) -> None:
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        
        self.setObjectName("FileBoxPanel")
        self.setStyleSheet("""
            QWidget#FileBoxPanel {
                background-color: #1A1D22;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        current_label = QLabel("Archivos en uso")
        current_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #e6edf3;")
        header_layout.addWidget(current_label)
        
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
        
        self._current_files_list = FileBoxFileListWidget()
        self._current_files_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #2A2E36;
                border-radius: 8px;
                padding: 4px;
                background-color: #1A1D22;
                min-height: 120px;
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
        self._current_files_list.setAcceptDrops(False)
        self._current_files_list.setDragEnabled(True)
        self._current_files_list.setDefaultDropAction(Qt.DropAction.CopyAction)
        self._current_files_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._current_files_list.set_drag_handler(self._start_drag_files)
        self._populate_current_files()
        layout.addWidget(self._current_files_list)
        
        open_folder_btn = QPushButton("Abrir carpeta")
        open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        open_folder_btn.clicked.connect(self._on_open_current_folder)
        layout.addWidget(open_folder_btn)
        
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #2A2E36;")
        layout.addWidget(separator)
        
        history_label = QLabel("Historial")
        history_label.setStyleSheet("font-weight: 600; font-size: 14px; margin-top: 8px; color: #e6edf3;")
        layout.addWidget(history_label)
        
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
    
    def _populate_current_files(self) -> None:
        self._current_files_list.clear()
        self._current_files_list.setIconSize(LIST_ROW_ICON_SIZE)
        
        for file_path in self._current_session.file_paths:
            file_name = os.path.basename(file_path)
            icon = get_file_box_icon(file_path, self._icon_service)
            
            if icon and not icon.isNull():
                item = QListWidgetItem(icon, file_name)
            else:
                item = QListWidgetItem(file_name)
            
            item.setToolTip(file_path)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self._current_files_list.addItem(item)
    
    def _start_drag_files(self, supported_actions: Qt.DropActions) -> None:
        selected_items = self._current_files_list.selectedItems()
        if not selected_items:
            current_item = self._current_files_list.currentItem()
            if current_item:
                selected_items = [current_item]
            else:
                return
        
        file_paths = []
        for item in selected_items:
            original_path = item.data(Qt.ItemDataRole.UserRole)
            if original_path:
                file_name = os.path.basename(original_path)
                temp_file_path = os.path.join(self._current_session.temp_folder_path, file_name)
                if os.path.exists(temp_file_path):
                    file_paths.append(temp_file_path)
        
        if not file_paths:
            return
        
        drag = QDrag(self._current_files_list)
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(path) for path in file_paths]
        mime_data.setUrls(urls)
        drag.setMimeData(mime_data)
        
        preview_pixmap = create_multi_file_preview(file_paths, self._icon_service, QSize(48, 48))
        if not preview_pixmap.isNull():
            drag.setPixmap(preview_pixmap)
            hot_spot = QPoint(preview_pixmap.width() // 2, preview_pixmap.height() // 2)
            drag.setHotSpot(hot_spot)
        
        drag.exec(Qt.DropAction.CopyAction)
    
    def _load_temporary_history(self) -> None:
        try:
            recent_sessions = self._history_service.get_recent_sessions(limit=5)
            
            temporary_history = [
                s for s in recent_sessions
                if s.temp_folder_path != self._current_session.temp_folder_path
            ]
            
            temporary_history = temporary_history[:4]
            
            grouped_sessions = group_sessions_by_date(temporary_history)
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
    
    def _on_open_current_folder(self) -> None:
        open_folder_in_system_manager(self._current_session.temp_folder_path, self)
    
    def _on_history_item_double_clicked(self, item: QListWidgetItem) -> None:
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path:
            open_folder_in_system_manager(folder_path, self)
    
    def refresh(self) -> None:
        self._load_temporary_history()

