"""
ToolbarButtonStyles - Stylesheet utilities for toolbar buttons.

Provides consistent button styling for ViewToolbar.
"""


def get_view_button_style(checked: bool) -> str:
    """Get stylesheet for view toggle button (Grid/List) based on checked state."""
    if checked:
        return """
            QPushButton {
                background-color: #e0edff;
                color: #1d1d1f;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 400;
            }
            QPushButton:hover {
                background-color: #e0edff;
            }
        """
    else:
        return """
            QPushButton {
                background-color: transparent;
                color: #1d1d1f;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 400;
            }
            QPushButton:hover {
                background-color: #f0f6ff;
            }
        """


def get_nav_button_style() -> str:
    """Get stylesheet for navigation buttons (Back/Forward)."""
    return """
        QPushButton {
            background-color: transparent;
            border: 1px solid #e5e5e7;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #f5f5f7;
            border-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #e5e5e7;
        }
        QPushButton:disabled {
            opacity: 0.4;
        }
    """


def get_state_button_style() -> str:
    """Get stylesheet for state action buttons."""
    return """
        QPushButton {
            background-color: transparent;
            border: 1px solid #e5e5e7;
            border-radius: 6px;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: #f5f5f7;
            border-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #e5e5e7;
        }
    """


def get_clear_button_style() -> str:
    """Get stylesheet for clear state button."""
    return """
        QPushButton {
            background-color: transparent;
            border: 1px solid #e5e5e7;
            border-radius: 6px;
            font-size: 14px;
            color: #8e8e93;
        }
        QPushButton:hover {
            background-color: #f5f5f7;
            border-color: #d0d0d0;
            color: #2d2d2d;
        }
        QPushButton:pressed {
            background-color: #e5e5e7;
        }
    """

