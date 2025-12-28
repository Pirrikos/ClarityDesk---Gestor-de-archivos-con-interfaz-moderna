"""
Rendering helpers for FileListView.

Handles UI setup and table row creation.
"""

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import QCheckBox, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

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


def _ensure_column_count(view: QTableWidget, count: int) -> None:
    """Ensure table has exactly the specified number of columns."""
    if view.columnCount() > count:
        view.setColumnCount(count)
    for i in range(count, view.columnCount()):
        view.setColumnHidden(i, True)


def create_header_checkbox(view) -> QCheckBox:
    """Create checkbox for header that selects/deselects all files."""
    checkbox = CustomCheckBox()
    checkbox.setText("")
    checkbox.setCheckState(Qt.CheckState.Unchecked)
    checkbox.setTristate(True)  # Permite estado indeterminado
    
    def on_header_checkbox_changed(state: int) -> None:
        """Handle header checkbox state change."""
        # Ignorar estado PartiallyChecked - solo se establece programáticamente
        # cuando algunos archivos están seleccionados pero no todos
        if Qt.CheckState(state) == Qt.CheckState.PartiallyChecked:
            return
        
        # Solo responder a cambios explícitos a Checked o Unchecked desde clic del usuario
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            view.select_all_files()
        elif Qt.CheckState(state) == Qt.CheckState.Unchecked:
            view.deselect_all_files()
    
    checkbox.stateChanged.connect(on_header_checkbox_changed)
    return checkbox


def _update_header_checkbox_position(container: QWidget, header: QHeaderView) -> None:
    """Update checkbox position when header is resized."""
    if header.count() > 0:
        section_x = header.sectionPosition(0)
        section_width = header.sectionSize(0)
        header_height = header.height()
        # Desplazado 8px a la derecha y 2px hacia abajo para alineación visual
        container.setGeometry(section_x + 8, 2, max(section_width, 20), header_height)


def _update_header_checkbox_visibility(container: QWidget, view: QTableWidget) -> None:
    """Update checkbox visibility based on horizontal scroll."""
    scrollbar = view.horizontalScrollBar()
    if scrollbar:
        scroll_value = scrollbar.value()
        # Mostrar solo cuando value == 0, ocultar cuando value > 0
        if scroll_value == 0:
            container.setVisible(True)
        else:
            container.setVisible(False)


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
    checkbox.setFixedSize(15, 15)
    
    # Conectar señal de cambio de tamaño del header
    def on_section_resized(logical_index: int, old_size: int, new_size: int) -> None:
        if logical_index == 0:
            _update_header_checkbox_position(container, header)
    
    header.sectionResized.connect(on_section_resized)
    header.geometriesChanged.connect(lambda: _update_header_checkbox_position(container, header))
    
    # Conectar scroll horizontal para mostrar/ocultar checkbox
    scrollbar = view.horizontalScrollBar()
    if scrollbar:
        scrollbar.valueChanged.connect(lambda: _update_header_checkbox_visibility(container, view))
    
    # Posicionar inicialmente después de que el header esté visible
    QTimer.singleShot(0, lambda: _update_header_checkbox_position(container, header))
    # Actualizar visibilidad inicial
    _update_header_checkbox_visibility(container, view)


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
    header.resizeSection(0, 16)  # Ancho mínimo: 15px widget + 1px margen de seguridad
    
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
    
    _ensure_column_count(view, 5)
    
    header.setStyleSheet("""
        QHeaderView::section {
            border-left: none !important;
            border-right: none !important;
        }
        QHeaderView::section:last {
            border-right: none !important;
        }
    """)
    
    header.setVisible(True)
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
    
    # La paleta ya no se usa, el delegate obtiene el color directamente desde AppSettings
    
    view.setStyleSheet(LIST_VIEW_STYLESHEET)
    
    FontManager.safe_set_font(
        view,
        'Segoe UI',
        12,  # Reducido de SIZE_LARGE (14px) a 12px
        QFont.Weight.Normal
    )
    
    FontManager.safe_set_font(
        header,
        'Segoe UI',
        FontManager.SIZE_NORMAL,
        QFont.Weight.DemiBold
    )
    
    view.viewport().setStyleSheet("""
        QWidget {
            background-color: transparent;
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


def refresh_table(view, files: list[str], icon_service, state_manager, checked_paths: set, checkbox_changed_callback, get_label_callback=None) -> None:
    """Rebuild table rows from file list."""
    _ensure_column_count(view, 5)
    
    # Soft reveal: ocultar viewport inicialmente durante construcción
    viewport_was_visible = view.viewport().isVisible()
    if viewport_was_visible and len(files) > 0:
        view.viewport().setVisible(False)
    
    view.setRowCount(len(files))
    for row, file_path in enumerate(files):
        create_row(view, row, file_path, icon_service, state_manager, checked_paths, checkbox_changed_callback, get_label_callback)
    
    # Revelar viewport en siguiente ciclo con micro-fade
    if len(files) > 0:
        QTimer.singleShot(0, lambda: _reveal_viewport_with_fade(view))
    
    # Actualizar estado del checkbox del header después de refrescar
    if hasattr(view, '_update_header_checkbox_state'):
        view._update_header_checkbox_state()


def create_row(view, row: int, file_path: str, icon_service, state_manager, checked_paths: set, checkbox_changed_callback, get_label_callback=None) -> None:
    """Create a single table row with all columns."""
    font = view.font()
    
    view.setCellWidget(row, 0, create_checkbox_cell(
        file_path, file_path in checked_paths, checkbox_changed_callback, view))
    name_item = create_name_cell(file_path, icon_service, font)
    name_item.setData(Qt.ItemDataRole.UserRole, file_path)
    view.setItem(row, 1, name_item)
    view.setItem(row, 2, create_extension_cell(file_path, font))
    view.setItem(row, 3, create_date_cell(file_path, font))
    
    state = state_manager.get_file_state(file_path) if state_manager else None
    state_widget = create_state_cell(state, font, view, get_label_callback)
    view.setCellWidget(row, 4, state_widget)
    view.setRowHeight(row, 56)


def _reveal_viewport_with_fade(view: QTableWidget) -> None:
    """Revelar viewport con micro-fade ≤120ms."""
    try:
        viewport = view.viewport()
        viewport.setVisible(True)
        viewport.setWindowOpacity(0.0)
        
        fade_anim = QPropertyAnimation(viewport, b"windowOpacity", viewport)
        fade_anim.setDuration(100)  # ≤120ms para rapidez percibida
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        fade_anim.start()
    except RuntimeError:
        # Widget fue destruido, simplemente mostrar
        try:
            viewport = view.viewport()
            viewport.setVisible(True)
            viewport.setWindowOpacity(1.0)
        except RuntimeError:
            pass

