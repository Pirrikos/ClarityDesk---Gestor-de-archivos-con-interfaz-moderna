"""
Workspace - Workspace model.

Represents a workspace container that holds tabs, sidebar state, and active tab.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Workspace:
    """Workspace container for tabs, sidebar state, and active tab."""
    
    id: str
    name: str
    tabs: List[str]
    active_tab: Optional[str]
    focus_tree_paths: List[str]
    expanded_nodes: List[str]
    
    def __post_init__(self):
        """Normalize empty lists if None."""
        if self.tabs is None:
            self.tabs = []
        if self.focus_tree_paths is None:
            self.focus_tree_paths = []
        if self.expanded_nodes is None:
            self.expanded_nodes = []

