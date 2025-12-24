"""
Rendering helpers for FileListView.

Handles UI setup and table row creation.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QHeaderView, QTableWidget, QVBoxLayout, QWidget

from app.models.file_stack import FileStack
from app.ui.utils.font_manager import FontManager
from app.ui.widgets.list_checkbox import CustomCheckBox
from app.ui.widgets.list_icon_delegate import ListViewDelegate
from app.ui.widgets.list_row_factory import (
    create_checkbox_cell,
    create_date_cell,
    create_extension_cell,
    create_name_cell,
    create_state_cell,
)
from app.ui.widgets.list_styles import LIST_VIEW_STYLESHEET
from app.core.constants import CENTRAL_AREA_BG


def create_header_checkbox(view) -> QCheckBox:
    """Create checkbox for header that selects/deselects all files."""
    checkbox = CustomCheckBox()
    checkbox.setText("")
    checkbox.setCheckState(Qt.CheckState.Unchecked)
    checkbox.setTristate(True)  # Permite estado indeterminado
    
    def on_header_checkbox_changed(state: int) -> None:
        """Handle header checkbox state change."""
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            view.select_all_files()
        elif Qt.CheckState(state) == Qt.CheckState.Unchecked:
            view.deselect_all_files()
        # Si está en estado indeterminado, no hacer nada (es solo visual)
    
    checkbox.stateChanged.connect(on_header_checkbox_changed)
    return checkbox


def setup_header_checkbox(view, header: QHeaderView) -> None:
    """Setup checkbox widget in header's first section."""
    checkbox = create_header_checkbox(view)
    view._header_checkbox = checkbox
    
    # Crear contenedor para posicionar el checkbox
    container = QWidget(header)
    container.setStyleSheet("QWidget { background-color: transparent; border: none; }")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(checkbox)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Posicionar el widget en la primera sección del header
    def update_checkbox_position():
        """Update checkbox position when header is resized."""
        if header.count() > 0:
            section_x = header.sectionPosition(0)
            section_width = header.sectionSize(0)
            header_height = header.height()
            # Calcular posición exacta: checkbox centrado en celda de 15px
            # Los checkboxes de las filas están centrados en la celda, así que el header debe estar igual
            checkbox_width = 15  # Ancho del widget (el indicador visual es 11px)
            # Centrar el checkbox en la columna reducida
            container.setGeometry(section_x, 0, section_width, header_height)
    
    # Conectar señal de cambio de tamaño del header
    header.sectionResized.connect(lambda logical_index, old_size, new_size: update_checkbox_position() if logical_index == 0 else None)
    header.geometriesChanged.connect(lambda: update_checkbox_position())
    
    # Posicionar inicialmente después de que el header esté visible
    from PySide6.QtCore import QTimer
    QTimer.singleShot(0, update_checkbox_position)
    container.show()


def setup_ui(view, checkbox_changed_callback, double_click_callback) -> None:
    """Build the UI layout."""
    view.setColumnCount(5)
    view.setHorizontalHeaderLabels(["", "Nombre", "Tipo", "Fecha", "Estado"])
    view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    view.setAlternatingRowColors(False)
    view.setShowGrid(False)
    
    header = view.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    header.resizeSection(0, 59)  # 15px + 44px de margen izquierdo
    
    # Agregar checkbox en el header de la primera columna
    setup_header_checkbox(view, header)
    # Columna "Nombre" se expande para ocupar el espacio disponible
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    header.setMinimumSectionSize(100)  # Ancho mínimo para evitar que se haga muy pequeña
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
    
    header.setDefaultSectionSize(100)
    header.setHighlightSections(False)
    # No estirar la última columna - la columna "Nombre" asume la expansión
    header.setSectionsMovable(False)
    
    # Asegurar que solo haya exactamente 5 columnas y ocultar cualquier columna extra
    if view.columnCount() > 5:
        # Si hay más columnas, reducir a 5
        view.setColumnCount(5)
    # Ocultar cualquier columna extra que pueda aparecer después
    for i in range(5, view.columnCount()):
        view.setColumnHidden(i, True)
    
    header.setStyleSheet("""
        QHeaderView::section {
            border-left: none !important;
            border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
        }
        QHeaderView::section:last {
            border-right: none !important;
        }
    """)
    
    # Asegurar que el header solo muestre las 5 columnas definidas
    # Esto previene que aparezcan columnas adicionales
    header.setVisible(True)
    if header.count() > 5:
        # Si el header tiene más secciones, forzar a 5
        view.setColumnCount(5)
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
    view.viewport().setStyleSheet(f"""
        QWidget {{
            background-color: {CENTRAL_AREA_BG};
            border: none;
            border-left: none;
            border-right: none;
            border-top: none;
            border-bottom: none;
        }}
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
    # Asegurar que solo haya 5 columnas
    if view.columnCount() != 5:
        view.setColumnCount(5)
    # Ocultar cualquier columna extra
    for i in range(5, view.columnCount()):
        view.setColumnHidden(i, True)
    
    view.setRowCount(len(files))
    for row, file_path in enumerate(files):
        create_row(view, row, file_path, icon_service, state_manager, checked_paths, checkbox_changed_callback)
    
    # Actualizar estado del checkbox del header después de refrescar
    if hasattr(view, '_update_header_checkbox_state'):
        view._update_header_checkbox_state()


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

