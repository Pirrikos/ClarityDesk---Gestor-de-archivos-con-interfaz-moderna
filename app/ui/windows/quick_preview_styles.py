"""
Quick Preview Styles - Stylesheet utilities for preview window.

Provides reusable stylesheets for scrollbars and UI elements.
"""


def get_scrollbar_style() -> str:
    """Get scrollbar stylesheet for preview window."""
    return """
        QScrollArea {
            background-color: #ffffff;
            border: none;
        }
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 12px;
            border: none;
            border-radius: 6px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-height: 40px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
        QScrollBar::handle:vertical:pressed {
            background-color: #808080;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            border: none;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
        }
        QScrollBar:horizontal {
            background-color: #f0f0f0;
            height: 12px;
            border: none;
            border-radius: 6px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-width: 40px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #a0a0a0;
        }
        QScrollBar::handle:horizontal:pressed {
            background-color: #808080;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
            border: none;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: transparent;
        }
    """


def get_loading_label_style() -> str:
    """Get stylesheet for loading/preview label."""
    return """
        QLabel {
            color: #333333;
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
            background-color: transparent;
        }
    """


def get_error_label_style() -> str:
    """Get stylesheet for error/no preview label."""
    return """
        QLabel {
            color: #666666;
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
            background-color: transparent;
        }
    """


def get_thumbnail_scrollbar_style() -> str:
    """Get scrollbar stylesheet for thumbnail panel."""
    return """
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 12px;
            border: none;
            border-radius: 6px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-height: 40px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
        QScrollBar::handle:vertical:pressed {
            background-color: #808080;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            border: none;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
        }
    """

