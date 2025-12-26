"""
Tests para FileBoxService.

Cubre preparación de archivos, añadir a carpeta existente y manejo de errores.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.file_box_service import FileBoxService


@pytest.fixture
def file_box_service():
    """Crear instancia de FileBoxService."""
    return FileBoxService()


@pytest.fixture
def temp_files():
    """Crear archivos temporales para tests."""
    temp_dir = tempfile.mkdtemp()
    
    files = {
        'test1.txt': b'content 1',
        'test2.pdf': b'pdf content',
        'document.docx': b'docx content',
    }
    
    file_paths = []
    for filename, content in files.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        file_paths.append(file_path)
    
    yield file_paths, temp_dir
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass


class TestPrepareFiles:
    """Tests para prepare_files."""
    
    def test_prepare_files_success(self, file_box_service, temp_files):
        """Preparar archivos exitosamente."""
        file_paths, _ = temp_files
        
        temp_dir = file_box_service.prepare_files(file_paths)
        
        assert temp_dir is not None
        assert os.path.isdir(temp_dir)
        assert len(os.listdir(temp_dir)) == len(file_paths)
        
        # Cleanup
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except OSError:
            pass
    
    def test_prepare_files_empty_list(self, file_box_service):
        """Preparar archivos con lista vacía."""
        temp_dir = file_box_service.prepare_files([])
        
        assert temp_dir is None
    
    def test_prepare_files_nonexistent(self, file_box_service):
        """Preparar archivos inexistentes."""
        temp_dir = file_box_service.prepare_files(["/nonexistent/file.txt"])
        
        assert temp_dir is None
    
    def test_prepare_files_includes_folders(self, file_box_service, temp_folder):
        """Preparar archivos incluyendo carpetas."""
        temp_dir = file_box_service.prepare_files([temp_folder])
        
        assert temp_dir is not None
        assert os.path.isdir(temp_dir)
        
        # Cleanup
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except OSError:
            pass
    
    def test_prepare_files_handles_duplicates(self, file_box_service, temp_files):
        """Manejar archivos duplicados (mismo nombre)."""
        file_paths, _ = temp_files
        
        # Crear archivo con mismo nombre en otra ubicación
        temp_dir2 = tempfile.mkdtemp()
        duplicate_file = os.path.join(temp_dir2, 'test1.txt')
        with open(duplicate_file, 'wb') as f:
            f.write(b'duplicate content')
        
        try:
            all_files = file_paths + [duplicate_file]
            temp_dir = file_box_service.prepare_files(all_files)
            
            assert temp_dir is not None
            # Debe manejar duplicados añadiendo sufijo
            
            # Cleanup
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir2)
            except OSError:
                pass


class TestAddFilesToExistingFolder:
    """Tests para add_files_to_existing_folder."""
    
    def test_add_files_to_existing_folder_success(self, file_box_service, temp_files, temp_folder):
        """Añadir archivos a carpeta existente exitosamente."""
        file_paths, _ = temp_files
        
        count = file_box_service.add_files_to_existing_folder(file_paths, temp_folder)
        
        assert count == len(file_paths)
        assert len(os.listdir(temp_folder)) == len(file_paths)
    
    def test_add_files_to_existing_folder_empty_list(self, file_box_service, temp_folder):
        """Añadir lista vacía de archivos."""
        count = file_box_service.add_files_to_existing_folder([], temp_folder)
        
        assert count == 0
    
    def test_add_files_to_existing_folder_nonexistent_folder(self, file_box_service, temp_files):
        """Añadir archivos a carpeta inexistente."""
        file_paths, _ = temp_files
        
        count = file_box_service.add_files_to_existing_folder(file_paths, "/nonexistent/folder")
        
        assert count == 0
    
    def test_add_files_to_existing_folder_nonexistent_files(self, file_box_service, temp_folder):
        """Añadir archivos inexistentes."""
        count = file_box_service.add_files_to_existing_folder(
            ["/nonexistent/file.txt"],
            temp_folder
        )
        
        assert count == 0
    
    def test_add_files_to_existing_folder_handles_duplicates(self, file_box_service, temp_files, temp_folder):
        """Manejar archivos duplicados al añadir."""
        file_paths, _ = temp_files
        
        # Añadir primera vez
        count1 = file_box_service.add_files_to_existing_folder(file_paths, temp_folder)
        assert count1 == len(file_paths)
        
        # Añadir segunda vez (duplicados)
        count2 = file_box_service.add_files_to_existing_folder(file_paths, temp_folder)
        # Debe manejar duplicados añadiendo sufijo
        assert count2 == len(file_paths)


class TestErrorHandling:
    """Tests para manejo de errores."""
    
    def test_prepare_files_permission_error(self, file_box_service):
        """Manejar error de permisos al preparar archivos."""
        # Intentar con archivo protegido (puede fallar por permisos)
        protected_path = "C:\\Windows\\System32\\config\\sam"
        
        temp_dir = file_box_service.prepare_files([protected_path])
        
        # No debe crashear
        assert temp_dir is None or isinstance(temp_dir, str)
    
    def test_add_files_permission_error(self, file_box_service, temp_folder):
        """Manejar error de permisos al añadir archivos."""
        protected_path = "C:\\Windows\\System32\\config\\sam"
        
        count = file_box_service.add_files_to_existing_folder([protected_path], temp_folder)
        
        assert count == 0


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_prepare_files_special_characters(self, file_box_service):
        """Preparar archivos con caracteres especiales en nombres."""
        temp_dir = tempfile.mkdtemp()
        special_file = os.path.join(temp_dir, "test file (1).txt")
        
        try:
            with open(special_file, 'wb') as f:
                f.write(b'content')
            
            result_dir = file_box_service.prepare_files([special_file])
            
            assert result_dir is not None
            
            # Cleanup
            import shutil
            try:
                shutil.rmtree(result_dir)
            except OSError:
                pass
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
    
    def test_prepare_files_unicode_names(self, file_box_service):
        """Preparar archivos con nombres Unicode."""
        temp_dir = tempfile.mkdtemp()
        unicode_file = os.path.join(temp_dir, "测试_тест.txt")
        
        try:
            with open(unicode_file, 'wb') as f:
                f.write(b'content')
            
            result_dir = file_box_service.prepare_files([unicode_file])
            
            assert result_dir is not None
            
            # Cleanup
            import shutil
            try:
                shutil.rmtree(result_dir)
            except OSError:
                pass
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
    
    def test_prepare_files_large_number(self, file_box_service):
        """Preparar gran número de archivos."""
        temp_dir = tempfile.mkdtemp()
        files = []
        
        try:
            for i in range(10):
                file_path = os.path.join(temp_dir, f"file_{i}.txt")
                with open(file_path, 'wb') as f:
                    f.write(f'content {i}'.encode())
                files.append(file_path)
            
            result_dir = file_box_service.prepare_files(files)
            
            assert result_dir is not None
            assert len(os.listdir(result_dir)) == len(files)
            
            # Cleanup
            import shutil
            try:
                shutil.rmtree(result_dir)
            except OSError:
                pass
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass

