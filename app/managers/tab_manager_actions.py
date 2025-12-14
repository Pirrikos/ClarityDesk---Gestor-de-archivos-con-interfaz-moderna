"""
Tab actions for TabManager.

Handles tab operations: add, remove, select, and get files.
"""

from typing import List, Optional
import os

from app.services.file_extensions import SUPPORTED_EXTENSIONS
from app.services.file_list_service import get_files
from app.services.path_utils import normalize_path
from app.services.tab_helpers import find_tab_index, validate_folder
from app.services.tab_history_manager import TabHistoryManager


def adjust_active_index_after_remove(
    current_index: int,
    removed_index: int,
    total_tabs: int
) -> int:
    """
    Calculate new active index after removing a tab.

    Args:
        current_index: Current active index.
        removed_index: Index of tab being removed.
        total_tabs: Total number of tabs after removal.

    Returns:
        New active index.
    """
    if total_tabs == 0:
        return -1
    elif current_index >= total_tabs:
        return total_tabs - 1
    elif current_index > removed_index:
        return current_index - 1
    else:
        return current_index


def add_tab(
    manager,
    folder_path: str,
    tabs: List[str],
    active_index: int,
    history_manager: TabHistoryManager,
    save_state_callback,
    watch_and_emit_callback,
    tabs_changed_signal=None,
    active_tab_changed_signal=None
) -> tuple[bool, List[str], int]:
    """Add a folder as a tab and make it active."""
    if not validate_folder(folder_path):
        return False, tabs, active_index

    normalized_path = normalize_path(folder_path)

    # Avoid duplicates using normalized comparison
    existing_index = find_tab_index(tabs, normalized_path)
    if existing_index is not None:
        # Get watcher from manager
        watcher = manager._watcher if hasattr(manager, '_watcher') else None
        return select_tab(manager, existing_index, tabs, active_index, history_manager, watcher, save_state_callback, watch_and_emit_callback)

    new_tabs = tabs.copy()
    new_tabs.append(normalized_path)
    new_active_index = len(new_tabs) - 1
    history_manager.update_on_navigate(normalized_path, normalize_path)
    save_state_callback()
    
    # Emit tabs changed signal
    if tabs_changed_signal:
        tabs_changed_signal.emit(new_tabs.copy())
    
    # NOTE: watch_and_emit_callback is NOT called here because active_index hasn't been updated yet
    # It will be called after execute_action updates the manager's active_index
    # This ensures activeTabChanged is emitted with the correct index
    return True, new_tabs, new_active_index


def remove_tab(
    manager,
    index: int,
    tabs: List[str],
    active_index: int,
    watcher,
    save_state_callback,
    watch_and_emit_callback,
    tabs_changed_signal,
    active_tab_changed_signal,
    focus_cleared_signal=None
) -> tuple[bool, List[str], int]:
    """Remove a tab by index."""
    if not (0 <= index < len(tabs)):
        return False, tabs, active_index

    # Check if we're removing the active tab BEFORE removing it
    was_active = (index == active_index)

    new_tabs = tabs.copy()
    new_tabs.pop(index)

    # Adjust active index
    new_active_index = adjust_active_index_after_remove(
        active_index, index, len(new_tabs)
    )

    save_state_callback()
    
    watcher.stop_watching()
    tabs_changed_signal.emit(new_tabs.copy())

    # If we removed the active tab, handle accordingly
    if was_active:
        if new_active_index < 0:
            # No tabs remain - emit focus_cleared and activeTabChanged(-1, "")
            if focus_cleared_signal:
                focus_cleared_signal.emit()
            active_tab_changed_signal.emit(-1, "")
        else:
            # There are more tabs - activate the next one
            try:
                manager._active_index = new_active_index
            except Exception:
                pass
            watch_and_emit_callback(new_tabs[new_active_index])
    elif new_active_index >= 0:
        # Not the active tab was removed - continue normally
        try:
            manager._active_index = new_active_index
        except Exception:
            pass
        watch_and_emit_callback(new_tabs[new_active_index])
    else:
        # Edge case: inactive tab removed and no tabs remain
        if focus_cleared_signal:
            focus_cleared_signal.emit()
        active_tab_changed_signal.emit(-1, "")

    return True, new_tabs, new_active_index


