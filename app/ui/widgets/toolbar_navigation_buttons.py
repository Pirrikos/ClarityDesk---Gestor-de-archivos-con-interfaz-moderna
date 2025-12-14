"""
ToolbarNavigationButtons - Navigation button creation helpers.

Creates Back/Forward navigation buttons for ViewToolbar.
"""

from PySide6.QtWidgets import QPushButton

from app.ui.widgets.toolbar_button_styles import get_nav_button_style


def create_navigation_buttons(parent_widget) -> tuple[QPushButton, QPushButton]:
    """
    Create Back and Forward navigation buttons.
    
    Args:
        parent_widget: Parent widget for buttons.
        
    Returns:
        Tuple of (back_button, forward_button).
    """
    # Back button
    back_button = QPushButton(parent_widget)
    back_button.setText("←")
    back_button.setToolTip("Atrás")
    back_button.setFixedSize(30, 30)
    back_button.setStyleSheet(get_nav_button_style())
    back_button.setEnabled(False)
    
    # Forward button
    forward_button = QPushButton(parent_widget)
    forward_button.setText("→")
    forward_button.setToolTip("Adelante")
    forward_button.setFixedSize(30, 30)
    forward_button.setStyleSheet(get_nav_button_style())
    forward_button.setEnabled(False)
    
    return back_button, forward_button

