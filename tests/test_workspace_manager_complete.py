"""
Tests completos para WorkspaceManager.

Cubre create_workspace, delete_workspace, switch_workspace y señales Qt.
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject

from app.managers.workspace_manager import WorkspaceManager


@pytest.fixture
def workspace_manager(qapp, monkeypatch):
    """Crear instancia de WorkspaceManager para tests."""
    # Mockear storage para usar directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    def mock_get_storage_dir():
        from pathlib import Path
        storage_path = Path(temp_dir) / 'storage'
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path
    
    monkeypatch.setattr(
        'app.services.workspace_storage_service.get_storage_dir',
        mock_get_storage_dir
    )
    
    manager = WorkspaceManager()
    
    # Mock tab_manager y sidebar para evitar errores en switch_workspace
    class MockTabManager:
        def get_current_state(self):
            return {'tabs': [], 'active_index': -1}
        def load_workspace_state(self, state):
            pass
    
    class MockSidebar:
        def get_current_state(self):
            return ([], [])
        def get_root_folders_order(self):
            return None
    
    manager._tab_manager = MockTabManager()
    manager._sidebar = MockSidebar()
    
    yield manager
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass


class TestCreateWorkspace:
    """Tests para create_workspace."""
    
    def test_create_workspace_success(self, workspace_manager):
        """Crear workspace exitosamente."""
        workspace = workspace_manager.create_workspace("Test Workspace")
        
        assert workspace is not None
        assert workspace.name == "Test Workspace"
        assert workspace.id is not None
        assert workspace in workspace_manager.get_workspaces()
    
    def test_create_workspace_emits_signal(self, workspace_manager):
        """Validar que emite señal workspace_created."""
        signal_received = []
        
        def on_workspace_created(workspace_id):
            signal_received.append(workspace_id)
        
        workspace_manager.workspace_created.connect(on_workspace_created)
        workspace = workspace_manager.create_workspace("Test")
        
        assert len(signal_received) == 1
        assert signal_received[0] == workspace.id
    
    def test_create_workspace_persists(self, workspace_manager):
        """Validar que workspace se persiste."""
        workspace = workspace_manager.create_workspace("Persistent Workspace")
        
        # Verificar que está en la lista
        workspaces = workspace_manager.get_workspaces()
        assert any(w.id == workspace.id for w in workspaces)


class TestDeleteWorkspace:
    """Tests para delete_workspace."""
    
    def test_delete_workspace_success(self, workspace_manager):
        """Eliminar workspace exitosamente."""
        workspace = workspace_manager.create_workspace("To Delete")
        workspace_id = workspace.id
        
        success = workspace_manager.delete_workspace(workspace_id)
        
        assert success is True
        assert workspace_manager.get_workspace(workspace_id) is None
    
    def test_delete_workspace_nonexistent(self, workspace_manager):
        """Eliminar workspace inexistente."""
        success = workspace_manager.delete_workspace("nonexistent-id")
        
        assert success is False
    
    def test_delete_workspace_emits_signal(self, workspace_manager):
        """Validar que emite señal workspace_deleted."""
        workspace = workspace_manager.create_workspace("To Delete")
        
        signal_received = []
        
        def on_workspace_deleted(workspace_id):
            signal_received.append(workspace_id)
        
        workspace_manager.workspace_deleted.connect(on_workspace_deleted)
        workspace_manager.delete_workspace(workspace.id)
        
        assert len(signal_received) == 1
        assert signal_received[0] == workspace.id
    
    def test_delete_active_workspace_switches(self, workspace_manager):
        """Validar que eliminar workspace activo cambia a otro."""
        workspace1 = workspace_manager.create_workspace("Workspace 1")
        workspace2 = workspace_manager.create_workspace("Workspace 2")
        
        # Activar workspace1
        workspace_manager.switch_workspace(workspace1.id, None, None)
        
        # Eliminar workspace activo
        workspace_manager.delete_workspace(workspace1.id)
        
        # Debe cambiar a otro workspace válido (puede ser Default o workspace2)
        active_id = workspace_manager.get_active_workspace_id()
        assert active_id is not None
        assert active_id != workspace1.id  # No debe ser el eliminado
        assert active_id in [w.id for w in workspace_manager.get_workspaces()]  # Debe existir


class TestSwitchWorkspace:
    """Tests para switch_workspace."""
    
    def test_switch_workspace_success(self, workspace_manager):
        """Cambiar workspace exitosamente."""
        workspace1 = workspace_manager.create_workspace("Workspace 1")
        workspace2 = workspace_manager.create_workspace("Workspace 2")
        
        success = workspace_manager.switch_workspace(workspace2.id, None, None)
        
        assert success is True
        assert workspace_manager.get_active_workspace_id() == workspace2.id
    
    def test_switch_workspace_nonexistent(self, workspace_manager):
        """Cambiar a workspace inexistente."""
        success = workspace_manager.switch_workspace("nonexistent-id", None, None)
        
        assert success is False
    
    def test_switch_workspace_emits_signal(self, workspace_manager):
        """Validar que emite señal workspace_changed."""
        workspace1 = workspace_manager.create_workspace("Workspace 1")
        workspace2 = workspace_manager.create_workspace("Workspace 2")
        
        signal_received = []
        
        def on_workspace_changed(workspace_id):
            signal_received.append(workspace_id)
        
        workspace_manager.workspace_changed.connect(on_workspace_changed)
        workspace_manager.switch_workspace(workspace2.id, None, None)
        
        assert len(signal_received) == 1
        assert signal_received[0] == workspace2.id


class TestGetActiveWorkspace:
    """Tests para get_active_workspace."""
    
    def test_get_active_workspace_success(self, workspace_manager):
        """Obtener workspace activo exitosamente."""
        workspace = workspace_manager.create_workspace("Active Workspace")
        workspace_manager.switch_workspace(workspace.id, None, None)
        
        active = workspace_manager.get_active_workspace()
        
        assert active is not None
        assert active.id == workspace.id
    
    def test_get_active_workspace_none(self, workspace_manager):
        """Obtener workspace activo cuando no hay ninguno."""
        # Eliminar todos los workspaces
        workspaces = workspace_manager.get_workspaces()
        for w in workspaces:
            workspace_manager.delete_workspace(w.id)
        
        active = workspace_manager.get_active_workspace()
        
        # Debe crear uno por defecto o retornar None
        remaining_workspaces = workspace_manager.get_workspaces()
        if remaining_workspaces:
            # Si hay workspaces, debe ser uno de ellos o None
            assert active is None or isinstance(active, type(remaining_workspaces[0]))
        else:
            assert active is None


class TestRenameWorkspace:
    """Tests para rename_workspace."""
    
    def test_rename_workspace_success(self, workspace_manager):
        """Renombrar workspace exitosamente."""
        workspace = workspace_manager.create_workspace("Old Name")
        
        success = workspace_manager.rename_workspace(workspace.id, "New Name")
        
        assert success is True
        renamed = workspace_manager.get_workspace(workspace.id)
        assert renamed.name == "New Name"
    
    def test_rename_workspace_empty_name(self, workspace_manager):
        """Renombrar con nombre vacío."""
        workspace = workspace_manager.create_workspace("Test")
        
        success = workspace_manager.rename_workspace(workspace.id, "")
        
        assert success is False
    
    def test_rename_workspace_nonexistent(self, workspace_manager):
        """Renombrar workspace inexistente."""
        success = workspace_manager.rename_workspace("nonexistent-id", "New Name")
        
        assert success is False


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_multiple_workspaces(self, workspace_manager):
        """Manejar múltiples workspaces."""
        initial_count = len(workspace_manager.get_workspaces())
        workspaces = []
        for i in range(5):
            workspace = workspace_manager.create_workspace(f"Workspace {i}")
            workspaces.append(workspace)
        
        # Debe haber 5 nuevos + los existentes (puede haber un default)
        assert len(workspace_manager.get_workspaces()) >= 5
        
        # Cambiar entre workspaces
        workspace_manager.switch_workspace(workspaces[2].id, None, None)
        assert workspace_manager.get_active_workspace_id() == workspaces[2].id
    
    def test_delete_last_workspace(self, workspace_manager):
        """Eliminar último workspace (debe crear uno por defecto)."""
        # Eliminar todos excepto uno
        workspaces = workspace_manager.get_workspaces()
        for w in workspaces[:-1]:
            workspace_manager.delete_workspace(w.id)
        
        last_workspace = workspace_manager.get_workspaces()[0]
        workspace_manager.delete_workspace(last_workspace.id)
        
        # Debe crear workspace por defecto
        assert len(workspace_manager.get_workspaces()) > 0

