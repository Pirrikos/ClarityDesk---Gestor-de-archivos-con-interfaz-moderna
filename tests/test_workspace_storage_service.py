"""
Tests para WorkspaceStorageService.

Cubre guardado y carga de workspaces y su estado en JSON.
"""

import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest

from app.models.workspace import Workspace
from app.services.workspace_storage_service import (
    get_storage_dir,
    get_workspaces_file,
    get_workspace_state_file,
    load_workspaces,
    save_workspaces,
    load_workspace_state,
    save_workspace_state,
    get_active_workspace_id
)


@pytest.fixture
def temp_storage_dir(monkeypatch):
    """Crear directorio de almacenamiento temporal."""
    temp_dir = tempfile.mkdtemp()
    
    # Mockear get_storage_dir para usar directorio temporal
    original_get_storage_dir = get_storage_dir
    
    def mock_get_storage_dir():
        storage_path = Path(temp_dir) / 'storage'
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path
    
    monkeypatch.setattr('app.services.workspace_storage_service.get_storage_dir', mock_get_storage_dir)
    
    yield temp_dir
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass


@pytest.fixture
def sample_workspace():
    """Crear workspace de ejemplo."""
    return Workspace(
        id=str(uuid.uuid4()),
        name="Test Workspace",
        tabs=[],
        active_tab=None,
        focus_tree_paths=[],
        expanded_nodes=[],
        view_mode="grid"
    )


class TestGetStorageDir:
    """Tests para get_storage_dir."""
    
    def test_get_storage_dir_creates_directory(self, temp_storage_dir):
        """Validar que crea el directorio si no existe."""
        storage_dir = get_storage_dir()
        
        assert storage_dir.exists()
        assert storage_dir.is_dir()


class TestGetWorkspacesFile:
    """Tests para get_workspaces_file."""
    
    def test_get_workspaces_file_returns_path(self, temp_storage_dir):
        """Obtener path del archivo de workspaces."""
        workspaces_file = get_workspaces_file()
        
        assert isinstance(workspaces_file, Path)
        assert workspaces_file.name == 'workspaces.json'


class TestGetWorkspaceStateFile:
    """Tests para get_workspace_state_file."""
    
    def test_get_workspace_state_file_returns_path(self, temp_storage_dir):
        """Obtener path del archivo de estado de workspace."""
        workspace_id = str(uuid.uuid4())
        state_file = get_workspace_state_file(workspace_id)
        
        assert isinstance(state_file, Path)
        assert state_file.name == f'workspace_{workspace_id}.json'


class TestLoadWorkspaces:
    """Tests para load_workspaces."""
    
    def test_load_workspaces_empty(self, temp_storage_dir):
        """Cargar workspaces cuando no hay ninguno."""
        workspaces = load_workspaces()
        
        assert isinstance(workspaces, list)
        assert len(workspaces) == 0
    
    def test_load_workspaces_success(self, temp_storage_dir, sample_workspace):
        """Cargar workspaces exitosamente."""
        # Guardar workspace primero
        save_workspace_state(sample_workspace.id, {
            'tabs': sample_workspace.tabs,
            'active_tab': sample_workspace.active_tab,
            'focus_tree_paths': sample_workspace.focus_tree_paths,
            'expanded_nodes': sample_workspace.expanded_nodes,
            'view_mode': sample_workspace.view_mode
        })
        save_workspaces([sample_workspace], sample_workspace.id)
        
        # Cargar
        workspaces = load_workspaces()
        
        assert isinstance(workspaces, list)
        assert len(workspaces) > 0
        assert any(w.id == sample_workspace.id for w in workspaces)
    
    def test_load_workspaces_invalid_json(self, temp_storage_dir):
        """Cargar workspaces de archivo JSON inválido."""
        workspaces_file = get_workspaces_file()
        workspaces_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(workspaces_file, 'w') as f:
            f.write('invalid json')
        
        workspaces = load_workspaces()
        
        assert isinstance(workspaces, list)
        assert len(workspaces) == 0


