"""
Test defensivo T2 — Preview (iconos / PDF / imágenes)

Objetivo del contrato:
- Nunca devolver preview inválido al UI.
- Si falla el render → usar fallback.
- No crashear ante entradas inválidas.
"""

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap

from app.services.icon_service import IconService
from app.services.preview_pdf_service import PreviewPdfService
from app.services.preview_file_extensions import validate_pixmap


def test_preview_service_no_devuelve_pixmap_invalido(qapp, temp_file):
    """
    Protege: que el servicio de preview nunca emita datos gráficos inválidos.
    - Acepta dos salidas: pixmap válido o fallback vacío (QPixmap nulo).
    - Nunca debe retornar un pixmap no nulo pero inválido.
    """
    service = PreviewPdfService(IconService())
    size = QSize(200, 200)

    # Caso 1: archivo de texto → debe renderizar imagen de texto o fallback
    pixmap = service.get_quicklook_pixmap(temp_file, size)
    # Contrato: válido o fallback nulo, pero NO inválido
    assert validate_pixmap(pixmap) or pixmap.isNull()

    # Caso 2: archivo inexistente → no crashea y retorna fallback
    missing = temp_file + ".missing"
    result = service.get_quicklook_pixmap(missing, size)
    # Debe ser QPixmap y cumplir contrato (válido o nulo, nunca inválido)
    assert isinstance(result, QPixmap)
    assert validate_pixmap(result) or result.isNull()

