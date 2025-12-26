"""
FolderTreeStateManager - Gestión de estado y selección del sidebar.

Maneja la lógica de selección única entre estados y carpetas.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QTreeView

from app.ui.widgets.state_section_widget import StateSectionWidget

if TYPE_CHECKING:
    from app.managers.tab_manager import TabManager


class FolderTreeStateManager:
    """Gestiona el estado de selección del sidebar (estados vs carpetas)."""
    
    def __init__(
        self,
        tree_view: QTreeView,
        state_section: Optional[StateSectionWidget] = None,
        tab_manager: Optional["TabManager"] = None
    ):
        self._tree_view = tree_view
        self._state_section = state_section
        self._tab_manager = tab_manager
        # Guard de reentrancia: previene que cambios programáticos disparen handlers de usuario
        self._is_syncing_sidebar_selection = False
    
    def clear_tree_selection(self) -> None:
        """Limpiar selección del árbol de carpetas."""
        if not self._tree_view:
            return
        
        # Guard de reentrancia: si ya estamos sincronizando, no hacer nada
        if self._is_syncing_sidebar_selection:
            return
        
        self._is_syncing_sidebar_selection = True
        
        try:
            # Bloquear señales para evitar que cambios programáticos disparen handlers
            self._tree_view.blockSignals(True)
            try:
                self._tree_view.clearSelection()
                self._tree_view.setCurrentIndex(QModelIndex())
                selection_model = self._tree_view.selectionModel()
                if selection_model:
                    selection_model.clearSelection()
                    selection_model.clearCurrentIndex()
            finally:
                self._tree_view.blockSignals(False)
        finally:
            self._is_syncing_sidebar_selection = False
    
    def clear_state_selection(self, from_user_action: bool = False) -> None:
        """
        Limpiar selección del estado activo.
        
        Args:
            from_user_action: Si True, viene de acción del usuario (no activar guard).
        """
        if not self._state_section:
            return
        
        # Si viene de acción del usuario, no activar guard (permite navegación)
        if from_user_action:
            self._state_section.set_active_state(None)
            return
        
        # Guard de reentrancia: si ya estamos sincronizando, no hacer nada
        if self._is_syncing_sidebar_selection:
            return
        
        self._is_syncing_sidebar_selection = True
        
        try:
            self._state_section.set_active_state(None)
        finally:
            self._is_syncing_sidebar_selection = False
    
    def on_state_selected(self, state: str) -> None:
        """
        Manejar selección de estado desde StateSectionWidget.
        
        REGLA OBLIGATORIA: Solo puede existir un único item activo en todo el sidebar.
        Seleccionar un estado debe desactivar explícitamente todos los demás.
        
        NAVEGACIÓN: Este método se llama desde click del usuario, NO es sync visual.
        """
        self.clear_tree_selection()
        if self._state_section:
            self._state_section.set_active_state(state)
    
    def on_tab_changed(self, index: int, path: str = None) -> None:
        """
        Manejar cambio de tab para actualizar estado activo.
        
        REGLA OBLIGATORIA: Solo puede existir un único item activo en todo el sidebar.
        
        SYNC VISUAL: Este método sincroniza la selección visual basándose en el estado
        actual de TabManager. NO dispara navegación, solo actualiza la vista.
        La navegación la controla TabManager (folder_selected signal o set_state_context).
        """
        if not self._state_section or not self._tab_manager:
            return
        
        # Guard de reentrancia: si ya estamos sincronizando, no hacer nada
        if self._is_syncing_sidebar_selection:
            return
        
        self._is_syncing_sidebar_selection = True
        
        try:
            if self._tab_manager.has_state_context():
                active_state = self._tab_manager.get_state_context()
                self._state_section.set_active_state(active_state)
                # SOLO aquí limpiamos el árbol cuando se activa un estado
                self.clear_tree_selection()
            else:
                # Volvemos a modo carpeta
                self._state_section.set_active_state(None)
                # NO limpiar el árbol aquí - la selección del árbol la controla el propio click del usuario
        finally:
            self._is_syncing_sidebar_selection = False

