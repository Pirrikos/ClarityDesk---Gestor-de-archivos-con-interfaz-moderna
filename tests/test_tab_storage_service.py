"""
Tests para TabStorageService.

Cubre guardado y carga de estado de tabs en JSON.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from app.services.tab_storage_service import (
    load_state,
    save_state,
    load_app_state,
    save_app_state
)


@pytest.fixture
def temp_storage():
    """Crear archivo de almacenamiento temporal."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_path = temp_file.name
    temp_file.close()
    
    yield Path(temp_path)
    
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def temp_folders():
    """Crear carpetas temporales para tests."""
    folders = []
    for i in range(3):
        folder = tempfile.mkdtemp()
        folders.append(folder)
    
    yield folders
    
    import shutil
    for folder in folders:
        try:
            shutil.rmtree(folder)
        except OSError:
            pass


def validate_folder(path: str) -> bool:
    """Función de validación simple para tests."""
    return os.path.isdir(path)


class TestLoadState:
    """Tests para load_state."""
    
    def test_load_state_success(self, temp_storage, temp_folders):
        """Cargar estado exitosamente."""
        tabs = temp_folders
        active_index = 0
        
        save_state(temp_storage, tabs, active_index)
        
        loaded_tabs, loaded_index, needs_save = load_state(temp_storage, validate_folder)
        
        assert isinstance(loaded_tabs, list)
        assert len(loaded_tabs) == len(tabs)
        assert loaded_index == active_index
        assert needs_save is False
    
    def test_load_state_nonexistent_file(self, temp_storage):
        """Cargar estado de archivo inexistente."""
        tabs, index, needs_save = load_state(temp_storage, validate_folder)
        
        assert isinstance(tabs, list)
        assert len(tabs) == 0
        assert index == -1
        assert needs_save is False
    
    def test_load_state_invalid_json(self, temp_storage):
        """Cargar estado de archivo JSON inválido."""
        with open(temp_storage, 'w') as f:
            f.write('invalid json')
        
        tabs, index, needs_save = load_state(temp_storage, validate_folder)
        
        assert isinstance(tabs, list)
        assert len(tabs) == 0
        assert index == -1
    
    def test_load_state_filters_invalid_tabs(self, temp_storage, temp_folders):
        """Filtrar tabs inválidos al cargar."""
        tabs = temp_folders + ["/nonexistent/folder"]
        active_index = 0
        
        save_state(temp_storage, tabs, active_index)
        
        loaded_tabs, loaded_index, needs_save = load_state(temp_storage, validate_folder)
        
        assert len(loaded_tabs) == len(temp_folders)
        assert needs_save is True  # Debe marcar que necesita guardar
    
    def test_load_state_adjusts_active_index(self, temp_storage, temp_folders):
        """Ajustar active_index cuando está fuera de rango."""
        tabs = temp_folders
        active_index = 10  # Fuera de rango
        
        save_state(temp_storage, tabs, active_index)
        
        loaded_tabs, loaded_index, needs_save = load_state(temp_storage, validate_folder)
        
        assert loaded_index == 0  # Debe ajustarse a 0
        assert needs_save is True


