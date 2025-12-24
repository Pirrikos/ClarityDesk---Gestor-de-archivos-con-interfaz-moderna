"""FolderTreeStyles - Paleta Raycast para FolderTreeSidebar."""

from app.core.constants import SIDEBAR_BG

PANEL_BG = "#181B1E"
HOVER_BG = "#23262D"
SELECT_BG = "#23262D"
BORDER_COLOR = "rgba(255, 255, 255, 0.09)"
TEXT_PRIMARY = "#E6E6E6"
TEXT_SECONDARY = "#9AA0A6"
TEXT_DISABLED = "#6B7078"
ACCENT_COLOR = "#4A90E2"
SCROLL_HANDLE = "rgba(255, 255, 255, 0.15)"
SCROLL_HANDLE_HOVER = "rgba(255, 255, 255, 0.25)"
SEPARATOR_VERTICAL_COLOR_RGBA = (255, 255, 255, 23)
FONT_FAMILY = '"Inter", "SF Pro Display", "Segoe UI", -apple-system, system-ui'
FONT_SIZE_BASE = "13px"
FONT_SIZE_L1 = "14px"
ICON_SIZE_PX = 16
ITEM_HEIGHT = 30
ITEM_V_SPACING = 12
ITEM_H_PADDING = 24
ITEM_RIGHT_MARGIN = 10

def get_base_stylesheet() -> str:
    return f"""
        QWidget#FolderTreeSidebar {{
            background-color: transparent;
            border: none;
        }}
        
        QWidget#TreeContainer {{
            background-color: transparent;
            border: none;
        }}
        
        QWidget#ButtonContainer {{
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        }}
        
        QPushButton#AddButton {{
            background-color: transparent;
            border: none;
            /* font-size: establecido explícitamente */
            font-weight: 400;
            font-family: {FONT_FAMILY};
            color: {TEXT_PRIMARY};
            padding: 6px 0px;
            padding-left: 16px;
            padding-right: {ITEM_RIGHT_MARGIN}px;
            text-align: left;
            border-radius: 0px;
            margin: 0px 0px;
        }}
        
        QPushButton#AddButton:hover {{
            background-color: {HOVER_BG};
        }}
        
        QPushButton#AddButton:pressed {{
            background-color: {SELECT_BG};
        }}
    """

def get_tree_base_stylesheet() -> str:
    return f"""
        QTreeView {{
            background: transparent;
            color: {TEXT_PRIMARY};
            border: none;
            outline: none;
            /* font-size: establecido explícitamente */
            font-family: {FONT_FAMILY};
            font-weight: 400;
            letter-spacing: -0.2px;
            padding: 0px 0px;
            padding-left: 0px;
            selection-background-color: rgba(0,0,0,0);
            selection-color: {TEXT_PRIMARY};
            show-decoration-selected: 0;
        }}
        
        QTreeView::viewport {{
            background: transparent;
            padding: 0px;
            padding-left: 0px;
        }}
        
        QTreeView::item {{
            height: {ITEM_HEIGHT}px;
            min-height: {ITEM_HEIGHT}px;
            padding: 4px 0px;
            padding-left: 0px;
            padding-right: {ITEM_RIGHT_MARGIN}px;
            border-radius: 0px;
            margin: 0px 0px;
            border: none;
            border-left: none;
            border-right: none;
            border-top: none;
            border-bottom: none;
            outline: none;
            background-color: transparent;
        }}
        
        QTreeView::item:hover {{
            background-color: transparent;
        }}
        
        QTreeView::item:selected {{
            background-color: transparent;
            color: {TEXT_PRIMARY};
            border: none;
            border-left: none;
            border-right: none;
            border-top: none;
            border-bottom: none;
            outline: none;
        }}
        
        QTreeView::item:selected:hover {{ 
            background-color: transparent;
            border: none;
            border-left: none;
        }}
        QTreeView::item:selected:active {{ 
            background-color: transparent;
            border: none;
            border-left: none;
        }}
        QTreeView::item:selected:!active {{ 
            background-color: transparent;
            border: none;
            border-left: none;
        }}
    """

def get_tree_branch_stylesheet() -> str:
    return f"""
        QTreeView::branch {{
            background-color: transparent;
            border: none;
        }}
        
        QTreeView::branch:has-siblings:!adjoins-item {{
            border: none;
            border-image: none;
            background: transparent;
        }}
        
        QTreeView::branch:has-siblings:adjoins-item {{
            border: none;
            border-image: none;
            background: transparent;
        }}
        
        QTreeView::branch:!has-children:!has-siblings:adjoins-item {{
            border: none;
            border-image: none;
            background: transparent;
        }}
        
        QTreeView::branch:has-children:!has-siblings:closed,
        QTreeView::branch:closed:has-children:has-siblings {{
            border: none;
            border-image: none;
            background: transparent;
            margin: 0px;
            image: none;
        }}
        
        QTreeView::branch:open:has-children:!has-siblings,
        QTreeView::branch:open:has-children:has-siblings {{
            border: none;
            border-image: none;
            background: transparent;
            margin: 0px;
            image: none;
        }}
    """

def get_scrollbar_stylesheet() -> str:
    return f"""
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background: {SCROLL_HANDLE};
            border-radius: 4px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {SCROLL_HANDLE_HOVER};
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
    """

def get_menu_stylesheet() -> str:
    return f"""
        QMenu {{
            background: {PANEL_BG};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 6px 8px;
            color: {TEXT_PRIMARY};
        }}
        QMenu::item {{
            padding: 6px 12px;
            border-radius: 6px;
            background: transparent;
            color: {TEXT_PRIMARY};
        }}
        QMenu::item:selected {{
            background: {HOVER_BG};
        }}
    """


def get_complete_stylesheet() -> str:
    return (
        get_base_stylesheet() +
        get_tree_base_stylesheet() +
        get_tree_branch_stylesheet() +
        get_scrollbar_stylesheet()
    )
