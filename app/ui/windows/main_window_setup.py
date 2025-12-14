"""
UI setup helpers for MainWindow.

Handles window layout and widget creation.
Focus Dock is now integrated directly in FileViewContainer.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout, QWidget

from app.ui.widgets.file_view_container import FileViewContainer
from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar
from app.ui.widgets.raycast_panel import RaycastPanel


def setup_ui(window, tab_manager, icon_service) -> tuple[FileViewContainer, FolderTreeSidebar]:
    """Build the UI layout with Focus Dock integrated in content area."""
    central_widget = RaycastPanel()
    window.setCentralWidget(central_widget)
    # Layout vertical: header arriba y contenido debajo
    root_layout = QVBoxLayout(central_widget)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)
    # Espacio superior vacío para separar el borde superior de los botones
    root_layout.addSpacing(16)
    
    # Splitter redimensionable entre sidebar y file view
    splitter = QSplitter(Qt.Orientation.Horizontal, central_widget)
    splitter.setChildrenCollapsible(False)  # No permitir colapsar completamente
    splitter.setHandleWidth(3)  # Ancho del separador (más visible)
    splitter.setStyleSheet("""
        QSplitter::handle {
            background-color: rgba(255, 255, 255, 0.08);
            border: none;
        }
        QSplitter::handle:hover {
            background-color: rgba(255, 255, 255, 0.15);
        }
        QSplitter::handle:horizontal {
            width: 3px;
            margin: 0px;
        }
    """)
    
    # Sidebar de navegación (Arc-style)
    sidebar = FolderTreeSidebar(splitter)
    sidebar.show()  # Fuerza visibilidad antes de añadir al layout

    # File view container with Focus Dock integrated
    file_view_container = FileViewContainer(
        tab_manager,
        icon_service,
        None,  # filesystem_service deprecated, not needed
        splitter
    )
    
    # Agregar widgets al splitter
    splitter.addWidget(sidebar)
    splitter.addWidget(file_view_container)
    
    # Configurar proporciones iniciales (sidebar ~22%, file_view ~78%)
    # Para ventana de 1100px: sidebar=240px, file_view=860px
    splitter.setStretchFactor(0, 0)  # Sidebar no se estira
    splitter.setStretchFactor(1, 1)  # File view se estira
    splitter.setSizes([240, 860])  # Tamaños iniciales
    
    root_layout.addWidget(splitter, 1)

    # Apple-inspired window styling
    window.setWindowTitle("ClarityDesk Pro")
    window.setMinimumSize(900, 800)
    window.resize(1100, 800)
    window.setStyleSheet("""
        QMainWindow { background-color: transparent; }
    """)
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    window.setWindowFlags(
        Qt.WindowType.Window |
        Qt.WindowType.FramelessWindowHint
    )
    
    return file_view_container, sidebar