class TestSaveState:
    """Tests para save_state."""
    
    def test_save_state_success(self, temp_storage, temp_folders):
        """Guardar estado exitosamente."""
        tabs = temp_folders
        active_index = 1
        
        save_state(temp_storage, tabs, active_index)
        
        assert temp_storage.exists()
        
        with open(temp_storage, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['tabs'] == tabs
        assert data['active_index'] == active_index
    
    def test_save_state_empty_tabs(self, temp_storage):
        """Guardar estado con tabs vacíos."""
        save_state(temp_storage, [], -1)
        
        assert temp_storage.exists()
        
        with open(temp_storage, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['tabs'] == []
        assert data['active_index'] == -1


class TestLoadAppState:
    """Tests para load_app_state."""
    
    def test_load_app_state_success(self, temp_storage):
        """Cargar estado completo de aplicación."""
        state = {
            'open_tabs': ['/folder1', '/folder2'],
            'active_tab': '/folder1',
            'history': ['/folder1'],
            'history_index': 0,
            'focus_tree_paths': [],
            'expanded_nodes': []
        }
        
        save_app_state(temp_storage, state)
        
        loaded_state = load_app_state(temp_storage)
        
        assert loaded_state is not None
        assert loaded_state['open_tabs'] == state['open_tabs']
        assert loaded_state['active_tab'] == state['active_tab']
    
    def test_load_app_state_old_format(self, temp_storage):
        """Cargar estado en formato antiguo (tabs/active_index)."""
        old_state = {
            'tabs': ['/folder1', '/folder2'],
            'active_index': 0
        }
        
        with open(temp_storage, 'w', encoding='utf-8') as f:
            json.dump(old_state, f)
        
        loaded_state = load_app_state(temp_storage)
        
        assert loaded_state is not None
        assert loaded_state['open_tabs'] == old_state['tabs']
        assert loaded_state['active_tab'] == old_state['tabs'][0]
    
    def test_load_app_state_nonexistent(self, temp_storage):
        """Cargar estado de archivo inexistente."""
        loaded_state = load_app_state(temp_storage)
        
        assert loaded_state is None
    
    def test_load_app_state_invalid_json(self, temp_storage):
        """Cargar estado de archivo JSON inválido."""
        with open(temp_storage, 'w') as f:
            f.write('invalid json')
        
        loaded_state = load_app_state(temp_storage)
        
        assert loaded_state is None


class TestSaveAppState:
    """Tests para save_app_state."""
    
    def test_save_app_state_success(self, temp_storage):
        """Guardar estado completo de aplicación."""
        state = {
            'open_tabs': ['/folder1', '/folder2'],
            'active_tab': '/folder1',
            'history': ['/folder1'],
            'history_index': 0,
            'focus_tree_paths': [],
            'expanded_nodes': []
        }
        
        save_app_state(temp_storage, state)
        
        assert temp_storage.exists()
        
        loaded_state = load_app_state(temp_storage)
        
        assert loaded_state is not None
        assert loaded_state['open_tabs'] == state['open_tabs']
        assert loaded_state['active_tab'] == state['active_tab']
    
    def test_save_app_state_backwards_compatibility(self, temp_storage):
        """Validar compatibilidad hacia atrás (incluye tabs/active_index)."""
        state = {
            'open_tabs': ['/folder1', '/folder2'],
            'active_tab': '/folder1',
            'history': [],
            'history_index': -1,
            'focus_tree_paths': [],
            'expanded_nodes': []
        }
        
        save_app_state(temp_storage, state)
        
        with open(temp_storage, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Debe incluir tabs y active_index para compatibilidad
        assert 'tabs' in data
        assert 'active_index' in data
        assert data['tabs'] == state['open_tabs']
        assert data['active_index'] == 0


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_load_state_empty_file(self, temp_storage):
        """Cargar estado de archivo vacío."""
        temp_storage.touch()
        
        tabs, index, needs_save = load_state(temp_storage, validate_folder)
        
        assert isinstance(tabs, list)
        assert index == -1
    
    def test_save_state_special_characters(self, temp_storage):
        """Guardar estado con caracteres especiales en paths."""
        tabs = ["C:/test folder (1)", "C:/test folder (2)"]
        save_state(temp_storage, tabs, 0)
        
        loaded_tabs, _, _ = load_state(temp_storage, validate_folder)
        
        assert isinstance(loaded_tabs, list)
    
    def test_save_state_unicode_paths(self, temp_storage):
        """Guardar estado con caracteres Unicode en paths."""
        tabs = ["C:/测试_тест", "C:/文档_document"]
        save_state(temp_storage, tabs, 0)
        
        loaded_tabs, _, _ = load_state(temp_storage, validate_folder)
        
        assert isinstance(loaded_tabs, list)

