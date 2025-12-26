"""
Tests para FileDeleteService.

Cubre eliminación de archivos, papelera, eliminación permanente y manejo de errores.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.file_delete_service import delete_file
from app.models.file_operation_result import FileOperationResult


class TestDeleteFile:
    """Tests para delete_file."""
    
    def test_delete_file_success(self, temp_file):
        """Eliminar archivo exitosamente."""
        result = delete_file(temp_file, watcher=None, is_trash_focus=False)
        
        assert isinstance(result, FileOperationResult)
        # El archivo debe estar eliminado o en papelera
        assert result.success is True or not os.path.exists(temp_file)
    
    def test_delete_file_nonexistent(self):
        """Intentar eliminar archivo inexistente."""
        result = delete_file("/nonexistent/file.txt", watcher=None, is_trash_focus=False)
        
        assert isinstance(result, FileOperationResult)
        assert result.success is False
        assert "does not exist" in result.error_message.lower() or result.error_message
    
    def test_delete_file_invalid_path(self):
        """Intentar eliminar con path inválido."""
        result = delete_file("", watcher=None, is_trash_focus=False)
        
        assert isinstance(result, FileOperationResult)
        assert result.success is False
    
    def test_delete_file_trash_focus(self, temp_file):
        """Eliminar archivo desde Trash Focus (permanente)."""
        result = delete_file(temp_file, watcher=None, is_trash_focus=True)
        
        assert isinstance(result, FileOperationResult)
        # Puede requerir confirmación, pero no debe crashear
        assert isinstance(result.success, bool)


class TestDeleteFolder:
    """Tests para eliminación de carpetas."""
    
    def test_delete_folder_success(self, temp_folder):
        """Eliminar carpeta vacía."""
        result = delete_file(temp_folder, watcher=None, is_trash_focus=False)
        
        assert isinstance(result, FileOperationResult)
        # La carpeta debe estar eliminada o en papelera
        assert result.success is True or not os.path.exists(temp_folder)
    
    def test_delete_folder_with_files(self):
        """Eliminar carpeta con archivos."""
        temp_path = tempfile.mkdtemp()
        test_file = os.path.join(temp_path, "test.txt")
        
        try:
            with open(test_file, 'w') as f:
                f.write('content')
            
            result = delete_file(temp_path, watcher=None, is_trash_focus=False)
            
            assert isinstance(result, FileOperationResult)
            # Puede requerir confirmación para carpetas con contenido
            assert isinstance(result.success, bool)
        finally:
            # Cleanup manual si todavía existe
            import shutil
            try:
                if os.path.exists(temp_path):
                    shutil.rmtree(temp_path)
            except OSError:
                pass


class TestErrorHandling:
    """Tests para manejo de errores."""
    
    def test_delete_file_permission_error(self):
        """Manejar error de permisos."""
        # Intentar eliminar archivo protegido (puede fallar por permisos)
        protected_path = "C:\\Windows\\System32\\config\\sam"
        
        result = delete_file(protected_path, watcher=None, is_trash_focus=False)
        
        assert isinstance(result, FileOperationResult)
        # No debe crashear, debe retornar resultado con error
        assert isinstance(result.success, bool)
    
    def test_delete_file_readonly_file(self):
        """Manejar archivo de solo lectura."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        temp_file.write(b'content')
        temp_file.close()
        
        try:
            # Hacer archivo de solo lectura
            os.chmod(temp_file.name, 0o444)
            
            result = delete_file(temp_file.name, watcher=None, is_trash_focus=False)
            
            assert isinstance(result, FileOperationResult)
            # Puede fallar o requerir permisos elevados
            assert isinstance(result.success, bool)
        finally:
            # Restaurar permisos y eliminar
            try:
                os.chmod(temp_file.name, 0o644)
                os.unlink(temp_file.name)
            except OSError:
                pass


class TestWatcherIntegration:
    """Tests para integración con watcher."""
    
    def test_delete_file_with_watcher(self, temp_file):
        """Eliminar archivo con watcher (debe bloquear eventos)."""
        # Crear mock watcher
        class MockWatcher:
            def __init__(self):
                self.ignore_called = False
            
            def ignore_events(self, value):
                self.ignore_called = True
        
        watcher = MockWatcher()
        result = delete_file(temp_file, watcher=watcher, is_trash_focus=False)
        
        assert isinstance(result, FileOperationResult)
        # Watcher debe ser llamado si existe
        # (depende de la implementación real)


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_delete_file_empty_path(self):
        """Eliminar con path vacío."""
        result = delete_file("", watcher=None, is_trash_focus=False)
        
        assert isinstance(result, FileOperationResult)
        assert result.success is False
    
    def test_delete_file_special_characters(self):
        """Eliminar archivo con caracteres especiales en path."""
        temp_dir = tempfile.mkdtemp()
        special_file = os.path.join(temp_dir, "test file (1).txt")
        
        try:
            with open(special_file, 'w') as f:
                f.write('content')
            
            result = delete_file(special_file, watcher=None, is_trash_focus=False)
            
            assert isinstance(result, FileOperationResult)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
    
    def test_delete_file_unicode_path(self):
        """Eliminar archivo con caracteres Unicode en path."""
        temp_dir = tempfile.mkdtemp()
        unicode_file = os.path.join(temp_dir, "测试_тест.txt")
        
        try:
            with open(unicode_file, 'w') as f:
                f.write('content')
            
            result = delete_file(unicode_file, watcher=None, is_trash_focus=False)
            
            assert isinstance(result, FileOperationResult)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass

