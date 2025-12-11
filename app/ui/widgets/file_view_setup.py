"""
FileViewSetup - UI setup for FileViewContainer.

Handles initial UI construction and widget connections.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout

from app.ui.widgets.dock_separator import DockSeparator
from app.ui.widgets.file_grid_view import FileGridView
from app.ui.widgets.file_list_view import FileListView
from app.ui.widgets.focus_dock_widget import FocusDockWidget
from app.ui.widgets.focus_header_panel import FocusHeaderPanel
from app.ui.widgets.view_toolbar import ViewToolbar


def setup_ui(container) -> None:
    """Build the UI layout with view switcher."""
    is_desktop_window = container._check_if_desktop_window()
    
    if is_desktop_window:
        container.setStyleSheet("QWidget { background-color: transparent; }")
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
    
    if is_desktop_window:
        container._focus_panel.hide()
    else:
        layout.addWidget(container._focus_panel)


def _setup_views(container, layout: QVBoxLayout) -> None:
    """Setup grid and list views with dock outside stacked widget."""
    # Create Focus dock widget outside stacked widget (always visible)
    is_desktop_window = container._check_if_desktop_window()
    container._focus_dock = None
    container._dock_separator = None
    
    # No crear FocusDockWidget en Focus mode (se usa sidebar)
    if False and not is_desktop_window and container._tab_manager:
        container._focus_dock = FocusDockWidget(
            container._tab_manager,
            container._icon_service,
            container
        )
        # Connect signals for file drops
        container._focus_dock.files_dropped_on_focus.connect(
            container._on_files_dropped_on_focus
        )
        
        container._dock_separator = DockSeparator(container)
    
    # Create stacked widget with grid and list views
    container._stacked = QStackedWidget()
    container._grid_view = FileGridView(
        container._icon_service, None, container, container._tab_manager, container._state_manager
    )
    container._list_view = FileListView(
        container._icon_service, None, container, container._tab_manager, container._state_manager
    )

    container._stacked.addWidget(container._grid_view)
    container._stacked.addWidget(container._list_view)
    
    # Use horizontal layout: Dock | Separator | StackedWidget
    views_layout = QHBoxLayout()
    views_layout.setContentsMargins(0, 0, 0, 0)
    views_layout.setSpacing(0)
    
    # Add dock and separator if not desktop window
    if container._focus_dock:
        views_layout.addWidget(container._focus_dock)
        if container._dock_separator:
            views_layout.addWidget(container._dock_separator)
    
    # Add stacked widget (takes remaining space)
    views_layout.addWidget(container._stacked, 1)
    
    layout.addLayout(views_layout)


def _connect_view_signals(container) -> None:
    """Connect signals from grid and list views."""
    container._grid_view.open_file.connect(container.open_file.emit)
    container._list_view.open_file.connect(container.open_file.emit)
    
    container._grid_view.file_dropped.connect(container._handlers.handle_file_dropped)
    container._list_view.file_dropped.connect(container._handlers.handle_file_dropped)
    
    container._grid_view.file_deleted.connect(container._handlers.handle_file_deleted)
    container._list_view.file_deleted.connect(container._handlers.handle_file_deleted)
    
    container._grid_view.stack_expand_requested.connect(container._on_stack_expand_requested)
    container._grid_view.expansion_height_changed.connect(container._on_expansion_height_changed)
    container._grid_view.stacks_count_changed.connect(container._on_stacks_count_changed)

