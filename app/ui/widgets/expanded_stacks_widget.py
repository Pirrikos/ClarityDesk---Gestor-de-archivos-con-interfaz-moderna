"""
ExpandedStacksWidget - QStackedWidget para archivos expandidos del Dock.

PATRÓN PROFESIONAL: Cada stack tiene su propia "página" pre-renderizada.
Al cambiar de stack: solo se cambia la página visible (instantáneo, sin recrear widgets).
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from math import ceil

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget, QWidget, QGridLayout, QSizePolicy

from app.ui.widgets.file_tile import FileTile
from app.ui.widgets.grid_tile_builder import create_file_tile

if TYPE_CHECKING:
    from app.ui.widgets.file_grid_view import FileGridView


class StackPage(QWidget):
    """
    Página individual para un stack expandido.
    
    Contiene un grid de FileTiles para los archivos del stack.
    """
    
    # Layout constants - DEBEN coincidir con emit_expansion_height
    TILE_HEIGHT = 85        # Altura del FileTile en dock style
    TILE_SPACING = 16       # Espacio entre tiles
    MARGIN_TOP = 8          # Margen superior
    MARGIN_BOTTOM = 16      # Margen inferior (más espacio para nombres)
    MARGIN_LEFT = 20        # Margen izquierdo (alineado con stacks)
    MARGIN_RIGHT = 12       # Margen derecho
    
    def __init__(self, stack_type: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._stack_type = stack_type
        self._tiles: List[FileTile] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configurar layout del grid."""
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        self._grid_layout = QGridLayout(self)
        self._grid_layout.setContentsMargins(
            self.MARGIN_LEFT, self.MARGIN_TOP,
            self.MARGIN_RIGHT, self.MARGIN_BOTTOM
        )
        self._grid_layout.setSpacing(self.TILE_SPACING)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    
    @property
    def stack_type(self) -> str:
        return self._stack_type
    
    @property
    def tiles(self) -> List[FileTile]:
        return self._tiles
    
    def populate(
        self,
        files: List[str],
        view: 'FileGridView',
        files_per_row: int
    ) -> None:
        """
        Poblar la página con tiles para los archivos dados.
        
        Args:
            files: Lista de rutas de archivos.
            view: FileGridView padre (para icon_service, state_manager, etc).
            files_per_row: Número de archivos por fila.
        """
        # Limpiar tiles existentes
        self.clear()
        
        # Crear nuevos tiles
        # FileTile emite open_file a través de su _parent_view, no tiene señal propia
        for idx, file_path in enumerate(files):
            tile = create_file_tile(
                file_path, view, view._icon_service, view._state_manager,
                dock_style=True
            )
            # No conectar señal aquí - FileTile usa _parent_view.open_file.emit()
            
            row = idx // files_per_row
            col = idx % files_per_row
            
            self._grid_layout.addWidget(tile, row, col)
            self._tiles.append(tile)
        
        self._grid_layout.activate()
        self.updateGeometry()
    
    def update_files(
        self,
        files: List[str],
        view: 'FileGridView',
        files_per_row: int
    ) -> None:
        """
        Actualizar la página con nuevos archivos (reutilizando tiles cuando sea posible).
        
        Args:
            files: Lista de rutas de archivos.
            view: FileGridView padre.
            files_per_row: Número de archivos por fila.
        """
        # Mapear tiles existentes por path
        existing_by_path = {}
        for tile in self._tiles:
            try:
                path = tile.get_file_path()
                if path:
                    existing_by_path[path] = tile
            except RuntimeError:
                pass
        
        # Determinar qué tiles reutilizar y cuáles crear
        new_tiles = []
        
        for idx, file_path in enumerate(files):
            if file_path in existing_by_path:
                # Reutilizar tile existente
                tile = existing_by_path[file_path]
                del existing_by_path[file_path]
            else:
                # Crear nuevo tile
                # FileTile emite open_file a través de su _parent_view
                tile = create_file_tile(
                    file_path, view, view._icon_service, view._state_manager,
                    dock_style=True
                )
            
            row = idx // files_per_row
            col = idx % files_per_row
            self._grid_layout.addWidget(tile, row, col)
            new_tiles.append(tile)
        
        # Eliminar tiles que ya no se necesitan
        for tile in existing_by_path.values():
            try:
                self._grid_layout.removeWidget(tile)
                tile.setParent(None)
                tile.deleteLater()
            except RuntimeError:
                pass
        
        self._tiles = new_tiles
        self._grid_layout.activate()
        self.updateGeometry()
    
    def clear(self) -> None:
        """Eliminar todos los tiles de la página."""
        for tile in self._tiles:
            try:
                self._grid_layout.removeWidget(tile)
                tile.setParent(None)
                tile.deleteLater()
            except RuntimeError:
                pass
        self._tiles.clear()


