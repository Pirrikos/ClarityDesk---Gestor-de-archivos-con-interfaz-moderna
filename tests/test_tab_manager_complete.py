"""
Tests completos para TabManager.

Cubre add_tab, remove_tab, select_tab, get_files y señales Qt.
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject

from app.managers.tab_manager import TabManager


@pytest.fixture
def tab_manager(qapp, temp_storage):
    """Crear instancia de TabManager para tests."""
    manager = TabManager(storage_path=temp_storage)
    return manager


class TestAddTab:
    """Tests para add_tab."""
    
    def test_add_tab_success(self, tab_manager, temp_folder):
        """Añadir tab válido exitosamente."""
        success = tab_manager.add_tab(temp_folder)
        
        assert success is True
        assert temp_folder in tab_manager.get_tabs()
        assert tab_manager.get_active_index() == 0
    
    def test_add_tab_duplicate(self, tab_manager, temp_folder):
        """Añadir tab duplicado (debe activar existente)."""
        tab_manager.add_tab(temp_folder)
        original_index = tab_manager.get_active_index()
        
        # Intentar añadir mismo tab
        success = tab_manager.add_tab(temp_folder)
        
        assert success is True
        # Debe activar el tab existente, no crear duplicado
        assert len(tab_manager.get_tabs()) == 1
        assert tab_manager.get_active_index() == original_index
    
    def test_add_tab_invalid_path(self, tab_manager):
        """Añadir tab con path inválido."""
        success = tab_manager.add_tab("/nonexistent/folder")
        
        assert success is False
    
    def test_add_tab_empty_path(self, tab_manager):
        """Añadir tab con path vacío."""
        success = tab_manager.add_tab("")
        
        assert success is False
    
    def test_add_tab_emits_signals(self, tab_manager, temp_folder):
        """Validar que emite señales al añadir tab."""
        tabs_changed_received = []
        active_tab_changed_received = []
        
        def on_tabs_changed(tabs):
            tabs_changed_received.append(tabs)
        
        def on_active_tab_changed(index, path):
            active_tab_changed_received.append((index, path))
        
        tab_manager.tabsChanged.connect(on_tabs_changed)
        tab_manager.activeTabChanged.connect(on_active_tab_changed)
        
        tab_manager.add_tab(temp_folder)
        
        assert len(tabs_changed_received) > 0
        assert len(active_tab_changed_received) > 0


class TestRemoveTab:
    """Tests para remove_tab."""
    
    def test_remove_tab_success(self, tab_manager, temp_folder):
        """Eliminar tab exitosamente."""
        tab_manager.add_tab(temp_folder)
        
        success = tab_manager.remove_tab(0)
        
        assert success is True
        assert len(tab_manager.get_tabs()) == 0
    
    def test_remove_tab_invalid_index(self, tab_manager):
        """Eliminar tab con índice inválido."""
        success = tab_manager.remove_tab(10)
        
        assert success is False
    
    def test_remove_tab_by_path_success(self, tab_manager, temp_folder):
        """Eliminar tab por path exitosamente."""
        tab_manager.add_tab(temp_folder)
        
        success = tab_manager.remove_tab_by_path(temp_folder)
        
        assert success is True
        assert len(tab_manager.get_tabs()) == 0
    
    def test_remove_tab_by_path_nonexistent(self, tab_manager):
        """Eliminar tab por path inexistente."""
        success = tab_manager.remove_tab_by_path("/nonexistent/folder")
        
        assert success is False
    
    def test_remove_tab_emits_signals(self, tab_manager, temp_folder):
        """Validar que emite señales al eliminar tab."""
        tabs_changed_received = []
        
        def on_tabs_changed(tabs):
            tabs_changed_received.append(tabs)
        
        tab_manager.tabsChanged.connect(on_tabs_changed)
        tab_manager.add_tab(temp_folder)
        tab_manager.remove_tab(0)
        
        assert len(tabs_changed_received) >= 2  # Al menos add y remove


class TestSelectTab:
    """Tests para select_tab."""
    
    def test_select_tab_success(self, tab_manager):
        """Seleccionar tab exitosamente."""
        folders = [tempfile.mkdtemp() for _ in range(3)]
        
        try:
            for folder in folders:
                tab_manager.add_tab(folder)
            
            success = tab_manager.select_tab(1)
            
            assert success is True
            assert tab_manager.get_active_index() == 1
        finally:
            import shutil
            for folder in folders:
                try:
                    shutil.rmtree(folder)
                except OSError:
                    pass
    
    def test_select_tab_invalid_index(self, tab_manager, temp_folder):
        """Seleccionar tab con índice inválido."""
        tab_manager.add_tab(temp_folder)
        
        success = tab_manager.select_tab(10)
        
        assert success is False
    
    def test_select_tab_emits_signal(self, tab_manager):
        """Validar que emite señal al seleccionar tab."""
        folders = [tempfile.mkdtemp() for _ in range(2)]
        
        try:
            for folder in folders:
                tab_manager.add_tab(folder)
            
            # Después de añadir tabs, el último es activo (índice 1)
            # Seleccionar el primero (índice 0) para que cambie
            active_tab_changed_received = []
            
            def on_active_tab_changed(index, path):
                active_tab_changed_received.append((index, path))
            
            tab_manager.activeTabChanged.connect(on_active_tab_changed)
            tab_manager.select_tab(0)  # Cambiar de índice 1 a 0
            
            assert len(active_tab_changed_received) > 0
        finally:
            import shutil
            for folder in folders:
                try:
                    shutil.rmtree(folder)
                except OSError:
                    pass


class TestGetActiveFolder:
    """Tests para get_active_folder."""
    
    def test_get_active_folder_success(self, tab_manager, temp_folder):
        """Obtener carpeta activa exitosamente."""
        tab_manager.add_tab(temp_folder)
        
        active_folder = tab_manager.get_active_folder()
        
        assert active_folder == temp_folder
    
    def test_get_active_folder_no_tabs(self, tab_manager):
        """Obtener carpeta activa cuando no hay tabs."""
        active_folder = tab_manager.get_active_folder()
        
        assert active_folder is None


class TestGetFiles:
    """Tests para get_files."""
    
    def test_get_files_success(self, tab_manager, temp_folder):
        """Obtener archivos de tab activo exitosamente."""
        # Crear archivos en carpeta
        for i in range(3):
            file_path = os.path.join(temp_folder, f"test_{i}.txt")
            with open(file_path, 'w') as f:
                f.write('content')
        
        tab_manager.add_tab(temp_folder)
        
        files = tab_manager.get_files()
        
        assert isinstance(files, list)
        assert len(files) >= 3  # Al menos los archivos creados
    
    def test_get_files_no_active_tab(self, tab_manager):
        """Obtener archivos cuando no hay tab activo."""
        files = tab_manager.get_files()
        
        assert isinstance(files, list)
        assert len(files) == 0


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_multiple_tabs(self, tab_manager):
        """Manejar múltiples tabs."""
        folders = [tempfile.mkdtemp() for _ in range(5)]
        
        try:
            for folder in folders:
                tab_manager.add_tab(folder)
            
            assert len(tab_manager.get_tabs()) == 5
            
            # Seleccionar diferentes tabs
            tab_manager.select_tab(2)
            assert tab_manager.get_active_index() == 2
            
            tab_manager.select_tab(4)
            assert tab_manager.get_active_index() == 4
        finally:
            import shutil
            for folder in folders:
                try:
                    shutil.rmtree(folder)
                except OSError:
                    pass
    
    def test_remove_active_tab(self, tab_manager):
        """Eliminar tab activo."""
        folders = [tempfile.mkdtemp() for _ in range(3)]
        
        try:
            for folder in folders:
                tab_manager.add_tab(folder)
            
            tab_manager.select_tab(1)
            tab_manager.remove_tab(1)
            
            # Debe ajustar índice activo
            assert tab_manager.get_active_index() >= 0
            assert tab_manager.get_active_index() < len(tab_manager.get_tabs())
        finally:
            import shutil
            for folder in folders:
                try:
                    shutil.rmtree(folder)
                except OSError:
                    pass

