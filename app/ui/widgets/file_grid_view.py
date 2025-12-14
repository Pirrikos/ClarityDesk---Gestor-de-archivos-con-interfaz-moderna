"""
FileGridView - Grid/tile view for displaying files.

Shows files as tiles with icons and filenames.
Emits signal on double-click to open file.
"""

from typing import List, Optional, Tuple, Union, TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.managers.tab_manager import TabManager
from app.models.file_stack import FileStack
from app.services.file_category_service import get_categorized_files_with_labels
from app.services.icon_service import IconService
from app.ui.widgets.file_grid_view_drag import drag_enter_event, drag_move_event, drop_event
from app.ui.widgets.file_grid_view_events import (
    resize_event, on_stack_clicked, emit_expansion_height,
    remove_tile_safely, animate_tile_exit
)
from app.ui.widgets.file_grid_view_layout import setup_grid_layout, clear_old_tiles
from app.ui.widgets.file_grid_view_scroll import create_scroll_area, configure_scroll_area
from app.ui.widgets.file_stack_tile import FileStackTile
from app.ui.widgets.file_tile import FileTile
from app.ui.widgets.grid_content_widget import GridContentWidget
from app.ui.widgets.grid_layout_engine import build_dock_layout, build_normal_grid
from app.ui.widgets.grid_selection_logic import (
    clear_selection, select_tile, get_selected_paths, set_selected_states
)
from app.ui.widgets.grid_tile_builder import create_file_tile, create_stack_tile

# Temporary import for state manager stub
try:
    from app.managers.file_state_manager import FileStateManager
except ImportError:
    FileStateManager = None

if TYPE_CHECKING:
    from app.ui.windows.desktop_window import DesktopWindow


