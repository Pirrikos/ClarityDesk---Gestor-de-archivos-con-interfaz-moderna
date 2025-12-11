"""
ClarityDesk Pro - Main entry point.

Bootstrap application: creates QApplication and DesktopWindow (auto-start).
MainWindow opens only when user requests it.
"""

import sys
import time

from PySide6.QtWidgets import QApplication

from app.ui.windows.desktop_window import DesktopWindow
from app.ui.windows.main_window import MainWindow


def main() -> int:
    """Application entry point."""
    # Start timing
    startup_start = time.perf_counter()
    
    app = QApplication(sys.argv)
    app.setApplicationName("ClarityDesk Pro")
    
    app_init_time = time.perf_counter()
    print(f"[STARTUP] QApplication init: {(app_init_time - startup_start) * 1000:.2f} ms")

    # Create DesktopWindow (auto-start)
    window_create_start = time.perf_counter()
    desktop_window = DesktopWindow()
    window_create_time = time.perf_counter()
    print(f"[STARTUP] DesktopWindow.__init__: {(window_create_time - window_create_start) * 1000:.2f} ms")
    
    # Show window
    show_start = time.perf_counter()
    desktop_window.show()
    show_time = time.perf_counter()
    window_visible_time = show_time - startup_start
    print(f"[STARTUP] desktop_window.show(): {(show_time - show_start) * 1000:.2f} ms")
    print(f"[STARTUP] ⚡ VENTANA VISIBLE en: {window_visible_time * 1000:.2f} ms")
    
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
            
            tab_manager = TabManager()
            focus_manager = FocusManager(tab_manager)
            main_window = MainWindow(tab_manager, focus_manager)
        
        if not main_window.isVisible():
            main_window.show()
        main_window.raise_()
        main_window.activateWindow()
    
    # Connect DesktopWindow signal to open MainWindow
    desktop_window.open_main_window.connect(open_main_window)
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

