"""
ListStyles - Stylesheet constants for list view.

Contains CSS styles for FileListView table and checkboxes.
"""

LIST_VIEW_STYLESHEET = """
    /* Estilo con fondo oscuro #1A1D22 */
    QTableWidget {
        background-color: #1A1D22;
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: none;
        font-family: 'Segoe UI', sans-serif;
        /* font-size: establecido explícitamente */
        color: #E8E8E8;
        gridline-color: rgba(0, 0, 0, 0) !important;
        selection-background-color: transparent;
        selection-color: #E8E8E8;
        outline: none;
        show-decoration-selected: 0;
    }
    QTableView {
        background-color: #1A1D22;
        border: none;
        gridline-color: rgba(0, 0, 0, 0) !important;
        outline: none;
    }
    QTableWidget::viewport {
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: none;
        background-color: #1A1D22;
    }
    QTableView::viewport {
        border: none;
        background-color: #1A1D22;
    }
    QTableWidget::item,
    QTableView::item {
        border: 0 !important;
        border-left: 0 !important;
        border-right: 0 !important;
        border-top: 0 !important;
        border-bottom: 0 !important;
        padding: 0px 20px;
        color: #E8E8E8;
        outline: 0 !important;
        background-color: transparent;
    }
    QTableWidget::item:!selected,
    QTableView::item:!selected,
    QTableWidget::item:selected,
    QTableView::item:selected,
    QTableWidget::item:selected:focus,
    QTableView::item:selected:focus,
    QTableWidget::item:focus,
    QTableView::item:focus,
    QTableWidget::item:hover,
    QTableView::item:hover {
        border: 0 !important;
        border-left: 0 !important;
        border-right: 0 !important;
        border-top: 0 !important;
        border-bottom: 0 !important;
        outline: 0 !important;
        background-color: transparent;
        color: #E8E8E8;
    }
    QTableWidget::item:hover {
        background-color: transparent;
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: none;
    }
    /* Checkboxes estilo Finder claro */
    QCheckBox {
        spacing: 0px;
        padding: 0px;
        margin: 0px;
    }
    QCheckBox::indicator {
        width: 22px;
        height: 22px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 4px;
        background-color: #1A1D22;
        margin: 0px;
    }
    QCheckBox::indicator:hover {
        border-color: #007AFF;
        background-color: #1A1D22;
    }
    QCheckBox::indicator:checked {
        background-color: #007AFF;
        border-color: #007AFF;
    }
    QCheckBox::indicator:checked:hover {
        background-color: #0051D5;
        border-color: #0051D5;
    }
    /* Header con fondo oscuro - sin bordes verticales */
    QHeaderView {
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: none;
        outline: none;
    }
    QHeaderView::section {
        background-color: #1A1D22;
        color: rgba(255, 255, 255, 0.6);
        border: none !important;
        border-left: none !important;
        border-right: none !important;
        border-top: none !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 8px 12px;
        font-family: 'Segoe UI', sans-serif;
        /* font-size: establecido explícitamente */
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    QHeaderView::section:first {
        border-left: none !important;
    }
    QHeaderView::section:last {
        border-right: none !important;
    }
    QHeaderView::section:selected {
        border-left: none !important;
        border-right: none !important;
    }
    QTableCornerButton::section {
        background-color: #1A1D22;
        border: none;
        border-left: none;
        border-right: none;
        border-top: none;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
"""

