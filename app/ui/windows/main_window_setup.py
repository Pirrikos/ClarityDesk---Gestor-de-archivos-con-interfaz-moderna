"""
UI setup helpers for MainWindow.

Handles window layout and widget creation.
Focus Dock is now integrated directly in FileViewContainer.
"""

from PySide6.QtWidgets import QHBoxLayout, QWidget

from app.ui.widgets.file_view_container import FileViewContainer
from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar


def setup_ui(window, tab_manager, icon_service) -> tuple[FileViewContainer, FolderTreeSidebar]:
    """Build the UI layout with Focus Dock integrated in content area."""
    central_widget = QWidget()
    window.setCentralWidget(central_widget)

    layout = QHBoxLayout(central_widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # Sidebar de navegación (Arc-style)
    sidebar = FolderTreeSidebar(central_widget)
    sidebar.show()  # Fuerza visibilidad antes de añadir al layout

    # File view container with Focus Dock integrated
    file_view_container = FileViewContainer(
        tab_manager,
        icon_service,
        None  # filesystem_service deprecated, not needed
    )
    layout.addWidget(sidebar, 0)  # 0 = no stretch (ancho fijo)
    layout.addWidget(file_view_container, 1)  # Stretch factor 1

    # Apple-inspired window styling
    window.setWindowTitle("ClarityDesk Pro")
    window.setMinimumSize(900, 600)
    window.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f7;
        }
    """)
    
    return file_view_container, sidebar

