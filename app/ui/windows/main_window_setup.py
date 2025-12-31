"""
UI setup helpers for MainWindow.

Handles window layout and widget creation.
Focus Dock is now integrated directly in FileViewContainer.
"""

import os
from PySide6.QtCore import Qt, QObject, QEvent, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSplitter, QVBoxLayout, QWidget, QSizePolicy

from app.core.constants import (
    SEPARATOR_LINE_COLOR, SIDEBAR_BG,
    BUTTON_BG_DARK, BUTTON_BORDER_DARK, BUTTON_BG_DARK_HOVER, BUTTON_BORDER_DARK_HOVER,
    APP_HEADER_BG, APP_HEADER_BORDER, USE_ROUNDED_CORNERS_IN_ROOT
)
from app.core.logger import get_logger
from app.ui.widgets.app_header import AppHeader
from app.ui.widgets.background_container import BackgroundContainer
from app.ui.widgets.secondary_header import SecondaryHeader
from app.ui.widgets.file_box_history_panel import FileBoxHistoryPanel
from app.ui.widgets.file_view_container import FileViewContainer
from app.ui.widgets.file_view_sync import switch_view
from app.ui.widgets.file_view_tabs import on_nav_back, on_nav_forward
from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar
# from app.ui.widgets.raycast_panel import RaycastPanel  # Ya no se usa
from app.ui.widgets.window_header import WindowHeader
from app.ui.widgets.workspace_selector import WorkspaceSelector

HEADER_BG = "#F5F5F7"
HEADER_BORDER = "rgba(0, 0, 0, 0.1)"


