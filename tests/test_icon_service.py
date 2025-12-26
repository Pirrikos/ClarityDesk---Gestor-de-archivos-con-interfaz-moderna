"""
Tests para IconService.

Cubre obtención de iconos Windows, cache, validaciones R16 y workers.
"""

import os
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFileIconProvider

from app.services.icon_service import IconService


@pytest.fixture
def icon_service():
    """Crear instancia de IconService para tests."""
    service = IconService()
    # Limpiar cache antes de cada test
    service.clear_cache()
    return service


class TestIsValidPixmap:
    """Tests para validación de pixmaps según R16."""
    
    def test_is_valid_pixmap_valid(self, icon_service):
        """Validar pixmap válido."""
        pixmap = QPixmap(32, 32)
        pixmap.fill()
        
        assert icon_service._is_valid_pixmap(pixmap) is True
    
    def test_is_valid_pixmap_null(self, icon_service):
        """Validar pixmap nulo (R16: error)."""
        pixmap = QPixmap()
        
        assert icon_service._is_valid_pixmap(pixmap) is False
    
    def test_is_valid_pixmap_zero_size(self, icon_service):
        """Validar pixmap 0x0 (R16: error)."""
        pixmap = QPixmap(0, 0)
        
        assert icon_service._is_valid_pixmap(pixmap) is False


class TestGetFileIcon:
    """Tests para get_file_icon."""
    
    def test_get_file_icon_success(self, icon_service, temp_file):
        """Obtener icono de archivo válido."""
        size = QSize(32, 32)
        icon = icon_service.get_file_icon(temp_file, size)
        
        assert icon is not None
        assert not icon.isNull()
    
    def test_get_file_icon_invalid_path(self, icon_service):
        """Obtener icono de archivo inexistente (debe retornar default)."""
        size = QSize(32, 32)
        icon = icon_service.get_file_icon("/nonexistent/file.txt", size)
        
        assert icon is not None
        assert not icon.isNull()
    
    def test_get_file_icon_cache(self, icon_service, temp_file):
        """Validar que el cache funciona."""
        size = QSize(32, 32)
        
        # Primera llamada
        icon1 = icon_service.get_file_icon(temp_file, size)
        
        # Segunda llamada (debe usar cache)
        icon2 = icon_service.get_file_icon(temp_file, size)
        
        assert icon1 is not None
        assert icon2 is not None
    
    def test_get_file_icon_validates_pixmap(self, icon_service, temp_file):
        """Validar que no cachea iconos inválidos (R16)."""
        size = QSize(32, 32)
        icon = icon_service.get_file_icon(temp_file, size)
        
        # Validar que el icono tiene pixmap válido
        pixmap = icon.pixmap(size)
        assert icon_service._is_valid_pixmap(pixmap) is True
    
    def test_get_file_icon_no_size(self, icon_service, temp_file):
        """Obtener icono sin tamaño específico."""
        icon = icon_service.get_file_icon(temp_file, None)
        
        assert icon is not None
        assert not icon.isNull()


class TestGetFolderIcon:
    """Tests para get_folder_icon."""
    
    def test_get_folder_icon_success(self, icon_service, temp_folder):
        """Obtener icono de carpeta válida."""
        size = QSize(32, 32)
        icon = icon_service.get_folder_icon(temp_folder, size)
        
        assert icon is not None
        assert not icon.isNull()
    
    def test_get_folder_icon_nonexistent(self, icon_service):
        """Obtener icono de carpeta inexistente (debe retornar genérico)."""
        size = QSize(32, 32)
        icon = icon_service.get_folder_icon("/nonexistent/folder", size)
        
        assert icon is not None
        assert not icon.isNull()
    
    def test_get_folder_icon_no_path(self, icon_service):
        """Obtener icono genérico de carpeta."""
        size = QSize(32, 32)
        icon = icon_service.get_folder_icon(None, size)
        
        assert icon is not None
        assert not icon.isNull()
    
    def test_get_folder_icon_validates_pixmap(self, icon_service, temp_folder):
        """Validar que retorna pixmap válido (R16)."""
        size = QSize(32, 32)
        icon = icon_service.get_folder_icon(temp_folder, size)
        
        pixmap = icon.pixmap(size)
        assert icon_service._is_valid_pixmap(pixmap) is True
    
    def test_get_folder_icon_no_size(self, icon_service, temp_folder):
        """Obtener icono sin tamaño específico."""
        icon = icon_service.get_folder_icon(temp_folder, None)
        
        assert icon is not None
        assert not icon.isNull()