class TestSaveWorkspaces:
    """Tests para save_workspaces."""
    
    def test_save_workspaces_success(self, temp_storage_dir, sample_workspace):
        """Guardar workspaces exitosamente."""
        save_workspaces([sample_workspace], sample_workspace.id)
        
        workspaces_file = get_workspaces_file()
        assert workspaces_file.exists()
        
        with open(workspaces_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'workspaces' in data
        assert len(data['workspaces']) == 1
        assert data['workspaces'][0]['id'] == sample_workspace.id
        assert data['active_workspace_id'] == sample_workspace.id
    
    def test_save_workspaces_multiple(self, temp_storage_dir):
        """Guardar múltiples workspaces."""
        workspaces = [
            Workspace(
                id=str(uuid.uuid4()),
                name=f"Workspace {i}",
                tabs=[],
                active_tab=None,
                focus_tree_paths=[],
                expanded_nodes=[],
                view_mode="grid"
            )
            for i in range(3)
        ]
        
        # Guardar estados de cada workspace primero
        from app.services.workspace_storage_service import save_workspace_state
        for workspace in workspaces:
            save_workspace_state(workspace.id, {
                'tabs': workspace.tabs,
                'active_tab': workspace.active_tab,
                'focus_tree_paths': workspace.focus_tree_paths,
                'expanded_nodes': workspace.expanded_nodes,
                'view_mode': workspace.view_mode
            })
        
        save_workspaces(workspaces, workspaces[0].id)
        
        loaded = load_workspaces()
        assert len(loaded) == 3


class TestLoadWorkspaceState:
    """Tests para load_workspace_state."""
    
    def test_load_workspace_state_nonexistent(self, temp_storage_dir):
        """Cargar estado de workspace inexistente."""
        workspace_id = str(uuid.uuid4())
        state = load_workspace_state(workspace_id)
        
        assert state is None
    
    def test_load_workspace_state_success(self, temp_storage_dir, sample_workspace):
        """Cargar estado de workspace exitosamente."""
        state_data = {
            'tabs': ['/folder1', '/folder2'],
            'active_tab': '/folder1',
            'focus_tree_paths': [],
            'expanded_nodes': [],
            'view_mode': 'grid'
        }
        
        save_workspace_state(sample_workspace.id, state_data)
        
        loaded_state = load_workspace_state(sample_workspace.id)
        
        assert loaded_state is not None
        assert loaded_state['tabs'] == state_data['tabs']
        assert loaded_state['active_tab'] == state_data['active_tab']
        assert loaded_state['view_mode'] == state_data['view_mode']
    
    def test_load_workspace_state_invalid_json(self, temp_storage_dir):
        """Cargar estado de archivo JSON inválido."""
        workspace_id = str(uuid.uuid4())
        state_file = get_workspace_state_file(workspace_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_file, 'w') as f:
            f.write('invalid json')
        
        state = load_workspace_state(workspace_id)
        
        assert state is None


class TestSaveWorkspaceState:
    """Tests para save_workspace_state."""
    
    def test_save_workspace_state_success(self, temp_storage_dir, sample_workspace):
        """Guardar estado de workspace exitosamente."""
        state_data = {
            'tabs': ['/folder1'],
            'active_tab': '/folder1',
            'focus_tree_paths': [],
            'expanded_nodes': [],
            'view_mode': 'list'
        }
        
        save_workspace_state(sample_workspace.id, state_data)
        
        state_file = get_workspace_state_file(sample_workspace.id)
        assert state_file.exists()
        
        loaded_state = load_workspace_state(sample_workspace.id)
        assert loaded_state is not None
        assert loaded_state['view_mode'] == 'list'


class TestGetActiveWorkspaceId:
    """Tests para get_active_workspace_id."""
    
    def test_get_active_workspace_id_nonexistent(self, temp_storage_dir):
        """Obtener active_workspace_id cuando no existe archivo."""
        active_id = get_active_workspace_id()
        
        assert active_id is None
    
    def test_get_active_workspace_id_success(self, temp_storage_dir, sample_workspace):
        """Obtener active_workspace_id exitosamente."""
        save_workspaces([sample_workspace], sample_workspace.id)
        
        active_id = get_active_workspace_id()
        
        assert active_id == sample_workspace.id


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_save_load_workspace_complete_cycle(self, temp_storage_dir):
        """Ciclo completo de guardado y carga."""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name="Complete Test",
            tabs=['/test1', '/test2'],
            active_tab='/test1',
            focus_tree_paths=['/test1'],
            expanded_nodes=['/test1'],
            view_mode='grid'
        )
        
        # Guardar estado
        save_workspace_state(workspace.id, {
            'tabs': workspace.tabs,
            'active_tab': workspace.active_tab,
            'focus_tree_paths': workspace.focus_tree_paths,
            'expanded_nodes': workspace.expanded_nodes,
            'view_mode': workspace.view_mode
        })
        
        # Guardar workspaces
        save_workspaces([workspace], workspace.id)
        
        # Cargar
        loaded_workspaces = load_workspaces()
        
        assert len(loaded_workspaces) == 1
        loaded = loaded_workspaces[0]
        assert loaded.id == workspace.id
        assert loaded.name == workspace.name
        assert loaded.tabs == workspace.tabs

