"""
Quick Preview UI Setup - UI layout and window configuration.

Handles window geometry, layout creation, and widget setup.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.windows.quick_preview_styles import get_scrollbar_style


class QuickPreviewUISetup:
    """Handles UI setup for preview window."""
    
    @staticmethod
    def setup_window(window: QWidget) -> QSize:
        """Setup window geometry and flags."""
        window.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        
        max_width = int(screen_geo.width() * 0.65)
        max_height = int(screen_geo.height() * 0.75)
        
        if max_width > max_height * 1.2:
            max_width = int(max_height * 1.2)
        elif max_height > max_width * 1.2:
            max_height = int(max_width * 1.2)
        
        window_x = screen_geo.x() + (screen_geo.width() - max_width) // 2
        window_y = screen_geo.y() + (screen_geo.height() - max_height) // 2
        
        window.setGeometry(window_x, window_y, max_width, max_height)
        window.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        max_size = QSize(
            int(max_width * 0.98),
            int(max_height * 0.92)
        )
        
        window.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        return max_size
    
    
    @staticmethod
    def create_content_area(thumbnails_panel: QWidget, image_label: QLabel) -> QHBoxLayout:
        """Create content area with thumbnails and image scroll."""
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        content_layout.addWidget(thumbnails_panel)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(get_scrollbar_style())
        
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background-color: transparent;")
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(image_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        scroll.setWidget(container)
        content_layout.addWidget(scroll, 1)
        
        return content_layout