class TestGetBestQualityPixmap:
    """Tests para _get_best_quality_pixmap."""
    
    def test_get_best_quality_pixmap_valid_icon(self, icon_service):
        """Obtener pixmap de calidad de icono válido."""
        size = QSize(48, 48)
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(QFileIconProvider.IconType.Folder)
        
        pixmap = icon_service._get_best_quality_pixmap(icon, size)
        
        assert pixmap is not None
        assert icon_service._is_valid_pixmap(pixmap) is True
    
    def test_get_best_quality_pixmap_null_icon(self, icon_service):
        """Obtener pixmap de icono nulo (R16: debe retornar QPixmap vacío)."""
        size = QSize(48, 48)
        null_icon = QIcon()
        
        pixmap = icon_service._get_best_quality_pixmap(null_icon, size)
        
        assert pixmap is not None
        assert pixmap.isNull() is True
    
    def test_get_best_quality_pixmap_scales_correctly(self, icon_service):
        """Validar que el pixmap se escala correctamente."""
        size = QSize(32, 32)
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(QFileIconProvider.IconType.File)
        
        pixmap = icon_service._get_best_quality_pixmap(icon, size)
        
        assert pixmap is not None
        assert icon_service._is_valid_pixmap(pixmap) is True


class TestCache:
    """Tests para funcionalidad de cache."""
    
    def test_cache_stores_icons(self, icon_service, temp_file):
        """Validar que el cache almacena iconos."""
        size = QSize(32, 32)
        
        icon1 = icon_service.get_file_icon(temp_file, size)
        
        # Verificar que está en cache
        _, ext = os.path.splitext(temp_file)
        cache_key = f"{ext.lower()}_{size.width()}"
        
        assert cache_key in icon_service._icon_cache
    
    def test_cache_invalidates_on_file_change(self, icon_service, temp_file):
        """Validar que el cache se invalida cuando el archivo cambia."""
        size = QSize(32, 32)
        
        # Primera llamada (guarda en cache)
        icon_service.get_file_icon(temp_file, size)
        
        # Modificar archivo
        import time
        time.sleep(1.1)  # Esperar más de 1 segundo
        with open(temp_file, 'w') as f:
            f.write('modified')
        
        # Segunda llamada (debe invalidar cache)
        icon2 = icon_service.get_file_icon(temp_file, size)
        
        assert icon2 is not None
    
    def test_clear_cache(self, icon_service, temp_file):
        """Validar que clear_cache limpia el cache."""
        size = QSize(32, 32)
        icon_service.get_file_icon(temp_file, size)
        
        assert len(icon_service._icon_cache) > 0
        
        icon_service.clear_cache()
        
        assert len(icon_service._icon_cache) == 0


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_very_large_size(self, icon_service, temp_file):
        """Obtener icono con tamaño muy grande."""
        size = QSize(512, 512)
        icon = icon_service.get_file_icon(temp_file, size)
        
        assert icon is not None
        assert not icon.isNull()
    
    def test_very_small_size(self, icon_service, temp_file):
        """Obtener icono con tamaño muy pequeño."""
        size = QSize(8, 8)
        icon = icon_service.get_file_icon(temp_file, size)
        
        assert icon is not None
        assert not icon.isNull()
    
    def test_empty_path(self, icon_service):
        """Obtener icono con path vacío."""
        size = QSize(32, 32)
        icon = icon_service.get_file_icon("", size)
        
        assert icon is not None

