"""Tests for FocusController."""

from app.controllers.focus_controller import FocusController


class StubFocusManager:
    """Stub for FocusManager."""
    
    def __init__(self):
        self.opened_paths = []
        self.removed_paths = []
    
    def open_or_create_focus_for_path(self, path: str) -> None:
        """Track opened paths."""
        self.opened_paths.append(path)
    
    def remove_focus(self, path: str) -> None:
        """Track removed paths."""
        self.removed_paths.append(path)


class StubTabManager:
    """Stub for TabManager."""
    
    def __init__(self):
        self._tabs = []
        self._active_index = -1
        self._history = []
        self._history_index = -1
    
    def get_active_index(self) -> int:
        """Return active index."""
        return self._active_index
    
    def get_tabs(self) -> list[str]:
        """Return tabs list."""
        return self._tabs.copy()
    
    def get_history(self) -> list[str]:
        """Return history list."""
        return self._history.copy()
    
    def get_history_index(self) -> int:
        """Return history index."""
        return self._history_index


def test_open_focus_with_valid_path():
    """Test that open_focus() opens a valid folder."""
    focus_manager = StubFocusManager()
    tab_manager = StubTabManager()
    controller = FocusController(focus_manager, tab_manager)
    
    test_path = "/test/folder"
    controller.open_focus(test_path)
    
    assert test_path in focus_manager.opened_paths
    assert len(focus_manager.opened_paths) == 1


def test_open_focus_rejects_empty_path():
    """Test that open_focus() rejects empty path."""
    focus_manager = StubFocusManager()
    tab_manager = StubTabManager()
    controller = FocusController(focus_manager, tab_manager)
    
    controller.open_focus("")
    
    assert len(focus_manager.opened_paths) == 0


def test_close_focus_does_not_break_execution():
    """Test that close_focus() does not break execution."""
    focus_manager = StubFocusManager()
    tab_manager = StubTabManager()
    controller = FocusController(focus_manager, tab_manager)
    
    # Test with invalid index
    controller.close_focus(-1)
    controller.close_focus(999)
    
    # Test with None (should use active index)
    tab_manager._active_index = -1
    controller.close_focus(None)
    
    # Test with valid index
    tab_manager._tabs = ["/path1", "/path2"]
    tab_manager._active_index = 0
    controller.close_focus(0)
    
    assert "/path1" in focus_manager.removed_paths

