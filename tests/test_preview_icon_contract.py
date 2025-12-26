"""
Tests CRÍTICOS de contrato de producto para Preview/Iconos.

Estos tests validan que el sistema nunca devuelve pixmaps inválidos al UI,
aplicando fallbacks cuando sea necesario.

Categoría: CRÍTICO
Regla: Si falla → cambiar código de producción, no el test.
"""

import os
import tempfile

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap

from app.services.icon_render_service import IconRenderService
from app.services.icon_service import IconService


@pytest.fixture
def qapp():
    """Crear QApplication para tests de Qt."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def icon_service(qapp):
    """Crear instancia de IconService para tests."""
    return IconService()


@pytest.fixture
def render_service(icon_service):
    """Crear instancia de IconRenderService para tests."""
    return IconRenderService(icon_service)


@pytest.fixture
def temp_file():
    """Crear archivo temporal para tests."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.unknown') as f:
        f.write(b'test content')
        temp_path = f.name
    
    yield temp_path
    
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except OSError:
        pass


class TestPreviewIconContract:
    """Tests CRÍTICOS que validan contrato de producto de Preview/Iconos."""
    
    def test_always_returns_valid_pixmap_on_failure(
        self,
        render_service: IconRenderService,
        temp_file: str,
        qapp
    ):
        """
        Validar que el sistema nunca devuelve un pixmap inválido al UI.
        
        Contrato de producto (R16):
        - Cuando se solicita un icono o preview de un archivo
        - El sistema nunca debe devolver un pixmap inválido al UI
        - Si la fuente falla o devuelve un pixmap inválido
        - El sistema debe aplicar fallback y retornar un pixmap válido
        - El sistema NO debe crashear
        
        Un pixmap válido según R16 es:
        - No nulo (not None)
        - No isNull()
        - Dimensiones > 0 (width() > 0 and height() > 0)
        
        Este test valida comportamiento observable sin inspeccionar implementación interna.
        Solo usa API pública: IconRenderService.get_file_preview().
        """
        # Paso 1: Configurar estado inicial
        # Usar un archivo con extensión desconocida/no soportada para forzar fallback
        target_size = QSize(96, 96)
        
        # Paso 2: Solicitar preview del archivo
        # Este archivo puede no tener un icono válido en el sistema,
        # forzando al sistema a usar fallbacks
        result_pixmap = render_service.get_file_preview(temp_file, target_size)
        
        # Paso 3: Verificar comportamiento observable del contrato
        # 3a: Verificar que el resultado NO es None
        assert result_pixmap is not None, \
            f"El sistema nunca debe devolver None. " \
            f"Archivo: {temp_file}"
        
        # 3b: Verificar que el pixmap NO es nulo (isNull() == False)
        assert not result_pixmap.isNull(), \
            f"El sistema nunca debe devolver un pixmap nulo (isNull() == True). " \
            f"Archivo: {temp_file}, Pixmap: {result_pixmap}"
        
        # 3c: Verificar que las dimensiones son válidas (> 0)
        assert result_pixmap.width() > 0, \
            f"El pixmap debe tener ancho > 0. " \
            f"Archivo: {temp_file}, Ancho: {result_pixmap.width()}"
        
        assert result_pixmap.height() > 0, \
            f"El pixmap debe tener alto > 0. " \
            f"Archivo: {temp_file}, Alto: {result_pixmap.height()}"
        
        # 3d: Verificar consistencia: múltiples llamadas deben retornar pixmaps válidos
        result_pixmap_2 = render_service.get_file_preview(temp_file, target_size)
        
        assert result_pixmap_2 is not None, \
            f"Llamadas repetidas deben retornar pixmaps válidos. " \
            f"Segunda llamada retornó None"
        
        assert not result_pixmap_2.isNull(), \
            f"Llamadas repetidas deben retornar pixmaps válidos. " \
            f"Segunda llamada retornó pixmap nulo"
        
        assert result_pixmap_2.width() > 0 and result_pixmap_2.height() > 0, \
            f"Llamadas repetidas deben retornar pixmaps con dimensiones válidas. " \
            f"Segunda llamada: {result_pixmap_2.width()}x{result_pixmap_2.height()}"
        
        # Paso 4: Verificar con diferentes tamaños
        # El sistema debe retornar pixmaps válidos independientemente del tamaño solicitado
        test_sizes = [
            QSize(32, 32),
            QSize(64, 64),
            QSize(128, 128),
            QSize(256, 256),
        ]
        
        for size in test_sizes:
            size_pixmap = render_service.get_file_preview(temp_file, size)
            
            assert size_pixmap is not None, \
                f"El sistema debe retornar pixmap válido para tamaño {size.width()}x{size.height()}. " \
                f"Retornó None"
            
            assert not size_pixmap.isNull(), \
                f"El sistema debe retornar pixmap válido para tamaño {size.width()}x{size.height()}. " \
                f"Retornó pixmap nulo"
            
            assert size_pixmap.width() > 0 and size_pixmap.height() > 0, \
                f"El sistema debe retornar pixmap con dimensiones válidas para tamaño {size.width()}x{size.height()}. " \
                f"Obtenido: {size_pixmap.width()}x{size_pixmap.height()}"
        
        # Paso 5: Verificar con archivo inexistente (edge case extremo)
        # El sistema debe manejar archivos inexistentes sin crashear
        non_existent_file = os.path.join(os.path.dirname(temp_file), "nonexistent_file.xyz")
        
        # Verificar que el archivo realmente no existe
        assert not os.path.exists(non_existent_file), \
            f"El archivo de prueba no debe existir. " \
            f"Archivo: {non_existent_file}"
        
        # Solicitar preview de archivo inexistente
        nonexistent_pixmap = render_service.get_file_preview(non_existent_file, target_size)
        
        # El sistema debe retornar un pixmap válido (fallback) incluso para archivos inexistentes
        assert nonexistent_pixmap is not None, \
            f"El sistema debe retornar pixmap válido (fallback) incluso para archivos inexistentes. " \
            f"Archivo: {non_existent_file}, Retornó None"
        
        assert not nonexistent_pixmap.isNull(), \
            f"El sistema debe retornar pixmap válido (fallback) incluso para archivos inexistentes. " \
            f"Archivo: {non_existent_file}, Retornó pixmap nulo"
        
        assert nonexistent_pixmap.width() > 0 and nonexistent_pixmap.height() > 0, \
            f"El sistema debe retornar pixmap con dimensiones válidas incluso para archivos inexistentes. " \
            f"Archivo: {non_existent_file}, Dimensiones: {nonexistent_pixmap.width()}x{nonexistent_pixmap.height()}"

