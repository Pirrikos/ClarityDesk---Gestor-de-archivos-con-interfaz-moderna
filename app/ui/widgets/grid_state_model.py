"""
GridStateModel - Pure state calculation for grid layout.

Calculates differences between grid states without Qt dependencies.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class GridDiff:
    """Result of comparing two grid states."""
    added: List[str]  # tile_ids that are new
    removed: List[str]  # tile_ids that no longer exist
    moved: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]]  # tile_id -> (old_pos, new_pos)
    unchanged: List[str]  # tile_ids in same position
    new_state: Dict[str, Tuple[int, int]]  # tile_id -> (row, col)


class GridStateModel:
    """
    Pure calculation model for grid state differences.
    
    No Qt dependencies - only calculates positions and diffs.
    """
    
    @staticmethod
    def calculate_changes(
        old_state: Dict[str, Tuple[int, int]],
        ordered_ids: List[str],
        columns: int
    ) -> GridDiff:
        """
        Calculate differences between old state and new ordered list.
        
        Args:
            old_state: Previous state mapping tile_id -> (row, col)
            ordered_ids: New ordered list of tile_ids
            columns: Number of columns in grid
            
        Returns:
            GridDiff with added, removed, moved, unchanged, and new_state
        """
        # Calculate new positions for all ordered_ids
        new_state = {}
        for index, tile_id in enumerate(ordered_ids):
            row = index // columns
            col = index % columns
            new_state[tile_id] = (row, col)
        
        # Find differences
        old_ids = set(old_state.keys())
        new_ids = set(ordered_ids)
        
        added = list(new_ids - old_ids)
        removed = list(old_ids - new_ids)
        
        # Find moved and unchanged
        moved = {}
        unchanged = []
        
        for tile_id in old_ids & new_ids:  # Intersection: tiles that exist in both
            old_pos = old_state[tile_id]
            new_pos = new_state[tile_id]
            
            if old_pos == new_pos:
                unchanged.append(tile_id)
            else:
                moved[tile_id] = (old_pos, new_pos)
        
        return GridDiff(
            added=added,
            removed=removed,
            moved=moved,
            unchanged=unchanged,
            new_state=new_state
        )

