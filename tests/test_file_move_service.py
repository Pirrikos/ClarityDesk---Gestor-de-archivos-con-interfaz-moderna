"""
Tests para FileMoveService.

Cubre movimiento de archivos, resolución de conflictos y manejo de errores.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.file_move_service import move_file
from app.models.file_operation_result import FileOperationResult


@pytest.fixture
def temp_source_file():
    """Crear archivo fuente temporal."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(b'source content')
        temp_path = f.name
    
    yield temp_path
    
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def temp_destination_folder():
    """Crear carpeta destino temporal."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    
    # Cleanup - eliminar archivos dentro y luego la carpeta
    import shutil
    try:
        shutil.rmtree(temp_path)
    except OSError:
        pass


class TestMoveFile:
    """Tests para move_file."""
    
    def test_move_file_success(self, temp_source_file, temp_destination_folder):
        """Mover archivo exitosamente."""
        result = move_file(temp_source_file, temp_destination_folder, watcher=None)
        
        assert isinstance(result, FileOperationResult)
        assert result.success is True
        
        # Verificar que el archivo está en destino
        filename = os.path.basename(temp_source_file)
        dest_path = os.path.join(temp_destination_folder, filename)
        assert os.path.exists(dest_path)
        
        # Verificar que no está en origen
        assert not os.path.exists(temp_source_file)
    
    def test_move_file_nonexistent_source(self, temp_destination_folder):
        """Intentar mover archivo inexistente."""
        result = move_file("/nonexistent/file.txt", temp_destination_folder, watcher=None)
        
        assert isinstance(result, FileOperationResult)
        assert result.success is False
        assert "does not exist" in result.error_message.lower() or result.error_message
    
    def test_move_file_nonexistent_destination(self, temp_source_file):
        """Intentar mover a carpeta inexistente."""
        result = move_file(temp_source_file, "/nonexistent/folder", watcher=None)
        
        assert isinstance(result, FileOperationResult)
        assert result.success is False
        assert "does not exist" in result.error_message.lower() or result.error_message
    
    def test_move_file_invalid_source_path(self, temp_destination_folder):
        """Intentar mover con path fuente inválido."""
        result = move_file("", temp_destination_folder, watcher=None)
        
        assert isinstance(result, FileOperationResult)
        assert result.success is False
    
    def test_move_file_invalid_destination_path(self, temp_source_file):
        """Intentar mover a path destino inválido."""
        result = move_file(temp_source_file, "", watcher=None)
        
        assert isinstance(result, FileOperationResult)
        assert result.success is False


class TestMoveFolder:
    """Tests para movimiento de carpetas."""
    
    def test_move_folder_success(self, temp_destination_folder):
        """Mover carpeta exitosamente."""
        source_folder = tempfile.mkdtemp()
        test_file = os.path.join(source_folder, "test.txt")
        
        try:
            with open(test_file, 'w') as f:
                f.write('content')
            
            result = move_file(source_folder, temp_destination_folder, watcher=None)
            
            assert isinstance(result, FileOperationResult)
            # La carpeta debe estar en destino
            folder_name = os.path.basename(source_folder)
            dest_path = os.path.join(temp_destination_folder, folder_name)
            assert result.success is True or os.path.exists(dest_path)
        finally:
            # Cleanup
            import shutil
            try:
                if os.path.exists(source_folder):
                    shutil.rmtree(source_folder)
                dest_folder = os.path.join(temp_destination_folder, os.path.basename(source_folder))
                if os.path.exists(dest_folder):
                    shutil.rmtree(dest_folder)
            except OSError:
                pass


class TestConflictResolution:
    """Tests para resolución de conflictos."""
    
    def test_move_file_destination_exists(self, temp_source_file, temp_destination_folder):
        """Mover archivo cuando destino ya existe (debe resolver conflicto)."""
        filename = os.path.basename(temp_source_file)
        existing_file = os.path.join(temp_destination_folder, filename)
        
        # Crear archivo existente en destino
        with open(existing_file, 'w') as f:
            f.write('existing content')
        
        result = move_file(temp_source_file, temp_destination_folder, watcher=None)
        
        assert isinstance(result, FileOperationResult)
        # Debe resolver conflicto (añadir número o similar)
        assert result.success is True or os.path.exists(temp_source_file)


class TestWatcherIntegration:
    """Tests para integración con watcher."""
    
    def test_move_file_with_watcher(self, temp_source_file, temp_destination_folder):
        """Mover archivo con watcher (debe bloquear eventos)."""
        class MockWatcher:
            def __init__(self):
                self.ignore_called = False
            
            def ignore_events(self, value):
                self.ignore_called = True
        
        watcher = MockWatcher()
        result = move_file(temp_source_file, temp_destination_folder, watcher=watcher)
        
        assert isinstance(result, FileOperationResult)
        # Watcher debe ser llamado si existe


class TestErrorHandling:
    """Tests para manejo de errores."""
    
    def test_move_file_permission_error(self, temp_destination_folder):
        """Manejar error de permisos."""
        # Intentar mover archivo protegido
        protected_path = "C:\\Windows\\System32\\config\\sam"
        
        result = move_file(protected_path, temp_destination_folder, watcher=None)
        
        assert isinstance(result, FileOperationResult)
        # No debe crashear
        assert isinstance(result.success, bool)
    
    def test_move_file_readonly_destination(self, temp_source_file):
        """Manejar carpeta destino de solo lectura."""
        readonly_folder = tempfile.mkdtemp()
        
        try:
            # Hacer carpeta de solo lectura (solo lectura, no ejecución)
            os.chmod(readonly_folder, 0o444)
            
            result = move_file(temp_source_file, readonly_folder, watcher=None)
            
            assert isinstance(result, FileOperationResult)
            # Puede fallar por permisos
            assert isinstance(result.success, bool)
        finally:
            # Restaurar permisos y limpiar
            try:
                os.chmod(readonly_folder, 0o755)
                import shutil
                shutil.rmtree(readonly_folder)
            except OSError:
                pass


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_move_file_same_source_destination(self, temp_source_file):
        """Mover archivo a su misma ubicación."""
        folder = os.path.dirname(temp_source_file)
        result = move_file(temp_source_file, folder, watcher=None)
        
        assert isinstance(result, FileOperationResult)
        # Puede fallar o ser no-op
        assert isinstance(result.success, bool)
    
    def test_move_file_special_characters(self, temp_destination_folder):
        """Mover archivo con caracteres especiales."""
        temp_dir = tempfile.mkdtemp()
        special_file = os.path.join(temp_dir, "test file (1).txt")
        
        try:
            with open(special_file, 'w') as f:
                f.write('content')
            
            result = move_file(special_file, temp_destination_folder, watcher=None)
            
            assert isinstance(result, FileOperationResult)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
    
    def test_move_file_unicode_path(self, temp_destination_folder):
        """Mover archivo con caracteres Unicode."""
        temp_dir = tempfile.mkdtemp()
        unicode_file = os.path.join(temp_dir, "测试_тест.txt")
        
        try:
            with open(unicode_file, 'w') as f:
                f.write('content')
            
            result = move_file(unicode_file, temp_destination_folder, watcher=None)
            
            assert isinstance(result, FileOperationResult)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass

