"""
ListStyles - Stylesheet constants for list view.

Contains CSS styles for FileListView table and checkboxes.
"""

LIST_VIEW_STYLESHEET = """
    /* Fondo y contenido transparentes para mantener el estilo visual del modo Grid */
    QTableWidget {
        background-color: transparent;
        border: none;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        color: #E6E7EA;
        gridline-color: transparent;
        selection-background-color: transparent;
        outline: none;
    }
    QTableWidget::item {
        border: none;
        padding: 12px 20px;
        color: #E6E7EA;
        outline: none;
    }
    QTableWidget::item:selected {
        background-color: rgba(255,255,255,0.06);
        color: #E6E7EA;
        border: none;
        outline: none;
    }
    QTableWidget::item:focus {
        outline: none;
        border: none;
    }
    QTableWidget::item:hover {
        background-color: rgba(255,255,255,0.04);
    }
    /* Checkboxes con contraste sobre fondo oscuro */
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
        background-color: #14161A;
        margin-left: 19px;
    }
    QCheckBox::indicator:hover {
        border-color: #66A8FF;
        background-color: #1B1E24;
    }
    QCheckBox::indicator:checked {
        background-color: #3BA55D;
        border-color: #3BA55D;
    }
    QCheckBox::indicator:checked:hover {
        background-color: #349957;
        border-color: #349957;
    }
    /* Header transparente con línea sutil */
    QHeaderView::section {
        background-color: transparent;
        color: #8e92a0;
        border: none;
        border-bottom: 1px solid rgba(255,255,255,0.12);
        padding: 8px 12px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    QTableCornerButton::section {
        background-color: transparent;
        border: none;
        border-bottom: 1px solid rgba(255,255,255,0.12);
    }
"""

