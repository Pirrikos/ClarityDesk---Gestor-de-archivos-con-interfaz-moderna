"""
Test workspace switching functionality.

Tests the last step of the workspace implementation plan:
- Create 2 workspaces
- Open different tabs in each one
- Switch between them
- Verify that state is maintained correctly
"""

import os
import tempfile
import shutil
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.managers.workspace_manager import WorkspaceManager
from app.managers.tab_manager import TabManager
from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar
from app.services.path_utils import normalize_path


@pytest.fixture(scope="function")
def qapp():
    """Create QApplication for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(scope="function")
def temp_dirs():
    """Create temporary directories for testing."""
    temp_base = tempfile.mkdtemp()
    dirs = {
        'ws1_tab1': Path(temp_base) / "workspace1_tab1",
        'ws1_tab2': Path(temp_base) / "workspace1_tab2",
        'ws2_tab1': Path(temp_base) / "workspace2_tab1",
        'ws2_tab2': Path(temp_base) / "workspace2_tab2",
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield dirs
    
    # Cleanup
    shutil.rmtree(temp_base, ignore_errors=True)


@pytest.fixture(scope="function")
def workspace_manager():
    """Create WorkspaceManager instance."""
    # Mock storage directory to use temp
    import app.services.workspace_storage_service as ws_module
    original_get_storage_dir = ws_module.get_storage_dir
    
    temp_storage = tempfile.mkdtemp()
    
    def mock_get_storage_dir():
        storage_path = Path(temp_storage) / 'storage'
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path
    
    ws_module.get_storage_dir = mock_get_storage_dir
    
    manager = WorkspaceManager()
    
    yield manager
    
    # Restore and cleanup
    ws_module.get_storage_dir = original_get_storage_dir
    shutil.rmtree(temp_storage, ignore_errors=True)


@pytest.fixture(scope="function")
def tab_manager():
    """Create TabManager instance."""
    manager = TabManager(storage_path=None)
    yield manager


@pytest.fixture(scope="function")
def sidebar(qapp):
    """Create FolderTreeSidebar instance."""
    sidebar = FolderTreeSidebar()
    yield sidebar


def test_workspace_switching_maintains_state(workspace_manager, tab_manager, sidebar, temp_dirs, qapp):
    """
    Test workspace switching maintains state correctly.
    
    This test implements the last step of the plan:
    1. Create 2 workspaces
    2. Open different tabs in each one
    3. Switch between them
    4. Verify that state is maintained correctly
    """
    # Connect TabManager to WorkspaceManager
    tab_manager.set_workspace_manager(workspace_manager)
    
    # Step 1: Create 2 workspaces
    workspace1 = workspace_manager.create_workspace("Trabajo")
    workspace2 = workspace_manager.create_workspace("Clases")
    
    assert workspace1.id is not None
    assert workspace2.id is not None
    assert workspace1.name == "Trabajo"
    assert workspace2.name == "Clases"
    
    # Step 2: Open different tabs in workspace 1
    workspace_manager.switch_workspace(workspace1.id, tab_manager, sidebar)
    
    # Add tabs to workspace 1
    tab_manager.add_tab(str(temp_dirs['ws1_tab1']))
    tab_manager.add_tab(str(temp_dirs['ws1_tab2']))
    
    # Add paths to sidebar for workspace 1
    sidebar.add_focus_path(str(temp_dirs['ws1_tab1']))
    sidebar.add_focus_path(str(temp_dirs['ws1_tab2']))
    
    # Save workspace 1 state
    workspace_manager.save_current_state(tab_manager, sidebar)
    
    # Verify workspace 1 state was saved
    state1 = workspace_manager.get_workspace_state(workspace1.id)
    assert state1 is not None
    assert len(state1['tabs']) == 2
    # Normalize paths for comparison (TabManager normalizes paths)
    normalized_ws1_tab1 = normalize_path(str(temp_dirs['ws1_tab1']))
    normalized_ws1_tab2 = normalize_path(str(temp_dirs['ws1_tab2']))
    assert normalized_ws1_tab1 in state1['tabs']
    assert normalized_ws1_tab2 in state1['tabs']
    assert len(state1['focus_tree_paths']) == 2
    
    # Step 3: Switch to workspace 2 and open different tabs
    workspace_manager.switch_workspace(workspace2.id, tab_manager, sidebar)
    
    # Verify workspace 1 state was saved before switching
    saved_state1 = workspace_manager.get_workspace_state(workspace1.id)
    assert saved_state1 is not None
    assert len(saved_state1['tabs']) == 2
    
    # Verify workspace 2 is now empty (new workspace)
    tabs_after_switch = tab_manager.get_tabs()
    assert len(tabs_after_switch) == 0
    
    # Add different tabs to workspace 2
    tab_manager.add_tab(str(temp_dirs['ws2_tab1']))
    tab_manager.add_tab(str(temp_dirs['ws2_tab2']))
    
    # Add paths to sidebar for workspace 2
    sidebar.add_focus_path(str(temp_dirs['ws2_tab1']))
    sidebar.add_focus_path(str(temp_dirs['ws2_tab2']))
    
    # Save workspace 2 state
    workspace_manager.save_current_state(tab_manager, sidebar)
    
    # Verify workspace 2 state
    state2 = workspace_manager.get_workspace_state(workspace2.id)
    assert state2 is not None
    assert len(state2['tabs']) == 2
    # Normalize paths for comparison
    normalized_ws2_tab1 = normalize_path(str(temp_dirs['ws2_tab1']))
    normalized_ws2_tab2 = normalize_path(str(temp_dirs['ws2_tab2']))
    assert normalized_ws2_tab1 in state2['tabs']
    assert normalized_ws2_tab2 in state2['tabs']
    assert len(state2['focus_tree_paths']) == 2
    
    # Step 4: Switch back to workspace 1 and verify state is restored
    workspace_manager.switch_workspace(workspace1.id, tab_manager, sidebar)
    
    # Verify workspace 1 tabs are restored
    tabs1 = tab_manager.get_tabs()
    assert len(tabs1) == 2
    # Normalize paths for comparison
    normalized_ws1_tab1 = normalize_path(str(temp_dirs['ws1_tab1']))
    normalized_ws1_tab2 = normalize_path(str(temp_dirs['ws1_tab2']))
    assert normalized_ws1_tab1 in tabs1
    assert normalized_ws1_tab2 in tabs1
    
    # Verify workspace 1 sidebar paths are restored
    sidebar_paths1, sidebar_expanded1 = sidebar.get_current_state()
    assert len(sidebar_paths1) == 2
    # Normalize sidebar paths for comparison
    normalized_sidebar_paths1 = [normalize_path(p) for p in sidebar_paths1]
    assert normalized_ws1_tab1 in normalized_sidebar_paths1
    assert normalized_ws1_tab2 in normalized_sidebar_paths1
    
    # Step 5: Switch back to workspace 2 and verify state is restored
    workspace_manager.switch_workspace(workspace2.id, tab_manager, sidebar)
    
    # Verify workspace 2 tabs are restored
    tabs2 = tab_manager.get_tabs()
    assert len(tabs2) == 2
    # Normalize paths for comparison
    normalized_ws2_tab1 = normalize_path(str(temp_dirs['ws2_tab1']))
    normalized_ws2_tab2 = normalize_path(str(temp_dirs['ws2_tab2']))
    assert normalized_ws2_tab1 in tabs2
    assert normalized_ws2_tab2 in tabs2
    
    # Verify workspace 2 sidebar paths are restored
    sidebar_paths2, sidebar_expanded2 = sidebar.get_current_state()
    assert len(sidebar_paths2) == 2
    # Normalize sidebar paths for comparison
    normalized_sidebar_paths2 = [normalize_path(p) for p in sidebar_paths2]
    assert normalized_ws2_tab1 in normalized_sidebar_paths2
    assert normalized_ws2_tab2 in normalized_sidebar_paths2
    
    # Step 6: Verify that workspaces maintain independent state
    # Switch to workspace 1 again
    workspace_manager.switch_workspace(workspace1.id, tab_manager, sidebar)
    
    # Verify workspace 1 still has its original tabs
    tabs1_final = tab_manager.get_tabs()
    assert len(tabs1_final) == 2
    # Normalize paths for comparison
    normalized_ws1_tab1 = normalize_path(str(temp_dirs['ws1_tab1']))
    normalized_ws1_tab2 = normalize_path(str(temp_dirs['ws1_tab2']))
    normalized_ws2_tab1 = normalize_path(str(temp_dirs['ws2_tab1']))
    normalized_ws2_tab2 = normalize_path(str(temp_dirs['ws2_tab2']))
    assert normalized_ws1_tab1 in tabs1_final
    assert normalized_ws1_tab2 in tabs1_final
    # Verify workspace 1 does NOT have workspace 2 tabs
    assert normalized_ws2_tab1 not in tabs1_final
    assert normalized_ws2_tab2 not in tabs1_final


def test_empty_workspace_switching(workspace_manager, tab_manager, sidebar, qapp):
    """Test switching to an empty workspace (new workspace without state)."""
    tab_manager.set_workspace_manager(workspace_manager)
    
    # Create new workspace (will be empty)
    workspace = workspace_manager.create_workspace("Empty")
    
    # Switch to empty workspace
    success = workspace_manager.switch_workspace(workspace.id, tab_manager, sidebar)
    assert success is True
    
    # Verify workspace is empty
    tabs = tab_manager.get_tabs()
    assert len(tabs) == 0
    
    sidebar_paths, _ = sidebar.get_current_state()
    assert len(sidebar_paths) == 0
