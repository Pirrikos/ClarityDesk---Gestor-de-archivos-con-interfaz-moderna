"""
Layout helpers for FocusDockWidget.

Handles UI setup: buttons, scroll area, and tiles container.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def setup_dock_widget(widget: QWidget) -> None:
    """Setup basic widget properties."""
    widget.setFixedWidth(100)
    widget.setMinimumHeight(400)
    widget.setSizePolicy(
        QSizePolicy.Policy.Fixed,
        QSizePolicy.Policy.Expanding
    )
    palette = widget.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 32, 38))
    widget.setPalette(palette)
    widget.setAutoFillBackground(True)
    widget.setStyleSheet("""
        FocusDockWidget {
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
    """)
    widget.setVisible(True)
    widget.show()


def setup_buttons() -> tuple[QPushButton, QPushButton, QHBoxLayout]:
    """Setup + and - buttons."""
    buttons_layout = QHBoxLayout()
    buttons_layout.setContentsMargins(0, 0, 0, 0)
    buttons_layout.setSpacing(4)
    
    add_button = QPushButton("+")
    add_button.setFixedSize(33, 36)
    add_button.setStyleSheet("""
        QPushButton {
            background-color: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(200, 200, 200, 0.5);
            border-radius: 8px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 20px;
            font-weight: 400;
            color: rgb(60, 60, 60);
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 1.0);
            border-color: rgba(150, 150, 150, 0.7);
        }
    """)
    
    remove_button = QPushButton("−")
    remove_button.setFixedSize(33, 36)
    remove_button.setStyleSheet("""
        QPushButton {
            background-color: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(200, 200, 200, 0.5);
            border-radius: 8px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 20px;
            font-weight: 400;
            color: rgb(60, 60, 60);
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 1.0);
            border-color: rgba(150, 150, 150, 0.7);
        }
        QPushButton:disabled {
            background-color: rgba(200, 200, 200, 0.5);
            color: rgba(120, 120, 120, 0.7);
        }
    """)
    
    buttons_layout.addWidget(add_button)
    buttons_layout.addWidget(remove_button)
    buttons_layout.addStretch()
    
    return add_button, remove_button, buttons_layout


def setup_scroll_area(parent: QWidget) -> QScrollArea:
    """Setup scroll area for tiles."""
    scroll_area = QScrollArea(parent)
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll_area.setFrameShape(scroll_area.Shape.NoFrame)
    scroll_area.viewport().setAutoFillBackground(False)
    scroll_area.setStyleSheet("""
        QScrollArea {
            border: none;
            background: transparent;
        }
        QScrollArea > QWidget > QWidget {
            background: transparent;
        }
        QScrollBar:vertical {
            background: rgba(255, 255, 255, 0.05);
            width: 6px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(255, 255, 255, 0.3);
        }
    """)
    scroll_area.setMinimumHeight(200)
    return scroll_area


def setup_tiles_container(parent: QWidget) -> tuple[QWidget, QVBoxLayout]:
    """Setup container widget for tiles."""
    tiles_container = QWidget()
    tiles_container.setObjectName("tiles_container")
    tiles_container.setStyleSheet("background-color: transparent;")
    tiles_container.setMinimumWidth(90)
    tiles_container.setMinimumHeight(100)
    
    tiles_layout = QVBoxLayout(tiles_container)
    tiles_layout.setContentsMargins(4, 4, 4, 4)
    tiles_layout.setSpacing(8)
    tiles_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
    
    return tiles_container, tiles_layout

