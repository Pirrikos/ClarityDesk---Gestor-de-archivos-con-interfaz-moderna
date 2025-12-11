"""
Event handlers for FocusDockWidget.

Handles clicks, overlay management, and file drops.
"""

from PySide6.QtCore import QPoint

from app.managers.tab_manager import TabManager
from app.ui.widgets.subfolder_overlay import SubfolderOverlay


def handle_focus_click(tab_manager: TabManager, folder_path: str) -> None:
    """Handle Focus tile click - switch to that Focus using normalized path comparison."""
    from app.services.tab_finder import find_tab_index
    
    tabs = tab_manager.get_tabs()
    # Use normalized path comparison to find tab index
    index = find_tab_index(tabs, folder_path)
    if index is not None:
        tab_manager.select_tab(index)


def handle_add_click(tab_manager: TabManager) -> str:
    """Handle + button click - open folder picker."""
    from PySide6.QtWidgets import QFileDialog
    
    folder_path = QFileDialog.getExistingDirectory(
        None,
        "Select Folder",
        "",
        QFileDialog.Option.ShowDirsOnly
    )
    
    if folder_path:
        tab_manager.add_tab(folder_path)
    
    return folder_path


def handle_remove_click(tab_manager: TabManager) -> None:
    """Handle - button click - remove active tab."""
    active_index = tab_manager.get_active_index()
    if active_index >= 0:
        tab_manager.remove_tab(active_index)


def handle_focus_remove_request(tab_manager: TabManager, folder_path: str) -> None:
    """Handle remove request from a Focus tile."""
    tabs = tab_manager.get_tabs()
    normalized_requested = folder_path.replace('\\', '/').lower().strip()
    for idx, tab_path in enumerate(tabs):
        normalized_tab = tab_path.replace('\\', '/').lower().strip()
        if normalized_tab == normalized_requested:
            tab_manager.remove_tab(idx)
            return
    if folder_path in tabs:
        index = tabs.index(folder_path)
        tab_manager.remove_tab(index)


def handle_overlay_request(
    folder_path: str,
    global_pos: QPoint,
    current_overlay: SubfolderOverlay,
    parent_widget
) -> SubfolderOverlay:
    """Handle overlay request - show subfolder overlay."""
    if current_overlay:
        current_overlay.close()
    
    overlay = SubfolderOverlay(folder_path, parent_widget)
    return overlay


def handle_file_dropped_in_overlay(
    source_path: str,
    target_path: str,
    tab_manager: TabManager
) -> None:
    """Handle file drop in overlay - move file using file_move_service."""
    from app.services.file_move_service import move_file
    from app.services.desktop_path_helper import is_desktop_focus
    from app.services.desktop_operations import move_out_of_desktop
    import os
    
    watcher = None
    if hasattr(tab_manager, 'get_watcher'):
        watcher = tab_manager.get_watcher()
    
    file_dir = os.path.dirname(os.path.abspath(source_path))
    if is_desktop_focus(file_dir):
        move_out_of_desktop(source_path, target_path, watcher=watcher)
    else:
        move_file(source_path, target_path, watcher=watcher)

