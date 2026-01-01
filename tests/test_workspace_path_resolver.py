import os
from dataclasses import dataclass
from typing import List, Optional

from app.services.workspace_path_resolver import resolve_workspace_for_path, get_workspace_name_for_path
from app.models.path_utils import normalize_path


@dataclass
class Workspace:
    id: str
    name: str
    tabs: List[str]
    focus_tree_paths: List[str]


class FakeWorkspaceManager:
    def __init__(self, workspaces: List[Workspace]) -> None:
        self._workspaces = workspaces
        self._by_id = {w.id: w for w in workspaces}

    def get_workspaces(self) -> List[Workspace]:
        return self._workspaces

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        return self._by_id.get(workspace_id)


def test_resolve_workspace_inside_tab():
    # Comentario: archivo dentro del tab debe resolver el workspace correctamente
    ws = Workspace(
        id="ws-1",
        name="Trabajo",
        tabs=[normalize_path(r"C:\Projects\Alpha")],
        focus_tree_paths=[]
    )
    manager = FakeWorkspaceManager([ws])
    file_path = normalize_path(r"C:\Projects\Alpha\src\main.py")

    resolved = resolve_workspace_for_path(file_path, manager)
    assert resolved == "ws-1"


def test_resolve_workspace_exact_match_tab():
    # Comentario: si la ruta del archivo coincide exactamente con el tab, debe resolver
    ws = Workspace(
        id="ws-2",
        name="Docs",
        tabs=[normalize_path(r"C:\Docs")],
        focus_tree_paths=[]
    )
    manager = FakeWorkspaceManager([ws])
    file_path = normalize_path(r"C:\Docs")

    resolved = resolve_workspace_for_path(file_path, manager)
    assert resolved == "ws-2"


def test_resolve_workspace_in_focus_tree_paths():
    # Comentario: archivo dentro de focus_tree_paths también debe resolver
    ws = Workspace(
        id="ws-3",
        name="Beta",
        tabs=[],
        focus_tree_paths=[normalize_path(r"D:\Beta\data")]
    )
    manager = FakeWorkspaceManager([ws])
    file_path = normalize_path(r"D:\Beta\data\items\list.json")

    resolved = resolve_workspace_for_path(file_path, manager)
    assert resolved == "ws-3"


def test_resolve_workspace_not_found_returns_none():
    # Comentario: cuando no hay coincidencias, debe retornar None
    ws = Workspace(
        id="ws-4",
        name="Gamma",
        tabs=[normalize_path(r"C:\Gamma")],
        focus_tree_paths=[]
    )
    manager = FakeWorkspaceManager([ws])
    file_path = normalize_path(r"C:\Other\file.txt")

    resolved = resolve_workspace_for_path(file_path, manager)
    assert resolved is None


def test_resolve_workspace_manager_none_returns_none():
    # Comentario: si workspace_manager es None, debe retornar None
    file_path = normalize_path(r"C:\Projects\Alpha\README.md")
    resolved = resolve_workspace_for_path(file_path, None)
    assert resolved is None


def test_get_workspace_name_for_path_success():
    # Comentario: get_workspace_name_for_path debe devolver el nombre correcto
    ws = Workspace(
        id="ws-5",
        name="Omega",
        tabs=[normalize_path(r"E:\Omega")],
        focus_tree_paths=[]
    )
    manager = FakeWorkspaceManager([ws])
    file_path = normalize_path(r"E:\Omega\notes.txt")

    name = get_workspace_name_for_path(file_path, manager)
    assert name == "Omega"
