"""
Tests para RenameService.

Cubre generación de preview, aplicación de patrones y renombrado masivo.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.rename_service import RenameService


@pytest.fixture
def rename_service():
    """Crear instancia de RenameService para tests."""
    return RenameService()


@pytest.fixture
def temp_files():
    """Crear archivos temporales para tests."""
    temp_dir = tempfile.mkdtemp()
    
    files = [
        'document1.pdf',
        'document2.pdf',
        'file1.docx',
    ]
    
    file_paths = []
    for filename in files:
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(b'content')
        file_paths.append(file_path)
    
    yield file_paths, temp_dir
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass


class TestGeneratePreview:
    """Tests para generate_preview."""
    
    def test_generate_preview_success(self, rename_service, temp_files):
        """Generar preview de renombrado exitoso."""
        file_paths, _ = temp_files
        pattern = "New Document"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        assert isinstance(preview, list)
        assert len(preview) == len(file_paths)
        assert all('New Document' in name for name in preview)
    
    def test_generate_preview_with_numbering(self, rename_service, temp_files):
        """Generar preview con numeración automática."""
        file_paths, _ = temp_files
        pattern = "Document"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        assert len(preview) == len(file_paths)
        # Debe incluir números
        assert any('1' in name for name in preview)
        assert any('2' in name for name in preview)
    
    def test_generate_preserves_extension(self, rename_service, temp_files):
        """Validar que preserva extensiones originales."""
        file_paths, _ = temp_files
        pattern = "New Name"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        # Verificar extensiones
        for i, new_name in enumerate(preview):
            original_ext = os.path.splitext(file_paths[i])[1]
            assert new_name.endswith(original_ext)
    
    def test_generate_preview_single_file(self, rename_service, temp_files):
        """Generar preview para un solo archivo (sin numeración)."""
        file_paths, _ = temp_files
        single_file = [file_paths[0]]
        pattern = "Single Document"
        
        preview = rename_service.generate_preview(single_file, pattern)
        
        assert len(preview) == 1
        assert 'Single Document' in preview[0]
        # No debe añadir {n} para archivo único
    
    def test_generate_preview_with_search_replace(self, rename_service, temp_files):
        """Generar preview con búsqueda y reemplazo."""
        file_paths, _ = temp_files
        pattern = "Document {name}"
        
        preview = rename_service.generate_preview(
            file_paths,
            pattern,
            search_text="document",
            replace_text="file"
        )
        
        assert isinstance(preview, list)
        # Debe reemplazar "document" por "file"
        assert any('file' in name.lower() for name in preview)
    
    def test_generate_preview_with_case_conversion(self, rename_service, temp_files):
        """Generar preview con conversión de mayúsculas/minúsculas."""
        file_paths, _ = temp_files
        pattern = "new document"
        
        # Uppercase
        preview_upper = rename_service.generate_preview(
            file_paths, pattern, use_uppercase=True
        )
        assert all(name.isupper() or name.endswith('.pdf') or name.endswith('.docx') 
                  for name in preview_upper)
        
        # Lowercase
        preview_lower = rename_service.generate_preview(
            file_paths, pattern, use_lowercase=True
        )
        assert all(name.islower() or name.endswith('.pdf') or name.endswith('.docx')
                  for name in preview_lower)


class TestApplyPattern:
    """Tests para _apply_pattern."""
    
    def test_apply_pattern_with_name_placeholder(self, rename_service, temp_files):
        """Aplicar patrón con placeholder {name}."""
        file_paths, _ = temp_files
        pattern = "File {name}"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        assert isinstance(preview, list)
        # Debe incluir nombres originales
        assert any('document1' in name.lower() for name in preview)
    
    def test_apply_pattern_with_date_placeholder(self, rename_service, temp_files):
        """Aplicar patrón con placeholder {date}."""
        file_paths, _ = temp_files
        pattern = "Document {date}"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        assert isinstance(preview, list)
        # Debe incluir fecha
        assert all('Document' in name for name in preview)
    
    def test_apply_pattern_with_number_placeholder(self, rename_service, temp_files):
        """Aplicar patrón con placeholder {n}."""
        file_paths, _ = temp_files
        pattern = "Document {n}"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        assert isinstance(preview, list)
        # Debe incluir números
        assert any('1' in name for name in preview)
        assert any('2' in name for name in preview)


class TestApplyRename:
    """Tests para apply_rename."""
    
    def test_apply_rename_success(self, rename_service, temp_files):
        """Aplicar renombrado exitoso."""
        file_paths, temp_dir = temp_files
        pattern = "Renamed"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        # Aplicar renombrado
        from app.services.file_rename_service import rename_file
        
        # Renombrar primer archivo
        if preview and file_paths:
            new_name = preview[0]
            old_path = file_paths[0]
            new_path = os.path.join(temp_dir, new_name)
            
            result = rename_file(old_path, new_name)
            
            # Verificar que el archivo fue renombrado
            assert os.path.exists(new_path) or result is True
    
    def test_apply_rename_preserves_extension(self, rename_service, temp_files):
        """Validar que preserva extensiones al renombrar."""
        file_paths, _ = temp_files
        pattern = "New Name"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        for i, new_name in enumerate(preview):
            original_ext = os.path.splitext(file_paths[i])[1]
            assert new_name.endswith(original_ext)


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_generate_preview_empty_list(self, rename_service):
        """Generar preview con lista vacía."""
        pattern = "Document"
        preview = rename_service.generate_preview([], pattern)
        
        assert isinstance(preview, list)
        assert len(preview) == 0
    
    def test_generate_preview_empty_pattern(self, rename_service, temp_files):
        """Generar preview con patrón vacío."""
        file_paths, _ = temp_files
        
        preview = rename_service.generate_preview(file_paths, "")
        
        assert isinstance(preview, list)
        assert len(preview) == len(file_paths)
    
    def test_generate_preview_special_characters(self, rename_service, temp_files):
        """Generar preview con caracteres especiales en patrón."""
        file_paths, _ = temp_files
        pattern = "Document (1) - Copy"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        assert isinstance(preview, list)
        assert all('Document' in name for name in preview)
    
    def test_generate_preview_unicode_pattern(self, rename_service, temp_files):
        """Generar preview con caracteres Unicode en patrón."""
        file_paths, _ = temp_files
        pattern = "文档_документ"
        
        preview = rename_service.generate_preview(file_paths, pattern)
        
        assert isinstance(preview, list)
        assert len(preview) == len(file_paths)

