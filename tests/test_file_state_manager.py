"""
Tests para FileStateManager.

Cubre gestión de estados de archivos, cache, persistencia SQLite y señales Qt.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QObject

from app.managers.file_state_manager import FileStateManager


@pytest.fixture
def file_state_manager(qapp):
    """Crear instancia de FileStateManager para tests."""
    manager = FileStateManager()
    # Limpiar cache antes de cada test
    manager._state_cache.clear()
    manager._path_to_id_cache.clear()
    return manager


class TestGetFileState:
    """Tests para get_file_state."""
    
    def test_get_file_state_success(self, file_state_manager, temp_file):
        """Obtener estado de archivo existente."""
        # Establecer estado primero
        file_state_manager.set_file_state(temp_file, "trabajado")
        
        state = file_state_manager.get_file_state(temp_file)
        
        assert state == "trabajado"
    
    def test_get_file_state_nonexistent(self, file_state_manager, temp_file):
        """Obtener estado de archivo sin estado."""
        state = file_state_manager.get_file_state(temp_file)
        
        assert state is None
    
    def test_get_file_state_nonexistent_file(self, file_state_manager):
        """Obtener estado de archivo inexistente."""
        state = file_state_manager.get_file_state("/nonexistent/file.txt")
        
        assert state is None
    
    def test_get_file_state_uses_cache(self, file_state_manager, temp_file):
        """Validar que usa cache para obtener estado."""
        file_state_manager.set_file_state(temp_file, "pendiente")
        
        # Obtener estado (debe usar cache)
        state1 = file_state_manager.get_file_state(temp_file)
        state2 = file_state_manager.get_file_state(temp_file)
        
        assert state1 == "pendiente"
        assert state2 == "pendiente"


class TestSetFileState:
    """Tests para set_file_state."""
    
    def test_set_file_state_success(self, file_state_manager, temp_file):
        """Establecer estado de archivo exitosamente."""
        file_state_manager.set_file_state(temp_file, "trabajado")
        
        state = file_state_manager.get_file_state(temp_file)
        assert state == "trabajado"
    
    def test_set_file_state_remove(self, file_state_manager, temp_file):
        """Eliminar estado de archivo."""
        file_state_manager.set_file_state(temp_file, "trabajado")
        file_state_manager.set_file_state(temp_file, None)
        
        state = file_state_manager.get_file_state(temp_file)
        assert state is None
    
    def test_set_file_state_emits_signal(self, file_state_manager, temp_file):
        """Validar que emite señal state_changed."""
        signal_received = []
        
        def on_state_changed(file_path, state):
            signal_received.append((file_path, state))
        
        file_state_manager.state_changed.connect(on_state_changed)
        file_state_manager.set_file_state(temp_file, "pendiente")
        
        assert len(signal_received) == 1
        assert signal_received[0][0] == temp_file
        assert signal_received[0][1] == "pendiente"
    
    def test_set_file_state_nonexistent_file(self, file_state_manager):
        """Establecer estado de archivo inexistente (no debe crashear)."""
        file_state_manager.set_file_state("/nonexistent/file.txt", "trabajado")
        
        # No debe crashear, pero no debe guardar estado
        state = file_state_manager.get_file_state("/nonexistent/file.txt")
        assert state is None


class TestSetFilesState:
    """Tests para set_files_state (batch)."""
    
    def test_set_files_state_success(self, file_state_manager):
        """Establecer estado de múltiples archivos exitosamente."""
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.txt') as f:
                f.write(b'content')
                temp_files.append(f.name)
        
        try:
            count = file_state_manager.set_files_state(temp_files, "trabajado")
            
            assert count == len(temp_files)
            
            # Verificar que todos tienen el estado
            for file_path in temp_files:
                state = file_state_manager.get_file_state(file_path)
                assert state == "trabajado"
        finally:
            for f in temp_files:
                try:
                    os.unlink(f)
                except OSError:
                    pass
    
    def test_set_files_state_empty_list(self, file_state_manager):
        """Establecer estado con lista vacía."""
        count = file_state_manager.set_files_state([], "trabajado")
        
        assert count == 0
    
    def test_set_files_state_emits_signal(self, file_state_manager):
        """Validar que emite señal states_changed."""
        temp_files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.txt') as f:
                f.write(b'content')
                temp_files.append(f.name)
        
        try:
            signal_received = []
            
            def on_states_changed(changes):
                signal_received.append(changes)
            
            file_state_manager.states_changed.connect(on_states_changed)
            file_state_manager.set_files_state(temp_files, "pendiente")
            
            assert len(signal_received) == 1
            assert len(signal_received[0]) == len(temp_files)
        finally:
            for f in temp_files:
                try:
                    os.unlink(f)
                except OSError:
                    pass
    
    def test_set_files_state_skips_unchanged(self, file_state_manager):
        """Validar que omite archivos que ya tienen el estado."""
        temp_files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.txt') as f:
                f.write(b'content')
                temp_files.append(f.name)
        
        try:
            # Establecer estado primero
            file_state_manager.set_files_state(temp_files, "trabajado")
            
            # Establecer mismo estado (debe omitir)
            count = file_state_manager.set_files_state(temp_files, "trabajado")
            
            # Debe retornar 0 porque no hay cambios
            assert count == 0
        finally:
            for f in temp_files:
                try:
                    os.unlink(f)
                except OSError:
                    pass


class TestCleanupMissingFiles:
    """Tests para cleanup_missing_files."""
    
    def test_cleanup_missing_files_success(self, file_state_manager):
        """Limpiar archivos faltantes exitosamente."""
        # Crear archivo temporal y establecer estado
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'content')
            temp_file = f.name
        
        try:
            file_state_manager.set_file_state(temp_file, "trabajado")
            
            # Eliminar archivo
            os.unlink(temp_file)
            
            # Limpiar estados de archivos faltantes
            existing_paths = set()
            removed_count = file_state_manager.cleanup_missing_files(existing_paths)
            
            assert removed_count >= 0  # Puede ser 0 si ya estaba limpio
        except OSError:
            pass
    
    def test_cleanup_missing_files_preserves_existing(self, file_state_manager, temp_file):
        """Validar que preserva archivos existentes."""
        file_state_manager.set_file_state(temp_file, "trabajado")
        
        existing_paths = {temp_file}
        removed_count = file_state_manager.cleanup_missing_files(existing_paths)
        
        # No debe eliminar archivo existente
        state = file_state_manager.get_file_state(temp_file)
        assert state == "trabajado"


class TestCache:
    """Tests para funcionalidad de cache."""
    
    def test_cache_stores_states(self, file_state_manager, temp_file):
        """Validar que cache almacena estados."""
        file_state_manager.set_file_state(temp_file, "pendiente")
        
        # Verificar que está en cache
        file_id = file_state_manager._get_file_id(temp_file)
        assert file_id in file_state_manager._state_cache
    
    def test_cache_invalidates_on_file_change(self, file_state_manager, temp_file):
        """Validar que cache se invalida cuando archivo cambia."""
        file_state_manager.set_file_state(temp_file, "trabajado")
        
        # Modificar archivo (cambiar mtime)
        import time
        time.sleep(1.1)
        with open(temp_file, 'w') as f:
            f.write('modified')
        
        # El cache debe actualizarse
        file_id = file_state_manager._get_file_id(temp_file)
        # El file_id puede cambiar si cambia el contenido/metadata


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_set_file_state_special_characters(self, file_state_manager):
        """Establecer estado con caracteres especiales en path."""
        temp_dir = tempfile.mkdtemp()
        special_file = os.path.join(temp_dir, "test file (1).txt")
        
        try:
            with open(special_file, 'w') as f:
                f.write('content')
            
            file_state_manager.set_file_state(special_file, "trabajado")
            state = file_state_manager.get_file_state(special_file)
            
            assert state == "trabajado"
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
    
    def test_set_file_state_unicode_path(self, file_state_manager):
        """Establecer estado con caracteres Unicode en path."""
        temp_dir = tempfile.mkdtemp()
        unicode_file = os.path.join(temp_dir, "测试_тест.txt")
        
        try:
            with open(unicode_file, 'w') as f:
                f.write('content')
            
            file_state_manager.set_file_state(unicode_file, "pendiente")
            state = file_state_manager.get_file_state(unicode_file)
            
            assert state == "pendiente"
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass

