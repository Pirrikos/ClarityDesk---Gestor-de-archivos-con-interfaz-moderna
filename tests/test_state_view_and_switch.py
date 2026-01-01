import os
from pathlib import Path

import pytest

from PySide6.QtWidgets import QApplication

from app.managers.tab_manager import TabManager
from app.ui.widgets.file_view_container import FileViewContainer
from app.ui.widgets.file_view_sync import update_files, switch_view
from app.ui.widgets.file_view_setup import setup_ui
from app.services.file_extensions import SUPPORTED_EXTENSIONS
from app.services.path_utils import normalize_path
from app.services.file_list_service import get_files
from app.services.file_state_storage import initialize_database, set_state, get_file_id_from_path
from app.services.storage_path_service import get_storage_file, clear_cache


def _touch(p: Path, content: str):
    p.write_text(content, encoding="utf-8")


def _stat(p: Path):
    st = os.stat(p)
    return st.st_size, int(st.st_mtime)


def _expected_list(folder: Path):
    items = []
    for name in os.listdir(folder):
        full = folder / name
        if full.is_dir():
            items.append(str(full))
        elif full.is_file():
            ext = full.suffix.lower()
            if ext in SUPPORTED_EXTENSIONS or (ext == "" and False):
                items.append(str(full))
    return sorted(items)


@pytest.mark.parametrize("state_id", ["pending"])
def test_state_view_consistency_and_switch(tmp_path, state_id):
    # Ensure Qt app
    app = QApplication.instance() or QApplication([])

    # Prepare files
    a = tmp_path / "a.txt"
    b = tmp_path / "b.pdf"
    c = tmp_path / "c.docx"
    d = tmp_path / "ignore.xyz"
    _touch(a, "a")
    _touch(b, "b")
    _touch(c, "c")
    _touch(d, "x")

    # Tab manager and container
    tm = TabManager(storage_path=str(tmp_path / "tabs.json"))
    tm.add_tab(str(tmp_path))
    tm.select_tab(0)

    container = FileViewContainer(tm)
    setup_ui(container)
    # Ensure workspace buttons attributes exist to avoid AttributeError in helper
    container._workspace_grid_button = None
    container._workspace_list_button = None
    container._workspace_selector = None

    # Normal view files
    listed = get_files(str(tmp_path), SUPPORTED_EXTENSIONS, use_stacks=False)
    expected = _expected_list(tmp_path)
    assert sorted(listed) == expected

    # Populate views and switch list/grid
    update_files(container)
    switch_view(container, "list")
    assert container._list_view.rowCount() == len(expected)
    switch_view(container, "grid")

    # Initialize fresh DB and set states for a subset
    clear_cache()
    db_path = get_storage_file("claritydesk.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass
    initialize_database()
    for p in (a, c):
        file_id = get_file_id_from_path(str(p))
        size, modified = _stat(p)
        set_state(file_id, str(p), size, modified, state_id)

    # Activate state context and refresh
    tm.set_state_context(state_id)
    # FileViewContainer listens activeTabChanged with path=None for state context
    update_files(container)

    # Items by state should be exactly the two we set
    state_items = tm.get_files(use_stacks=False)
    expected_state = sorted([normalize_path(str(a)), normalize_path(str(c))])
    assert sorted([normalize_path(p) for p in state_items]) == expected_state

    # Views reflect the same count and switching preserves it
    switch_view(container, "list")
    assert container._list_view.rowCount() == len(expected_state)
    switch_view(container, "grid")

    # Clear state context, return to normal and verify counts again
    tm.clear_state_context()
    tm.select_tab(0)
    update_files(container)
    switch_view(container, "list")
    assert container._list_view.rowCount() == len(expected)
    switch_view(container, "grid")
