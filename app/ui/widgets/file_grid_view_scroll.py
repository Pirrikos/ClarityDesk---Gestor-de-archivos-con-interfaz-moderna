"""
Scroll area helpers for FileGridView.

Handles creation and configuration of scroll areas.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QSizePolicy, QWidget

from app.core.constants import (
    CENTRAL_AREA_BG,
    SCROLLBAR_HANDLE_BG,
    SCROLLBAR_HANDLE_HOVER,
    SCROLLBAR_HANDLE_PRESSED
)
from app.ui.widgets.grid_content_widget import GridContentWidget


def _remove_frame_and_margins(scroll: QScrollArea) -> None:
    """Remove frame and margins from scroll area."""
    scroll.setFrameShape(scroll.Shape.NoFrame)
    scroll.setFrameShadow(scroll.Shadow.Plain)


def create_scroll_area(view: QWidget) -> QScrollArea:
    """Create and configure base scroll area."""
    scroll = QScrollArea(view)
    scroll.setWidgetResizable(True)
    scroll.setAcceptDrops(True)
    scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    _remove_frame_and_margins(scroll)
    return scroll


def configure_scroll_area(scroll: QScrollArea, content_widget: GridContentWidget, is_desktop_window: bool) -> None:
    """Configure scroll area styles based on desktop window mode."""
    _remove_frame_and_margins(scroll)
    
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
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
                padding: 0;
                margin: 0;
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 12px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {SCROLLBAR_HANDLE_BG};
                border-radius: 6px;
                min-height: 40px;
                margin: 2px 2px 2px 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {SCROLLBAR_HANDLE_HOVER};
            }}
            QScrollBar::handle:vertical:pressed {{
                background-color: {SCROLLBAR_HANDLE_PRESSED};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 12px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {SCROLLBAR_HANDLE_BG};
                border-radius: 6px;
                min-width: 40px;
                margin: 4px 2px 2px 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {SCROLLBAR_HANDLE_HOVER};
            }}
            QScrollBar::handle:horizontal:pressed {{
                background-color: {SCROLLBAR_HANDLE_PRESSED};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
                border: none;
            }}
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: transparent;
            }}
        """)
        content_widget.setStyleSheet("QWidget { background-color: transparent; }")

