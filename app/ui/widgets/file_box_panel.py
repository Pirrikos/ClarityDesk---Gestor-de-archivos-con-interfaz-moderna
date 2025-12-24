import os
from typing import List, Optional

from PySide6.QtCore import Qt, QMimeData, QUrl, QPoint, QSize, Signal
from PySide6.QtGui import QDrag, QMouseEvent
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
from app.core.constants import FILE_BOX_BORDER
from app.ui.widgets.file_box_styles import (
    get_file_box_panel_stylesheet,
    get_file_box_header_stylesheet,
    get_file_box_body_stylesheet,
    get_file_box_list_stylesheet,
    get_file_box_button_stylesheet,
    get_file_box_close_button_stylesheet,
    get_file_box_label_stylesheet,
    get_file_box_primary_button_stylesheet,
)
from app.services.file_box_utils import create_date_header_item, group_sessions_by_date
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
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - replicate grid view selection behavior without breaking drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item:
                modifiers = event.modifiers()
                
                # Control+Click: Qt maneja el toggle correctamente con ExtendedSelection
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    super().mousePressEvent(event)
                    return
                
                # Click normal: si el item ya está seleccionado y hay múltiples seleccionados,
                # mantener la selección (comportamiento del grid view para multi-drag)
                if item.isSelected() and len(self.selectedItems()) > 1:
                    # Guardar selección actual antes de que Qt la modifique
                    selected_items = list(self.selectedItems())
                    # Permitir que Qt procese el evento (necesario para drag)
                    super().mousePressEvent(event)
                    # Restaurar selección múltiple inmediatamente después
                    for selected_item in selected_items:
                        selected_item.setSelected(True)
                    self.setCurrentItem(item)
                    return
        
        # Comportamiento estándar para todos los demás casos
        super().mousePressEvent(event)
    
    def startDrag(self, supported_actions: Qt.DropActions) -> None:
        if self._drag_handler:
            self._drag_handler(supported_actions)
        else:
            super().startDrag(supported_actions)


