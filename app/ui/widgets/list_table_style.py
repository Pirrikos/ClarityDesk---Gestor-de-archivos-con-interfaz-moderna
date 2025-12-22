"""
ListTableStyle - Custom proxy style to eliminate column separator lines.

Intercepts Qt's native drawing to prevent brown vertical lines between columns
when rows are selected. This is a professional solution that prevents Qt from
drawing gridlines and separator lines at the style level.
"""

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QProxyStyle, QStyle, QStyleOption


class ListTableStyle(QProxyStyle):
    """
    Custom proxy style that eliminates column separator lines.
    
    Intercepts Qt's drawing primitives to prevent gridlines and separator
    lines from being drawn between columns when rows are selected.
    """
    
    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget=None
    ) -> None:
        """
        Intercept primitive drawing to eliminate gridlines and separators.
        
        Args:
            element: The primitive element being drawn
            option: Style options
            painter: Painter to use
            widget: Widget being painted
        """
        # Interceptar el dibujo de líneas de grid/focus que aparecen entre columnas
        # PE_FrameFocusRect puede dibujar líneas de separación
        if element == QStyle.PrimitiveElement.PE_FrameFocusRect:
            # No dibujar el frame de focus - esto elimina líneas marrones
            return
        
        # Permitir que todo lo demás se dibuje normalmente
        super().drawPrimitive(element, option, painter, widget)
    
    def drawControl(
        self,
        element: QStyle.ControlElement,
        option: QStyleOption,
        painter: QPainter,
        widget=None
    ) -> None:
        """
        Intercept control drawing to eliminate column separators.
        
        Args:
            element: The control element being drawn
            option: Style options
            painter: Painter to use
            widget: Widget being painted
        """
        # Interceptar el dibujo de controles que pueden incluir líneas de separación
        # CE_ItemViewItem puede dibujar líneas de grid entre columnas
        if element == QStyle.ControlElement.CE_ItemViewItem:
            # Obtener el option como QStyleOptionViewItem
            from PySide6.QtWidgets import QStyleOptionViewItem
            if isinstance(option, QStyleOptionViewItem):
                # Desactivar cualquier decoración que pueda dibujar líneas
                option.showDecorationSelected = False
                # Eliminar estados que puedan causar líneas de separación
                option.state &= ~QStyle.StateFlag.State_HasFocus
                option.state &= ~QStyle.StateFlag.State_KeyboardFocusChange
        
        # Permitir que todo lo demás se dibuje normalmente
        super().drawControl(element, option, painter, widget)

