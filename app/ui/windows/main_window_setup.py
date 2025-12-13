"""
UI setup helpers for MainWindow.

Handles window layout and widget creation.
Focus Dock is now integrated directly in FileViewContainer.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

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
    # Contenedor de contenido: sidebar + file view
    content = QWidget(central_widget)
    content_layout = QHBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(0)
    root_layout.addWidget(content, 1)

    # Sidebar de navegación (Arc-style)
    sidebar = FolderTreeSidebar(content)
    sidebar.show()  # Fuerza visibilidad antes de añadir al layout

    # File view container with Focus Dock integrated
    file_view_container = FileViewContainer(
        tab_manager,
        icon_service,
        None  # filesystem_service deprecated, not needed
    )
    content_layout.addWidget(sidebar, 0)  # 0 = no stretch (ancho fijo)
    content_layout.addWidget(file_view_container, 1)  # Stretch factor 1

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
