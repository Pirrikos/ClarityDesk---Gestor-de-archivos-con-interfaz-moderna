"""
ToolbarButtonStyles - Stylesheet utilities for toolbar buttons.

Provides consistent button styling for ViewToolbar.
"""


def get_view_button_style(checked: bool) -> str:
    """Get stylesheet for view toggle button (Grid/List) based on checked state."""
    if checked:
        return """
            QPushButton {
                background-color: #1F2228;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: 400;
            }
            QPushButton:hover {
                background-color: #1F2228;
                color: #FFFFFF;
            }
        """
    else:
        return """
            QPushButton {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: 400;
            }
            QPushButton:hover {
                background-color: #1F2228;
                color: #FFFFFF;
            }
        """


def get_nav_button_style() -> str:
    """Get stylesheet for navigation buttons (Back/Forward)."""
    return """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            color: #FFFFFF;
            font-size: 16px;
            font-weight: 700;
        }
        QPushButton:hover {
            background-color: transparent;
            color: #FFFFFF;
        }
        QPushButton:pressed {
            background-color: rgba(255,255,255,0.10);
            color: #FFFFFF;
        }
        QPushButton:disabled {
            color: rgba(255,255,255,0.4);
            background-color: transparent;
        }
    """


def get_state_button_style() -> str:
    """Get stylesheet for state action buttons."""
    return """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            color: #FFFFFF;
        }
        QPushButton:hover {
            background-color: rgba(255,255,255,0.08);
            color: #FFFFFF;
        }
        QPushButton:pressed {
            background-color: rgba(255,255,255,0.12);
            color: #FFFFFF;
        }
    """


def get_clear_button_style() -> str:
    """Get stylesheet for clear state button."""
    return """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            color: #FFFFFF;
        }
        QPushButton:hover {
            background-color: rgba(255,255,255,0.08);
            color: #FFFFFF;
        }
        QPushButton:pressed {
            background-color: rgba(255,255,255,0.12);
            color: #FFFFFF;
        }
    """
