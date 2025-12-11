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


def save_app_state(window, tab_manager) -> None:
    """Save complete application state before closing."""
    # Get current state from TabManager
    tabs = tab_manager.get_tabs()
    active_tab = tab_manager.get_active_folder()
    history = tab_manager.get_history()
    history_index = tab_manager.get_history_index()
    
    # Build state dict (no folder tree state needed)
    state_manager = tab_manager.get_state_manager()
    state = state_manager.build_app_state(
        tabs=tabs,
        active_tab_path=active_tab,
        history=history,
        history_index=history_index,
        focus_tree_paths=[],  # Not used anymore
        expanded_nodes=[]     # Not used anymore
    )
    
    # Save state
    state_manager.save_app_state(state)

