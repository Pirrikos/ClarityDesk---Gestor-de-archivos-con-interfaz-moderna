"""
WorkspaceSelectorStyles - Stylesheet constants for WorkspaceSelector.

Contains CSS styles for workspace selector buttons and menus.
"""

from app.core.constants import (
    APP_HEADER_BORDER,
    MENU_BG, MENU_BORDER, MENU_HOVER_BG, MENU_ACCENT, MENU_ACCENT_BORDER,
    MENU_BG_ALPHA, MENU_BORDER_LIGHT, MENU_TEXT, MENU_TEXT_HOVER,
    MENU_ITEM_TEXT, MENU_ITEM_TEXT_HOVER, MENU_ITEM_HOVER_BG,
    BUTTON_BG_LIGHT, BUTTON_BORDER_LIGHT, BUTTON_TEXT_LIGHT,
    BUTTON_BG_LIGHT_HOVER, BUTTON_BORDER_LIGHT_HOVER, BUTTON_BG_LIGHT_PRESSED,
    BUTTON_BG_HEADER, BUTTON_BORDER_HEADER, BUTTON_TEXT_HEADER,
    BUTTON_BG_HEADER_HOVER, BUTTON_BORDER_HEADER_HOVER, BUTTON_TEXT_HEADER_HOVER,
    BUTTON_BG_HEADER_PRESSED, BUTTON_TEXT_HEADER_DISABLED,
    BUTTON_BG_DARK, BUTTON_BORDER_DARK, BUTTON_BG_DARK_HOVER, BUTTON_BORDER_DARK_HOVER
)

# File box button colors (local constants)
FILE_BOX_BUTTON_ACTIVE_BG = "#007AFF"
FILE_BOX_BUTTON_ACTIVE_HOVER = "#0056CC"


def get_base_stylesheet() -> str:
    """Get base stylesheet for WorkspaceSelector widget."""
    return f"""
        QWidget#WorkspaceSelector {{
            border-bottom: 1px solid {APP_HEADER_BORDER} !important;
        }}
        QPushButton#WorkspaceButton {{
            background-color: {BUTTON_BG_LIGHT};
            border: 1px solid {BUTTON_BORDER_LIGHT};
            border-radius: 6px;
            color: {BUTTON_TEXT_LIGHT};
            font-size: 12px;
            padding: 6px 14px;
            text-align: left;
            margin: 2px;
        }}
        QPushButton#WorkspaceButton:hover {{
            background-color: {BUTTON_BG_LIGHT_HOVER};
            border-color: {BUTTON_BORDER_LIGHT_HOVER};
        }}
        QPushButton#WorkspaceButton:pressed {{
            background-color: {BUTTON_BG_LIGHT_PRESSED};
        }}
        QPushButton#WorkspaceButton::menu-indicator {{
            subcontrol-origin: padding;
            subcontrol-position: center;
            width: 12px;
            height: 12px;
        }}
        QPushButton#StateButton {{
            background-color: {BUTTON_BG_LIGHT};
            border: 1px solid {BUTTON_BORDER_LIGHT};
            border-radius: 6px;
            color: {BUTTON_TEXT_LIGHT};
            font-size: 12px;
            padding: 0px;
            text-align: center;
        }}
        QPushButton#StateButton:hover {{
            background-color: {BUTTON_BG_LIGHT_HOVER};
            border-color: {BUTTON_BORDER_LIGHT_HOVER};
        }}
        QPushButton#StateButton:pressed {{
            background-color: {BUTTON_BG_LIGHT_PRESSED};
        }}
        QPushButton#StateButton::menu-indicator {{
            image: none;
            width: 0px;
        }}
        QPushButton#HeaderButton {{
            background-color: {BUTTON_BG_HEADER};
            border: 1px solid {BUTTON_BORDER_HEADER};
            border-radius: 6px;
            color: {BUTTON_TEXT_HEADER};
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton#HeaderButton:checked {{
            background-color: rgba(255, 255, 255, 0.2) !important;
            border: 1px solid {BUTTON_BORDER_HEADER} !important;
            color: {BUTTON_TEXT_HEADER_HOVER} !important;
        }}
        QPushButton#HeaderButton:hover {{
            background-color: {BUTTON_BG_HEADER_HOVER};
            border-color: {BUTTON_BORDER_HEADER_HOVER};
            color: {BUTTON_TEXT_HEADER_HOVER};
        }}
        QPushButton#HeaderButton:checked:hover {{
            background-color: rgba(255, 255, 255, 0.25) !important;
            border-color: {BUTTON_BORDER_HEADER} !important;
            color: {BUTTON_TEXT_HEADER_HOVER} !important;
        }}
        QPushButton#HeaderButton:pressed {{
            background-color: {BUTTON_BG_HEADER_PRESSED};
        }}
        QPushButton#HeaderButton:checked:pressed {{
            background-color: rgba(255, 255, 255, 0.2) !important;
            border-color: {BUTTON_BORDER_HEADER} !important;
            color: {BUTTON_TEXT_HEADER_HOVER} !important;
        }}
        QPushButton#HeaderButton:disabled {{
            background-color: {BUTTON_BG_HEADER};
            border: 1px solid {BUTTON_BORDER_HEADER};
            color: {BUTTON_TEXT_HEADER_DISABLED};
        }}
    """


