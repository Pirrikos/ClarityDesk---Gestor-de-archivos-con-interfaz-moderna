import os
from pathlib import Path

import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.managers.tab_manager import TabManager
from app.ui.widgets.file_view_container import FileViewContainer
from app.ui.widgets.file_view_sync import update_files, switch_view
from app.ui.widgets.file_view_setup import setup_ui
from app.services.file_extensions import SUPPORTED_EXTENSIONS
from app.services.file_list_service import get_files
from app.services.file_state_storage import initialize_database, set_state, get_file_id_from_path
from app.services.storage_path_service import get_storage_file, clear_cache
from app.services.path_utils import normalize_path


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
def test_state_sort_and_navigation(tmp_path, state_id):
    app = QApplication.instance() or QApplication([])

    # Prepare files (multiple in the same state)
    a = tmp_path / "a.txt"
    b = tmp_path / "b.pdf"
    c = tmp_path / "c.docx"
    e = tmp_path / "e.txt"
    _touch(a, "a")
    _touch(b, "b")
    _touch(c, "c")
    _touch(e, "e")

    tm = TabManager(storage_path=str(tmp_path / "tabs.json"))
    tm.add_tab(str(tmp_path))
    tm.select_tab(0)

    container = FileViewContainer(tm)
    setup_ui(container)
    container._workspace_grid_button = None
    container._workspace_list_button = None
    container._workspace_selector = None

    # Normal list/grid
    update_files(container)
    switch_view(container, "list")
    expected = _expected_list(tmp_path)
    assert container._list_view.rowCount() == len(expected)

    # Clean DB and set states for a,b,c
    clear_cache()
    db_path = get_storage_file("claritydesk.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass
    initialize_database()
    for p in (a, b, c):
        fid = get_file_id_from_path(str(p))
        size, modified = _stat(p)
        set_state(fid, str(p), size, modified, state_id)

    # Activate state view and refresh
    tm.set_state_context(state_id)
    update_files(container)

    # Sort by name asc then by date desc
    container._list_view.sortItems(1, Qt.SortOrder.AscendingOrder)
    container._list_view.sortItems(3, Qt.SortOrder.DescendingOrder)
    # Verify visible count matches items by state
    state_items = [normalize_path(p) for p in tm.get_files(use_stacks=False)]
    assert container._list_view.rowCount() == len(state_items)

    # Navigate to other folder and back
    other = tmp_path / "other"
    other.mkdir()
    _touch(other / "z.txt", "z")
    tm.add_tab(str(other))
    tm.select_tab(1)
    update_files(container)
    switch_view(container, "grid")
    assert container._grid_view is not None

    tm.select_tab(0)
    update_files(container)
    switch_view(container, "list")
    # Al seleccionar tab físico se limpia contexto de estado automáticamente
    expected_after = _expected_list(tmp_path)
    assert container._list_view.rowCount() == len(expected_after)
