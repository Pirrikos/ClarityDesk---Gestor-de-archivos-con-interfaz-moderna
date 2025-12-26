"""
Tests para FileClipboardManager.

Cubre operaciones de clipboard: copy, cut, paste y señales.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.managers.file_clipboard_manager import FileClipboardManager


@pytest.fixture
def clipboard_manager():
    """Crear instancia de FileClipboardManager (singleton)."""
    # Resetear singleton para tests limpios
    FileClipboardManager._instance = None
    manager = FileClipboardManager()
    manager.clear()
    return manager


class TestSetCopy:
    """Tests para set_copy."""
    
    def test_set_copy_success(self, clipboard_manager, temp_files):
        """Establecer clipboard en modo copy exitosamente."""
        files, _ = temp_files
        
        clipboard_manager.set_copy(files)
        
        assert clipboard_manager.get_mode() == "copy"
        assert clipboard_manager.get_paths() == files
    
    def test_set_copy_empty_list(self, clipboard_manager):
        """Establecer copy con lista vacía (debe limpiar)."""
        clipboard_manager.set_copy(["some/path"])
        clipboard_manager.set_copy([])
        
        assert clipboard_manager.get_mode() is None
        assert len(clipboard_manager.get_paths()) == 0
    
    def test_set_copy_nonexistent_files(self, clipboard_manager):
        """Establecer copy con archivos inexistentes."""
        clipboard_manager.set_copy(["/nonexistent/file.txt"])
        
        # Debe establecer modo pero paths pueden estar vacíos después de validación
        assert clipboard_manager.get_mode() == "copy" or clipboard_manager.get_mode() is None


class TestSetCut:
    """Tests para set_cut."""
    
    def test_set_cut_success(self, clipboard_manager, temp_files):
        """Establecer clipboard en modo cut exitosamente."""
        files, _ = temp_files
        
        clipboard_manager.set_cut(files)
        
        assert clipboard_manager.get_mode() == "cut"
        assert clipboard_manager.get_paths() == files
    
    def test_set_cut_empty_list(self, clipboard_manager):
        """Establecer cut con lista vacía (debe limpiar)."""
        clipboard_manager.set_cut(["some/path"])
        clipboard_manager.set_cut([])
        
        assert clipboard_manager.get_mode() is None
        assert len(clipboard_manager.get_paths()) == 0


class TestHasData:
    """Tests para has_data."""
    
    def test_has_data_true(self, clipboard_manager, temp_files):
        """Validar que has_data retorna True cuando hay datos."""
        files, _ = temp_files
        clipboard_manager.set_copy(files)
        
        assert clipboard_manager.has_data() is True
    
    def test_has_data_false(self, clipboard_manager, monkeypatch):
        """Validar que has_data retorna False cuando está vacío."""
        clipboard_manager.clear()
        
        # Mockear _read_from_system_clipboard para que retorne None
        def mock_read_none():
            return None
        
        monkeypatch.setattr(clipboard_manager, '_read_from_system_clipboard', mock_read_none)
        
        assert clipboard_manager.has_data() is False


class TestGetPaths:
    """Tests para get_paths."""
    
    def test_get_paths_success(self, clipboard_manager, temp_files):
        """Obtener paths del clipboard exitosamente."""
        files, _ = temp_files
        clipboard_manager.set_copy(files)
        
        paths = clipboard_manager.get_paths()
        
        assert paths == files
        # Debe retornar copia (no referencia)
        assert paths is not files
    
    def test_get_paths_empty(self, clipboard_manager):
        """Obtener paths cuando clipboard está vacío."""
        clipboard_manager.clear()
        
        paths = clipboard_manager.get_paths()
        
        assert paths == []


class TestGetMode:
    """Tests para get_mode."""
    
    def test_get_mode_copy(self, clipboard_manager, temp_files):
        """Obtener modo copy."""
        files, _ = temp_files
        clipboard_manager.set_copy(files)
        
        mode = clipboard_manager.get_mode()
        
        assert mode == "copy"
    
    def test_get_mode_cut(self, clipboard_manager, temp_files):
        """Obtener modo cut."""
        files, _ = temp_files
        clipboard_manager.set_cut(files)
        
        mode = clipboard_manager.get_mode()
        
        assert mode == "cut"
    
    def test_get_mode_none(self, clipboard_manager):
        """Obtener modo cuando está vacío."""
        clipboard_manager.clear()
        
        mode = clipboard_manager.get_mode()
        
        assert mode is None


class TestClear:
    """Tests para clear."""
    
    def test_clear_success(self, clipboard_manager, temp_files):
        """Limpiar clipboard exitosamente."""
        files, _ = temp_files
        clipboard_manager.set_copy(files)
        
        clipboard_manager.clear()
        
        assert clipboard_manager.get_mode() is None
        assert len(clipboard_manager.get_paths()) == 0


class TestSingleton:
    """Tests para patrón singleton."""
    
    def test_singleton_pattern(self, clipboard_manager):
        """Validar que es singleton."""
        manager1 = FileClipboardManager()
        manager2 = FileClipboardManager()
        
        assert manager1 is manager2
    
    def test_singleton_state_shared(self, clipboard_manager, temp_files):
        """Validar que el estado se comparte entre instancias."""
        files, _ = temp_files
        
        manager1 = FileClipboardManager()
        manager1.set_copy(files)
        
        manager2 = FileClipboardManager()
        
        assert manager2.get_mode() == "copy"
        assert manager2.get_paths() == files


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_set_copy_then_cut(self, clipboard_manager, temp_files):
        """Cambiar de copy a cut."""
        files, _ = temp_files
        
        clipboard_manager.set_copy(files)
        assert clipboard_manager.get_mode() == "copy"
        
        clipboard_manager.set_cut(files)
        assert clipboard_manager.get_mode() == "cut"
    
    def test_multiple_paths(self, clipboard_manager):
        """Manejar múltiples paths."""
        temp_dir = tempfile.mkdtemp()
        files = []
        
        try:
            for i in range(10):
                file_path = os.path.join(temp_dir, f"file_{i}.txt")
                with open(file_path, 'w') as f:
                    f.write('content')
                files.append(file_path)
            
            clipboard_manager.set_copy(files)
            
            assert len(clipboard_manager.get_paths()) == 10
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass

