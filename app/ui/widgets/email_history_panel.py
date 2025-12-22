"""
EmailHistoryPanel - Collapsible side panel for email history.

Shows persistent email sending history with expandable entries.
"""

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
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

logger = get_logger(__name__)


class EmailHistoryPanel(QWidget):
    """Collapsible panel showing persistent email sending history."""
    
    def __init__(
        self,
        history_service: EmailHistoryService,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize email history panel.
        
        Args:
            history_service: EmailHistoryService instance.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._history_service = history_service
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self) -> None:
        """Build the panel UI."""
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Historial de envíos")
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
        
        # History list
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
        
        # Empty state
        self._empty_label = QLabel("No hay historial de envíos")
        self._empty_label.setStyleSheet("color: #8e8e93; padding: 20px;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)
    
    def _load_history(self) -> None:
        """Load and display email history."""
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
            logger.error(f"Failed to load email history: {e}", exc_info=True)
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on history item - open folder."""
        session = item.data(Qt.ItemDataRole.UserRole)
        if session and isinstance(session, EmailSession):
            self._open_folder(session.temp_folder_path)
    
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
        """Refresh history display."""
        self._load_history()
    
    def showEvent(self, event) -> None:
        """Handle show event - refresh history when shown."""
        super().showEvent(event)
        self._load_history()

