"""
EmailSendPanel - Integrated panel for email sending.

Panel that appears to the right of FileViewContainer, like Finder preview.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt, QMimeData, QUrl, QPoint, QSize, Signal
from PySide6.QtGui import QColor, QDrag, QIcon, QMouseEvent
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
from app.models.email_session import EmailSession
from app.services.email_history_service import EmailHistoryService
from app.services.icon_service import IconService
from app.services.icon_render_service import IconRenderService
from app.ui.widgets.drag_preview_helper import create_multi_file_preview

logger = get_logger(__name__)

LIST_ROW_ICON_SIZE = QSize(28, 28)


class EmailFileListWidget(QListWidget):
    """QListWidget with custom drag handling for email files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_handler = None
    
    def set_drag_handler(self, handler):
        """Set custom drag handler function."""
        self._drag_handler = handler
    
    def startDrag(self, supported_actions: Qt.DropActions) -> None:
        """Override startDrag to use custom handler."""
        if self._drag_handler:
            self._drag_handler(supported_actions)
        else:
            super().startDrag(supported_actions)


class EmailSendPanel(QWidget):
    """Integrated panel for email sending, appears to the right of FileViewContainer."""
    
    # Signal emitted when close button is clicked
    close_requested = Signal()
    
    def __init__(
        self,
        current_session: EmailSession,
        history_service: EmailHistoryService,
        parent: Optional[QWidget] = None,
        icon_service: Optional[IconService] = None
    ):
        """
        Initialize email send panel.
        
        Args:
            current_session: Current email session to display.
            history_service: EmailHistoryService instance.
            parent: Parent widget.
            icon_service: IconService instance for file icons.
        """
        super().__init__(parent)
        self._current_session = current_session
        self._history_service = history_service
        self._icon_service = icon_service or IconService()
        self._temporary_history: List[EmailSession] = []
        
        # Add current session to temporary history
        self._temporary_history.append(current_session)
        
        self._setup_ui()
        self._load_temporary_history()
    
    def _setup_ui(self) -> None:
        """Build the panel UI."""
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        
        # Set background color to match FileViewContainer
        # Usar objectName para evitar que afecte a QTableWidget hijos
        self.setObjectName("EmailSendPanel")
        self.setStyleSheet("""
            QWidget#EmailSendPanel {
                background-color: #1A1D22;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Current selection section with close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        current_label = QLabel("Archivos preparados para enviar")
        current_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #e6edf3;")
        header_layout.addWidget(current_label)
        
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
        
        self._current_files_list = EmailFileListWidget()
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
        """)
        self._current_files_list.setAcceptDrops(False)  # No aceptar drops, solo drag
        self._current_files_list.setDragEnabled(True)
        self._current_files_list.setDefaultDropAction(Qt.DropAction.CopyAction)
        self._current_files_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        # Set custom drag handler
        self._current_files_list.set_drag_handler(self._start_drag_files)
        self._populate_current_files()
        layout.addWidget(self._current_files_list)
        
        open_folder_btn = QPushButton("Abrir carpeta para enviar")
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
        
        # Separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #2A2E36;")
        layout.addWidget(separator)
        
        # Recent history section
        history_label = QLabel("Historial reciente")
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
        """)
        self._history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        layout.addWidget(self._history_list, 1)
    
    def _populate_current_files(self) -> None:
        """Populate current files list with icons."""
        self._current_files_list.clear()
        
        # Set icon size for list widget (QListWidget needs this to display icons)
        self._current_files_list.setIconSize(LIST_ROW_ICON_SIZE)
        
        for file_path in self._current_session.file_paths:
            file_name = os.path.basename(file_path)
            
            # Get file icon FIRST, before creating item
            icon = self._get_file_icon(file_path)
            if not icon or icon.isNull():
                # Fallback: try to get icon directly from service
                try:
                    icon = self._icon_service.get_file_icon(file_path, LIST_ROW_ICON_SIZE)
                except Exception as e:
                    logger.debug(f"Failed to get fallback icon for {file_path}: {e}")
                    icon = None
            
            # Create item with icon if available
            if icon and not icon.isNull():
                item = QListWidgetItem(icon, file_name)
            else:
                item = QListWidgetItem(file_name)
            
            item.setToolTip(file_path)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self._current_files_list.addItem(item)
    
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
    
    def _start_drag_files(self, supported_actions: Qt.DropActions) -> None:
        """Handle drag start - drag files from temp folder to email client."""
        selected_items = self._current_files_list.selectedItems()
        if not selected_items:
            # If nothing selected, use current item
            current_item = self._current_files_list.currentItem()
            if current_item:
                selected_items = [current_item]
            else:
                return
        
        # Get file paths from temp folder
        file_paths = []
        for item in selected_items:
            original_path = item.data(Qt.ItemDataRole.UserRole)
            if original_path:
                # Use file from temp folder, not original
                file_name = os.path.basename(original_path)
                temp_file_path = os.path.join(self._current_session.temp_folder_path, file_name)
                if os.path.exists(temp_file_path):
                    file_paths.append(temp_file_path)
        
        if not file_paths:
            return
        
        # Create drag operation
        drag = QDrag(self._current_files_list)
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(path) for path in file_paths]
        mime_data.setUrls(urls)
        drag.setMimeData(mime_data)
        
        # Create preview pixmap
        preview_pixmap = create_multi_file_preview(file_paths, self._icon_service, QSize(48, 48))
        if not preview_pixmap.isNull():
            drag.setPixmap(preview_pixmap)
            hot_spot = QPoint(preview_pixmap.width() // 2, preview_pixmap.height() // 2)
            drag.setHotSpot(hot_spot)
        
        # Execute drag - CopyAction only (for email attachment)
        drag.exec(Qt.DropAction.CopyAction)
    
    def _load_temporary_history(self) -> None:
        """Load temporary history (max 5 entries, excluding current)."""
        try:
            # Get recent sessions from persistent history
            recent_sessions = self._history_service.get_recent_sessions(limit=5)
            
            # Filter out current session
            self._temporary_history = [
                s for s in recent_sessions
                if s.temp_folder_path != self._current_session.temp_folder_path
            ]
            
            # Limit to 4 more entries (current is already shown separately)
            self._temporary_history = self._temporary_history[:4]
            
            # Populate history list with files and icons
            self._history_list.clear()
            for session in self._temporary_history:
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
            logger.error(f"Failed to load temporary history: {e}", exc_info=True)
    
    def _on_open_current_folder(self) -> None:
        """Open current session's temporary folder."""
        self._open_folder(self._current_session.temp_folder_path)
    
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
                "La carpeta temporal ya no está disponible."
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
        """Refresh panel content."""
        self._load_temporary_history()

