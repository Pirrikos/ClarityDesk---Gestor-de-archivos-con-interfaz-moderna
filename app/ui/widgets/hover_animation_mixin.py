"""
HoverAnimationMixin - Mixin para agregar animación suave de hover a widgets.

Centraliza la lógica de animación de hover para evitar duplicación de código.
"""

from typing import Optional

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt


class HoverAnimationMixin:
    """Mixin para agregar animación suave de hover a widgets."""
    
    def _init_hover_animation(self) -> None:
        """Inicializar propiedades de hover animation."""
        self._hover_opacity: float = 0.0
        self._hover_animation: Optional[QPropertyAnimation] = None
    
    def _get_hover_opacity(self) -> float:
        """Getter para la propiedad animada de opacidad del hover."""
        return self._hover_opacity
    
    def _set_hover_opacity(self, opacity: float) -> None:
        """Setter para la propiedad animada de opacidad del hover."""
        self._hover_opacity = opacity
        if hasattr(self, 'update'):
            self.update()
    
    hover_opacity = Property(float, _get_hover_opacity, _set_hover_opacity)
    
    def _start_hover_animation(self, target_opacity: float, duration_ms: int = 200) -> None:
        """Iniciar animación suave del hover."""
        if self._hover_animation:
            self._hover_animation.stop()
        
        self._hover_animation = QPropertyAnimation(self, b"hover_opacity")
        self._hover_animation.setDuration(duration_ms)
        self._hover_animation.setStartValue(self._hover_opacity)
        self._hover_animation.setEndValue(target_opacity)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_animation.start()

