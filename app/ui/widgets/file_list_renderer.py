"""
Renderizado para FileListView.

Gestiona la configuración de UI y la creación de filas de la tabla.
"""
import os

from typing import Optional, Callable
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import QCheckBox, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.models.file_stack import FileStack
from app.ui.utils.font_manager import FontManager
from app.ui.widgets.list_checkbox import CustomCheckBox
from app.ui.widgets.list_icon_delegate import ListViewDelegate
from app.ui.widgets.list_name_delegate import ListNameDelegate
from app.ui.widgets.list_row_factory import (
    create_checkbox_cell,
    create_date_cell,
    create_extension_cell,
    create_name_cell,
    create_state_cell,
)
from app.ui.widgets.list_styles import LIST_VIEW_STYLESHEET
from app.core.constants import CENTRAL_AREA_BG
from app.services.icon_service import IconService
from app.managers.file_state_manager import FileStateManager
from app.managers.tab_manager import TabManager


def _ensure_column_count(view: QTableWidget, count: int) -> None:
    """Asegurar que la tabla tenga exactamente el número de columnas especificado."""
    if view.columnCount() > count:
        view.setColumnCount(count)
    for i in range(count, view.columnCount()):
        view.setColumnHidden(i, True)


def create_header_checkbox(view: QTableWidget, parent: Optional[QWidget] = None) -> QCheckBox:
    """Crear checkbox para el header que selecciona/deselecciona todos los archivos."""
    checkbox = CustomCheckBox(parent)
    checkbox.setText("")
    checkbox.setCheckState(Qt.CheckState.Unchecked)
    checkbox.setTristate(True)  # Permite estado indeterminado
    
    def on_header_checkbox_changed(state: int) -> None:
        """Manejar cambio de estado del checkbox del header."""
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
    """Actualizar posición del checkbox cuando el header cambia de tamaño."""
    if header.count() > 0:
        section_x = header.sectionPosition(0)
        section_width = header.sectionSize(0)
        header_height = header.height()
        # Desplazado 8px a la derecha y 2px hacia abajo para alineación visual
        container.setGeometry(section_x + 8, 2, max(section_width, 20), header_height)


def _update_header_checkbox_visibility(container: QWidget, view: QTableWidget) -> None:
    """Actualizar visibilidad del checkbox según el scroll horizontal."""
    scrollbar = view.horizontalScrollBar()
    if scrollbar:
        scroll_value = scrollbar.value()
        # Mostrar solo cuando value == 0, ocultar cuando value > 0
        if scroll_value == 0:
            container.setVisible(True)
        else:
            container.setVisible(False)


def setup_header_checkbox(view: QTableWidget, header: QHeaderView) -> None:
    """Configurar widget checkbox en la primera sección del header."""
    # Crear contenedor primero para establecer el parent explícito del checkbox
    container = QWidget(header)
    container.setStyleSheet("QWidget { background-color: transparent; border: none; }")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    checkbox = create_header_checkbox(view, parent=container)
    view._header_checkbox = checkbox
    layout.addWidget(checkbox)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    checkbox.setFixedSize(15, 15)
    
    # Coalescer reposición para evitar repintados por píxel durante resize
    repos_timer = QTimer(container)
    repos_timer.setSingleShot(True)
    repos_timer.setInterval(80)  # Comentario: coalesce suave durante drag
    def schedule_reposition(*_args) -> None:
        # Bloquear señales durante el resize para evitar cascada de eventos
        header.blockSignals(True)
        repos_timer.stop()
        repos_timer.start()
        header.blockSignals(False)
        
    repos_timer.timeout.connect(lambda: _update_header_checkbox_position(container, header))
    # header.sectionResized.connect(schedule_reposition)
    # header.geometriesChanged.connect(schedule_reposition)
    
    # Conectar scroll horizontal para mostrar/ocultar checkbox
    scrollbar = view.horizontalScrollBar()
    if scrollbar:
        scrollbar.valueChanged.connect(lambda: _update_header_checkbox_visibility(container, view))
    
    # Posicionar inicialmente después de que el header esté visible
    QTimer.singleShot(0, lambda: _update_header_checkbox_position(container, header))
    # Actualizar visibilidad inicial
    _update_header_checkbox_visibility(container, view)


