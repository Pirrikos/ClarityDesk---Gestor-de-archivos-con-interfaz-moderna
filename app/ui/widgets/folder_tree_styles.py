"""FolderTreeStyles - Arc Browser inspired stylesheet for FolderTreeSidebar."""

def get_base_stylesheet() -> str:
    """Get base widget stylesheet (Arc-style)."""
    return """
        QWidget#FolderTreeSidebar {
            background-color: #FAFAFA;
            border-right: 1px solid #E5E5E5;
        }
        
        QPushButton#AddButton {
            background-color: transparent;
            border: none;
            font-size: 20px;
            font-weight: 600;
            color: #1A1A1A;
            padding: 8px 12px;
            text-align: left;
            border-radius: 6px;
            margin: 8px 8px 4px 8px;
            min-width: 50px;
        }
        
        QPushButton#AddButton:hover {
            background-color: #F0F0F0;
        }
        
        QPushButton#AddButton:pressed {
            background-color: #E8E8E8;
        }
    """

def get_tree_base_stylesheet() -> str:
    """Get QTreeView base stylesheet (Arc-style)."""
    return """
        QTreeView {
            background-color: transparent;
            color: #1A1A1A;
            border: none;
            outline: none;
            font-size: 13px;
            font-family: "Segoe UI", -apple-system, system-ui;
            font-weight: 500;
            padding: 0px 4px;
        }
        
        QTreeView::item {
            height: 36px;
            min-height: 36px;
            padding: 8px 12px;
            border-radius: 6px;
            margin: 2px 4px;
            border: none;
            background-color: transparent;
        }
        
        QTreeView::item:hover {
            background-color: #F0F0F0;
        }
        
        QTreeView::item:selected {
            background-color: #E8E8E8;
            color: #000000;
            border-left: 3px solid #0066FF;
            padding-left: 12px;
            margin-left: 0px;
        }
        
        QTreeView::item:selected:hover {
            background-color: #E0E0E0;
        }
    """

def get_tree_branch_stylesheet() -> str:
    """Get QTreeView branch stylesheet (Arc-style chevrons)."""
    return """
        QTreeView::branch {
            background-color: transparent;
        }
        
        QTreeView::branch:has-siblings:!adjoins-item,
        QTreeView::branch:has-siblings:adjoins-item,
        QTreeView::branch:!has-children:!has-siblings:adjoins-item {
            border-image: none;
            background: transparent;
        }
        
        /* Chevron collapsed (▶) */
        QTreeView::branch:has-children:!has-siblings:closed,
        QTreeView::branch:closed:has-children:has-siblings {
            border-image: none;
            background: transparent;
            image: none;
            margin: 0px;
        }
        
        /* Chevron expanded (▼) */
        QTreeView::branch:open:has-children:!has-siblings,
        QTreeView::branch:open:has-children:has-siblings {
            border-image: none;
            background: transparent;
            image: none;
            margin: 0px;
        }
    """

def get_scrollbar_stylesheet() -> str:
    """Get scrollbar stylesheet (Arc-style thin scrollbar)."""
    return """
        QScrollBar:vertical {
            background: transparent;
            width: 8px;
            margin: 0px;
            border: none;
        }
        
        QScrollBar::handle:vertical {
            background: #D1D1D6;
            border-radius: 4px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #AEAEB2;
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
            border: none;
        }
        
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: transparent;
        }
    """

def get_button_stylesheet() -> str:
    """Get button-only stylesheet (for direct application to button)."""
    return """
        QPushButton#AddButton {
            background-color: transparent;
            border: none;
            font-size: 16px;
            font-weight: 500;
            color: #1A1A1A;
            padding: 8px 12px;
            text-align: left;
            border-radius: 6px;
            margin: 8px 8px 4px 8px;
        }
        
        QPushButton#AddButton:hover {
            background-color: #F0F0F0;
        }
        
        QPushButton#AddButton:pressed {
            background-color: #E8E8E8;
        }
    """

def get_complete_stylesheet() -> str:
    """Get complete Arc-style stylesheet."""
    return (
        get_base_stylesheet() +
        get_tree_base_stylesheet() +
        get_tree_branch_stylesheet() +
        get_scrollbar_stylesheet()
    )