class ExpandedStacksWidget(QStackedWidget):
    """
    QStackedWidget que contiene una página por cada stack expandido.
    
    Ventajas sobre recrear tiles:
    - Cambio de stack instantáneo (solo cambia página visible)
    - Sin flicker ni recreación de widgets
    - Tiles pre-renderizados y listos para mostrar
    
    NOTA: FileTile emite open_file directamente a través de su _parent_view,
    por lo que no necesitamos señales propias aquí.
    """
    
    # Constantes para cálculo de altura - DEBEN coincidir con StackPage y emit_expansion_height
    TILE_HEIGHT = 85
    TILE_SPACING = 16
    MARGIN_TOP = 8
    MARGIN_BOTTOM = 16  # Más espacio para nombres de archivos
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._pages: Dict[str, StackPage] = {}
        self._current_stack_type: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configurar el stacked widget."""
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Altura 0 por defecto (colapsado) - evita transiciones visible/invisible
        self.setFixedHeight(0)
    
    def get_or_create_page(self, stack_type: str) -> StackPage:
        """
        Obtener página para un stack, creándola si no existe.
        
        Args:
            stack_type: Tipo de stack (ej: "documents", "images").
            
        Returns:
            StackPage para el stack.
        """
        if stack_type not in self._pages:
            page = StackPage(stack_type, self)
            self.addWidget(page)
            self._pages[stack_type] = page
        
        return self._pages[stack_type]
    
    def show_stack(
        self,
        stack_type: str,
        files: List[str],
        view: 'FileGridView',
        files_per_row: int
    ) -> None:
        """
        Mostrar un stack expandido.
        
        Si la página ya existe, actualiza sus archivos.
        Si no existe, la crea y la pobla.
        Finalmente, la muestra.
        
        Args:
            stack_type: Tipo de stack a mostrar.
            files: Archivos del stack.
            view: FileGridView padre.
            files_per_row: Archivos por fila.
        """
        page = self.get_or_create_page(stack_type)
        
        # Actualizar archivos si cambiaron
        current_paths = set(t.get_file_path() for t in page.tiles if t)
        new_paths = set(files)
        
        if current_paths != new_paths or len(page.tiles) == 0:
            page.update_files(files, view, files_per_row)
        
        # Cambiar a esta página
        self.setCurrentWidget(page)
        self._current_stack_type = stack_type
        
        # Calcular y aplicar altura necesaria
        from math import ceil
        num_rows = ceil(len(files) / files_per_row) if files_per_row > 0 else 1
        num_rows = max(1, min(3, num_rows))
        height = self.calculate_height_for_rows(num_rows)
        self.setFixedHeight(height)
    
    def hide_stack(self) -> None:
        """
        Ocultar el stack expandido actual.
        
        Usa altura 0 en lugar de hide() para evitar transiciones visible/invisible.
        """
        self._current_stack_type = None
        self.setFixedHeight(0)
    
    def get_current_stack_type(self) -> Optional[str]:
        """Obtener el tipo de stack actualmente visible."""
        return self._current_stack_type
    
    def calculate_height(self, num_files: int, files_per_row: int) -> int:
        """
        Calcular altura necesaria para mostrar los archivos.
        
        Fórmula: (filas * altura_tile) + ((filas-1) * spacing) + margen_top + margen_bottom
        
        Args:
            num_files: Número de archivos.
            files_per_row: Archivos por fila.
            
        Returns:
            Altura en píxeles.
        """
        if num_files == 0 or files_per_row == 0:
            return 0
        
        num_rows = ceil(num_files / files_per_row)
        # Altura = tiles + spacing entre filas (no después de la última) + márgenes
        tiles_height = num_rows * self.TILE_HEIGHT
        spacing_height = max(0, num_rows - 1) * self.TILE_SPACING
        margins = self.MARGIN_TOP + self.MARGIN_BOTTOM
        
        return tiles_height + spacing_height + margins
    
    @classmethod
    def calculate_height_for_rows(cls, num_rows: int) -> int:
        """
        Calcular altura para un número dado de filas.
        
        Usado por emit_expansion_height para consistencia.
        """
        if num_rows <= 0:
            return 0
        
        tiles_height = num_rows * cls.TILE_HEIGHT
        spacing_height = max(0, num_rows - 1) * cls.TILE_SPACING
        margins = cls.MARGIN_TOP + cls.MARGIN_BOTTOM
        
        return tiles_height + spacing_height + margins
    
    def get_tiles_for_stack(self, stack_type: str) -> List[FileTile]:
        """Obtener tiles de un stack específico."""
        if stack_type in self._pages:
            return self._pages[stack_type].tiles
        return []
    
    def clear_all(self) -> None:
        """Eliminar todas las páginas y limpiar."""
        for page in self._pages.values():
            page.clear()
            self.removeWidget(page)
            page.deleteLater()
        
        self._pages.clear()
        self._current_stack_type = None
        self.hide()
    
    def remove_page(self, stack_type: str) -> None:
        """Eliminar una página específica."""
        if stack_type in self._pages:
            page = self._pages[stack_type]
            page.clear()
            self.removeWidget(page)
            page.deleteLater()
            del self._pages[stack_type]
            
            if self._current_stack_type == stack_type:
                self._current_stack_type = None
                self.hide()

