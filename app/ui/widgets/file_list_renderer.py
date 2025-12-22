"""
Rendering helpers for FileListView.

Handles UI setup and table row creation.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHeaderView, QTableWidget

from app.models.file_stack import FileStack
from app.ui.utils.font_manager import FontManager
from app.ui.widgets.list_icon_delegate import ListViewDelegate
from app.ui.widgets.list_row_factory import (
    create_checkbox_cell,
    create_date_cell,
    create_extension_cell,
    create_name_cell,
    create_state_cell,
)
from app.ui.widgets.list_styles import LIST_VIEW_STYLESHEET


def setup_ui(view, checkbox_changed_callback, double_click_callback) -> None:
    """Build the UI layout."""
    view.setColumnCount(5)
    view.setHorizontalHeaderLabels(["", "Nombre", "Extensión", "Modificado", "Estado"])
    view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    view.setAlternatingRowColors(False)
    view.setShowGrid(False)
    
    header = view.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    header.resizeSection(0, 60)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
    
    header.setDefaultSectionSize(100)
    header.setHighlightSections(False)
    header.setStretchLastSection(False)
    header.setSectionsMovable(False)
    
    header.setStyleSheet("""
        QHeaderView::section {
            border-left: none !important;
            border-right: none !important;
        }
    """)
    vheader = view.verticalHeader()
    vheader.setVisible(False)
    vheader.setDefaultSectionSize(56)
    vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    
    view.setSortingEnabled(True)
    
    view.setItemDelegateForColumn(0, ListViewDelegate(view, column_index=0))
    view.setItemDelegateForColumn(1, ListViewDelegate(view, column_index=1))
    view.setItemDelegateForColumn(2, ListViewDelegate(view, column_index=2))
    view.setItemDelegateForColumn(3, ListViewDelegate(view, column_index=3))
    view.setItemDelegateForColumn(4, ListViewDelegate(view, column_index=4))
    
    view.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
    view.setShowGrid(False)
    
    view.setFrameShape(QTableWidget.Shape.NoFrame)
    view.setFrameShadow(QTableWidget.Shadow.Plain)
    
    view.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
    
    # NO aplicar estilo personalizado ni viewport personalizado durante construcción inicial
    # Se activarán después del primer show para evitar flash de ventana marrón/blanca
    
    view.setStyleSheet(LIST_VIEW_STYLESHEET)
    
    FontManager.safe_set_font(
        view,
        'Segoe UI',
        FontManager.SIZE_LARGE,
        QFont.Weight.Normal
    )
    
    FontManager.safe_set_font(
        header,
        'Segoe UI',
        FontManager.SIZE_NORMAL,
        QFont.Weight.DemiBold
    )
    
    # NO reemplazar viewport durante construcción inicial
    # Se activará después del primer show para evitar flash de ventana marrón/blanca
    view.viewport().setStyleSheet("""
        QWidget {
            background-color: #111318;
            border: none;
            border-left: none;
            border-right: none;
            border-top: none;
            border-bottom: none;
        }
    """)
    view.itemDoubleClicked.connect(double_click_callback)
    view.setDragEnabled(True)
    view.setAcceptDrops(True)
    view.setDropIndicatorShown(True)


def expand_stacks_to_files(file_list: list) -> list[str]:
    """Expand stacks to individual files for list view."""
    expanded_files = []
    for item in file_list:
        if isinstance(item, FileStack):
            expanded_files.extend(item.files)
        else:
            expanded_files.append(item)
    return expanded_files


def refresh_table(view, files: list[str], icon_service, state_manager, checked_paths: set, checkbox_changed_callback) -> None:
    """Rebuild table rows from file list."""
    view.setRowCount(len(files))
    for row, file_path in enumerate(files):
        create_row(view, row, file_path, icon_service, state_manager, checked_paths, checkbox_changed_callback)


def create_row(view, row: int, file_path: str, icon_service, state_manager, checked_paths: set, checkbox_changed_callback) -> None:
    """Create a single table row with all columns."""
    font = view.font()
    
    view.setCellWidget(row, 0, create_checkbox_cell(
        file_path, file_path in checked_paths, checkbox_changed_callback))
    name_item = create_name_cell(file_path, icon_service, font)
    name_item.setData(Qt.ItemDataRole.UserRole, file_path)
    view.setItem(row, 1, name_item)
    view.setItem(row, 2, create_extension_cell(file_path, font))
    view.setItem(row, 3, create_date_cell(file_path, font))
    
    state = state_manager.get_file_state(file_path) if state_manager else None
    state_widget = create_state_cell(state, font)
    view.setCellWidget(row, 4, state_widget)
    
    view.setRowHeight(row, 56)

