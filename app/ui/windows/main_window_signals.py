"""
Signal connection helpers for MainWindow.

Handles connecting UI signals to managers and handlers.
Note: Focus Dock replaces FolderTreeSidebar - no tree sidebar needed.
"""


def connect_signals(
    window,
    focus_manager,
    tab_manager,
    file_view_container
) -> None:
    """Connect UI signals to TabManager and vice versa."""
    # TabManager -> UI
    tab_manager.tabsChanged.connect(window._on_tabs_changed)
    tab_manager.activeTabChanged.connect(window._on_active_tab_changed)

    # FileViewContainer -> (future: open file handler)
    file_view_container.open_file.connect(window._on_file_open)

