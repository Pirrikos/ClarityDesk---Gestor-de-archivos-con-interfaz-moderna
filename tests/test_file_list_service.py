"""
Tests para FileListService.

Cubre listado de archivos, filtrado por extensión, stacks y Desktop/Trash Focus.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.models.file_stack import FileStack
from app.services.file_list_service import get_files, _natural_sort_key


@pytest.fixture
def temp_folder_with_files():
    """Crear carpeta temporal con archivos de prueba."""
    temp_path = tempfile.mkdtemp()
    
    # Crear archivos de diferentes tipos
    files = {
        'test1.pdf': b'pdf content',
        'test2.docx': b'docx content',
        'test3.txt': b'text content',
        'document.pdf': b'another pdf',
    }
    
    for filename, content in files.items():
        file_path = os.path.join(temp_path, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
    
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


class TestGetFiles:
    """Tests para get_files."""
    
    def test_get_files_success(self, temp_folder_with_files):
        """Obtener lista de archivos de carpeta válida."""
        extensions = {'.pdf', '.docx', '.txt'}
        result = get_files(temp_folder_with_files, extensions, use_stacks=False)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Debe incluir archivos y carpetas
        assert any('.pdf' in f for f in result)
        assert any('subfolder' in f for f in result)
    
    def test_get_files_empty_folder(self, empty_folder):
        """Obtener archivos de carpeta vacía."""
        extensions = {'.pdf', '.docx'}
        result = get_files(empty_folder, extensions, use_stacks=False)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_files_with_extensions(self, temp_folder_with_files):
        """Filtrar archivos por extensiones."""
        extensions = {'.pdf'}
        result = get_files(temp_folder_with_files, extensions, use_stacks=False)
        
        # Solo debe incluir PDFs y carpetas
        files_only = [f for f in result if os.path.isfile(f)]
        assert all('.pdf' in f for f in files_only)
    
    def test_get_files_includes_folders(self, temp_folder_with_files):
        """Validar que siempre incluye carpetas."""
        extensions = {'.pdf'}
        result = get_files(temp_folder_with_files, extensions, use_stacks=False)
        
        folders = [f for f in result if os.path.isdir(f)]
        assert len(folders) > 0
    
    def test_get_files_with_stacks(self, temp_folder_with_files):
        """Obtener archivos agrupados en stacks."""
        extensions = {'.pdf', '.docx', '.txt'}
        result = get_files(temp_folder_with_files, extensions, use_stacks=True)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Debe contener FileStack objects
        assert any(isinstance(item, FileStack) for item in result)
    
    def test_get_files_empty_path(self):
        """Obtener archivos con path vacío."""
        extensions = {'.pdf'}
        result = get_files("", extensions, use_stacks=False)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_files_nonexistent_folder(self):
        """Obtener archivos de carpeta inexistente."""
        extensions = {'.pdf'}
        result = get_files("/nonexistent/folder", extensions, use_stacks=False)
        
        # Debe retornar lista vacía sin crashear
        assert isinstance(result, list)


class TestNaturalSortKey:
    """Tests para _natural_sort_key."""
    
    def test_natural_sort_key_numbers(self):
        """Validar ordenamiento natural con números."""
        paths = [
            "/test10.txt",
            "/test2.txt",
            "/test1.txt",
        ]
        
        sorted_paths = sorted(paths, key=_natural_sort_key)
        
        assert sorted_paths[0] == "/test1.txt"
        assert sorted_paths[1] == "/test2.txt"
        assert sorted_paths[2] == "/test10.txt"
    
    def test_natural_sort_key_text(self):
        """Validar ordenamiento natural con texto."""
        paths = [
            "/zebra.txt",
            "/apple.txt",
            "/banana.txt",
        ]
        
        sorted_paths = sorted(paths, key=_natural_sort_key)
        
        assert sorted_paths[0] == "/apple.txt"
        assert sorted_paths[1] == "/banana.txt"
        assert sorted_paths[2] == "/zebra.txt"
    
    def test_natural_sort_key_mixed(self):
        """Validar ordenamiento natural con texto y números."""
        paths = [
            "/file10.txt",
            "/file2.txt",
            "/file1.txt",
            "/afile.txt",
        ]
        
        sorted_paths = sorted(paths, key=_natural_sort_key)
        
        assert sorted_paths[0] == "/afile.txt"
        assert sorted_paths[1] == "/file1.txt"
        assert sorted_paths[2] == "/file2.txt"
        assert sorted_paths[3] == "/file10.txt"
    
    def test_natural_sort_key_case_insensitive(self):
        """Validar que es case-insensitive."""
        paths = [
            "/Zebra.txt",
            "/apple.txt",
            "/Banana.txt",
        ]
        
        sorted_paths = sorted(paths, key=_natural_sort_key)
        
        assert sorted_paths[0] == "/apple.txt"
        assert sorted_paths[1] == "/Banana.txt"
        assert sorted_paths[2] == "/Zebra.txt"


class TestDesktopFocus:
    """Tests para Desktop Focus."""
    
    def test_get_files_desktop_focus(self):
        """Obtener archivos de Desktop Focus."""
        from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH
        
        extensions = {'.pdf', '.docx', '.txt'}
        result = get_files(DESKTOP_FOCUS_PATH, extensions, use_stacks=False)
        
        assert isinstance(result, list)
        # Puede estar vacío si no hay archivos, pero no debe crashear
    
    def test_get_files_desktop_focus_with_stacks(self):
        """Obtener archivos de Desktop Focus con stacks."""
        from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH
        
        extensions = {'.pdf', '.docx'}
        result = get_files(DESKTOP_FOCUS_PATH, extensions, use_stacks=True)
        
        assert isinstance(result, list)


class TestTrashFocus:
    """Tests para Trash Focus."""
    
    def test_get_files_trash_focus(self):
        """Obtener archivos de Trash Focus."""
        from app.services.trash_storage import TRASH_FOCUS_PATH
        
        extensions = {'.pdf', '.docx'}
        result = get_files(TRASH_FOCUS_PATH, extensions, use_stacks=False)
        
        assert isinstance(result, list)
        # Puede estar vacío, pero no debe crashear
    
    def test_get_files_trash_focus_with_stacks(self):
        """Obtener archivos de Trash Focus con stacks."""
        from app.services.trash_storage import TRASH_FOCUS_PATH
        
        extensions = {'.pdf'}
        result = get_files(TRASH_FOCUS_PATH, extensions, use_stacks=True)
        
        assert isinstance(result, list)


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_get_files_empty_extensions(self, temp_folder_with_files):
        """Obtener archivos con extensiones vacías."""
        extensions = set()
        result = get_files(temp_folder_with_files, extensions, use_stacks=False)
        
        # Debe retornar solo carpetas (las extensiones vacías no matchean archivos)
        assert isinstance(result, list)
    
    def test_get_files_special_characters(self):
        """Obtener archivos con caracteres especiales en path."""
        temp_path = tempfile.mkdtemp()
        special_file = os.path.join(temp_path, "test file (1).pdf")
        
        try:
            with open(special_file, 'wb') as f:
                f.write(b'content')
            
            extensions = {'.pdf'}
            result = get_files(temp_path, extensions, use_stacks=False)
            
            assert isinstance(result, list)
            assert any('test file' in f for f in result)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_path)
            except OSError:
                pass
    
    def test_get_files_unicode_path(self):
        """Obtener archivos con caracteres Unicode en path."""
        temp_path = tempfile.mkdtemp()
        unicode_file = os.path.join(temp_path, "测试_тест.pdf")
        
        try:
            with open(unicode_file, 'wb') as f:
                f.write(b'content')
            
            extensions = {'.pdf'}
            result = get_files(temp_path, extensions, use_stacks=False)
            
            assert isinstance(result, list)
        finally:
            import shutil
            try:
                shutil.rmtree(temp_path)
            except OSError:
                pass