class FileBoxPanel(QWidget):
    """Integrated panel for file box (files in use), appears to the right of FileViewContainer."""
    
    close_requested = Signal()
    minimize_requested = Signal()
    file_open_requested = Signal(str)
    
    def __init__(
        self,
        current_session: Optional[FileBoxSession] = None,
        history_service: Optional[FileBoxHistoryService] = None,
        parent: Optional[QWidget] = None,
        icon_service: Optional[IconService] = None
    ):
        super().__init__(parent)
        self._current_session = current_session
        self._history_service = history_service or FileBoxHistoryService()
        self._icon_service = icon_service or IconService()
        
        self._setup_ui()
        if self._current_session:
            self._load_temporary_history()
        else:
            self._current_files_list.clear()
            self._history_list.clear()
    
    def _setup_ui(self) -> None:
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        
        self.setObjectName("FileBoxPanel")
        self.setStyleSheet(get_file_box_panel_stylesheet("FileBoxPanel"))
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header_widget = QWidget()
        header_widget.setObjectName("FileBoxHeader")
        header_widget.setFixedHeight(44)
        header_widget.setStyleSheet(get_file_box_header_stylesheet("FileBoxHeader"))
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 0, 12, 0)
        header_layout.setSpacing(8)
        
        current_label = QLabel("File Box")
        current_label.setStyleSheet(get_file_box_label_stylesheet())
        header_layout.addWidget(current_label)
        
        header_layout.addStretch()
        
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(24, 24)
        minimize_btn.setStyleSheet(get_file_box_button_stylesheet())
        minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        minimize_btn.setToolTip("Minimizar")
        minimize_btn.clicked.connect(self.minimize_requested.emit)
        header_layout.addWidget(minimize_btn)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(get_file_box_close_button_stylesheet())
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Cerrar")
        close_btn.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header_widget)
        
        body_widget = QWidget()
        body_widget.setObjectName("FileBoxBody")
        body_widget.setStyleSheet(get_file_box_body_stylesheet("FileBoxBody"))
        
        body_layout = QVBoxLayout(body_widget)
        body_layout.setSpacing(16)
        body_layout.setContentsMargins(16, 16, 16, 16)
        
        current_label = QLabel("Archivos en uso")
        current_label.setStyleSheet(get_file_box_label_stylesheet())
        body_layout.addWidget(current_label)
        
        self._current_files_list = FileBoxFileListWidget()
        self._current_files_list.setStyleSheet(get_file_box_list_stylesheet(min_height=120))
        self._current_files_list.setAcceptDrops(False)
        self._current_files_list.setDragEnabled(True)
        self._current_files_list.setDefaultDropAction(Qt.DropAction.CopyAction)
        self._current_files_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._current_files_list.set_drag_handler(self._start_drag_files)
        self._current_files_list.itemDoubleClicked.connect(self._on_current_file_double_clicked)
        self._populate_current_files()
        body_layout.addWidget(self._current_files_list)
        
        open_folder_btn = QPushButton("Abrir carpeta")
        open_folder_btn.setStyleSheet(get_file_box_primary_button_stylesheet())
        open_folder_btn.clicked.connect(self._on_open_current_folder)
        body_layout.addWidget(open_folder_btn)
        
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {FILE_BOX_BORDER};")
        body_layout.addWidget(separator)
        
        history_label = QLabel("Historial")
        history_label.setStyleSheet(get_file_box_label_stylesheet() + " margin-top: 8px;")
        body_layout.addWidget(history_label)
        
        self._history_list = QListWidget()
        self._history_list.setIconSize(LIST_ROW_ICON_SIZE)
        self._history_list.setStyleSheet(get_file_box_list_stylesheet())
        self._history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        body_layout.addWidget(self._history_list, 1)
        
        layout.addWidget(body_widget, 1)
    
    def _populate_current_files(self) -> None:
        self._current_files_list.clear()
        self._current_files_list.setIconSize(LIST_ROW_ICON_SIZE)
        
        if not self._current_session:
            return
        
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
    
    def get_current_session(self) -> Optional[FileBoxSession]:
        """Get the current active session."""
        return self._current_session
    
    def set_session(self, session: Optional[FileBoxSession]) -> None:
        """Set or update the current session."""
        self._current_session = session
        if session:
            self._populate_current_files()
            self._load_temporary_history()
        else:
            self._current_files_list.clear()
            self._history_list.clear()
    
    def add_files_to_session(self, new_file_paths: List[str]) -> None:
        """Add files to the current session and refresh the UI."""
        from datetime import datetime
        
        existing_paths = set(self._current_session.file_paths)
        for file_path in new_file_paths:
            if file_path not in existing_paths:
                self._current_session.file_paths.append(file_path)
        
        self._current_session.timestamp = datetime.now()
        self._populate_current_files()
    
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
            from app.services.file_box_utils import populate_history_list
            
            recent_sessions = self._history_service.get_recent_sessions(limit=5)
            
            temporary_history = [
                s for s in recent_sessions
                if s.temp_folder_path != self._current_session.temp_folder_path
            ]
            
            temporary_history = temporary_history[:4]
            populate_history_list(self._history_list, temporary_history, self._icon_service)
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}", exc_info=True)
    
    def _on_open_current_folder(self) -> None:
        open_folder_in_system_manager(self._current_session.temp_folder_path, self)
    
    def _on_current_file_double_clicked(self, item: QListWidgetItem) -> None:
        original_path = item.data(Qt.ItemDataRole.UserRole)
        if not original_path or not self._current_session:
            return
        
        file_name = os.path.basename(original_path)
        temp_file_path = os.path.join(self._current_session.temp_folder_path, file_name)
        
        if os.path.exists(temp_file_path):
            self.file_open_requested.emit(temp_file_path)
    
    def get_selected_files(self) -> list[str]:
        """Obtener rutas temporales de archivos seleccionados en la lista actual."""
        if not self._current_session:
            return []
        
        selected_items = self._current_files_list.selectedItems()
        if not selected_items:
            current_item = self._current_files_list.currentItem()
            if current_item:
                selected_items = [current_item]
            else:
                return []
        
        file_paths = []
        for item in selected_items:
            original_path = item.data(Qt.ItemDataRole.UserRole)
            if original_path:
                file_name = os.path.basename(original_path)
                temp_file_path = os.path.join(self._current_session.temp_folder_path, file_name)
                if os.path.exists(temp_file_path):
                    file_paths.append(temp_file_path)
        
        return file_paths
    
    def _on_history_item_double_clicked(self, item: QListWidgetItem) -> None:
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path:
            open_folder_in_system_manager(folder_path, self)
    
    def refresh(self) -> None:
        self._load_temporary_history()

