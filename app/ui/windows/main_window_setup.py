"""
UI setup helpers for MainWindow.

Handles window layout and widget creation.
Focus Dock is now integrated directly in FileViewContainer.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout, QWidget, QSizeGrip, QSizePolicy

from app.core.constants import DEBUG_LAYOUT
from app.core.logger import get_logger
from app.ui.widgets.app_header import AppHeader
from app.ui.widgets.secondary_header import SecondaryHeader
from app.ui.widgets.file_box_history_panel_sidebar import FileBoxHistoryPanelSidebar
from app.ui.widgets.file_view_container import FileViewContainer
from app.ui.widgets.file_view_sync import switch_view
from app.ui.widgets.file_view_tabs import on_nav_back, on_nav_forward
from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar
from app.ui.widgets.raycast_panel import RaycastPanel
from app.ui.widgets.window_header import WindowHeader
from app.ui.widgets.workspace_selector import WorkspaceSelector

HEADER_BG = "#F5F5F7"
HEADER_BORDER = "rgba(0, 0, 0, 0.1)"
APP_HEADER_BG = "#1A1D22"
APP_HEADER_BORDER = "#2A2E36"
SIDEBAR_BG = "#E8E8ED"
SIDEBAR_BORDER = "rgba(0, 0, 0, 0.12)"


def setup_ui(window, tab_manager, icon_service, workspace_manager) -> tuple[FileViewContainer, FolderTreeSidebar, WindowHeader, AppHeader, SecondaryHeader, WorkspaceSelector, FileBoxHistoryPanelSidebar]:
    try:
        root_layout = QVBoxLayout(window)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        window_header = WindowHeader(window)
        root_layout.addWidget(window_header, 0)
        
        app_header = AppHeader(window)
        app_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        root_layout.addWidget(app_header, 0)
        
        secondary_header = SecondaryHeader(window)
        secondary_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        root_layout.addWidget(secondary_header, 0)
        
        workspace_selector = WorkspaceSelector(window)
        workspace_selector.set_workspace_manager(workspace_manager)
        root_layout.addWidget(workspace_selector, 0)
        
        central_widget = RaycastPanel(window)
        central_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        
        # Main splitter: sidebar | content | history panel
        main_splitter = QSplitter(Qt.Orientation.Horizontal, central_widget)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(4)
        main_splitter.setStyleSheet("""
            QSplitter {
                background-color: transparent;
            }
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
            }
            QSplitter::handle:hover {
                background-color: rgba(255, 255, 255, 0.15);
                border: none;
            }
            QSplitter::handle:horizontal {
                width: 4px;
                margin: 0px;
            }
        """)
        
        # Content splitter: sidebar | file view | file box panel
        content_splitter = QSplitter(Qt.Orientation.Horizontal, main_splitter)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setHandleWidth(4)
        content_splitter.setStyleSheet(main_splitter.styleSheet())
        
        sidebar = FolderTreeSidebar(content_splitter)
        file_view_container = FileViewContainer(
            tab_manager,
            icon_service,
            None,
            content_splitter
        )
        
        # File box panel (initially hidden)
        file_box_panel_placeholder = QWidget(content_splitter)  # Placeholder, will be replaced
        file_box_panel_placeholder.hide()
        
        content_splitter.addWidget(sidebar)
        content_splitter.addWidget(file_view_container)
        content_splitter.addWidget(file_box_panel_placeholder)
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setStretchFactor(2, 0)
        content_splitter.setSizes([200, 900, 0])  # File box panel starts with 0 width (hidden)
        
        # History panel (initially hidden)
        from app.services.file_box_history_service import FileBoxHistoryService
        history_service = FileBoxHistoryService()
        history_panel = FileBoxHistoryPanelSidebar(history_service, main_splitter)
        history_panel.hide()  # Initially hidden
        
        main_splitter.addWidget(content_splitter)
        main_splitter.addWidget(history_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0)
        main_splitter.setSizes([1100, 300])
        
        central_layout.addWidget(main_splitter, 1)
        
        size_grip_container = QWidget(central_widget)
        size_grip_container.setObjectName("SizeGripContainer")
        size_grip_layout = QHBoxLayout(size_grip_container)
        size_grip_layout.setContentsMargins(0, 0, 8, 8)
        size_grip_layout.setSpacing(0)
        size_grip = QSizeGrip(size_grip_container)
        size_grip.setFixedSize(16, 16)
        size_grip_layout.addStretch(1)
        size_grip_layout.addWidget(size_grip, 0)
        central_layout.addWidget(size_grip_container, 0)
        
        root_layout.addWidget(central_widget, 1)

        window.setStyleSheet("""
            QWidget { 
                margin: 0px;
                padding: 0px;
            }
        """)
        
        file_view_container.set_header(app_header)
        file_view_container._grid_button = app_header.get_grid_button()
        file_view_container._list_button = app_header.get_list_button()
        file_view_container._grid_button.clicked.connect(lambda: switch_view(file_view_container, "grid"))
        file_view_container._list_button.clicked.connect(lambda: switch_view(file_view_container, "list"))
        app_header.state_button_clicked.connect(file_view_container._on_state_button_clicked)
        app_header.navigation_back.connect(lambda: on_nav_back(file_view_container))
        app_header.navigation_forward.connect(lambda: on_nav_forward(file_view_container))
        
        # Conectar secondary header con file view container
        file_view_container.set_secondary_header(secondary_header)

        def apply_visual_separation():
            window_header.setStyleSheet("""
                QWidget {
                    background-color: """ + HEADER_BG + """ !important;
                    border-bottom: 1px solid """ + HEADER_BORDER + """ !important;
                }
                QPushButton {
                    border: none !important;
                    border-radius: 6px;
                    padding: 4px 6px;
                    /* font-size: establecido explícitamente */
                    color: rgba(0, 0, 0, 0.7) !important;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.08) !important;
                }
            """)
            
            app_header.setStyleSheet("""
                QWidget#AppHeader {
                    /* Tinte azul sutil para coherencia con workspace */
                    background-color: """ + APP_HEADER_BG + """ !important;
                    border-bottom: 1px solid """ + APP_HEADER_BORDER + """ !important;
                }
                QLineEdit {
                    /* Mantener campo de búsqueda claro para contraste */
                    background-color: rgba(255, 255, 255, 0.9) !important;
                    border: 1px solid rgba(0, 0, 0, 0.15) !important;
                    border-radius: 8px;
                    padding: 8px 12px 8px 36px;
                    color: rgba(0, 0, 0, 0.85) !important;
                    /* font-size: establecido explícitamente */
                    font-weight: 400;
                }
                QLineEdit:focus {
                    background-color: #FFFFFF !important;
                    border: 1px solid rgba(0, 0, 0, 0.25) !important;
                    color: rgba(0, 0, 0, 0.95) !important;
                }
                QLineEdit::placeholder {
                    color: rgba(0, 0, 0, 0.5) !important;
                }
            """)
            
            secondary_header.setStyleSheet("""
                QWidget#SecondaryHeader {
                    /* Mismo estilo que AppHeader para continuidad visual */
                    background-color: """ + APP_HEADER_BG + """ !important;
                    border-bottom: 1px solid """ + APP_HEADER_BORDER + """ !important;
                }
            """)
            
            workspace_selector.setStyleSheet("""
                QWidget#WorkspaceSelector {
                    /* Igual que el AppHeader para continuidad visual */
                    background-color: """ + APP_HEADER_BG + """ !important;
                    border-bottom: 1px solid """ + APP_HEADER_BORDER + """ !important;
                }
                QPushButton#WorkspaceButton {
                    /* Botón un punto más claro para destacar sobre el header */
                    background-color: #20242A !important;
                    border: 1px solid #343A44 !important;
                    border-radius: 6px;
                    color: rgba(255, 255, 255, 0.88) !important;
                    /* font-size: establecido explícitamente */
                    padding: 6px 12px;
                }
                QPushButton#WorkspaceButton:hover {
                    background-color: #252A31 !important;
                    border-color: #3A404B !important;
                }
                QPushButton#WorkspaceAddButton {
                    background-color: #20242A !important;
                    border: 1px solid #343A44 !important;
                    border-radius: 6px;
                    color: rgba(255, 255, 255, 0.88) !important;
                    /* font-size: establecido explícitamente */
                }
                QPushButton#WorkspaceAddButton:hover {
                    background-color: #252A31 !important;
                    border-color: #3A404B !important;
                }
            """)
        
        apply_visual_separation()
        
        if DEBUG_LAYOUT:
            _apply_layout_debug_styles(
                window, central_widget, window_header, app_header, secondary_header,
                main_splitter, workspace_selector, sidebar, file_view_container, size_grip_container
            )

        return file_view_container, sidebar, window_header, app_header, secondary_header, workspace_selector, history_panel, content_splitter, file_box_panel_placeholder
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Excepción crítica en setup_ui: {e}", exc_info=True)
        raise


def _apply_layout_debug_styles(
    window, central_widget, window_header, app_header, secondary_header,
    main_splitter, workspace_selector, sidebar, file_view_container, size_grip_container
) -> None:
    """Apply debug styles when DEBUG_LAYOUT is enabled."""
    pass
