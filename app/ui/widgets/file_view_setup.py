"""
FileViewSetup - UI setup for FileViewContainer.

Handles initial UI construction and widget connections.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QStackedWidget, QVBoxLayout
from PySide6.QtGui import QColor

from app.core.constants import CENTRAL_AREA_BG, FILE_VIEW_LEFT_MARGIN
from app.core.logger import get_logger

from app.ui.widgets.file_grid_view import FileGridView
from app.ui.widgets.file_list_view import FileListView
from app.ui.widgets.focus_header_panel import FocusHeaderPanel
from app.ui.widgets.path_footer_widget import PathFooterWidget

logger = get_logger(__name__)
logger.debug("🚀 Loading file_view_setup.py")

def setup_ui(container: "FileViewContainer") -> None:
    """Build the UI layout with view switcher."""
    is_desktop_window = container._is_desktop
    if is_desktop_window:
        container.setStyleSheet("QWidget { background-color: transparent; }")
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    else:
        container.setObjectName("FileViewContainer")
        container.setStyleSheet("QWidget#FileViewContainer { background-color: transparent; }")
    
    layout = QVBoxLayout(container)
    left_margin = FILE_VIEW_LEFT_MARGIN if not is_desktop_window else 0
    layout.setContentsMargins(left_margin, 0, 0, 0)
    layout.setSpacing(0)
    
    _setup_toolbar(container, layout, is_desktop_window)
    _setup_focus_panel(container, layout, is_desktop_window)
    _setup_views(container, layout)
    _setup_footer(container, layout, is_desktop_window)
    _connect_view_signals(container)


def _setup_toolbar(container: "FileViewContainer", layout: QVBoxLayout, is_desktop_window: bool) -> None:
    """Configurar toolbar con espaciado mínimo."""
    if not is_desktop_window:
        layout.addSpacing(4)
    container._toolbar = None


def _setup_focus_panel(container: "FileViewContainer", layout: QVBoxLayout, is_desktop_window: bool) -> None:
    """Setup focus header panel."""
    container._focus_panel = FocusHeaderPanel(container)
    container._focus_panel.rename_clicked.connect(container._on_rename_clicked)
    container._focus_panel.hide()


def _setup_views(container: "FileViewContainer", layout: QVBoxLayout) -> None:
    """Setup grid y list views sin panel dock."""
    desktop_window: Optional["DesktopWindow"] = None
    if container._is_desktop:
        from app.ui.windows.desktop_window import DesktopWindow
        parent = container.parent()
        while parent:
            if isinstance(parent, DesktopWindow):
                desktop_window = parent
                break
            parent = parent.parent()
    
    container._stacked = QStackedWidget()
    container._stacked.setAutoFillBackground(False)
    # Asegurar que el stacked expanda para rellenar el alto disponible
    from PySide6.QtWidgets import QSizePolicy
    container._stacked.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    container._stacked.setContentsMargins(0, 0, 0, 0)
    if container._is_desktop:
        container._stacked.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        container._stacked.setStyleSheet("""
            QStackedWidget { 
                background-color: transparent;
                border: none;
                border-left: none;
                border-right: none;
                border-top: none;
                border-bottom: none;
            }
        """)
    else:
        container._stacked.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        container._stacked.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        container._stacked.setAutoFillBackground(True)
        palette = container._stacked.palette()
        palette.setColor(container._stacked.backgroundRole(), QColor(CENTRAL_AREA_BG))
        container._stacked.setPalette(palette)
        container._stacked.setStyleSheet(f"""
            QStackedWidget {{ 
                background-color: {CENTRAL_AREA_BG};
                border: none;
            }}
        """)
    container._grid_view = FileGridView(
        container._icon_service,
        None,
        container._stacked,
        container._tab_manager,
        container._state_manager,
        is_desktop=container._is_desktop,
        desktop_window=desktop_window,
        get_label_callback=container._get_label_callback
    )
    container._list_view = FileListView(
        icon_service=container._icon_service,
        parent=container,
        tab_manager=container._tab_manager,
        state_manager=container._state_manager,
        get_label_callback=container._get_label_callback
    )

    container._stacked.addWidget(container._grid_view)
    container._stacked.addWidget(container._list_view)
    
    views_layout = QHBoxLayout()
    views_layout.setContentsMargins(0, 0, 0, 0)
    views_layout.setSpacing(0)
    
    views_layout.addWidget(container._stacked, 1)
    
    layout.addLayout(views_layout, 1)


def _setup_footer(container: "FileViewContainer", layout: QVBoxLayout, is_desktop_window: bool) -> None:
    """Setup footer widget for displaying selected file path."""
    if is_desktop_window:
        container._path_footer = None
        return
    
    container._path_footer = PathFooterWidget(container)
    container._path_footer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    container._path_footer.setStyleSheet("""
        QWidget {
            background-color: #F5F5F7;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
        }
    """)
    layout.addWidget(container._path_footer, 0)


def _connect_view_signals(container: "FileViewContainer") -> None:
    """Connect signals from grid and list views."""
    container._grid_view.open_file.connect(container._on_open_file)
    container._list_view.open_file.connect(container._on_open_file)
    
    def _on_file_dropped(source_file_path: str) -> None:
        """Handle file drop and emit folder_moved signal if folder was moved."""
        success, old_path, new_path = container._handlers.handle_file_dropped(source_file_path)
        if success and new_path:
            container.folder_moved.emit(old_path, new_path)
    
    container._grid_view.file_dropped.connect(_on_file_dropped)
    container._list_view.file_dropped.connect(_on_file_dropped)
    
    container._grid_view.file_deleted.connect(container._handlers.handle_file_deleted)
    container._list_view.file_deleted.connect(container._handlers.handle_file_deleted)
    
    container._grid_view.folder_moved.connect(container.folder_moved.emit)
    container._list_view.folder_moved.connect(container.folder_moved.emit)
    
    container._grid_view.expansion_height_changed.connect(container._on_expansion_height_changed)
    container._grid_view.stacks_count_changed.connect(container._on_stacks_count_changed)
