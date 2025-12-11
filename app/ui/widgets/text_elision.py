"""
TextElision - Text truncation utilities for UI widgets.

Provides manual text elision functions for Apple-style middle truncation.
"""

from PySide6.QtGui import QFontMetrics


def elide_middle_manual(text: str, metrics: QFontMetrics, max_width: int) -> str:
    """
    Elide text in the middle manually (estilo Apple).
    Preserves beginning and end of text, truncates middle.
    """
    if not text:
        return text
    
    # Si el texto cabe completo, devolverlo tal cual
    if metrics.horizontalAdvance(text) <= max_width:
        return text
    
    # Calcular el ancho de "..."
    ellipsis = "..."
    ellipsis_width = metrics.horizontalAdvance(ellipsis)
    
    # Ancho disponible para texto (total - ellipsis)
    available_width = max_width - ellipsis_width
    
    if available_width <= 0:
        return ellipsis
    
    # Dividir el espacio disponible entre inicio y final
    # Dar un poco más al inicio (60%) que al final (40%)
    start_width = int(available_width * 0.6)
    end_width = available_width - start_width
    
    # Encontrar cuántos caracteres caben al inicio
    start_text = _find_start_text(text, metrics, start_width)
    
    # Encontrar cuántos caracteres caben al final
    end_text = _find_end_text(text, metrics, end_width)
    
    # Combinar inicio + ellipsis + final
    result = start_text + ellipsis + end_text
    
    # Asegurar que no exceda el ancho máximo
    return _ensure_max_width(result, start_text, end_text, ellipsis, metrics, max_width)


def _find_start_text(text: str, metrics: QFontMetrics, max_width: int) -> str:
    """Find characters that fit at the start."""
    start_text = ""
    for char in text:
        test_text = start_text + char
        if metrics.horizontalAdvance(test_text) > max_width:
            break
        start_text = test_text
    return start_text


def _find_end_text(text: str, metrics: QFontMetrics, max_width: int) -> str:
    """Find characters that fit at the end."""
    end_text = ""
    for char in reversed(text):
        test_text = char + end_text
        if metrics.horizontalAdvance(test_text) > max_width:
            break
        end_text = test_text
    return end_text


def _ensure_max_width(
    result: str,
    start_text: str,
    end_text: str,
    ellipsis: str,
    metrics: QFontMetrics,
    max_width: int
) -> str:
    """Ensure result doesn't exceed max width by trimming if needed."""
    current_start = start_text
    current_end = end_text
    
    while metrics.horizontalAdvance(result) > max_width and (len(current_start) > 0 or len(current_end) > 0):
        if len(current_start) > 0:
            current_start = current_start[:-1]
        elif len(current_end) > 0:
            current_end = current_end[1:]
        result = current_start + ellipsis + current_end
        if not current_start and not current_end:
            return ellipsis
    
    return result



