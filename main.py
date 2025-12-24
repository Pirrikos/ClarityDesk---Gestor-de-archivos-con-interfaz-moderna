"""
ClarityDesk Pro - Main entry point.

Bootstrap application: creates QApplication and DesktopWindow (auto-start).
MainWindow opens only when user requests it.
"""

import sys
import traceback

from PySide6.QtCore import QtMsgType, QTimer, qInstallMessageHandler
from PySide6.QtWidgets import QApplication

from app.ui.windows.desktop_window import DesktopWindow
from app.ui.windows.main_window import MainWindow


def qt_message_handler(msg_type, context, message):
    """Qt message handler para errores de fuente."""
    if "QFont::setPointSize" in message or "Point size <= 0" in message:
        print(f"\n[FONT WARNING] {message}")
        if context.file:
            print(f"  Ubicación: {context.file}:{context.line} ({context.function})")
        print()
    
    # Mostrar mensajes críticos y fatales
    if msg_type == QtMsgType.QtCriticalMsg or msg_type == QtMsgType.QtFatalMsg:
        print(f"[QT {msg_type.name}] {message}")
        if context.file:
            print(f"  En: {context.file}:{context.line} ({context.function})")


def main() -> int:
    """Application entry point."""
    # Instalar handler personalizado para capturar mensajes de Qt
    qInstallMessageHandler(qt_message_handler)
    
    app = QApplication(sys.argv)
    app.setApplicationName("ClarityDesk Pro")
    # No cerrar aplicación cuando se oculta MainWindow (DesktopWindow siempre está activo)
    app.setQuitOnLastWindowClosed(False)

    # Create DesktopWindow (auto-start)
    desktop_window = DesktopWindow()
    
    # Show window
    desktop_window.show()
    
    # Initialize heavy components after window is shown (non-blocking)
    QTimer.singleShot(0, desktop_window.initialize_after_show)
    
    # MainWindow instance (created but not shown)
    main_window = None
    
    def open_main_window():
        """Open MainWindow when user requests it."""
        nonlocal main_window
        
        try:
            if main_window is None:
                from app.managers.tab_manager import TabManager
                from app.managers.workspace_manager import WorkspaceManager
                workspace_manager = WorkspaceManager()
                tab_manager = TabManager()
                # Inyectar DesktopWindow como dependencia (Rule 5: Dependency Injection)
                main_window = MainWindow(tab_manager, workspace_manager, desktop_window)
            if not main_window.isVisible():
                main_window.show()
            main_window.raise_()
            main_window.activateWindow()
            
        except Exception as e:
            print(f"\n[ERROR CRÍTICO] Excepción en open_main_window:\n{e}")
            traceback.print_exc()
            print("[ERROR CRÍTICO] Fin de traza.\n")
    
    # Connect DesktopWindow signal to open MainWindow
    desktop_window.open_main_window.connect(open_main_window)
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

