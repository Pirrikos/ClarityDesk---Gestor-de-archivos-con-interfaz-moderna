"""
Scroll area helpers for FileGridView.

Handles creation and configuration of scroll areas.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QSizePolicy

from app.ui.widgets.grid_content_widget import GridContentWidget


def create_scroll_area(view) -> QScrollArea:
    """Create and configure base scroll area."""
    scroll = QScrollArea(view)
    scroll.setWidgetResizable(True)
    scroll.setAcceptDrops(True)
    scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    # Remove any frame or margins
    scroll.setFrameShape(scroll.Shape.NoFrame)
    scroll.setFrameShadow(scroll.Shadow.Plain)
    return scroll


def configure_scroll_area(scroll: QScrollArea, content_widget: GridContentWidget, is_desktop_window: bool) -> None:
    """Configure scroll area styles based on desktop window mode."""
    # Remove any frame or margins from scroll area
    scroll.setFrameShape(scroll.Shape.NoFrame)
    scroll.setFrameShadow(scroll.Shadow.Plain)
    
    if is_desktop_window:
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }
            QScrollArea > QWidget > QWidget {
                padding: 0;
                margin: 0;
            }
        """)
        content_widget.setStyleSheet("QWidget { background-color: transparent; }")
    else:
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1A1D22;
                border: none;
                padding: 0;
                margin: 0;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #1A1D22;
                padding: 0;
                margin: 0;
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
            QScrollBar:horizontal {
                background-color: transparent;
                height: 12px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                min-width: 40px;
                margin: 4px 2px 2px 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(255, 255, 255, 0.22);
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: rgba(255, 255, 255, 0.30);
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
                border: none;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        """)
        content_widget.setStyleSheet("QWidget { background-color: #1A1D22; }")