def _apply_visual_separation(window_header, app_header, secondary_header, workspace_selector) -> None:
    """Apply visual styling to header components."""
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
    """)

    secondary_header.setStyleSheet(f"""
        QWidget#SecondaryHeader {{
            /* Mismo estilo que AppHeader para continuidad visual */
            background-color: {APP_HEADER_BG} !important;
            border-bottom: 1px solid {APP_HEADER_BORDER} !important;
        }}
    """)

    workspace_selector.setStyleSheet(f"""
        QWidget#WorkspaceSelector {{
            border-bottom: 1px solid {APP_HEADER_BORDER} !important;
        }}
        QPushButton#WorkspaceButton {{
            background-color: {BUTTON_BG_DARK} !important;
            border: 1px solid {BUTTON_BORDER_DARK} !important;
            border-radius: 6px;
            color: rgba(255, 255, 255, 0.88) !important;
            padding: 6px 12px;
        }}
        QPushButton#WorkspaceButton:hover {{
            background-color: {BUTTON_BG_DARK_HOVER} !important;
            border-color: {BUTTON_BORDER_DARK_HOVER} !important;
        }}
    """)


def setup_ui(window, tab_manager, icon_service, workspace_manager, state_label_manager=None) -> tuple[FileViewContainer, FolderTreeSidebar, WindowHeader, AppHeader, SecondaryHeader, WorkspaceSelector, FileBoxHistoryPanel, QSplitter, 'FileBoxPanel']:
    try:
        root_layout = QVBoxLayout(window)

        # Márgenes según feature flag
        if USE_ROUNDED_CORNERS_IN_ROOT:
            # SISTEMA ANTIGUO: Margen de 3px para detección de bordes en resize
            root_layout.setContentsMargins(3, 3, 3, 3)
        else:
            # SISTEMA ACTUAL: Sin margen (overlay maneja detección de bordes)
            root_layout.setContentsMargins(0, 0, 0, 0)

        root_layout.setSpacing(0)

        # Parent widget para headers según feature flag
        if USE_ROUNDED_CORNERS_IN_ROOT:
            # SISTEMA ANTIGUO: Widgets directos en window (sin BackgroundContainer)
            parent_widget = window
            main_layout = root_layout  # Layout directamente en window
        else:
            # SISTEMA ACTUAL: Usar BackgroundContainer como intermediario
            background_container = BackgroundContainer(window)
            background_container.set_background_color(SIDEBAR_BG)
            background_container.set_corner_radius(12)

            container_layout = QVBoxLayout(background_container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)

            parent_widget = background_container
            main_layout = container_layout

        # Crear headers (parent depende del feature flag)
        window_header = WindowHeader(parent_widget)
        window_header.hide()  # Ocultar visualmente temporalmente
        main_layout.addWidget(window_header, 0)

        app_header = AppHeader(parent_widget)
        app_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(app_header, 0)

        secondary_header = SecondaryHeader(parent_widget)
        secondary_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(secondary_header, 0)

        workspace_selector = WorkspaceSelector(parent_widget)
        workspace_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        workspace_selector.set_workspace_manager(workspace_manager)
        main_layout.addWidget(workspace_selector, 0)

        # Línea horizontal separadora (invisible)
        separator_line = QFrame(parent_widget)
        separator_line.setFrameShape(QFrame.Shape.HLine)
        separator_line.setFrameShadow(QFrame.Shadow.Plain)
        separator_line.setFixedHeight(1)
        separator_line.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
                margin: 0px;
            }}
        """)
        main_layout.addWidget(separator_line, 0)

        # Main splitter: sidebar | content | history panel
        # Parent depende del feature flag (window o background_container)
        main_splitter = QSplitter(Qt.Orientation.Horizontal, parent_widget)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(4)
        main_splitter.setStyleSheet("""
            QSplitter {
                background-color: transparent;
            }
            QSplitter::handle {
                background-color: transparent;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: transparent;
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
        
        sidebar = FolderTreeSidebar(
            content_splitter,
            state_label_manager=state_label_manager,
            tab_manager=tab_manager
        )
        file_view_container = FileViewContainer(
            tab_manager,
            icon_service,
            None,
            content_splitter
        )
        
        from app.ui.widgets.file_box_panel import FileBoxPanel
        from app.ui.widgets.file_box_history_panel import FileBoxHistoryPanel
        from app.services.file_box_history_service import FileBoxHistoryService
        
        history_service = FileBoxHistoryService()
        
        file_box_panel = FileBoxPanel(
            current_session=None,
            history_service=history_service,
            parent=content_splitter,
            icon_service=icon_service
        )
        file_box_panel.hide()
        
        history_panel = FileBoxHistoryPanel(
            history_service,
            content_splitter,
            icon_service=icon_service
        )
        history_panel.hide()
        
        content_splitter.addWidget(sidebar)
        content_splitter.addWidget(file_view_container)
        content_splitter.addWidget(file_box_panel)
        content_splitter.addWidget(history_panel)
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setStretchFactor(2, 0)
        content_splitter.setStretchFactor(3, 0)
        content_splitter.setSizes([200, 900, 0, 0])  # Both panels start with 0 width (hidden)
        
        main_splitter.addWidget(content_splitter)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setSizes([1100])

        # Añadir splitter al layout (main_layout ya apunta al correcto según flag)
        main_layout.addWidget(main_splitter, 1)

        # Si estamos usando BackgroundContainer, agregarlo al root_layout
        if not USE_ROUNDED_CORNERS_IN_ROOT:
            root_layout.addWidget(background_container, 1)

        window.setStyleSheet("""
            QWidget {
                margin: 0px;
                padding: 0px;
            }
        """)
        
        file_view_container.set_header(app_header)
        file_view_container.set_workspace_selector(workspace_selector)
        
        # Mover botón de workspace al SecondaryHeader (solo posición visual)
        if workspace_selector._workspace_button:
            # Remover el botón del layout del WorkspaceSelector
            workspace_selector.layout().removeWidget(workspace_selector._workspace_button)
            # Cambiar el parent al SecondaryHeader
            workspace_selector._workspace_button.setParent(secondary_header)
            # Agregar al SecondaryHeader
            secondary_header.set_workspace_button(workspace_selector._workspace_button)
        
        # Navigation buttons ahora están en WorkspaceSelector
        workspace_selector.navigation_back.connect(lambda: on_nav_back(file_view_container))
        workspace_selector.navigation_forward.connect(lambda: on_nav_forward(file_view_container))
        
        # Conectar botones Grid/List del WorkspaceSelector
        workspace_selector.view_grid_requested.connect(lambda: workspace_manager.set_view_mode("grid"))
        workspace_selector.view_list_requested.connect(lambda: workspace_manager.set_view_mode("list"))
        
        # Asignar referencias para que switch_view() pueda actualizar el estado
        file_view_container._workspace_grid_button = workspace_selector._grid_button
        file_view_container._workspace_list_button = workspace_selector._list_button
        # Configurar headers para que sean estables pero permitan ver el fondo en las esquinas
        for widget in [window_header, app_header, secondary_header, workspace_selector, sidebar]:
            # NO usar WA_OpaquePaintEvent ni setAutoFillBackground(True) en widgets con
            # esquinas redondeadas, ya que dejarían de mostrar el fondo el BackgroundContainer
            # debajo de sus curvas, causando parpadeos transparentes durante el resize.
            widget.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
            widget.setAutoFillBackground(False)

            # Asegurar que tengan un estilo definido para consistencia
            if not widget.styleSheet():
                 widget.setStyleSheet(f"background-color: {HEADER_BG};")

        _apply_visual_separation(window_header, app_header, secondary_header, workspace_selector)

        # Configuración de splitters profesional (sin opaque resize para evitar flicker)
        # Esto elimina el "storm" de eventos durante el arrastre
        main_splitter.setOpaqueResize(False)
        content_splitter.setOpaqueResize(False)

        return file_view_container, sidebar, window_header, app_header, secondary_header, workspace_selector, history_panel, content_splitter, file_box_panel
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Excepción crítica en setup_ui: {e}", exc_info=True)
        raise
