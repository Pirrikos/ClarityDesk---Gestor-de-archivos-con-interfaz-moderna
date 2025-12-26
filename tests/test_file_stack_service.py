"""
Tests para FileStackService.

Cubre agrupación de archivos en stacks por familia/tipo.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.models.file_stack import FileStack
from app.services.file_stack_service import (
    create_file_stacks,
    get_file_family,
    _natural_sort_key
)


@pytest.fixture
def temp_files():
    """Crear archivos temporales de diferentes tipos."""
    temp_dir = tempfile.mkdtemp()
    
    files = {
        'document1.pdf': b'pdf content',
        'document2.pdf': b'another pdf',
        'file1.docx': b'docx content',
        'file2.txt': b'text content',
        'image1.jpg': b'image content',
        'image2.png': b'png content',
    }
    
    file_paths = []
    for filename, content in files.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        file_paths.append(file_path)
    
    # Crear subcarpeta
    subfolder = os.path.join(temp_dir, 'subfolder')
    os.makedirs(subfolder)
    file_paths.append(subfolder)
    
    yield file_paths, temp_dir
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass


def is_executable(file_path: str) -> bool:
    """Función mock para detectar ejecutables."""
    return file_path.endswith('.exe') or file_path.endswith('.bat')


class TestGetFileFamily:
    """Tests para get_file_family."""
    
    def test_get_file_family_pdf(self, temp_files):
        """Obtener familia de archivo PDF."""
        file_paths, _ = temp_files
        pdf_path = [f for f in file_paths if f.endswith('.pdf')][0]
        
        family = get_file_family(pdf_path, is_executable)
        
        assert family == 'pdf'
    
    def test_get_file_family_documents(self, temp_files):
        """Obtener familia de archivos de documentos."""
        file_paths, _ = temp_files
        docx_path = [f for f in file_paths if f.endswith('.docx')][0]
        
        family = get_file_family(docx_path, is_executable)
        
        assert family == 'documents'
    
    def test_get_file_family_images(self, temp_files):
        """Obtener familia de archivos de imágenes."""
        file_paths, _ = temp_files
        jpg_path = [f for f in file_paths if f.endswith('.jpg')][0]
        
        family = get_file_family(jpg_path, is_executable)
        
        assert family == 'images'
    
    def test_get_file_family_folder(self, temp_files):
        """Obtener familia de carpeta."""
        file_paths, _ = temp_files
        folder_path = [f for f in file_paths if os.path.isdir(f)][0]
        
        family = get_file_family(folder_path, is_executable)
        
        assert family == 'folder'
    
    def test_get_file_family_executable(self):
        """Obtener familia de ejecutable."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
        temp_file.write(b'MZ\x90\x00')
        temp_file.close()
        
        try:
            family = get_file_family(temp_file.name, is_executable)
            assert family == 'executables'
        finally:
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass
    
    def test_get_file_family_others(self):
        """Obtener familia 'others' para extensión desconocida."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.unknown')
        temp_file.write(b'content')
        temp_file.close()
        
        try:
            family = get_file_family(temp_file.name, is_executable)
            assert family == 'others'
        finally:
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass


class TestCreateFileStacks:
    """Tests para create_file_stacks."""
    
    def test_create_file_stacks_success(self, temp_files):
        """Crear stacks exitosamente."""
        file_paths, _ = temp_files
        
        stacks = create_file_stacks(file_paths, is_executable)
        
        assert isinstance(stacks, list)
        assert len(stacks) > 0
        assert all(isinstance(stack, FileStack) for stack in stacks)
    
    def test_create_file_stacks_groups_by_family(self, temp_files):
        """Validar que agrupa archivos por familia."""
        file_paths, _ = temp_files
        
        stacks = create_file_stacks(file_paths, is_executable)
        
        # Debe tener stack de PDFs
        pdf_stack = next((s for s in stacks if s.stack_type == 'pdf'), None)
        assert pdf_stack is not None
        assert len(pdf_stack.files) >= 2  # Al menos 2 PDFs
    
    def test_create_file_stacks_includes_folders(self, temp_files):
        """Validar que incluye carpetas en stack."""
        file_paths, _ = temp_files
        
        stacks = create_file_stacks(file_paths, is_executable)
        
        folder_stack = next((s for s in stacks if s.stack_type == 'folder'), None)
        assert folder_stack is not None
        assert len(folder_stack.files) > 0
    
    def test_create_file_stacks_empty_list(self):
        """Crear stacks con lista vacía."""
        stacks = create_file_stacks([], is_executable)
        
        assert isinstance(stacks, list)
        assert len(stacks) == 0
    
    def test_create_file_stacks_ordered_by_family_order(self, temp_files):
        """Validar que stacks están ordenados por FAMILY_ORDER."""
        file_paths, _ = temp_files
        
        stacks = create_file_stacks(file_paths, is_executable)
        
        # Verificar orden: folder debe estar primero
        if stacks:
            assert stacks[0].stack_type == 'folder'
    
    def test_create_file_stacks_sorted_files(self, temp_files):
        """Validar que archivos dentro de cada stack están ordenados."""
        file_paths, _ = temp_files
        
        stacks = create_file_stacks(file_paths, is_executable)
        
        pdf_stack = next((s for s in stacks if s.stack_type == 'pdf'), None)
        if pdf_stack and len(pdf_stack.files) > 1:
            # Verificar orden natural
            files = pdf_stack.files
            assert files == sorted(files, key=_natural_sort_key)


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


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_create_file_stacks_single_file(self):
        """Crear stacks con un solo archivo."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(b'content')
        temp_file.close()
        
        try:
            stacks = create_file_stacks([temp_file.name], is_executable)
            
            assert isinstance(stacks, list)
            assert len(stacks) == 1
            assert stacks[0].stack_type == 'pdf'
        finally:
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass
    
    def test_create_file_stacks_only_folders(self):
        """Crear stacks solo con carpetas."""
        folders = [tempfile.mkdtemp() for _ in range(3)]
        
        try:
            stacks = create_file_stacks(folders, is_executable)
            
            assert isinstance(stacks, list)
            assert len(stacks) == 1
            assert stacks[0].stack_type == 'folder'
            assert len(stacks[0].files) == 3
        finally:
            import shutil
            for folder in folders:
                try:
                    shutil.rmtree(folder)
                except OSError:
                    pass

