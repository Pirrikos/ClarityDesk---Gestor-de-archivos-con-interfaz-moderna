"""
ToolbarNavigationButtons - Navigation button creation helpers.

Creates Back/Forward navigation buttons for ViewToolbar.
"""

from PySide6.QtWidgets import QPushButton, QStyle

from app.ui.widgets.toolbar_button_styles import get_nav_button_style


def create_navigation_buttons(parent_widget) -> tuple[QPushButton, QPushButton]:
    """
    Create Back and Forward navigation buttons.
    
    Args:
        parent_widget: Parent widget for buttons.
        
    Returns:
        Tuple of (back_button, forward_button).
    """
    style = parent_widget.style()
    
    # Back button
    back_button = QPushButton(parent_widget)
    back_icon = style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
    back_button.setIcon(back_icon)
    back_button.setToolTip("Atrás")
    back_button.setFixedSize(36, 36)
    back_button.setStyleSheet(get_nav_button_style())
    back_button.setEnabled(False)
    
    # Forward button
    forward_button = QPushButton(parent_widget)
    forward_icon = style.standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
    forward_button.setIcon(forward_icon)
    forward_button.setToolTip("Adelante")
    forward_button.setFixedSize(36, 36)
    forward_button.setStyleSheet(get_nav_button_style())
    forward_button.setEnabled(False)
    
    return back_button, forward_button

