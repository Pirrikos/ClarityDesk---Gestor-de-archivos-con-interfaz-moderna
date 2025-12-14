"""
ToolbarStateButtons - State action button creation helpers.

Creates state quick action buttons for ViewToolbar.
"""

from typing import Callable, Dict

from PySide6.QtWidgets import QPushButton, QWidget

from app.ui.widgets.toolbar_button_styles import (
    get_clear_button_style,
    get_state_button_style,
)


def create_state_buttons(
    layout, 
    state_button_clicked_signal: Callable[[str], None]
) -> Dict[str, QPushButton]:
    """
    Create state quick action buttons.
    
    Args:
        layout: Layout to add buttons to.
        state_button_clicked_signal: Signal to emit when button is clicked.
        
    Returns:
        Dictionary mapping state constants to button widgets.
    """
    state_buttons: Dict[str, QPushButton] = {}
    
    # Import state constants
    try:
        from app.ui.widgets.state_badge_widget import (
            STATE_CORRECTED,
            STATE_DELIVERED,
            STATE_PENDING,
            STATE_REVIEW,
        )
    except ImportError:
        return state_buttons

    # Sin separador de línea entre grupos; mantener espaciado mínimo
    layout.addSpacing(6)

    # State buttons configuration
    state_configs = [
        (STATE_PENDING, "🟡", "Marcar archivos seleccionados como Pendiente"),
        (STATE_DELIVERED, "🔵", "Marcar archivos seleccionados como Entregado"),
        (STATE_CORRECTED, "✅", "Marcar archivos seleccionados como Corregido"),
        (STATE_REVIEW, "🔴", "Marcar archivos seleccionados como Revisar"),
    ]

    for state, emoji, tooltip in state_configs:
        btn = QPushButton(emoji)
        btn.setFixedSize(30, 30)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(get_state_button_style())
        btn.clicked.connect(lambda checked, s=state: state_button_clicked_signal(s))
        layout.addWidget(btn)
        state_buttons[state] = btn
    
    # Add "Clear state" button
    layout.addSpacing(8)
    clear_btn = QPushButton("✕")
    clear_btn.setFixedSize(30, 30)
    clear_btn.setToolTip("Quitar estado de archivos seleccionados")
    clear_btn.setStyleSheet(get_clear_button_style())
    clear_btn.clicked.connect(lambda: state_button_clicked_signal(None))
    layout.addWidget(clear_btn)
    
    return state_buttons