class FileGridView(QWidget):
    """Grid view widget displaying files as tiles."""

    open_file = Signal(str)
    file_dropped = Signal(str)
    file_deleted = Signal(str)
    folder_moved = Signal(str, str)  # Emitted when folder is moved (old_path, new_path)
    stack_expand_requested = Signal(FileStack)
    expansion_height_changed = Signal(int)
    stacks_count_changed = Signal(int)

    def __init__(
        self,
        icon_service: Optional[IconService] = None,
        filesystem_service: Optional = None,
        parent=None,
        tab_manager: Optional[TabManager] = None,
        state_manager=None,
        is_desktop: bool = False,
        desktop_window: Optional['DesktopWindow'] = None
    ):
        """
        Initialize FileGridView with empty file list.
        
        Args:
            icon_service: Service for icon generation.
            filesystem_service: Deprecated, kept for compatibility.
            parent: Parent widget.
            tab_manager: TabManager instance.
            state_manager: FileStateManager instance.
            is_desktop: True if this view represents Desktop Focus.
            desktop_window: Optional DesktopWindow instance (for Desktop Focus context).
        """
        super().__init__(parent)
        # _files puede ser lista de paths o lista de tuplas (category_label, files) para categorización
        self._files: Union[List[str], List[Tuple[str, List[str]]]] = []
        self._stacks: list[FileStack] = []
        self._icon_service = icon_service or IconService()
        self._tab_manager = tab_manager
        self._selected_tiles: set[FileTile] = set()
        self._use_stacks = False
        self._expanded_stacks: dict[str, list] = {}
        self._expanded_file_tiles: dict[str, list[FileTile]] = {}
        self._state_manager = state_manager or (FileStateManager() if FileStateManager else None)
        # Flag explícito del modo - no se infiere desde la jerarquía
        self._is_desktop_window = is_desktop
        self._desktop_window = desktop_window
        # Desktop files are always visible - stacks are always shown
        self._desktop_files_hidden = True  # Always True - stacks always visible
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll = create_scroll_area(self)
        self._content_widget = GridContentWidget(self, self._desktop_window)
        # _is_desktop_window ya está establecido desde __init__ (flag explícito)
        self._use_stacks = self._is_desktop_window
        
        configure_scroll_area(scroll, self._content_widget, self._is_desktop_window)
        self._grid_layout = setup_grid_layout(self._content_widget)
        
        scroll.setWidget(self._content_widget)
        layout.addWidget(scroll)

    def set_desktop_mode(self, is_desktop: bool) -> None:
        """
        Actualizar explícitamente el estado de Desktop Focus.
        
        Este método se llama cuando cambia el tab activo para asegurar que
        FileGridView sepa correctamente si está mostrando Desktop Focus o una carpeta normal.
        
        Args:
            is_desktop: True si la carpeta activa es Desktop Focus, False en caso contrario.
        """
        self._is_desktop_window = is_desktop
        self._use_stacks = is_desktop
    
    def update_files(self, file_list: list) -> None:
        """Update displayed files or stacks."""
        if file_list and isinstance(file_list[0], FileStack):
            old_expanded = self._expanded_stacks.copy()
            self._expanded_stacks = {}
            self._stacks = file_list
            self._files = []
            for stack in self._stacks:
                if stack.stack_type in old_expanded:
                    self._expanded_stacks[stack.stack_type] = stack.files
        else:
            # Categorizar archivos solo en MainWindow (no en DesktopWindow)
            if not self._is_desktop_window:
                self._files = get_categorized_files_with_labels(file_list)
            else:
                self._files = file_list
                self._stacks = []
                self._expanded_stacks = {}
        self._refresh_tiles()

    def _refresh_tiles(self) -> None:
        """Rebuild file tiles or stack tiles in grid layout."""
        clear_selection(self)
        old_expanded_tiles_to_animate = clear_old_tiles(self)
        items_to_render = self._stacks if self._stacks else self._files
        
        if self._is_desktop_window:
            build_dock_layout(self, items_to_render, old_expanded_tiles_to_animate, self._grid_layout)
            # Emit stacks count change to adjust window width
            stacks_count = len(self._stacks) if self._stacks else 0
            self.stacks_count_changed.emit(stacks_count)
        else:
            build_normal_grid(self, items_to_render, self._grid_layout)
        
        # Force content widget to recalculate size after adding tiles
        # This ensures vertical expansion and proper scrolling
        # Use QTimer to ensure layout has been processed
        QTimer.singleShot(0, lambda: self._content_widget.adjustSize())
        QTimer.singleShot(0, lambda: self._content_widget.updateGeometry())

    def _on_stack_clicked(self, file_stack: FileStack) -> None:
        """Handle stack click - toggle expansion horizontally below stack."""
        on_stack_clicked(self, file_stack)
    
    def _emit_expansion_height(self) -> None:
        """Calculate and emit the height needed for expanded stacks."""
        emit_expansion_height(self)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter for file drop on main widget."""
        drag_enter_event(self, event)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move to maintain drop acceptance."""
        drag_move_event(self, event)

    def dropEvent(self, event) -> None:
        """Handle file drop on main widget."""
        drop_event(self, event)

    def _clear_selection(self) -> None:
        """Clear all tile selections."""
        clear_selection(self)

    def _select_tile(self, tile: FileTile, modifiers: Qt.KeyboardModifiers) -> None:
        """Handle tile selection based on keyboard modifiers."""
        select_tile(self, tile, modifiers)

    def resizeEvent(self, event) -> None:
        """Handle resize to recalculate grid columns."""
        resize_event(self, event)

    def get_selected_paths(self) -> list[str]:
        """Get paths of currently selected files."""
        return get_selected_paths(self)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Context menu disabled - states are set via toolbar buttons only."""
        pass

    def set_selected_states(self, state) -> None:
        """Set state for all selected files and update badges."""
        set_selected_states(self, state)
    
    def _remove_tile_safely(self, tile: FileTile) -> None:
        """Safely remove a tile after exit animation completes."""
        remove_tile_safely(self, tile)
    
    def _animate_tile_exit(self, tile: FileTile, delay_ms: int = 0) -> None:
        """Animate tile exit with delay, then remove it."""
        animate_tile_exit(self, tile, delay_ms)
    