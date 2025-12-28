"""
ListStyles - Stylesheet constants for list view.

Contains CSS styles for FileListView table and checkboxes.
"""

from app.core.constants import (
    CENTRAL_AREA_BG, LIST_CELL_BG, TEXT_LIST,
    CHECKBOX_BORDER, CHECKBOX_BORDER_HOVER, CHECKBOX_BG_CHECKED, CHECKBOX_BG_CHECKED_HOVER,
    HEADER_BG, HEADER_TEXT_COLOR, HEADER_BORDER_RIGHT, HEADER_BORDER_BOTTOM,
    HEADER_TEXT_HOVER, HEADER_BORDER_CORNER
)

LIST_VIEW_STYLESHEET = f"""
    QTableWidget {{
        background-color: transparent;
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: none;
        font-family: 'Segoe UI', sans-serif;
        /* font-size: establecido explícitamente */
        color: {TEXT_LIST};
        gridline-color: rgba(0, 0, 0, 0) !important;
        selection-background-color: transparent;
        selection-color: {TEXT_LIST};
        outline: none;
        show-decoration-selected: 0;
    }}
    QTableView {{
        background-color: transparent;
        border: none;
        gridline-color: rgba(0, 0, 0, 0) !important;
        outline: none;
    }}
    QTableWidget::viewport {{
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: none;
        background-color: transparent;
    }}
    QTableView::viewport {{
        border: none;
        background-color: transparent;
    }}
    QTableWidget::item,
    QTableView::item {{
        border: 0 !important;
        border-left: 0 !important;
        border-right: 0 !important;
        border-top: 0 !important;
        border-bottom: 0 !important;
        padding: 0px 4px 0px 20px;
        color: {TEXT_LIST};
        outline: 0 !important;
        background-color: transparent;
    }}
    QTableWidget::item:!selected,
    QTableView::item:!selected,
    QTableWidget::item:selected,
    QTableView::item:selected,
    QTableWidget::item:selected:focus,
    QTableView::item:selected:focus,
    QTableWidget::item:focus,
    QTableView::item:focus,
    QTableWidget::item:hover,
    QTableView::item:hover {{
        border: 0 !important;
        border-left: 0 !important;
        border-right: 0 !important;
        border-top: 0 !important;
        border-bottom: 0 !important;
        outline: 0 !important;
        background-color: transparent;
        color: {TEXT_LIST};
    }}
    QTableWidget::item:hover {{
        background-color: transparent;
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: none;
    }}
    }}
    /* Checkboxes estilo Finder claro */
    QCheckBox {{
        spacing: 0px;
        padding: 0px;
        margin: 0px;
    }}
    QCheckBox::indicator {{
        width: 11px;
        height: 11px;
        border: 1px solid {CHECKBOX_BORDER};
        border-radius: 2px;
        background-color: {CENTRAL_AREA_BG};
        margin: 0px;
    }}
    QCheckBox::indicator:hover {{
        border-color: {CHECKBOX_BORDER_HOVER};
        background-color: {CENTRAL_AREA_BG};
    }}
    QCheckBox::indicator:checked {{
        background-color: {CHECKBOX_BG_CHECKED};
        border-color: {CHECKBOX_BG_CHECKED};
    }}
    QCheckBox::indicator:checked:hover {{
        background-color: {CHECKBOX_BG_CHECKED_HOVER};
        border-color: {CHECKBOX_BG_CHECKED_HOVER};
    }}
    /* Header estilo Finder - minimalista y sutil */
    QHeaderView {{
        border: none;
        outline: none;
        background-color: transparent;
        margin-top: 4px;
    }}
    QHeaderView::section {{
        background-color: transparent;
        color: {HEADER_TEXT_COLOR};
        border: none !important;
        border-right: none !important;
        border-bottom: none !important;
        padding: 6px 10px;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 500;
        border-radius: 8px;
        margin: 2px 4px;
    }}
    QHeaderView::section:first {{
        border-left: none !important;
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }}
    QHeaderView::section:hover {{
        color: {HEADER_TEXT_HOVER};
    }}
    QHeaderView::section:last {{
        border-right: none !important;
    }}
    QTableCornerButton::section {{
        background-color: {CENTRAL_AREA_BG};
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: 1px solid {HEADER_BORDER_CORNER};
    }}
"""

