"""
FileGridView - Grid/tile view for displaying files.

Shows files as tiles with icons and filenames.
Emits signal on double-click to open file.
"""

from typing import List, Optional, Tuple, Union, TYPE_CHECKING

from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QContextMenuEvent, QMouseEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.core.constants import CENTRAL_AREA_BG
from app.core.logger import get_logger
from app.managers.tab_manager import TabManager
from app.models.file_stack import FileStack
from app.services.file_category_service import get_categorized_files_with_labels
from app.services.icon_service import IconService
from app.ui.widgets.file_grid_view_drag import drag_enter_event, drag_move_event, drop_event
from app.ui.widgets.file_grid_view_events import (
    resize_event, on_stack_clicked, emit_expansion_height,
    remove_tile_safely, animate_tile_exit
)
from app.ui.widgets.file_grid_view_layout import setup_grid_layout
from app.ui.widgets.grid_tile_manager import TileManager
from app.ui.widgets.file_grid_view_scroll import create_scroll_area, configure_scroll_area
from app.ui.widgets.file_stack_tile import FileStackTile
from app.ui.widgets.file_tile import FileTile
from app.ui.widgets.grid_content_widget import GridContentWidget
from app.ui.widgets.grid_layout_engine import build_dock_layout, build_normal_grid
from app.ui.widgets.grid_selection_logic import (
    clear_selection, select_tile, get_selected_paths, set_selected_states
)
from app.ui.widgets.grid_tile_builder import create_file_tile, create_stack_tile
from app.ui.widgets.file_view_context_menu import show_background_menu, show_item_menu
from app.ui.widgets.file_view_utils import create_refresh_callback

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
        # Cache para optimización de cálculo de columnas
        self._cached_columns: Optional[int] = None
        self._cached_width: int = 0
        # Cache para categorización de archivos
        self._cached_categorized_files: Optional[Union[List[str], List[Tuple[str, List[str]]]]] = None
        self._cached_file_list_hash: Optional[int] = None
        # Estado del grid: tile_id -> (row, col)
        self._grid_state: dict[str, tuple[int, int]] = {}
        # Tile manager para gestión del ciclo de vida
        self._tile_manager: Optional[TileManager] = None
        # Estado anterior para actualización incremental
        self._previous_files: Optional[Union[List[str], List[Tuple[str, List[str]]]]] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        self.setAcceptDrops(True)
        
        if not self._is_desktop_window:
            self.setStyleSheet(f"QWidget {{ background-color: {CENTRAL_AREA_BG}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll = create_scroll_area(self)
        self._content_widget = GridContentWidget(self, self._desktop_window)
        # _is_desktop_window ya está establecido desde __init__ (flag explícito)
        self._use_stacks = self._is_desktop_window
        
        configure_scroll_area(scroll, self._content_widget, self._is_desktop_window)
        self._grid_layout = setup_grid_layout(self._content_widget)
        
        # Initialize tile manager
        self._tile_manager = TileManager(
            self,
            self._icon_service,
            self._state_manager,
            self._grid_layout,
            self._content_widget
        )
        
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
        """Update displayed files or stacks with incremental updates when possible."""
        # Almacenar datos y renderizar inmediatamente (como Lista)
        if file_list and isinstance(file_list[0], FileStack):
            old_expanded = self._expanded_stacks.copy()
            self._expanded_stacks = {}
            self._stacks = file_list
            self._files = []
            for stack in self._stacks:
                if stack.stack_type in old_expanded:
                    self._expanded_stacks[stack.stack_type] = stack.files
            # Limpiar cache de categorización cuando hay stacks
            self._cached_categorized_files = None
            self._cached_file_list_hash = None
            self._previous_files = None
        else:
            # Categorizar archivos solo en MainWindow (no en DesktopWindow)
            if not self._is_desktop_window:
                # Cache de categorización: solo recalcular si lista de archivos cambió
                file_list_hash = hash(tuple(file_list) if file_list else ())
                if (self._cached_categorized_files is None or 
                    self._cached_file_list_hash != file_list_hash):
                    self._files = get_categorized_files_with_labels(file_list)
                    self._cached_categorized_files = self._files
                    self._cached_file_list_hash = file_list_hash
                else:
                    # Reutilizar resultado cacheado
                    self._files = self._cached_categorized_files
            else:
                self._files = file_list
                # Limpiar cache de categorización cuando es desktop window
                self._cached_categorized_files = None
                self._cached_file_list_hash = None
            self._stacks = []
            self._expanded_stacks = {}
            
        # Refresh completo (el nuevo sistema maneja incrementalmente)
        self._previous_files = self._files.copy() if hasattr(self._files, 'copy') else self._files
        self._refresh_tiles()
    

    def _refresh_tiles(self) -> None:
        """Rebuild file tiles or stack tiles in grid layout."""
        items_to_render = self._stacks if self._stacks else self._files
        
        clear_selection(self)
        
        # Handle expanded tiles animation for dock layout
        old_expanded_tiles_to_animate = {}
        if self._is_desktop_window and self._expanded_file_tiles:
            old_expanded_tiles_to_animate = self._expanded_file_tiles.copy()
        
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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - clear selection if clicking on empty background."""
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_tile, _ = self._get_clicked_tile(event.pos())
            
            if clicked_tile is None:
                self._clear_selection()
                event.accept()
                return
        
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Show context menu - background menu or item menu depending on click location."""
        refresh_callback = create_refresh_callback(self)
        
        # Detectar si el clic es sobre un tile o sobre el fondo
        clicked_tile, item_path = self._get_clicked_tile(event.pos())
        
        if clicked_tile and item_path:
            # Clic sobre un elemento (archivo/carpeta)
            # Obtener selección múltiple si existe
            selected_paths = self.get_selected_paths()
            
            # Normalizar a lista siempre: usar selección múltiple si hay 2+ elementos, sino usar item_path como lista
            if len(selected_paths) > 1:
                # Hay selección múltiple (2+ elementos)
                item_paths = selected_paths
            else:
                # No hay selección múltiple, usar item_path como lista de 1 elemento
                item_paths = [item_path]
            
            show_item_menu(self, event, item_paths, self._tab_manager, refresh_callback)
        else:
            # Clic sobre el fondo (espacio vacío)
            show_background_menu(self, event, self._tab_manager, refresh_callback)
    
    def _get_clicked_tile(self, pos: QPoint) -> tuple[Optional[object], Optional[str]]:
        """
        Detectar si el clic es sobre un tile o sobre el fondo.
        
        Args:
            pos: Posición del clic en coordenadas del widget (FileGridView).
            
        Returns:
            Tuple de (tile_widget, item_path) o (None, None) si es fondo.
        """
        # Convertir posición a coordenadas del content_widget
        content_pos = self._content_widget.mapFrom(self, pos)
        
        # Buscar widget hijo en la posición del clic
        child_widget = self._content_widget.childAt(content_pos)
        
        if not child_widget:
            return None, None
        
        # Verificar si el widget o alguno de sus padres es un tile
        widget = child_widget
        while widget and widget != self._content_widget:
            widget_type = type(widget).__name__
            
            # Verificar si es un tile (FileTile, FileStackTile, DesktopStackTile)
            if 'Tile' in widget_type:
                # Obtener ruta del archivo desde el tile
                if hasattr(widget, 'get_file_path'):
                    file_path = widget.get_file_path()
                    return widget, file_path
                elif hasattr(widget, '_file_stack') and widget._file_stack:
                    # Es un FileStackTile, usar el primer archivo del stack
                    if widget._file_stack.files:
                        return widget, widget._file_stack.files[0]
                elif hasattr(widget, '_file_path'):
                    return widget, widget._file_path
            
            widget = widget.parent()
        
        return None, None

    def set_selected_states(self, state) -> None:
        """Set state for all selected files and update badges."""
        set_selected_states(self, state)
    
    def _remove_tile_safely(self, tile: FileTile) -> None:
        """Safely remove a tile after exit animation completes."""
        remove_tile_safely(self, tile)
    
    def _animate_tile_exit(self, tile: FileTile, delay_ms: int = 0) -> None:
        """Animate tile exit with delay, then remove it."""
        animate_tile_exit(self, tile, delay_ms)
    