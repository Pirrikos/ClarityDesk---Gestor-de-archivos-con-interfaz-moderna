"""
ToolbarButtonStyles - Stylesheet utilities for toolbar buttons.

Provides consistent button styling for ViewToolbar.
"""

# Constantes de estilo comunes
_BUTTON_BG_HOVER = "rgba(0, 0, 0, 0.08)"
_BUTTON_BG_PRESSED = "rgba(0, 0, 0, 0.12)"
_BUTTON_TEXT_PRIMARY = "rgba(0, 0, 0, 0.85)"
_BUTTON_TEXT_SECONDARY = "rgba(0, 0, 0, 0.65)"
_BUTTON_TEXT_DISABLED = "rgba(0, 0, 0, 0.3)"
_BUTTON_BORDER_RADIUS = "6px"
_BUTTON_PADDING = "6px 12px"
_FONT_FAMILY = "'Segoe UI', sans-serif"


def get_view_button_style(checked: bool) -> str:
    if checked:
        return f"""
            QPushButton {{
                background-color: {_BUTTON_BG_HOVER};
                color: {_BUTTON_TEXT_PRIMARY};
                border: none;
                border-radius: {_BUTTON_BORDER_RADIUS};
                padding: {_BUTTON_PADDING};
                font-family: {_FONT_FAMILY};
                /* font-size: establecido explícitamente */
                font-weight: 400;
            }}
            QPushButton:checked {{
                background-color: {_BUTTON_BG_HOVER} !important;
                color: {_BUTTON_TEXT_PRIMARY} !important;
                border: none !important;
            }}
            QPushButton:hover {{
                background-color: {_BUTTON_BG_PRESSED};
                color: {_BUTTON_TEXT_PRIMARY};
            }}
            QPushButton:checked:hover {{
                background-color: {_BUTTON_BG_PRESSED} !important;
                color: {_BUTTON_TEXT_PRIMARY} !important;
            }}
        """
    else:
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {_BUTTON_TEXT_SECONDARY};
                border: none;
                border-radius: {_BUTTON_BORDER_RADIUS};
                padding: {_BUTTON_PADDING};
                font-family: {_FONT_FAMILY};
                /* font-size: establecido explícitamente */
                font-weight: 400;
            }}
            QPushButton:!checked {{
                background-color: transparent !important;
                color: {_BUTTON_TEXT_SECONDARY} !important;
                border: none !important;
            }}
            QPushButton:hover {{
                background-color: {_BUTTON_BG_HOVER};
                color: {_BUTTON_TEXT_PRIMARY};
            }}
            QPushButton:!checked:hover {{
                background-color: {_BUTTON_BG_HOVER} !important;
                color: {_BUTTON_TEXT_PRIMARY} !important;
            }}
        """


def get_nav_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: {_BUTTON_BORDER_RADIUS};
            color: {_BUTTON_TEXT_PRIMARY};
            /* font-size: establecido explícitamente */
            font-weight: 700;
        }}
        QPushButton:hover {{
            background-color: {_BUTTON_BG_HOVER};
            color: {_BUTTON_TEXT_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {_BUTTON_BG_PRESSED};
            color: {_BUTTON_TEXT_PRIMARY};
        }}
        QPushButton:disabled {{
            color: {_BUTTON_TEXT_DISABLED};
            background-color: transparent;
        }}
    """


def get_state_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: {_BUTTON_BORDER_RADIUS};
            /* font-size: establecido explícitamente */
            color: {_BUTTON_TEXT_PRIMARY};
        }}
        QPushButton:hover {{
            background-color: {_BUTTON_BG_HOVER};
            color: {_BUTTON_TEXT_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {_BUTTON_BG_PRESSED};
            color: {_BUTTON_TEXT_PRIMARY};
        }}
    """


