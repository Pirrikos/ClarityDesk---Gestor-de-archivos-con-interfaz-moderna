"""
MainWindow - Main application window with Focus Dock layout.

Focus Dock replaces the old sidebar navigation system.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow

from app.managers.focus_manager import FocusManager
from app.managers.tab_manager import TabManager
from app.services.icon_service import IconService
from app.services.preview_service import PreviewService
from app.services.file_open_service import open_file_with_system
from app.ui.windows.main_window_file_handler import filter_previewable_files
from app.ui.windows.main_window_setup import setup_ui
from app.ui.windows.main_window_state import load_app_state, save_app_state
from app.ui.windows.quick_preview_window import QuickPreviewWindow


class MainWindow(QMainWindow):
    """Main application window with Focus Dock and content area."""

    def __init__(self, tab_manager: TabManager, focus_manager: FocusManager, parent=None):
        """Initialize MainWindow with TabManager and FocusManager."""
        super().__init__(parent)
        self._tab_manager = tab_manager
        self._focus_manager = focus_manager
        self._icon_service = IconService()
        self._preview_service = PreviewService(self._icon_service)
        self._current_preview_window = None
        self._setup_ui()
        self._connect_signals()
        # Sincronizar sidebar con tabs existentes
        for tab_path in self._tab_manager.get_tabs():
            self._sidebar.add_focus_path(tab_path)
        self._setup_shortcuts()
        self._load_app_state()

    def _setup_ui(self) -> None:
        """Build the UI layout with Focus Dock integrated."""
        self._file_view_container, self._sidebar = setup_ui(
            self, self._tab_manager, self._icon_service
        )

    def _connect_signals(self) -> None:
        """Connect UI signals to TabManager and FocusManager."""
        # NOTE: FocusManager is not currently used - Dock calls TabManager directly
        # Keeping FocusManager connection commented for potential future use
        # self._focus_manager.focus_opened.connect(
        #     lambda path: self._tab_manager.add_tab(path)
        # )
        
        # TabManager -> UI
        self._tab_manager.tabsChanged.connect(self._on_tabs_changed)
        self._tab_manager.activeTabChanged.connect(self._on_active_tab_changed)
        
        # FileViewContainer -> file open handler
        self._file_view_container.open_file.connect(self._on_file_open)
        
        # Sidebar -> TabManager
        self._sidebar.new_focus_requested.connect(self._on_sidebar_new_focus)
        self._sidebar.folder_selected.connect(self._on_sidebar_folder_selected)
        self._sidebar.focus_remove_requested.connect(self._on_sidebar_remove_focus)
        
        # TabManager -> Sidebar (sincronización)
        self._tab_manager.tabsChanged.connect(self._on_tabs_changed_sync_sidebar)

    def _load_app_state(self) -> None:
        """Load complete application state and restore UI."""
        load_app_state(self, self._tab_manager)

    def _on_tabs_changed(self, tabs: list) -> None:
        """Handle tabs list change from TabManager."""
        # Focus Dock handles this automatically via its own TabManager connection
        pass

    def _on_active_tab_changed(self, index: int, path: str) -> None:
        """Handle active tab change from TabManager."""
        # FileViewContainer will auto-update via its own TabManager connection
        pass
    
    def _on_files_moved(self, source_path: str, target_path: str) -> None:
        """Handle files moved - refresh affected Focus."""
        import os
        from PySide6.QtCore import QTimer
        
        source_dir = os.path.dirname(source_path)
        active_folder = self._tab_manager.get_active_folder()
        
        # Refresh source folder if it's the active Focus
        if source_dir == active_folder:
            QTimer.singleShot(100, lambda: self._file_view_container._update_files())
        
        # Refresh target folder if it's the active Focus  
        if target_path == active_folder:
            QTimer.singleShot(100, lambda: self._file_view_container._update_files())

    def _on_file_open(self, file_path: str) -> None:
        """
        Handle file or folder open request from FileViewContainer.
        
        IMPORTANT: When opening folders from Grid:
        - Only activates Focus if folder already exists as a Focus in Dock
        - Does NOT create new Focus - user must use "+" button in Dock
        - This keeps Dock stable and independent from Grid navigation
        """
        import os
        if os.path.isdir(file_path):
            # Check if this folder is already a Focus in the Dock
            tabs = self._tab_manager.get_tabs()
            normalized_path = file_path.replace('\\', '/').strip()
            
            # Normalize all tabs for comparison
            for idx, tab_path in enumerate(tabs):
                normalized_tab = tab_path.replace('\\', '/').strip()
                if normalized_tab.lower() == normalized_path.lower():
                    # Folder is already a Focus - switch to it
                    self._tab_manager.select_tab(idx)
                    return
            
            # Folder is NOT a Focus - do NOT add it
            # User must manually add Focus using "+" button in Dock
            # This keeps Dock stable and prevents automatic Focus creation from navigation
            return
        else:
            # Open file with default system application
            open_file_with_system(file_path)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        shortcut.activated.connect(self._open_quick_preview)

    def _open_quick_preview(self) -> None:
        """Toggle quick preview window (open/close)."""
        # Si la ventana existe y está visible, cerrarla (toggle)
        if (hasattr(self, "_current_preview_window") and 
            self._current_preview_window and 
            self._current_preview_window.isVisible()):
            self._current_preview_window.close()
            self._current_preview_window = None
            return

        # Si no hay ventana o está cerrada, abrir nueva
        selected = self._file_view_container.get_selected_files()
        if not selected:
            return

        # Filtrar solo archivos de texto e imágenes
        allowed_files = filter_previewable_files(selected)
        if not allowed_files:
            return

        # Pasar lista completa para navegación secuencial
        preview = QuickPreviewWindow(
            self._preview_service,
            file_paths=allowed_files,
            start_index=0,
            parent=self
        )

        self._current_preview_window = preview
        preview.show()
        preview.setFocus()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event - save state and cleanup resources."""
        # Stop filesystem watcher
        if hasattr(self._tab_manager, 'get_watcher'):
            watcher = self._tab_manager.get_watcher()
            if watcher:
                watcher.stop_watching()
        
        # Save complete application state
        self._save_app_state()
        
        if self._current_preview_window:
            self._current_preview_window.close()
        self._preview_service.clear_cache()
        event.accept()
    
    def _save_app_state(self) -> None:
        """Save complete application state before closing."""
        save_app_state(self, self._tab_manager)
    
    def _on_sidebar_new_focus(self, path: str) -> None:
        """Handle new focus request from sidebar."""
        self._tab_manager.add_tab(path)
    
    def _on_sidebar_folder_selected(self, path: str) -> None:
        """Handle folder selection from sidebar."""
        tabs = self._tab_manager.get_tabs()
        if path in tabs:
            index = tabs.index(path)
            self._tab_manager.select_tab(index)
        else:
            # Si no existe, añadirlo
            self._tab_manager.add_tab(path)
    
    def _on_sidebar_remove_focus(self, path: str) -> None:
        """Handle focus removal request from sidebar."""
        self._tab_manager.remove_tab_by_path(path)
        self._sidebar.remove_focus_path(path)
    
    def _on_tabs_changed_sync_sidebar(self, tabs: list) -> None:
        """Sync sidebar with current tabs."""
        for tab_path in tabs:
            self._sidebar.add_focus_path(tab_path)

