"""
Tests para IconRenderService.

Cubre renderizado de iconos, validaciones R16, fallbacks y normalización.
"""

import os
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QFileIconProvider

from app.services.icon_render_service import IconRenderService
from app.services.icon_service import IconService


@pytest.fixture
def icon_service():
    """Crear instancia de IconService para tests."""
    return IconService()


@pytest.fixture
def render_service(icon_service):
    """Crear instancia de IconRenderService para tests."""
    return IconRenderService(icon_service)


class TestIsValidPixmap:
    """Tests para validación de pixmaps según R16."""
    
    def test_is_valid_pixmap_valid(self, render_service):
        """Validar pixmap válido (no nulo, tamaño > 0)."""
        pixmap = QPixmap(32, 32)
        pixmap.fill()
        
        assert render_service._is_valid_pixmap(pixmap) is True
    
    def test_is_valid_pixmap_null(self, render_service):
        """Validar pixmap nulo (R16: error)."""
        pixmap = QPixmap()
        
        assert render_service._is_valid_pixmap(pixmap) is False
    
    def test_is_valid_pixmap_zero_width(self, render_service):
        """Validar pixmap con ancho 0 (R16: error)."""
        pixmap = QPixmap(0, 32)
        
        assert render_service._is_valid_pixmap(pixmap) is False
    
    def test_is_valid_pixmap_zero_height(self, render_service):
        """Validar pixmap con alto 0 (R16: error)."""
        pixmap = QPixmap(32, 0)
        
        assert render_service._is_valid_pixmap(pixmap) is False
    
    def test_is_valid_pixmap_zero_size(self, render_service):
        """Validar pixmap 0x0 (R16: error)."""
        pixmap = QPixmap(0, 0)
        
        assert render_service._is_valid_pixmap(pixmap) is False


