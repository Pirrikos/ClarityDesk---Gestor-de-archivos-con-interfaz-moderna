"""
Quick Preview Thumbnail Widget - Individual thumbnail widget creation.

Handles creation and styling of individual thumbnail widgets.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class QuickPreviewThumbnailWidget:
    """Creates individual thumbnail widgets."""
    
    @staticmethod
    def create(thumbnail: QPixmap, page_num: int, current_page: int, 
               on_click_callback) -> QWidget:
        """
        Create a single thumbnail widget.
        
        Args:
            thumbnail: Thumbnail pixmap.
            page_num: Page number (0-indexed).
            current_page: Currently selected page (0-indexed).
            on_click_callback: Callback function(page_num) for clicks.
            
        Returns:
            Configured thumbnail widget.
        """
        thumb_container = QWidget()
        thumb_container.setFixedSize(110, 135)
        thumb_container.setCursor(Qt.CursorShape.PointingHandCursor)
        thumb_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(4, 4, 4, 4)
        thumb_layout.setSpacing(3)
        
        thumb_label = QLabel()
        thumb_label.setPixmap(thumbnail)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setCursor(Qt.CursorShape.PointingHandCursor)
        thumb_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        thumb_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: none;
                border-radius: 2px;
            }
        """)
        
        page_num_label = QLabel(str(page_num + 1))
        page_num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_num_label.setCursor(Qt.CursorShape.PointingHandCursor)
        page_num_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        page_num_label.setStyleSheet("""
            QLabel {
                color: rgba(100, 100, 100, 255);
                font-size: 10px;
                font-weight: 500;
                background-color: transparent;
            }
        """)
        
        thumb_layout.addWidget(thumb_label)
        thumb_layout.addWidget(page_num_label)
        
        is_selected = page_num == current_page
        thumb_container.setStyleSheet(f"""
            QWidget {{
                background-color: {'rgba(200, 220, 255, 200)' if is_selected else 'transparent'};
                border: {'2px solid rgba(70, 130, 220, 255)' if is_selected else '1px solid transparent'};
                border-radius: 4px;
            }}
        """)
        
        def create_click_handler(p):
            def handler(event):
                if event.button() == Qt.MouseButton.LeftButton:
                    event.accept()
                    on_click_callback(p)
                else:
                    event.ignore()
            return handler
        
        thumb_container.mousePressEvent = create_click_handler(page_num)
        
        return thumb_container
    
    @staticmethod
    def update_style(widget: QWidget, is_selected: bool) -> None:
        """
        Update thumbnail widget style based on selection.
        
        Args:
            widget: Thumbnail widget.
            is_selected: Whether widget is selected.
        """
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {'rgba(200, 220, 255, 200)' if is_selected else 'transparent'};
                border: {'2px solid rgba(70, 130, 220, 255)' if is_selected else '1px solid transparent'};
                border-radius: 4px;
            }}
        """)

