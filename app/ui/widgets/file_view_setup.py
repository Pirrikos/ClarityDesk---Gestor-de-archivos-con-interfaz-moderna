"""
FileViewSetup - UI setup for FileViewContainer.

Handles initial UI construction and widget connections.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout

from app.ui.widgets.file_grid_view import FileGridView
from app.ui.widgets.file_list_view import FileListView
from app.ui.widgets.focus_header_panel import FocusHeaderPanel
from app.ui.widgets.view_toolbar import ViewToolbar


def setup_ui(container) -> None:
    """Build the UI layout with view switcher."""
    is_desktop_window = container._check_if_desktop_window()
    # Fondo transparente para unificar estilo entre Grid y Lista
    container.setStyleSheet("QWidget { background-color: transparent; }")
    if is_desktop_window:
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    _setup_toolbar(container, layout, is_desktop_window)
    _setup_focus_panel(container, layout, is_desktop_window)
    _setup_views(container, layout)
    _connect_view_signals(container)


def _setup_toolbar(container, layout: QVBoxLayout, is_desktop_window: bool) -> None:
    """Setup toolbar with view toggle buttons."""
    from app.ui.widgets.file_view_sync import switch_view
    from app.ui.widgets.file_view_tabs import on_nav_back, on_nav_forward
    
    container._toolbar = ViewToolbar(container)
    container._grid_button = container._toolbar.get_grid_button()
    container._list_button = container._toolbar.get_list_button()
    container._grid_button.clicked.connect(lambda: switch_view(container, "grid"))
    container._list_button.clicked.connect(lambda: switch_view(container, "list"))
    container._toolbar.state_button_clicked.connect(container._on_state_button_clicked)
    container._toolbar.navigation_back.connect(lambda: on_nav_back(container))
    container._toolbar.navigation_forward.connect(lambda: on_nav_forward(container))
    
    if is_desktop_window:
        container._toolbar.hide()
    else:
        layout.addWidget(container._toolbar)


def _setup_focus_panel(container, layout: QVBoxLayout, is_desktop_window: bool) -> None:
    """Setup focus header panel."""
    container._focus_panel = FocusHeaderPanel(container)
    container._focus_panel.rename_clicked.connect(container._on_rename_clicked)
    # Ocultar siempre el panel de encabezado para eliminar el "cuadrado blanco" visual,
    # manteniendo la lógica de ruta y selección disponible para uso futuro.
    container._focus_panel.hide()


def _setup_views(container, layout: QVBoxLayout) -> None:
    """Setup grid y list views sin panel dock."""
    # Create stacked widget with grid and list views
    container._stacked = QStackedWidget()
    container._stacked.setStyleSheet("QStackedWidget { background-color: transparent; }")
    container._grid_view = FileGridView(
        container._icon_service, None, container, container._tab_manager, container._state_manager
    )
    container._list_view = FileListView(
        container._icon_service, None, container, container._tab_manager, container._state_manager
    )

    container._stacked.addWidget(container._grid_view)
    container._stacked.addWidget(container._list_view)
    
    # Use horizontal layout: solo contenido
    views_layout = QHBoxLayout()
    views_layout.setContentsMargins(0, 0, 0, 0)
    views_layout.setSpacing(0)
    
    # Add stacked widget (takes remaining space)
    views_layout.addWidget(container._stacked, 1)
    
    layout.addLayout(views_layout)


def _connect_view_signals(container) -> None:
    """Connect signals from grid and list views."""
    # Enrutar por método centralizado:
    # - Aplica umbral anti-doble clic para evitar aperturas accidentales
    # - Muestra feedback visual breve (cursor ocupado) para mejorar UX
    container._grid_view.open_file.connect(container._on_open_file)
    container._list_view.open_file.connect(container._on_open_file)
    
    container._grid_view.file_dropped.connect(container._handlers.handle_file_dropped)
    container._list_view.file_dropped.connect(container._handlers.handle_file_dropped)
    
    container._grid_view.file_deleted.connect(container._handlers.handle_file_deleted)
    container._list_view.file_deleted.connect(container._handlers.handle_file_deleted)
    
    container._grid_view.stack_expand_requested.connect(container._on_stack_expand_requested)
    container._grid_view.expansion_height_changed.connect(container._on_expansion_height_changed)
    container._grid_view.stacks_count_changed.connect(container._on_stacks_count_changed)

