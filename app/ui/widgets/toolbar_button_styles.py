"""
ToolbarButtonStyles - Stylesheet utilities for toolbar buttons.

Provides consistent button styling for ViewToolbar.
"""


def get_view_button_style(checked: bool) -> str:
    if checked:
        return """
            QPushButton {
                background-color: rgba(0, 0, 0, 0.08);
                color: rgba(0, 0, 0, 0.85);
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI', sans-serif;
                /* font-size: establecido explícitamente */
                font-weight: 400;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.12);
                color: rgba(0, 0, 0, 0.85);
            }
        """
    else:
        return """
            QPushButton {
                background-color: transparent;
                color: rgba(0, 0, 0, 0.65);
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI', sans-serif;
                /* font-size: establecido explícitamente */
                font-weight: 400;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.08);
                color: rgba(0, 0, 0, 0.85);
            }
        """


def get_nav_button_style() -> str:
    return """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            color: rgba(0, 0, 0, 0.85);
            /* font-size: establecido explícitamente */
            font-weight: 700;
        }
        QPushButton:hover {
            background-color: rgba(0, 0, 0, 0.08);
            color: rgba(0, 0, 0, 0.85);
        }
        QPushButton:pressed {
            background-color: rgba(0, 0, 0, 0.12);
            color: rgba(0, 0, 0, 0.85);
        }
        QPushButton:disabled {
            color: rgba(0, 0, 0, 0.3);
            background-color: transparent;
        }
    """


def get_state_button_style() -> str:
    return """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            /* font-size: establecido explícitamente */
            color: rgba(0, 0, 0, 0.85);
        }
        QPushButton:hover {
            background-color: rgba(0, 0, 0, 0.08);
            color: rgba(0, 0, 0, 0.85);
        }
        QPushButton:pressed {
            background-color: rgba(0, 0, 0, 0.12);
            color: rgba(0, 0, 0, 0.85);
        }
    """


def get_clear_button_style() -> str:
    return """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            /* font-size: establecido explícitamente */
            color: rgba(0, 0, 0, 0.85);
        }
        QPushButton:hover {
            background-color: rgba(0, 0, 0, 0.08);
            color: rgba(0, 0, 0, 0.85);
        }
        QPushButton:pressed {
            background-color: rgba(0, 0, 0, 0.12);
            color: rgba(0, 0, 0, 0.85);
        }
    """
