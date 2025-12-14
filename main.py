"""
ClarityDesk Pro - Main entry point.

Bootstrap application: creates QApplication and DesktopWindow (auto-start).
MainWindow opens only when user requests it.
"""

import sys

from PySide6.QtWidgets import QApplication

from app.ui.windows.desktop_window import DesktopWindow
from app.ui.windows.main_window import MainWindow


def main() -> int:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("ClarityDesk Pro")

    # Create DesktopWindow (auto-start)
    desktop_window = DesktopWindow()
    
    # Show window
    desktop_window.show()
    
    # Initialize heavy components after window is shown (non-blocking)
    from PySide6.QtCore import QTimer
    QTimer.singleShot(0, desktop_window.initialize_after_show)
    
    # MainWindow instance (created but not shown)
    main_window = None
    
    def open_main_window():
        """Open MainWindow when user requests it."""
        nonlocal main_window
        if main_window is None:
            from app.managers.focus_manager import FocusManager
            from app.managers.tab_manager import TabManager
            from app.managers.workspace_manager import WorkspaceManager
            
            # Crear WorkspaceManager antes de TabManager
            workspace_manager = WorkspaceManager()
            
            tab_manager = TabManager()
            focus_manager = FocusManager(tab_manager)
            main_window = MainWindow(tab_manager, focus_manager, workspace_manager)
        
        if not main_window.isVisible():
            main_window.show()
        main_window.raise_()
        main_window.activateWindow()
    
    # Connect DesktopWindow signal to open MainWindow
    desktop_window.open_main_window.connect(open_main_window)
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

