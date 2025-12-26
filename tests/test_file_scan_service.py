"""
Tests para FileScanService.

Cubre escaneo de carpetas, Desktop Focus, Trash Focus y manejo de errores.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.file_scan_service import (
    scan_folder_files,
    scan_desktop_files,
    scan_trash_files,
    scan_files
)


@pytest.fixture
def temp_folder_with_files():
    """Crear carpeta temporal con archivos."""
    temp_path = tempfile.mkdtemp()
    
    # Crear archivos
    files = ['test1.txt', 'test2.pdf', 'document.docx']
    for filename in files:
        file_path = os.path.join(temp_path, filename)
        with open(file_path, 'wb') as f:
            f.write(b'content')
    
    # Crear subcarpeta
    subfolder = os.path.join(temp_path, 'subfolder')
    os.makedirs(subfolder)
    
    yield temp_path
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_path)
    except OSError:
        pass


@pytest.fixture
def empty_folder():
    """Crear carpeta vacía."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    
    try:
        os.rmdir(temp_path)
    except OSError:
        pass


class TestScanFolderFiles:
    """Tests para scan_folder_files."""
    
    def test_scan_folder_files_success(self, temp_folder_with_files):
        """Escanear carpeta con archivos exitosamente."""
        result = scan_folder_files(temp_folder_with_files)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Debe incluir archivos y carpetas
        assert any('.txt' in f for f in result)
        assert any('.pdf' in f for f in result)
        assert any('subfolder' in f for f in result)
    
    def test_scan_folder_files_empty(self, empty_folder):
        """Escanear carpeta vacía."""
        result = scan_folder_files(empty_folder)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_scan_folder_files_nonexistent(self):
        """Escanear carpeta inexistente."""
        result = scan_folder_files("/nonexistent/folder")
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_scan_folder_files_includes_folders(self, temp_folder_with_files):
        """Validar que incluye carpetas."""
        result = scan_folder_files(temp_folder_with_files)
        
        folders = [f for f in result if os.path.isdir(f)]
        assert len(folders) > 0
    
    def test_scan_folder_files_includes_files(self, temp_folder_with_files):
        """Validar que incluye archivos."""
        result = scan_folder_files(temp_folder_with_files)
        
        files = [f for f in result if os.path.isfile(f)]
        assert len(files) > 0


class TestScanDesktopFiles:
    """Tests para scan_desktop_files."""
    
    def test_scan_desktop_files_success(self):
        """Escanear archivos del escritorio."""
        result = scan_desktop_files()
        
        assert isinstance(result, list)
        # Puede estar vacío si no hay archivos, pero no debe crashear
    
    def test_scan_desktop_files_returns_list(self):
        """Validar que siempre retorna lista."""
        result = scan_desktop_files()
        
        assert isinstance(result, list)


class TestScanTrashFiles:
    """Tests para scan_trash_files."""
    
    def test_scan_trash_files_success(self):
        """Escanear archivos de la papelera."""
        result = scan_trash_files()
        
        assert isinstance(result, list)
        # Puede estar vacío, pero no debe crashear
    
    def test_scan_trash_files_returns_list(self):
        """Validar que siempre retorna lista."""
        result = scan_trash_files()
        
        assert isinstance(result, list)


class TestScanFiles:
    """Tests para scan_files (función genérica)."""
    
    def test_scan_files_normal_folder(self, temp_folder_with_files):
        """Escanear carpeta normal."""
        result = scan_files(temp_folder_with_files)
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_scan_files_desktop_focus(self):
        """Escanear Desktop Focus."""
        from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH
        
        result = scan_files(DESKTOP_FOCUS_PATH)
        
        assert isinstance(result, list)
    
    def test_scan_files_trash_focus(self):
        """Escanear Trash Focus."""
        from app.services.trash_storage import TRASH_FOCUS_PATH
        
        result = scan_files(TRASH_FOCUS_PATH)
        
        assert isinstance(result, list)
    
    def test_scan_files_empty_path(self):
        """Escanear con path vacío."""
        result = scan_files("")
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_scan_files_nonexistent_path(self):
        """Escanear path inexistente."""
        result = scan_files("/nonexistent/path")
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestErrorHandling:
    """Tests para manejo de errores."""
    
    def test_scan_folder_files_permission_error(self):
        """Manejar error de permisos."""
        # Intentar escanear carpeta protegida
        protected_path = "C:\\Windows\\System32\\config"
        
        result = scan_folder_files(protected_path)
        
        # No debe crashear, debe retornar lista (puede estar vacía)
        assert isinstance(result, list)
    
    def test_scan_folder_files_invalid_path(self):
        """Manejar path inválido."""
        result = scan_folder_files("::invalid::")
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_scan_folder_files_special_characters(self):
        """Escanear carpeta con caracteres especiales."""
        temp_path = tempfile.mkdtemp()
        special_file = os.path.join(temp_path, "test file (1).txt")
        
        try:
            with open(special_file, 'w') as f:
                f.write('content')
            
            result = scan_folder_files(temp_path)
            
            assert isinstance(result, list)
            assert any('test file' in f for f in result)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_path)
            except OSError:
                pass
    
    def test_scan_folder_files_unicode(self):
        """Escanear carpeta con caracteres Unicode."""
        temp_path = tempfile.mkdtemp()
        unicode_file = os.path.join(temp_path, "测试_тест.txt")
        
        try:
            with open(unicode_file, 'w') as f:
                f.write('content')
            
            result = scan_folder_files(temp_path)
            
            assert isinstance(result, list)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_path)
            except OSError:
                pass
    
    def test_scan_folder_files_nested_folders(self):
        """Escanear carpeta con subcarpetas anidadas."""
        temp_path = tempfile.mkdtemp()
        nested1 = os.path.join(temp_path, "level1")
        nested2 = os.path.join(nested1, "level2")
        
        try:
            os.makedirs(nested2)
            test_file = os.path.join(nested2, "test.txt")
            with open(test_file, 'w') as f:
                f.write('content')
            
            result = scan_folder_files(temp_path)
            
            assert isinstance(result, list)
            # Debe incluir subcarpetas
            assert any('level1' in f for f in result)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_path)
            except OSError:
                pass

