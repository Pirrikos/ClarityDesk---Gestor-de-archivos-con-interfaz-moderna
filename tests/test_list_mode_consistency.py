import os
import time
from pathlib import Path

import pytest

from app.managers.tab_manager import TabManager
from app.managers.state_label_manager import StateLabelManager
from app.services.file_extensions import SUPPORTED_EXTENSIONS
from app.services.file_list_service import get_files


def _touch(p: Path, content: str, delay: float = 0.0):
    p.write_text(content, encoding="utf-8")
    if delay:
        time.sleep(delay)


def _create_files(tmp: Path):
    _touch(tmp / "1 - alpha.txt", "a", 0.05)
    _touch(tmp / "2 - beta.pdf", "b", 0.05)
    _touch(tmp / "gamma.docx", "c", 0.05)
    _touch(tmp / "unsupported.xyz", "x")
    (tmp / "subfolder").mkdir()


def _list_dir_filtered(folder: Path):
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


def _sort_by_mtime(paths):
    return sorted(paths, key=lambda p: Path(p).stat().st_mtime, reverse=True)


@pytest.mark.parametrize("use_stacks", [False])
def test_consistency_with_navigation_and_sorting(tmp_path, use_stacks):
    _create_files(tmp_path)
    manager = TabManager(storage_path=str(tmp_path / "tabs.json"))
    manager.add_tab(str(tmp_path))
    manager.select_tab(0)

    expected = _list_dir_filtered(tmp_path)
    listed = get_files(str(tmp_path), SUPPORTED_EXTENSIONS, use_stacks=use_stacks)
    assert sorted(listed) == expected

    by_name = sorted(listed)
    by_date = _sort_by_mtime(listed)
    assert set(by_name) == set(by_date)

    state_labels = StateLabelManager()
    _ = state_labels.get_all_labels()

    manager.get_files(use_stacks=use_stacks)
    manager.get_files(use_stacks=use_stacks)

    other = tmp_path / "other"
    other.mkdir()
    _touch(other / "zeta.txt", "z")
    manager.add_tab(str(other))
    manager.select_tab(1)
    listed_other = manager.get_files(use_stacks=use_stacks)
    assert any(Path(p).name == "zeta.txt" for p in listed_other)

    manager.select_tab(0)
    again = manager.get_files(use_stacks=use_stacks)
    expected_after = _list_dir_filtered(tmp_path)
    assert sorted(again) == expected_after
