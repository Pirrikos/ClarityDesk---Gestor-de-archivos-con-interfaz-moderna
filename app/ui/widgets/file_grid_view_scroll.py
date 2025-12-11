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
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }
            QScrollArea > QWidget > QWidget {
                padding: 0;
                margin: 0;
            }
            QScrollBar:vertical {
                background-color: transparent; width: 10px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(208, 208, 208, 150);
                border-radius: 5px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(176, 176, 176, 200);
            }
        """)

