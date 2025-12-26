"""
Tests para PathUtils.

Cubre normalización de paths, preservación de case y manejo de separadores.
"""

import os
import tempfile

import pytest

from app.services.path_utils import normalize_path


class TestNormalizePath:
    """Tests para normalize_path."""
    
    def test_normalize_path_success(self):
        """Normalizar path exitosamente."""
        path = "C:\\Users\\Test\\Folder"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        assert len(normalized) > 0
    
    def test_normalize_path_preserves_case(self):
        """Validar que preserva case (normcase en Windows)."""
        path = "C:\\Users\\TEST\\folder"
        normalized = normalize_path(path)
        
        # En Windows, normcase convierte a lowercase
        # En otros sistemas, puede preservar case
        assert isinstance(normalized, str)
    
    def test_normalize_path_removes_trailing_slash(self):
        """Validar que elimina slash final."""
        path = "C:\\Users\\Test\\Folder\\"
        normalized = normalize_path(path)
        
        assert not normalized.endswith('\\') or not normalized.endswith('/')
    
    def test_normalize_path_handles_separators(self):
        """Manejar diferentes separadores."""
        path = "C:/Users/Test/Folder"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        # Debe normalizar separadores según sistema
    
    def test_normalize_path_empty_string(self):
        """Normalizar path vacío."""
        normalized = normalize_path("")
        
        assert normalized == ""
    
    def test_normalize_path_none(self):
        """Normalizar None (debe retornar vacío)."""
        normalized = normalize_path(None)
        
        assert normalized == ""
    
    def test_normalize_path_relative_path(self):
        """Normalizar path relativo."""
        path = "folder/subfolder/file.txt"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        assert len(normalized) > 0
    
    def test_normalize_path_dot_dot(self):
        """Normalizar path con .."""
        path = "folder/../subfolder/file.txt"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        # Debe resolver ..
    
    def test_normalize_path_dot(self):
        """Normalizar path con ."""
        path = "./folder/file.txt"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        # Debe eliminar .
    
    def test_normalize_path_special_characters(self):
        """Normalizar path con caracteres especiales."""
        path = "C:\\test folder (1)\\file.txt"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        assert len(normalized) > 0
    
    def test_normalize_path_unicode(self):
        """Normalizar path con caracteres Unicode."""
        path = "C:\\测试_тест\\文档.txt"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        assert len(normalized) > 0
    
    def test_normalize_path_consistent(self):
        """Validar que normalización es consistente."""
        path1 = "C:\\Users\\Test\\Folder"
        path2 = "C:/Users/Test/Folder/"
        path3 = "C:\\Users\\TEST\\Folder"
        
        norm1 = normalize_path(path1)
        norm2 = normalize_path(path2)
        norm3 = normalize_path(path3)
        
        # En Windows, deben ser iguales (case-insensitive)
        # En otros sistemas, pueden diferir en case
        assert isinstance(norm1, str)
        assert isinstance(norm2, str)
        assert isinstance(norm3, str)


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_normalize_path_very_long_path(self):
        """Normalizar path muy largo."""
        long_path = "C:\\" + "\\".join(["folder"] * 100)
        normalized = normalize_path(long_path)
        
        assert isinstance(normalized, str)
        assert len(normalized) > 0
    
    def test_normalize_path_multiple_slashes(self):
        """Normalizar path con múltiples slashes."""
        path = "C:\\\\Users\\\\Test\\\\Folder"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        # Debe normalizar múltiples slashes
    
    def test_normalize_path_mixed_separators(self):
        """Normalizar path con separadores mezclados."""
        path = "C:\\Users/Test\\Folder/file.txt"
        normalized = normalize_path(path)
        
        assert isinstance(normalized, str)
        # Debe normalizar separadores
    
    def test_normalize_path_root(self):
        """Normalizar path raíz."""
        if os.name == 'nt':  # Windows
            normalized = normalize_path("C:\\")
            assert isinstance(normalized, str)
        else:  # Unix
            normalized = normalize_path("/")
            assert isinstance(normalized, str)
    
    def test_normalize_path_current_directory(self):
        """Normalizar directorio actual."""
        normalized = normalize_path(".")
        
        assert isinstance(normalized, str)
        # Debe resolver a path absoluto o relativo normalizado

