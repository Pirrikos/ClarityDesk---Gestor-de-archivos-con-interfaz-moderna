"""
TileManager - Lifecycle management for grid tiles.

Single owner of tile creation, attachment, detachment, and destruction.
"""

from typing import Dict, Optional, TYPE_CHECKING

from PySide6.QtWidgets import QWidget, QGridLayout

from app.core.logger import get_logger
from app.models.file_stack import FileStack
from app.ui.widgets.grid_tile_builder import create_file_tile, create_stack_tile

if TYPE_CHECKING:
    from app.ui.widgets.file_grid_view import FileGridView
    from app.services.icon_service import IconService
    from app.managers.file_state_manager import FileStateManager

logger = get_logger(__name__)


class TileManager:
    """
    Manages tile lifecycle: creation, attachment, detachment, destruction.
    
    Maintains tiles_by_id dictionary and ensures safe reuse.
    """
    
    def __init__(
        self,
        view: 'FileGridView',
        icon_service: 'IconService',
        state_manager: Optional['FileStateManager'],
        grid_layout: QGridLayout,
        content_widget: QWidget
    ):
        """
        Initialize TileManager.
        
        Args:
            view: FileGridView instance
            icon_service: IconService for tile creation
            state_manager: Optional FileStateManager for file states
            grid_layout: QGridLayout to manage
            content_widget: Parent widget for tiles
        """
        self._view = view
        self._icon_service = icon_service
        self._state_manager = state_manager
        self._grid_layout = grid_layout
        self._content_widget = content_widget
        self._tiles_by_id: Dict[str, QWidget] = {}
    
    def get_or_create(self, tile_id: str) -> QWidget:
        """
        Get existing tile or create new one.
        
        Args:
            tile_id: Unique identifier (file_path or f"stack:{stack_type}")
            
        Returns:
            QWidget tile instance
        """
        # Check if tile exists and is alive
        if tile_id in self._tiles_by_id:
            tile = self._tiles_by_id[tile_id]
            try:
                # Verify C++ object still exists
                _ = tile.parent()
                # Reset visual state before reuse
                if hasattr(tile, 'set_selected'):
                    tile.set_selected(False)
                return tile
            except RuntimeError:
                # Object was deleted, remove from cache
                self._tiles_by_id.pop(tile_id, None)
        
        # Create new tile
        tile = self._create_tile(tile_id)
        self._tiles_by_id[tile_id] = tile
        return tile
    
    def attach(self, tile: QWidget, row: int, col: int) -> None:
        """
        Attach tile to grid layout at specified position.
        
        Verifies tile is NOT already in layout before attaching.
        
        Args:
            tile: Tile widget to attach
            row: Grid row position
            col: Grid column position
        """
        # Verify tile is not already in layout
        # Check if tile's parent is the content widget and it's in layout
        layout_item = self._grid_layout.itemAtPosition(row, col)
        if layout_item and layout_item.widget() == tile:
            # Already at this position, skip
            return
        
        # Remove from any previous position if needed
        for i in range(self._grid_layout.count()):
            item = self._grid_layout.itemAt(i)
            if item and item.widget() == tile:
                self._grid_layout.removeWidget(tile)
                break
        
        # Set parent if needed
        if tile.parent() != self._content_widget:
            tile.setParent(self._content_widget)
        
        # Add to layout
        self._grid_layout.addWidget(tile, row, col)
    
    def detach(self, tile: QWidget) -> None:
        """
        Detach tile from grid layout.
        
        Does NOT destroy the tile or remove from tiles_by_id.
        Only removes from layout.
        
        Args:
            tile: Tile widget to detach
        """
        self._grid_layout.removeWidget(tile)
        # Do NOT setParent(None) here - that's done in destroy()
    
    def destroy(self, tile_id: str) -> None:
        """
        Destroy tile completely: detach, setParent(None), deleteLater, remove from dict.
        
        Args:
            tile_id: Unique identifier of tile to destroy
        """
        if tile_id not in self._tiles_by_id:
            return
        
        tile = self._tiles_by_id[tile_id]
        
        # Detach from layout
        self.detach(tile)
        
        # Cleanup badge if exists
        if hasattr(tile, '_cleanup_badge'):
            tile._cleanup_badge()
        
        # Remove parent and schedule deletion
        tile.setParent(None)
        tile.deleteLater()
        
        # Remove from cache
        self._tiles_by_id.pop(tile_id, None)
    
    def _find_stack_by_type(self, stack_type: str) -> Optional[FileStack]:
        """
        Find stack by type in view._stacks.
        
        Args:
            stack_type: Type of stack to find
            
        Returns:
            FileStack instance or None if not found
        """
        if hasattr(self._view, '_stacks') and self._view._stacks:
            for stack in self._view._stacks:
                if stack.stack_type == stack_type:
                    return stack
        return None
    
    def _create_tile(self, tile_id: str) -> QWidget:
        """
        Create new tile based on tile_id format.
        
        Args:
            tile_id: file_path or f"stack:{stack_type}"
            
        Returns:
            QWidget tile instance
        """
        if tile_id.startswith("stack:"):
            # Stack tile
            stack_type = tile_id[6:]  # Remove "stack:" prefix
            stack = self._find_stack_by_type(stack_type)
            
            if not stack:
                logger.warning(f"Stack not found for tile_id: {tile_id}")
                # Create dummy stack as fallback
                stack = FileStack(stack_type, [])
            
            tile = create_stack_tile(stack, self._view, self._icon_service)
            tile.stack_clicked.connect(self._view._on_stack_clicked)
            tile.open_file.connect(self._view.open_file.emit)
            return tile
        else:
            # File tile
            file_path = tile_id
            return create_file_tile(
                file_path,
                self._view,
                self._icon_service,
                self._state_manager,
                dock_style=self._view._is_desktop_window
            )
    
    def get_tile(self, tile_id: str) -> Optional[QWidget]:
        """
        Get tile by id without creating if missing.
        
        Args:
            tile_id: Unique identifier
            
        Returns:
            QWidget or None if not found
        """
        return self._tiles_by_id.get(tile_id)
    
    def clear_all(self) -> None:
        """Destroy all tiles."""
        tile_ids = list(self._tiles_by_id.keys())
        for tile_id in tile_ids:
            self.destroy(tile_id)

