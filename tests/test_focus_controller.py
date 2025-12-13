"""Tests para FocusManager (sustituye al antiguo FocusController)."""

from app.managers.focus_manager import FocusManager


class StubTabManager:
    """Stub para TabManager usado por FocusManager."""
    def __init__(self):
        self._tabs = []
        self._active_index = -1
        self._history = []
        self._history_index = -1
        self.added_paths = []
        self.removed_paths = []

    def add_tab(self, path: str) -> bool:
        self.added_paths.append(path)
        self._tabs.append(path)
        self._active_index = len(self._tabs) - 1
        return True

    def remove_tab_by_path(self, path: str) -> bool:
        self.removed_paths.append(path)
        try:
            idx = self._tabs.index(path)
            self._tabs.pop(idx)
            self._active_index = min(self._active_index, len(self._tabs) - 1)
            return True
        except ValueError:
            return False

    def get_active_index(self) -> int:
        return self._active_index

    def get_tabs(self) -> list[str]:
        return self._tabs.copy()

    def get_history(self) -> list[str]:
        return self._history.copy()

    def get_history_index(self) -> int:
        return self._history_index


def test_open_focus_with_valid_path():
    """Verifica que open_focus() abre una carpeta válida."""
    tab_manager = StubTabManager()
    fm = FocusManager(tab_manager)

    test_path = "/test/folder"
    fm.open_focus(test_path)

    assert test_path in tab_manager.added_paths
    assert len(tab_manager.added_paths) == 1


def test_open_focus_rejects_empty_path():
    """Verifica que open_focus() rechaza un path vacío."""
    tab_manager = StubTabManager()
    fm = FocusManager(tab_manager)

    fm.open_focus("")

    assert len(tab_manager.added_paths) == 0


def test_close_focus_does_not_break_execution():
    """Verifica que close_focus() no rompe la ejecución y cierra el foco válido."""
    tab_manager = StubTabManager()
    fm = FocusManager(tab_manager)

    fm.close_focus(-1)
    fm.close_focus(999)

    tab_manager._active_index = -1
    fm.close_focus(None)

    tab_manager._tabs = ["/path1", "/path2"]
    tab_manager._active_index = 0
    fm.close_focus(0)

    assert "/path1" in tab_manager.removed_paths

