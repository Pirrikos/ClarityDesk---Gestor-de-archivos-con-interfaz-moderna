"""
Tests para FileFilterService.

Cubre filtrado por extensiones, detección de ejecutables e inclusión de carpetas.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.file_filter_service import (
    filter_files_by_extensions,
    filter_folder_files_by_extensions,
    is_executable,
    _filter_raw_folder_files
)


def _create_pe_header():
    """Crear un header PE válido para tests."""
    # MZ signature (DOS header) - bytes 0-1
    mz_header = b'MZ'
    # Padding hasta offset 0x3C (60) donde está el offset al PE header
    dos_stub = b'\x00' * 58  # Bytes 2-59 (58 bytes)
    # Offset al PE header (little-endian, 4 bytes) en offset 0x3C (60)
    pe_offset = 64  # El PE header estará en el byte 64
    pe_offset_bytes = pe_offset.to_bytes(4, 'little')  # Bytes 60-63
    # Padding hasta el PE header (64 - 64 = 0, pero necesitamos llegar a 64)
    # Ya tenemos 2 + 58 + 4 = 64 bytes, así que el PE header va después
    pe_sig = b'PE\x00\x00'  # Bytes 64-67
    
    return mz_header + dos_stub + pe_offset_bytes + pe_sig


@pytest.fixture
def temp_files():
    """Crear archivos temporales de diferentes tipos."""
    temp_dir = tempfile.mkdtemp()
    
    files = {
        'test1.pdf': b'pdf content',
        'test2.docx': b'docx content',
        'test3.txt': b'text content',
        'document.pdf': b'another pdf',
        'script.exe': _create_pe_header(),  # Header PE válido
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


class TestIsExecutable:
    """Tests para is_executable."""
    
    def test_is_executable_pe_file(self, temp_files):
        """Detectar archivo ejecutable PE."""
        file_paths, _ = temp_files
        exe_path = [f for f in file_paths if f.endswith('.exe')][0]
        
        result = is_executable(exe_path)
        
        assert result is True
    
    def test_is_executable_non_pe_file(self, temp_files):
        """No detectar archivo no ejecutable como ejecutable."""
        file_paths, _ = temp_files
        pdf_path = [f for f in file_paths if f.endswith('.pdf')][0]
        
        result = is_executable(pdf_path)
        
        assert result is False
    
    def test_is_executable_nonexistent_file(self):
        """Manejar archivo inexistente."""
        result = is_executable("/nonexistent/file.exe")
        
        assert result is False
    
    def test_is_executable_permission_error(self):
        """Manejar error de permisos."""
        # Intentar con path protegido (puede fallar por permisos)
        protected_path = "C:\\Windows\\System32\\config\\sam"
        result = is_executable(protected_path)
        
        # No debe lanzar excepción
        assert isinstance(result, bool)


class TestFilterFilesByExtensions:
    """Tests para filter_files_by_extensions."""
    
    def test_filter_files_by_extensions_success(self, temp_files):
        """Filtrar archivos por extensiones."""
        file_paths, _ = temp_files
        extensions = {'.pdf', '.docx'}
        
        result = filter_files_by_extensions(file_paths, extensions)
        
        assert isinstance(result, list)
        # Debe incluir PDFs, DOCX y carpetas
        assert any('.pdf' in f for f in result)
        assert any('.docx' in f for f in result)
        assert any('subfolder' in f for f in result)
    
    def test_filter_files_includes_folders(self, temp_files):
        """Validar que siempre incluye carpetas."""
        file_paths, _ = temp_files
        extensions = {'.pdf'}  # Solo PDFs
        
        result = filter_files_by_extensions(file_paths, extensions)
        
        folders = [f for f in result if os.path.isdir(f)]
        assert len(folders) > 0
    
    def test_filter_files_includes_executables(self, temp_files):
        """Validar que incluye ejecutables sin extensión."""
        file_paths, temp_dir = temp_files
        
        # Crear ejecutable sin extensión
        exe_no_ext = os.path.join(temp_dir, 'script')
        with open(exe_no_ext, 'wb') as f:
            f.write(_create_pe_header())
        
        file_paths.append(exe_no_ext)
        extensions = {'.pdf'}  # No incluye ejecutables
        
        result = filter_files_by_extensions(file_paths, extensions)
        
        # Debe incluir ejecutables sin extensión aunque no estén en extensions
        exe_files = [f for f in result if os.path.basename(f) == 'script']
        assert len(exe_files) > 0
    
    def test_filter_files_empty_extensions(self, temp_files):
        """Filtrar con extensiones vacías."""
        file_paths, _ = temp_files
        extensions = set()
        
        result = filter_files_by_extensions(file_paths, extensions)
        
        # Debe incluir solo carpetas y ejecutables
        assert isinstance(result, list)
        folders = [f for f in result if os.path.isdir(f)]
        assert len(folders) > 0
    
    def test_filter_files_empty_list(self):
        """Filtrar lista vacía."""
        extensions = {'.pdf', '.docx'}
        result = filter_files_by_extensions([], extensions)
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestFilterFolderFilesByExtensions:
    """Tests para filter_folder_files_by_extensions."""
    
    def test_filter_folder_files_by_extensions_success(self, temp_files):
        """Filtrar archivos de carpeta por extensiones."""
        _, temp_dir = temp_files
        extensions = {'.pdf', '.docx'}
        
        result = filter_folder_files_by_extensions(temp_dir, extensions)
        
        assert isinstance(result, list)
        assert any('.pdf' in f for f in result)
        assert any('.docx' in f for f in result)
    
    def test_filter_folder_files_empty_folder(self):
        """Filtrar carpeta vacía."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            extensions = {'.pdf'}
            result = filter_folder_files_by_extensions(temp_dir, extensions)
            
            assert isinstance(result, list)
            assert len(result) == 0
        finally:
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass
    
    def test_filter_folder_files_nonexistent_folder(self):
        """Filtrar carpeta inexistente."""
        extensions = {'.pdf'}
        result = filter_folder_files_by_extensions("/nonexistent/folder", extensions)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_filter_folder_files_empty_path(self):
        """Filtrar con path vacío."""
        extensions = {'.pdf'}
        result = filter_folder_files_by_extensions("", extensions)
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestFilterRawFolderFiles:
    """Tests para _filter_raw_folder_files."""
    
    def test_filter_raw_folder_files_success(self, temp_files):
        """Filtrar lista raw de archivos."""
        file_paths, _ = temp_files
        extensions = {'.pdf', '.docx'}
        
        result = _filter_raw_folder_files(file_paths, extensions)
        
        assert isinstance(result, list)
        assert any('.pdf' in f for f in result)
        assert any('.docx' in f for f in result)
    
    def test_filter_raw_folder_files_includes_folders(self, temp_files):
        """Validar que incluye carpetas."""
        file_paths, _ = temp_files
        extensions = {'.pdf'}
        
        result = _filter_raw_folder_files(file_paths, extensions)
        
        folders = [f for f in result if os.path.isdir(f)]
        assert len(folders) > 0
    
    def test_filter_raw_folder_files_permission_error(self):
        """Manejar error de permisos."""
        # Crear lista con path que puede causar error de permisos
        files = ["/nonexistent/file.pdf"]
        extensions = {'.pdf'}
        
        result = _filter_raw_folder_files(files, extensions)
        
        # No debe lanzar excepción
        assert isinstance(result, list)

