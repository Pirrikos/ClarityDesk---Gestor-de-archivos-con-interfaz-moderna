"""
GridLayoutConfig - Grid layout configuration helpers.

Handles layout spacing, margins, and alignment settings.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout


# Dock layout constants
DOCK_TILE_WIDTH = 85
DOCK_TILE_SPACING = 16
DOCK_EXPANDED_MARGIN = 32
DOCK_DEFAULT_FILES_PER_ROW = 5


def setup_dock_layout_config(grid_layout: QGridLayout) -> None:
    """Configure grid layout for Dock style."""
    grid_layout.setSpacing(12)
    # Margen izquierdo: 20px, margen derecho: 12px (simétrico con spacing después del separador)
    grid_layout.setContentsMargins(20, 16, 12, 16)
    grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)


def setup_normal_grid_config(grid_layout: QGridLayout) -> None:
    """Configure grid layout for normal grid style."""
    grid_layout.setSpacing(12)
    grid_layout.setContentsMargins(20, 8, 20, 16)  # Margen superior reducido de 16px a 8px
    grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)


def calculate_expansion_height(
    is_desktop_window: bool,
    stacks: list,
    expanded_stacks: dict
) -> int:
    """
    Calculate and return height needed for expanded stacks.
    
    Args:
        is_desktop_window: True if DesktopWindow.
        stacks: List of FileStack objects.
        expanded_stacks: Dict of expanded files by stack type.
        
    Returns:
        Height in pixels needed for expansion.
    """
    if not is_desktop_window or not expanded_stacks:
        return 0
    
    total_stacks = len(stacks) if stacks else 5
    total_expanded_files = sum(len(files) for files in expanded_stacks.values())
    num_rows = (total_expanded_files + total_stacks - 1) // total_stacks
    
    if num_rows == 0:
        return 0
    
    # Usar cálculo consistente con ExpandedStacksWidget
    from app.ui.widgets.expanded_stacks_widget import ExpandedStacksWidget
    return ExpandedStacksWidget.calculate_height_for_rows(num_rows)


def calculate_files_per_row(window_width: int) -> int:
    """
    Calculate files per row based on window width.
    
    Args:
        window_width: Width of the dock window in pixels.
        
    Returns:
        Number of files that fit per row.
    """
    available = window_width - DOCK_EXPANDED_MARGIN
    if available <= 0:
        return DOCK_DEFAULT_FILES_PER_ROW
    return max(1, available // (DOCK_TILE_WIDTH + DOCK_TILE_SPACING))