def remove_tab_by_path(
    manager,
    folder_path: str,
    tabs: List[str],
    active_index: int,
    watcher,
    save_state_callback,
    watch_and_emit_callback,
    tabs_changed_signal,
    active_tab_changed_signal,
    focus_cleared_signal=None
) -> tuple[bool, List[str], int]:
    """
    Remove a tab by folder path, also removing any child tabs under that path.
    
    Args:
        manager: TabManager instance
        folder_path: Folder path to remove.
        tabs: Current tabs list
        active_index: Current active index
        watcher: FileSystemWatcherService instance
        save_state_callback: Callback to save state
        watch_and_emit_callback: Callback to watch and emit
        tabs_changed_signal: Signal to emit tabs changed
        active_tab_changed_signal: Signal to emit active tab changed
        focus_cleared_signal: Signal to emit when active focus is cleared
        
    Returns:
        Tuple of (success, new_tabs, new_active_index)
    """
    norm_removed = normalize_path(folder_path)
    # Remove children of the removed path from the tabs list first (but keep the parent for the final removal)
    filtered_tabs = []
    for t in tabs:
        nt = normalize_path(t)
        if nt == norm_removed:
            filtered_tabs.append(t)  # keep parent for now; will be removed via remove_tab()
        elif nt.startswith(norm_removed + os.sep):
            continue  # drop child tab
        else:
            filtered_tabs.append(t)
    # Recompute indices in filtered list
    tab_index = find_tab_index(filtered_tabs, norm_removed)
    if tab_index is None:
        return False, filtered_tabs, active_index
    
    # Map active_index from original tabs to filtered tabs, if still present
    filtered_active_index = -1
    if 0 <= active_index < len(tabs):
        active_path = tabs[active_index]
        idx_in_filtered = find_tab_index(filtered_tabs, active_path)
        if idx_in_filtered is not None:
            filtered_active_index = idx_in_filtered
    
    return remove_tab(
        manager, tab_index, filtered_tabs, filtered_active_index, watcher,
        save_state_callback, watch_and_emit_callback,
        tabs_changed_signal, active_tab_changed_signal, focus_cleared_signal
    )


def select_tab(
    manager,
    index: int,
    tabs: List[str],
    active_index: int,
    history_manager: TabHistoryManager,
    watcher,
    save_state_callback,
    watch_and_emit_callback
) -> tuple[bool, List[str], int]:
    """Select a tab as active."""
    if not (0 <= index < len(tabs)):
        return False, tabs, active_index

    if active_index == index:
        return True, tabs, active_index

    watcher.stop_watching()
    folder_path = tabs[index]
    new_active_index = index
    history_manager.update_on_navigate(folder_path, normalize_path)
    # Update manager active index BEFORE emitting, to ensure correct index in signal
    try:
        manager._active_index = new_active_index
    except Exception:
        pass
    save_state_callback()
    watch_and_emit_callback(folder_path)
    return True, tabs, new_active_index


def get_files_from_active_tab(
    active_folder: Optional[str],
    extensions: Optional[set] = None,
    use_stacks: bool = False
) -> List:
    """Get filtered file list from active folder."""
    if not active_folder:
        return []
    ext_set = extensions or SUPPORTED_EXTENSIONS
    return get_files(active_folder, ext_set, use_stacks=use_stacks)


def activate_tab(manager, index: int, get_tabs_callback, select_tab_callback) -> None:
    """Activate tab by index with validation."""
    tabs = get_tabs_callback()
    if not (0 <= index < len(tabs)):
        return
    select_tab_callback(index)