def setup_ui(view: QTableWidget, checkbox_changed_callback: Callable[[str, int], None], double_click_callback: Callable[[QTableWidgetItem], None]) -> None:
    """Construir el layout de la UI."""
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
    # CONFIRMADO DEFINITIVO: Stretch causa parpadeo SIEMPRE en PySide6/Qt
    # Probado en columnas 1 (Nombre) y 4 (Estado) - ambas causan parpadeo
    # SOLUCIÓN FINAL: Todas las columnas Interactive (ancho fijo manual)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
    header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)

    header.setMinimumSectionSize(100)  # Ancho mínimo para evitar que se haga muy pequeña

    # Establecer anchos iniciales razonables
    header.resizeSection(1, 300)  # Nombre - ancho generoso (mínimo, puede expandirse)
    header.resizeSection(2, 100)  # Tipo
    header.resizeSection(3, 150)  # Fecha
    header.resizeSection(4, 120)  # Estado

    # Evitar que la columna Nombre se haga más pequeña que su ancho inicial
    MIN_NAME_COLUMN_WIDTH = 300

    def on_section_resized(logical_index: int, old_size: int, new_size: int) -> None:
        """Prevent Name column from shrinking below minimum width."""
        if logical_index == 1 and new_size < MIN_NAME_COLUMN_WIDTH:
            # Restaurar ancho mínimo sin disparar señal recursiva
            header.blockSignals(True)
            header.resizeSection(1, MIN_NAME_COLUMN_WIDTH)
            header.blockSignals(False)

    header.sectionResized.connect(on_section_resized)

    header.setDefaultSectionSize(100)
    header.setHighlightSections(False)
    # Todas las columnas tienen ancho fijo manual - sin expansión automática
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
    view.setItemDelegateForColumn(1, ListNameDelegate(view))  # Custom delegate for workspace text
    view.setItemDelegateForColumn(2, ListViewDelegate(view, column_index=2))
    view.setItemDelegateForColumn(3, ListViewDelegate(view, column_index=3))
    view.setItemDelegateForColumn(4, ListViewDelegate(view, column_index=4))
    
    view.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
    view.setShowGrid(False)
    
    view.setFrameShape(QTableWidget.Shape.NoFrame)
    view.setFrameShadow(QTableWidget.Shadow.Plain)
    
    # Respetar atributos del view definidos por FileListView
    
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
    
    # Mantener estilo del viewport definido por FileListView
    view.itemDoubleClicked.connect(double_click_callback)
    view.setDragEnabled(True)
    view.setAcceptDrops(True)
    view.setDropIndicatorShown(True)


def expand_stacks_to_files(file_list: list) -> list[str]:
    """Expandir stacks a archivos individuales para la vista de lista."""
    expanded_files = []
    for item in file_list:
        if isinstance(item, FileStack):
            expanded_files.extend(item.files)
        else:
            expanded_files.append(item)
    return expanded_files


def refresh_table(
    view: QTableWidget,
    files: list[str],
    icon_service: Optional[IconService],
    state_manager: Optional[FileStateManager],
    checked_paths: set,
    checkbox_changed_callback: Callable[[str, int], None],
    get_label_callback: Optional[Callable] = None,
    tab_manager: Optional[TabManager] = None,
    workspace_manager: Optional['WorkspaceManager'] = None
) -> None:
    """Reconstruir filas de la tabla a partir de la lista de archivos."""
    _ensure_column_count(view, 5)

    # Eliminado el "Soft reveal" que ocultaba el viewport.
    # Esto evita que se vea el escritorio a través de la transparencia del padre durante la navegación.

    view.setRowCount(len(files))
    for row, file_path in enumerate(files):
        create_row(
            view,
            row,
            file_path,
            icon_service,
            state_manager,
            checked_paths,
            checkbox_changed_callback,
            get_label_callback,
            tab_manager,
            workspace_manager
        )

    # OPTIMIZACIÓN: No ajustar columnas automáticamente para evitar recálculos costosos
    # Los anchos iniciales ya están definidos en setup_ui() (líneas 147-150)
    # El modo Interactive permite al usuario ajustar manualmente si lo necesita
    # Esto elimina un punto de recálculo costoso durante cada navegación

    # Solo asegurar que la columna 0 (checkbox) mantenga su ancho mínimo fijo
    view.setColumnWidth(0, 16)

    # Actualizar estado del checkbox del header después de refrescar
    if hasattr(view, '_update_header_checkbox_state'):
        view._update_header_checkbox_state()


def create_row(
    view: QTableWidget,
    row: int,
    file_path: str,
    icon_service: Optional[IconService],
    state_manager: Optional[FileStateManager],
    checked_paths: set,
    checkbox_changed_callback: Callable[[str, int], None],
    get_label_callback: Optional[Callable] = None,
    tab_manager: Optional[TabManager] = None,
    workspace_manager: Optional['WorkspaceManager'] = None
) -> None:
    """Crear una fila de tabla con todas las columnas."""
    font = view.font()

    # Resolver workspace_name solo si estamos en modo navegación por estado
    workspace_name = None

    if tab_manager and hasattr(tab_manager, 'has_state_context'):
        is_state_mode = tab_manager.has_state_context()

        if is_state_mode and workspace_manager:
            from app.services.workspace_path_resolver import get_workspace_name_for_path
            workspace_name = get_workspace_name_for_path(file_path, workspace_manager)

    view.setCellWidget(row, 0, create_checkbox_cell(
        file_path, file_path in checked_paths, checkbox_changed_callback, view))
    name_item = create_name_cell(file_path, icon_service, font, workspace_name)
    name_item.setData(Qt.ItemDataRole.UserRole, file_path)
    view.setItem(row, 1, name_item)
    view.setItem(row, 2, create_extension_cell(file_path, font))
    view.setItem(row, 3, create_date_cell(file_path, font))

    state = state_manager.get_file_state(file_path) if state_manager else None
    state_widget = create_state_cell(state, font, view, get_label_callback)
    view.setCellWidget(row, 4, state_widget)
    view.setRowHeight(row, 56)
