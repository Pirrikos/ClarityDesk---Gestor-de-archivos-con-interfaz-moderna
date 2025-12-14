"""
GridContentWidget - Content widget for grid view that handles drag-in.

Widget that contains the grid layout and handles file drop events.
"""

from typing import Optional, Tuple, TYPE_CHECKING

from PySide6.QtCore import Qt, QSize, QTimer, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.managers.tab_manager import TabManager
from app.ui.widgets.drag_common import should_reject_dock_to_dock_drop
from app.ui.widgets.file_drop_handler import handle_file_drop

if TYPE_CHECKING:
    from app.ui.windows.desktop_window import DesktopWindow
    from app.ui.widgets.file_view_container import FileViewContainer


def _get_tab_manager_from_view(parent_view: 'FileGridView') -> Optional[TabManager]:
    """Get TabManager from parent_view or its parent hierarchy."""
    if hasattr(parent_view, '_tab_manager') and parent_view._tab_manager:
        return parent_view._tab_manager
    
    # Buscar tab_manager en el árbol de padres (FileViewContainer)
    parent = parent_view.parent()
    while parent:
        if hasattr(parent, '_tab_manager') and parent._tab_manager:
            return parent._tab_manager
        parent = parent.parent()
    
    return None


class GridContentWidget(QWidget):
    """Content widget for grid view that handles drag-in."""

    def __init__(self, parent_view: 'FileGridView', desktop_window: Optional['DesktopWindow'] = None):
        """
        Initialize content widget.
        
        Args:
            parent_view: FileGridView instance that contains this widget.
            desktop_window: Optional DesktopWindow instance (for Desktop Focus context).
        """
        super().__init__(parent_view)
        self._parent_view = parent_view
        self._desktop_window = desktop_window
        self.setAcceptDrops(True)
        
        # Remove any margins or padding
        self.setContentsMargins(0, 0, 0, 0)
        
        # Allow both horizontal and vertical expansion for proper scrolling
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum  # Minimum height based on content
        )
        # Ensure minimum size hint allows expansion
        self.setMinimumSize(0, 0)
    
    def _get_tab_manager(self) -> Optional[TabManager]:
        """Get TabManager from parent view hierarchy."""
        return _get_tab_manager_from_view(self._parent_view)
    
    def _find_container_in_hierarchy(self) -> Optional['FileViewContainer']:
        """Find FileViewContainer in parent hierarchy."""
        # Import local para evitar import circular
        from app.ui.widgets.file_view_container import FileViewContainer
        parent = self.parent()
        while parent:
            if isinstance(parent, FileViewContainer):
                return parent
            parent = parent.parent()
        return None
    
    def _get_tab_manager_and_container(self) -> Tuple[Optional[TabManager], Optional['FileViewContainer']]:
        """
        Get TabManager and FileViewContainer for current context.
        
        Works for both DesktopWindow and MainWindow contexts.
        DesktopWindow: usa referencia directa pasada en __init__.
        MainWindow: usa tab_manager del parent_view y busca container en jerarquía.
        
        Returns:
            Tuple of (tab_manager, container) or (None, None) if not found.
        """
        # Si tenemos referencia directa a DesktopWindow, usarla
        if self._desktop_window:
            # DesktopWindow siempre tiene estos atributos cuando está inicializado
            tab_manager = self._desktop_window._desktop_tab_manager
            container = self._desktop_window._desktop_container
            return tab_manager, container
        
        # Es MainWindow - usar el tab_manager del parent_view y buscar container
        tab_manager = self._get_tab_manager()
        container = self._find_container_in_hierarchy()
        return tab_manager, container
    
    def _update_view_after_drop(self, container: Optional['FileViewContainer']) -> None:
        """
        Actualizar vista después de procesar drop.
        
        Se llama con delay para asegurar que los archivos existen en el sistema de archivos.
        
        Args:
            container: FileViewContainer a actualizar, o None si no existe.
        """
        if container:
            from app.ui.widgets.file_view_sync import update_files
            update_files(container)
    
    def sizeHint(self) -> QSize:
        """Return size hint based on layout contents."""
        layout = self.layout()
        if layout:
            return layout.sizeHint()
        return super().sizeHint()
    
    def minimumSizeHint(self) -> QSize:
        """Return minimum size hint based on layout contents."""
        layout = self.layout()
        if layout:
            return layout.minimumSize()
        return super().minimumSizeHint()

    def _handle_drag_event(self, event: QDragEnterEvent | QDragMoveEvent, mime_data: QMimeData) -> bool:
        """
        Handle common drag event logic.
        
        Args:
            event: Drag event (QDragEnterEvent or QDragMoveEvent).
            mime_data: MIME data from event.
        
        Returns:
            True if event should be accepted, False otherwise.
        """
        if not mime_data.hasUrls():
            return False
        
        # Prevenir dock-to-dock drops
        tab_manager = self._get_tab_manager()
        if should_reject_dock_to_dock_drop(mime_data, tab_manager):
            return False
        
        # Fondo siempre acepta drops - usar MoveAction (equivalente a Explorador de Windows)
        event.setDropAction(Qt.DropAction.MoveAction)
        return True

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter for file drop - fondo siempre acepta drops."""
        if self._handle_drag_event(event, event.mimeData()):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move to maintain drop acceptance - fondo siempre acepta drops."""
        if self._handle_drag_event(event, event.mimeData()):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handle file and folder drop into grid view.
        
        REGLA GLOBAL: El fondo del grid SIEMPRE es un destino válido.
        Comportamiento equivalente al Explorador de Windows - mover archivos a la carpeta abierta.
        """
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            event.ignore()
            return
        
        # Obtener tab_manager y container (una sola vez)
        tab_manager, container = self._get_tab_manager_and_container()
        if not tab_manager:
            event.ignore()
            return
        
        # Prevenir dock-to-dock drops (usar tab_manager ya obtenido)
        if should_reject_dock_to_dock_drop(mime_data, tab_manager):
            event.ignore()
            return
        
        if not container:
            event.ignore()
            return
        
        # Procesar drops usando handle_file_drop (comportamiento uniforme)
        # La actualización de vista se maneja después de procesar todos los archivos
        moved_any = False
        
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path:
                try:
                    success, source_path, new_path = handle_file_drop(
                        file_path,
                        tab_manager,
                        None  # No usar callback - actualizamos vista después
                    )
                    if success:
                        moved_any = True
                except Exception as e:
                    # Continuar procesando otros archivos aunque uno falle
                    # Los errores se manejan internamente en handle_file_drop
                    pass
        
        # Actualizar vista después de un breve delay para asegurar que los archivos existen
        if moved_any:
            QTimer.singleShot(300, lambda: self._update_view_after_drop(container))
        
        # Aceptar el evento con MoveAction (equivalente a Explorador de Windows)
        # Incluso si hubo errores, aceptamos el evento para que Windows complete la operación
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