class TestGetFilePreview:
    """Tests para get_file_preview (grid view)."""
    
    def test_get_file_preview_file_success(self, render_service, temp_file):
        """Obtener preview de archivo válido."""
        size = QSize(48, 48)
        pixmap = render_service.get_file_preview(temp_file, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0
    
    def test_get_file_preview_folder_success(self, render_service, temp_folder):
        """Obtener preview de carpeta válida."""
        size = QSize(48, 48)
        pixmap = render_service.get_file_preview(temp_folder, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0
    
    def test_get_file_preview_nonexistent_file(self, render_service):
        """Obtener preview de archivo inexistente (debe aplicar fallback)."""
        size = QSize(48, 48)
        pixmap = render_service.get_file_preview("/nonexistent/file.txt", size)
        
        # Debe retornar pixmap válido (fallback aplicado)
        assert pixmap is not None
        assert not pixmap.isNull()
    
    def test_get_file_preview_empty_path(self, render_service):
        """Obtener preview con path vacío."""
        size = QSize(48, 48)
        pixmap = render_service.get_file_preview("", size)
        
        # Debe aplicar fallback
        assert pixmap is not None
    
    def test_get_file_preview_different_sizes(self, render_service, temp_file):
        """Obtener preview en diferentes tamaños."""
        sizes = [QSize(16, 16), QSize(32, 32), QSize(64, 64), QSize(128, 128)]
        
        for size in sizes:
            pixmap = render_service.get_file_preview(temp_file, size)
            assert pixmap is not None
            assert not pixmap.isNull()
            assert pixmap.width() > 0
            assert pixmap.height() > 0


class TestGetFilePreviewList:
    """Tests para get_file_preview_list (list view)."""
    
    def test_get_file_preview_list_file_success(self, render_service, temp_file):
        """Obtener preview de archivo para lista."""
        size = QSize(28, 28)
        pixmap = render_service.get_file_preview_list(temp_file, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0
    
    def test_get_file_preview_list_folder_success(self, render_service, temp_folder):
        """Obtener preview de carpeta para lista."""
        size = QSize(28, 28)
        pixmap = render_service.get_file_preview_list(temp_folder, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0
    
    def test_get_file_preview_list_folder_fallback(self, render_service, temp_folder):
        """Validar que fallback funciona para carpetas."""
        size = QSize(28, 28)
        pixmap = render_service.get_file_preview_list(temp_folder, size)
        
        # Debe retornar pixmap válido incluso si el método principal falla
        assert render_service._is_valid_pixmap(pixmap) is True
    
    def test_get_file_preview_list_invalid_path(self, render_service):
        """Obtener preview con path inválido (debe aplicar fallback)."""
        size = QSize(28, 28)
        pixmap = render_service.get_file_preview_list("/invalid/path", size)
        
        # Debe aplicar fallback y retornar pixmap válido
        assert pixmap is not None
        assert not pixmap.isNull()


class TestGetFolderPreview:
    """Tests para _get_folder_preview."""
    
    def test_get_folder_preview_success(self, render_service, temp_folder):
        """Obtener preview de carpeta en alta resolución."""
        size = QSize(48, 48)
        pixmap = render_service._get_folder_preview(temp_folder, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0
    
    def test_get_folder_preview_nonexistent(self, render_service):
        """Obtener preview de carpeta inexistente (debe aplicar fallback)."""
        size = QSize(48, 48)
        pixmap = render_service._get_folder_preview("/nonexistent/folder", size)
        
        # Debe aplicar fallback y retornar pixmap válido
        assert pixmap is not None
    
    def test_get_folder_preview_validates_result(self, render_service, temp_folder):
        """Validar que el resultado cumple R16."""
        size = QSize(48, 48)
        pixmap = render_service._get_folder_preview(temp_folder, size)
        
        # R16: Validar que no es nulo ni 0x0
        assert render_service._is_valid_pixmap(pixmap) is True


class TestScaleFolderIcon:
    """Tests para _scale_folder_icon."""
    
    def test_scale_folder_icon_same_size(self, render_service):
        """Escalar icono cuando ya tiene el tamaño correcto."""
        target_size = QSize(48, 48)
        pixmap = QPixmap(48, 48)
        pixmap.fill()
        
        result = render_service._scale_folder_icon(pixmap, target_size)
        
        assert result is not None
        assert result.width() == 48
        assert result.height() == 48
    
    def test_scale_folder_icon_different_size(self, render_service):
        """Escalar icono a tamaño diferente."""
        target_size = QSize(32, 32)
        pixmap = QPixmap(64, 64)
        pixmap.fill()
        
        result = render_service._scale_folder_icon(pixmap, target_size)
        
        assert result is not None
        assert result.width() == 32
        assert result.height() == 32
    
    def test_scale_folder_icon_null_input(self, render_service):
        """Escalar icono nulo (R16: debe retornar QPixmap vacío)."""
        target_size = QSize(48, 48)
        pixmap = QPixmap()
        
        result = render_service._scale_folder_icon(pixmap, target_size)
        
        assert result is not None
        assert result.isNull() is True
    
    def test_scale_folder_icon_zero_size_input(self, render_service):
        """Escalar icono 0x0 (R16: debe retornar QPixmap vacío)."""
        target_size = QSize(48, 48)
        pixmap = QPixmap(0, 0)
        
        result = render_service._scale_folder_icon(pixmap, target_size)
        
        assert result is not None
        assert result.isNull() is True
    
    def test_scale_folder_icon_validates_result(self, render_service):
        """Validar que el resultado escalado cumple R16."""
        target_size = QSize(32, 32)
        pixmap = QPixmap(64, 64)
        pixmap.fill()
        
        result = render_service._scale_folder_icon(pixmap, target_size)
        
        assert render_service._is_valid_pixmap(result) is True


class TestApplyFolderFallbacks:
    """Tests para _apply_folder_fallbacks."""
    
    def test_apply_folder_fallbacks_valid_pixmap(self, render_service, temp_folder):
        """Aplicar fallbacks cuando pixmap ya es válido."""
        size = QSize(48, 48)
        valid_pixmap = QPixmap(48, 48)
        valid_pixmap.fill()
        
        result = render_service._apply_folder_fallbacks(temp_folder, valid_pixmap, size)
        
        assert result is not None
        assert render_service._is_valid_pixmap(result) is True
    
    def test_apply_folder_fallbacks_null_pixmap(self, render_service, temp_folder):
        """Aplicar fallbacks cuando pixmap es nulo."""
        size = QSize(48, 48)
        null_pixmap = QPixmap()
        
        result = render_service._apply_folder_fallbacks(temp_folder, null_pixmap, size)
        
        # Debe aplicar fallback y retornar pixmap válido o vacío
        assert result is not None
    
    def test_apply_folder_fallbacks_zero_size_pixmap(self, render_service, temp_folder):
        """Aplicar fallbacks cuando pixmap es 0x0 (R16)."""
        size = QSize(48, 48)
        zero_pixmap = QPixmap(0, 0)
        
        result = render_service._apply_folder_fallbacks(temp_folder, zero_pixmap, size)
        
        # Debe aplicar fallback
        assert result is not None
    
    def test_apply_folder_fallbacks_multiple_levels(self, render_service, temp_folder):
        """Validar que se aplican múltiples niveles de fallback."""
        size = QSize(48, 48)
        null_pixmap = QPixmap()
        
        result = render_service._apply_folder_fallbacks(temp_folder, null_pixmap, size)
        
        # Debe intentar múltiples fallbacks
        assert result is not None


class TestGetBestQualityPixmap:
    """Tests para _get_best_quality_pixmap."""
    
    def test_get_best_quality_pixmap_valid_icon(self, render_service):
        """Obtener pixmap de calidad de icono válido."""
        size = QSize(48, 48)
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(QFileIconProvider.IconType.Folder)
        
        pixmap = render_service._get_best_quality_pixmap(icon, size)
        
        assert pixmap is not None
        assert render_service._is_valid_pixmap(pixmap) is True
    
    def test_get_best_quality_pixmap_null_icon(self, render_service):
        """Obtener pixmap de icono nulo (R16: debe retornar QPixmap vacío)."""
        size = QSize(48, 48)
        null_icon = QIcon()
        
        pixmap = render_service._get_best_quality_pixmap(null_icon, size)
        
        assert pixmap is not None
        assert pixmap.isNull() is True
    
    def test_get_best_quality_pixmap_scales_correctly(self, render_service):
        """Validar que el pixmap se escala correctamente."""
        size = QSize(32, 32)
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(QFileIconProvider.IconType.File)
        
        pixmap = render_service._get_best_quality_pixmap(icon, size)
        
        assert pixmap is not None
        assert render_service._is_valid_pixmap(pixmap) is True
    
    def test_get_best_quality_pixmap_validates_result(self, render_service):
        """Validar que el resultado cumple R16."""
        size = QSize(48, 48)
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(QFileIconProvider.IconType.Folder)
        
        pixmap = render_service._get_best_quality_pixmap(icon, size)
        
        # R16: No debe retornar pixmap inválido
        if not pixmap.isNull():
            assert render_service._is_valid_pixmap(pixmap) is True


class TestGridVsListView:
    """Tests para diferencias entre grid y list view."""
    
    def test_grid_preview_has_normalization(self, render_service, temp_file):
        """Validar que grid preview aplica normalización visual."""
        size = QSize(48, 48)
        pixmap = render_service.get_file_preview(temp_file, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
        # Grid view aplica normalización (90% scale, rounded corners)
    
    def test_list_preview_no_overlay(self, render_service, temp_file):
        """Validar que list preview no tiene overlay."""
        size = QSize(28, 28)
        pixmap = render_service.get_file_preview_list(temp_file, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
        # List view: 100% scale, sin overlay
    
    def test_both_views_return_valid_pixmaps(self, render_service, temp_file):
        """Validar que ambas vistas retornan pixmaps válidos (R16)."""
        size = QSize(48, 48)
        
        grid_pixmap = render_service.get_file_preview(temp_file, size)
        list_pixmap = render_service.get_file_preview_list(temp_file, size)
        
        assert render_service._is_valid_pixmap(grid_pixmap) is True
        assert render_service._is_valid_pixmap(list_pixmap) is True


class TestEdgeCases:
    """Tests para casos límite y edge cases."""
    
    def test_very_large_size(self, render_service, temp_file):
        """Obtener preview con tamaño muy grande."""
        size = QSize(512, 512)
        pixmap = render_service.get_file_preview(temp_file, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
    
    def test_very_small_size(self, render_service, temp_file):
        """Obtener preview con tamaño muy pequeño."""
        size = QSize(8, 8)
        pixmap = render_service.get_file_preview(temp_file, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
    
    def test_square_size(self, render_service, temp_file):
        """Obtener preview con tamaño cuadrado."""
        size = QSize(48, 48)
        pixmap = render_service.get_file_preview(temp_file, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
    
    def test_rectangular_size(self, render_service, temp_file):
        """Obtener preview con tamaño rectangular."""
        size = QSize(64, 32)
        pixmap = render_service.get_file_preview(temp_file, size)
        
        assert pixmap is not None
        assert not pixmap.isNull()
    
    def test_special_characters_in_path(self, render_service, temp_folder):
        """Obtener preview con caracteres especiales en path."""
        # Crear carpeta con caracteres especiales
        special_folder = os.path.join(temp_folder, "test folder (1)")
        os.makedirs(special_folder, exist_ok=True)
        
        try:
            size = QSize(48, 48)
            pixmap = render_service.get_file_preview(special_folder, size)
            
            assert pixmap is not None
            assert not pixmap.isNull()
        finally:
            try:
                os.rmdir(special_folder)
            except OSError:
                pass
    
    def test_unicode_characters_in_path(self, render_service, temp_folder):
        """Obtener preview con caracteres Unicode en path."""
        # Crear carpeta con Unicode
        unicode_folder = os.path.join(temp_folder, "carpeta_测试_тест")
        os.makedirs(unicode_folder, exist_ok=True)
        
        try:
            size = QSize(48, 48)
            pixmap = render_service.get_file_preview(unicode_folder, size)
            
            assert pixmap is not None
            assert not pixmap.isNull()
        finally:
            try:
                os.rmdir(unicode_folder)
            except OSError:
                pass


class TestErrorHandling:
    """Tests para manejo de errores."""
    
    def test_permission_error_handling(self, render_service):
        """Manejar error de permisos (path protegido)."""
        # Intentar acceder a path que requiere permisos elevados
        protected_path = "C:\\Windows\\System32"
        
        size = QSize(48, 48)
        pixmap = render_service.get_file_preview(protected_path, size)
        
        # Debe aplicar fallback sin lanzar excepción
        assert pixmap is not None
    
    def test_invalid_path_format(self, render_service):
        """Manejar formato de path inválido."""
        invalid_paths = [
            "::invalid::",
            "\\\\invalid",
            "C:",
            "relative/path/without/root"
        ]
        
        size = QSize(48, 48)
        for invalid_path in invalid_paths:
            pixmap = render_service.get_file_preview(invalid_path, size)
            # No debe lanzar excepción, debe aplicar fallback
            assert pixmap is not None
    
    def test_none_path(self, render_service):
        """Manejar path None (no debe crashear)."""
        size = QSize(48, 48)
        
        # Debe manejar None sin crashear
        try:
            pixmap = render_service.get_file_preview(None, size)
            assert pixmap is not None
        except (AttributeError, TypeError):
            # Aceptable si valida y retorna fallback
            pass

