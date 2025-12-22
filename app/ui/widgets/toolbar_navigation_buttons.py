"""
ToolbarNavigationButtons - Navigation button creation helpers.

Creates Back/Forward navigation buttons for ViewToolbar and AppHeader.
"""

from typing import Tuple

from PySide6.QtWidgets import QPushButton

from app.ui.widgets.toolbar_button_styles import get_nav_button_style


def create_navigation_buttons(
    parent_widget,
    size: Tuple[int, int] = (30, 30),
    use_default_style: bool = True
) -> Tuple[QPushButton, QPushButton]:
    """
    Create Back and Forward navigation buttons.
    
    Args:
        parent_widget: Parent widget for buttons.
        size: Tuple of (width, height) for button size. Default: (30, 30).
        use_default_style: If True, applies default navigation button style. Default: True.
        
    Returns:
        Tuple of (back_button, forward_button).
    """
    back_button = QPushButton(parent_widget)
    back_button.setText("←")
    back_button.setToolTip("Atrás")
    back_button.setFixedSize(*size)
    if use_default_style:
        back_button.setStyleSheet(get_nav_button_style())
    back_button.setEnabled(False)
    
    forward_button = QPushButton(parent_widget)
    forward_button.setText("→")
    forward_button.setToolTip("Adelante")
    forward_button.setFixedSize(*size)
    if use_default_style:
        forward_button.setStyleSheet(get_nav_button_style())
    forward_button.setEnabled(False)
    
    return back_button, forward_button

