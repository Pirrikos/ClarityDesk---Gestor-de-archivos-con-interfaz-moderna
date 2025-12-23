"""
State management helpers for MainWindow.

Handles loading and saving application state.
Focus Dock replaces FolderTreeSidebar - no tree state needed.
"""


def load_app_state(window, tab_manager) -> None:
    """Load complete application state and restore UI."""
    # Get state manager from TabManager
    state_manager = tab_manager.get_state_manager()
    
    # Load saved state
    saved_state = state_manager.load_app_state()
    if not saved_state:
        # No saved state, nothing to restore
        return
    
    # Apply and validate state
    validated_state = state_manager.apply_app_state(saved_state)
    
    # Only restore if we have valid state (not empty)
    if validated_state['open_tabs'] or validated_state['history']:
        # Restore tabs and history in TabManager
        tab_manager.restore_state(
            tabs=validated_state['open_tabs'],
            active_tab_path=validated_state['active_tab'],
            history=validated_state['history'],
            history_index=validated_state['history_index']
        )
        
        # Restore sidebar tree with preserved root folder order
        if hasattr(window, '_sidebar') and validated_state.get('focus_tree_paths'):
            expanded_paths = validated_state.get('expanded_nodes', [])
            root_folders_order = validated_state.get('root_folders_order')
            window._sidebar.restore_tree(validated_state['focus_tree_paths'], expanded_paths, root_folders_order)


def save_app_state(window, tab_manager) -> None:
    """Save complete application state before closing."""
    # Get current state from TabManager
    tabs = tab_manager.get_tabs()
    active_tab = tab_manager.get_active_folder()
    history = tab_manager.get_history()
    history_index = tab_manager.get_history_index()
    
    # Get sidebar tree state (with preserved root folder order)
    focus_tree_paths = []
    expanded_nodes = []
    root_folders_order = None
    if hasattr(window, '_sidebar'):
        focus_tree_paths = window._sidebar.get_focus_tree_paths()
        expanded_nodes = window._sidebar.get_expanded_paths()
        root_folders_order = window._sidebar.get_root_folders_order()
    
    # Build state dict
    state_manager = tab_manager.get_state_manager()
    state = state_manager.build_app_state(
        tabs=tabs,
        active_tab_path=active_tab,
        history=history,
        history_index=history_index,
        focus_tree_paths=focus_tree_paths,
        expanded_nodes=expanded_nodes,
        root_folders_order=root_folders_order
    )
    
    # Save state
    state_manager.save_app_state(state)
