"""
EmailSendWindow - Auxiliary window for email sending.

Non-modal, movable window showing current selection and temporary history.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer
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
from app.services.file_open_service import open_file_with_system

logger = get_logger(__name__)


class EmailSendWindow(QWidget):
    """Non-modal window for email sending with current selection and temporary history."""
    
    def __init__(
        self,
        current_session: EmailSession,
        history_service: EmailHistoryService,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize email send window.
        
        Args:
            current_session: Current email session to display.
            history_service: EmailHistoryService instance.
            parent: Parent widget (MainWindow).
        """
        super().__init__(parent)
        self._current_session = current_session
        self._history_service = history_service
        self._temporary_history: List[EmailSession] = []
        
        # Add current session to temporary history
        self._temporary_history.append(current_session)
        
        self._setup_ui()
        self._load_temporary_history()
        self._position_window()
    
    def _setup_ui(self) -> None:
        """Build the window UI."""
        self.setWindowTitle("Enviar por correo")
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        self.setMinimumHeight(400)
        self.setWindowModality(Qt.WindowModality.NonModal)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Current selection section
        current_label = QLabel("Archivos preparados para enviar")
        current_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(current_label)
        
        self._current_files_list = QListWidget()
        self._current_files_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e5e7;
                border-radius: 8px;
                padding: 4px;
                background-color: #ffffff;
                min-height: 120px;
            }
            QListWidget::item {
                padding: 4px;
                border: none;
            }
        """)
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
        separator.setStyleSheet("background-color: #e5e5e7;")
        layout.addWidget(separator)
        
        # Recent history section
        history_label = QLabel("Historial reciente")
        history_label.setStyleSheet("font-weight: 600; font-size: 14px; margin-top: 8px;")
        layout.addWidget(history_label)
        
        self._history_list = QListWidget()
        self._history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e5e7;
                border-radius: 8px;
                padding: 4px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 6px;
                border: none;
            }
        """)
        self._history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        layout.addWidget(self._history_list, 1)
    
    def _populate_current_files(self) -> None:
        """Populate current files list."""
        self._current_files_list.clear()
        for file_path in self._current_session.file_paths:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setToolTip(file_path)
            self._current_files_list.addItem(item)
    
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
            
            # Populate history list
            self._history_list.clear()
            for session in self._temporary_history:
                timestamp_str = session.timestamp.strftime("%Y-%m-%d %H:%M")
                text = f"{timestamp_str} - {session.file_count} archivo(s)"
                
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, session.temp_folder_path)
                item.setToolTip(f"Carpeta: {session.temp_folder_path}")
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
    
    def _position_window(self) -> None:
        """Position window to the right of FileViewContainer, like Finder preview."""
        if not self.parent():
            return
        
        parent_window = self.parent()
        
        # Find FileViewContainer in MainWindow
        file_view_container = None
        if hasattr(parent_window, '_file_view_container'):
            file_view_container = parent_window._file_view_container
        
        if not file_view_container:
            # Fallback: center on screen
            self._center_on_screen()
            return
        
        # Get FileViewContainer geometry in global coordinates
        file_view_geo = file_view_container.geometry()
        file_view_global_pos = file_view_container.mapToGlobal(file_view_geo.topLeft())
        
        # Calculate position: to the right of FileViewContainer
        window_width = self.width() if self.width() > 0 else 400
        margin = 0  # No margin, flush against FileViewContainer like Finder
        
        # Position to the right of FileViewContainer
        new_x = file_view_global_pos.x() + file_view_geo.width() + margin
        
        # Use same Y position and height as FileViewContainer
        new_y = file_view_global_pos.y()
        
        # Set window size to match FileViewContainer height
        window_height = file_view_geo.height()
        self.setFixedHeight(window_height)
        
        # Set position
        self.move(new_x, new_y)
        
        # If window would go off screen, adjust
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            if new_x + window_width > screen_geo.right():
                # Adjust to fit on screen
                new_x = screen_geo.right() - window_width - 10
                self.move(new_x, new_y)
    
    def _center_on_screen(self) -> None:
        """Center window on screen."""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            window_geo = self.geometry()
            x = (screen_geo.width() - window_geo.width()) // 2
            y = (screen_geo.height() - window_geo.height()) // 2
            self.move(x, y)
    
    def showEvent(self, event) -> None:
        """Handle show event - position window when shown."""
        super().showEvent(event)
        # Delay positioning to ensure window and FileViewContainer have proper size
        QTimer.singleShot(50, self._position_window)
    
    def closeEvent(self, event) -> None:
        """Handle close event - clear temporary history."""
        self._temporary_history.clear()
        super().closeEvent(event)

