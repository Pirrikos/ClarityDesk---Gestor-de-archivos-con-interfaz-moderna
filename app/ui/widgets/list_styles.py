"""
ListStyles - Stylesheet constants for list view.

Contains CSS styles for FileListView table and checkboxes.
"""

LIST_VIEW_STYLESHEET = """
    QTableWidget {
        background-color: #ffffff;
        border: none;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        color: #2b2b2b;
        gridline-color: transparent;
        selection-background-color: #e9f3ff;
        outline: none;
    }
    QTableWidget::item {
        border: none;
        padding: 12px 20px;
        color: #2b2b2b;
        outline: none;
    }
    QTableWidget::item:selected {
        background-color: transparent;
        color: #2b2b2b;
        border: none;
        outline: none;
    }
    QTableWidget::item:focus {
        outline: none;
        border: none;
    }
    QTableWidget::item:hover {
        background-color: #f5f8ff;
    }
    QCheckBox {
        spacing: 0px;
        padding: 0px;
        margin: 0px;
    }
    QCheckBox::indicator {
        width: 22px;
        height: 22px;
        border: 2px solid #8e8e93;
        border-radius: 4px;
        background-color: #ffffff;
        margin-left: 19px;
    }
    QCheckBox::indicator:hover {
        border-color: #0078d4;
        background-color: #f0f8ff;
    }
    QCheckBox::indicator:checked {
        background-color: #0078d4;
        border-color: #0078d4;
    }
    QCheckBox::indicator:checked:hover {
        background-color: #106ebe;
        border-color: #106ebe;
    }
    QHeaderView::section {
        background-color: #ffffff;
        color: #8e8e93;
        border: none;
        border-bottom: 1px solid #e5e5e7;
        padding: 8px 12px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
"""