def get_view_toggle_button_style(checked: bool) -> str:
    """Get stylesheet for view toggle buttons (Grid/List) based on checked state."""
    if checked:
        return """
            QPushButton#ViewToggleButton {
                background-color: rgba(255, 255, 255, 0.2) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 6px !important;
                color: rgba(255, 255, 255, 0.9) !important;
                font-size: 14px !important;
                font-weight: bold !important;
            }
            QPushButton#ViewToggleButton:hover {
                background-color: rgba(255, 255, 255, 0.25) !important;
                border-color: rgba(255, 255, 255, 0.08) !important;
                color: rgba(255, 255, 255, 0.9) !important;
            }
            QPushButton#ViewToggleButton:pressed {
                background-color: rgba(255, 255, 255, 0.2) !important;
                border-color: rgba(255, 255, 255, 0.08) !important;
                color: rgba(255, 255, 255, 0.9) !important;
            }
        """
    else:
        return """
            QPushButton#ViewToggleButton {
                background-color: rgba(255, 255, 255, 0.03) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 6px !important;
                color: rgba(255, 255, 255, 0.7) !important;
                font-size: 14px !important;
                font-weight: bold !important;
            }
            QPushButton#ViewToggleButton:hover {
                background-color: rgba(255, 255, 255, 0.08) !important;
                border-color: rgba(255, 255, 255, 0.15) !important;
                color: rgba(255, 255, 255, 0.9) !important;
            }
            QPushButton#ViewToggleButton:pressed {
                background-color: rgba(255, 255, 255, 0.12) !important;
            }
        """


def get_workspace_menu_stylesheet() -> str:
    """Get stylesheet for workspace dropdown menu."""
    return f"""
        QMenu {{
            background-color: {MENU_BG};
            border: 1px solid {MENU_BORDER};
            border-radius: 8px;
            color: {MENU_TEXT};
            padding: 8px 8px;
        }}
        QMenu::item {{
            padding: 6px 12px;
            border-radius: 6px;
        }}
        QMenu::item:selected {{
            background-color: {MENU_HOVER_BG};
            color: {MENU_TEXT_HOVER};
        }}
        QMenu::separator {{
            height: 1px;
            background: {MENU_BORDER};
            margin: 6px 8px;
        }}
        QMenu::indicator {{
            width: 8px; height: 8px;
            border-radius: 4px;
            margin: 0 6px 0 0;
            background-color: transparent;
            border: none;
        }}
        QMenu::indicator:checked {{
            background-color: {MENU_ACCENT};
            border: 1px solid {MENU_ACCENT_BORDER};
        }}
        QMenu::indicator:unchecked {{
            background-color: transparent;
            border: none;
        }}
    """


def get_state_menu_stylesheet() -> str:
    """Get stylesheet for state dropdown menu."""
    return f"""
        QMenu {{
            background-color: {MENU_BG_ALPHA};
            border: 1px solid {MENU_BORDER_LIGHT};
            border-radius: 6px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 20px;
            border-radius: 4px;
            color: {MENU_ITEM_TEXT};
        }}
        QMenu::item:selected {{
            background-color: {MENU_ITEM_HOVER_BG};
            color: {MENU_ITEM_TEXT_HOVER};
        }}
    """


def get_workspace_button_dark_stylesheet() -> str:
    """Get dark stylesheet for workspace button (used when moved to SecondaryHeader)."""
    return f"""
        QPushButton {{
            background-color: {BUTTON_BG_DARK};
            border: 1px solid {BUTTON_BORDER_DARK};
            border-radius: 6px;
            color: rgba(255, 255, 255, 0.88);
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: {BUTTON_BG_DARK_HOVER};
            border-color: {BUTTON_BORDER_DARK_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {BUTTON_BG_DARK_HOVER};
            border-color: {BUTTON_BORDER_DARK_HOVER};
        }}
    """


def get_file_box_button_active_stylesheet() -> str:
    """Get stylesheet for active file box button."""
    return f"""
        QPushButton#HeaderButton {{
            background-color: {FILE_BOX_BUTTON_ACTIVE_BG};
            color: white;
            border: none;
            border-radius: 6px;
        }}
        QPushButton#HeaderButton:hover {{
            background-color: {FILE_BOX_BUTTON_ACTIVE_HOVER};
        }}
    """

