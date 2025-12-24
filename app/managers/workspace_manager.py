"""
WorkspaceManager - Manager for workspace containers.

Manages workspace list, active workspace, and coordinates state persistence.
WorkspaceManager is the owner of workspace state - it decides what to save and when.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import QObject, Signal

from app.core.logger import get_logger
from app.models.workspace import Workspace
from app.services.workspace_storage_service import (
    load_workspaces,
    save_workspaces,
    load_workspace_state,
    save_workspace_state,
    get_active_workspace_id
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.managers.tab_manager import TabManager
    from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar


class WorkspaceManager(QObject):
    """Manages workspaces and coordinates state persistence."""
    
    workspace_changed = Signal(str)  # Emitted when active workspace changes (workspace_id)
    workspace_created = Signal(str)  # Emitted when workspace is created (workspace_id)
    workspace_deleted = Signal(str)  # Emitted when workspace is deleted (workspace_id)
    view_mode_changed = Signal(str)  # Emitted when view mode changes (view_mode: "grid" | "list")
    
    def __init__(self):
        """Initialize WorkspaceManager and load workspaces."""
        super().__init__()
        self._workspaces: List[Workspace] = []
        self._active_workspace_id: Optional[str] = None
        self._load_workspaces()
    
    def _load_workspaces(self) -> None:
        """Load workspaces from storage."""
        self._workspaces = load_workspaces()
        self._active_workspace_id = get_active_workspace_id()
        
        # Validar que active_workspace_id existe en la lista de workspaces
        state_corrected = False
        if self._active_workspace_id:
            workspace_exists = any(w.id == self._active_workspace_id for w in self._workspaces)
            if not workspace_exists:
                logger.warning(f"Active workspace ID {self._active_workspace_id} not found, resetting to None")
                self._active_workspace_id = None
                state_corrected = True
        
        if not self._workspaces:
            default_workspace = self.create_workspace("Default")
            self._active_workspace_id = default_workspace.id
            state_corrected = True
        elif not self._active_workspace_id and self._workspaces:
            # Si hay workspaces pero no hay activo, seleccionar el primero
            self._active_workspace_id = self._workspaces[0].id
            logger.info(f"Auto-selected first workspace: {self._workspaces[0].name}")
            state_corrected = True
        
        # Persistir solo si se ha corregido el estado
        if state_corrected:
            self._save_workspaces_metadata()
    
    def _save_workspaces_metadata(self) -> None:
        """Save workspaces metadata to storage."""
        save_workspaces(self._workspaces, self._active_workspace_id)
    
    def create_workspace(self, name: str) -> Workspace:
        """
        Create a new workspace.
        
        Args:
            name: Name of the workspace.
        
        Returns:
            Created Workspace instance.
        """
        workspace_id = str(uuid.uuid4())
        workspace = Workspace(
            id=workspace_id,
            name=name,
            tabs=[],
            active_tab=None,
            focus_tree_paths=[],
            expanded_nodes=[],
            view_mode="grid"
        )
        
        self._workspaces.append(workspace)
        self._save_workspaces_metadata()
        save_workspace_state(workspace_id, {
            'tabs': [],
            'active_tab': None,
            'focus_tree_paths': [],
            'expanded_nodes': [],
            'root_folders_order': [],
            'view_mode': 'grid'
        })
        
        self.workspace_created.emit(workspace_id)
        logger.info(f"Created workspace: {name} ({workspace_id})")
        
        return workspace
    
    def rename_workspace(self, workspace_id: str, new_name: str) -> bool:
        """
        Rename a workspace.
        
        Args:
            workspace_id: ID of workspace to rename.
            new_name: New name for the workspace.
        
        Returns:
            True if renamed successfully, False if workspace not found or name is empty.
        """
        if not new_name or not new_name.strip():
            logger.warning("Cannot rename workspace: empty name")
            return False
        
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            logger.error(f"Workspace not found: {workspace_id}")
            return False
        
        old_name = workspace.name
        workspace.name = new_name.strip()
        
        # Persistir cambios en metadatos
        self._save_workspaces_metadata()
        
        logger.info(f"Renamed workspace from '{old_name}' to '{new_name.strip()}' ({workspace_id})")
        return True
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete a workspace.
        
        Si es el workspace activo, cambia automáticamente a otro workspace válido
        antes de eliminar. Si es el único workspace, crea uno por defecto.
        
        Args:
            workspace_id: ID of workspace to delete.
        
        Returns:
            True if deleted, False if not found.
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        is_active = workspace_id == self._active_workspace_id
        other_workspaces = [w for w in self._workspaces if w.id != workspace_id]
        
        # Si es el activo y hay otros workspaces, cambiar al primero antes de eliminar
        if is_active and other_workspaces:
            self._active_workspace_id = other_workspaces[0].id
            logger.info(f"Switched to workspace {other_workspaces[0].name} before deleting active workspace")
        # Si es el activo y es el único, resetear a None (se creará uno por defecto después)
        elif is_active and not other_workspaces:
            self._active_workspace_id = None
        
        # Eliminar workspace de la lista
        self._workspaces = [w for w in self._workspaces if w.id != workspace_id]
        
        # Si no quedan workspaces, crear uno por defecto
        if not self._workspaces:
            default_workspace = self.create_workspace("Default")
            self._active_workspace_id = default_workspace.id
        
        self._save_workspaces_metadata()
        
        # Eliminar archivo de estado
        try:
            from app.services.workspace_storage_service import get_workspace_state_file
            state_file = get_workspace_state_file(workspace_id)
            if state_file.exists():
                state_file.unlink()
        except Exception as e:
            logger.error(f"Error deleting workspace state file: {e}")
        
        self.workspace_deleted.emit(workspace_id)
        logger.info(f"Deleted workspace: {workspace_id}")
        
        return True
    
    def switch_workspace(self, workspace_id: str, tab_manager: 'TabManager', sidebar: 'FolderTreeSidebar', signal_controller=None) -> bool:
        """
        Switch to a different workspace.
        
        WorkspaceManager saves current state before switching.
        During switch, temporarily disables signal reactions to prevent multiple UI updates.
        
        Args:
            workspace_id: ID of workspace to switch to.
            tab_manager: TabManager instance to get/set state.
            sidebar: FolderTreeSidebar instance to get/set state.
            signal_controller: Optional object with disconnect_signals() and reconnect_signals() methods.
        
        Returns:
            True if switched successfully, False otherwise.
        """
        if workspace_id == self._active_workspace_id:
            return True
        
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            logger.error(f"Workspace not found: {workspace_id}")
            return False
        
        # Save current workspace state before switching
        if self._active_workspace_id:
            self.save_current_state(tab_manager, sidebar)
        
        # Load new workspace state (puede ser None si es workspace nuevo)
        state = load_workspace_state(workspace_id)
        
        # Update active workspace
        self._active_workspace_id = workspace_id
        self._save_workspaces_metadata()
        
        # Desconectar señales temporalmente para evitar reacciones durante el cambio
        if signal_controller and hasattr(signal_controller, 'disconnect_signals'):
            signal_controller.disconnect_signals()
        
        # Preparar estado con valores por defecto (evita duplicación de if state)
        tabs = state.get('tabs', []) if state else []
        active_tab = state.get('active_tab') if state else None
        focus_paths = state.get('focus_tree_paths', []) if state else []
        expanded_nodes = state.get('expanded_nodes', []) if state else []
        root_folders_order = state.get('root_folders_order') if state else None
        view_mode = state.get('view_mode', 'grid') if state else 'grid'
        workspace.view_mode = view_mode
        
        # Cargar estado en TabManager sin emitir señales
        tab_manager.load_workspace_state({
            'tabs': tabs,
            'active_tab': active_tab
        }, emit_signals=False)
        
        # Reconstruir sidebar explícitamente una sola vez desde aquí
        # (El reseteo visual se hace dentro de restore_tree con señales bloqueadas)
        sidebar.load_workspace_state(focus_paths, expanded_nodes, root_folders_order)
        
        # Reconectar señales
        if signal_controller and hasattr(signal_controller, 'reconnect_signals'):
            signal_controller.reconnect_signals()
        
        # Emitir única señal final activeTabChanged para actualizar vista
        if tab_manager.get_active_index() >= 0 and tab_manager.get_active_index() < len(tab_manager.get_tabs()):
            active_path = tab_manager.get_tabs()[tab_manager.get_active_index()]
            tab_manager._watch_and_emit_internal(active_path)
        else:
            # Si NO hay tab activo válido, vaciar explícitamente la vista central
            if signal_controller and hasattr(signal_controller, 'clear_file_view'):
                signal_controller.clear_file_view()
        
        # Emit signal with workspace state
        self.workspace_changed.emit(workspace_id)
        
        logger.info(f"Switched to workspace: {workspace.name} ({workspace_id})")
        
        return True
    
    def save_current_state(self, tab_manager: 'TabManager', sidebar: 'FolderTreeSidebar', view_mode: Optional[str] = None) -> None:
        """
        Save current workspace state.
        
        WorkspaceManager recopila estado de TabManager y Sidebar, luego persiste.
        
        Args:
            tab_manager: TabManager instance to get current state.
            sidebar: FolderTreeSidebar instance to get current state.
            view_mode: Optional view mode to save. If None, uses current workspace view_mode.
        """
        if not self._active_workspace_id:
            return
        
        # Recopilar estado de TabManager
        tab_state = tab_manager.get_current_state()
        
        # Recopilar estado de Sidebar
        sidebar_paths, sidebar_expanded = sidebar.get_current_state()
        root_folders_order = sidebar.get_root_folders_order()
        
        if view_mode is None:
            workspace = self.get_active_workspace()
            view_mode = workspace.view_mode if workspace else "grid"
        
        # Construir estado completo
        state = {
            'tabs': tab_state.get('tabs', []),
            'active_tab': tab_state.get('active_tab'),
            'focus_tree_paths': sidebar_paths,
            'expanded_nodes': sidebar_expanded,
            'root_folders_order': root_folders_order,
            'view_mode': view_mode
        }
        
        # Persistir estado
        save_workspace_state(self._active_workspace_id, state)
        
        # Actualizar workspace en memoria
        workspace = self.get_active_workspace()
        if workspace:
            workspace.tabs = state['tabs']
            workspace.active_tab = state['active_tab']
            workspace.focus_tree_paths = state['focus_tree_paths']
            workspace.expanded_nodes = state['expanded_nodes']
            workspace.view_mode = state['view_mode']
        
        # Persistir también el active_workspace_id en metadatos
        self._save_workspaces_metadata()
        
        logger.debug(f"Saved workspace state: {self._active_workspace_id}")
    
    def get_active_workspace(self) -> Optional[Workspace]:
        """
        Get currently active workspace.
        
        Returns:
            Active Workspace instance or None.
        """
        if not self._active_workspace_id:
            return None
        
        return self.get_workspace(self._active_workspace_id)
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """
        Get workspace by ID.
        
        Args:
            workspace_id: ID of workspace.
        
        Returns:
            Workspace instance or None if not found.
        """
        for workspace in self._workspaces:
            if workspace.id == workspace_id:
                return workspace
        return None
    
    def get_workspaces(self) -> List[Workspace]:
        """
        Get list of all workspaces.
        
        Returns:
            List of Workspace instances.
        """
        return self._workspaces.copy()
    
    def get_active_workspace_id(self) -> Optional[str]:
        """
        Get ID of active workspace.
        
        Returns:
            Workspace ID or None.
        """
        return self._active_workspace_id
    
    def get_workspace_state(self, workspace_id: str) -> Optional[dict]:
        """
        Get state of a workspace.
        
        Args:
            workspace_id: ID of workspace.
        
        Returns:
            State dict or None if not found.
        """
        state = load_workspace_state(workspace_id)
        if state is None:
            return None
        
        return {
            'tabs': state.get('tabs', []),
            'active_tab': state.get('active_tab'),
            'focus_tree_paths': state.get('focus_tree_paths', []),
            'expanded_nodes': state.get('expanded_nodes', []),
            'view_mode': state.get('view_mode', 'grid')
        }
    
    def set_view_mode(self, view_mode: str) -> bool:
        """
        Update view mode for active workspace and persist it.
        
        Args:
            view_mode: "grid" or "list"
        
        Returns:
            True if updated successfully, False if no active workspace or invalid mode.
        """
        if view_mode not in ("grid", "list"):
            logger.warning(f"Invalid view_mode: {view_mode}")
            return False
        
        if not self._active_workspace_id:
            return False
        
        workspace = self.get_active_workspace()
        if not workspace:
            return False
        
        workspace.view_mode = view_mode
        
        # Persistir inmediatamente
        state = load_workspace_state(self._active_workspace_id)
        if state:
            state['view_mode'] = view_mode
            save_workspace_state(self._active_workspace_id, state)
        
        self.view_mode_changed.emit(view_mode)
        logger.debug(f"Updated view_mode to {view_mode} for workspace {self._active_workspace_id}")
        
        return True
    
    def get_view_mode(self) -> str:
        """
        Get view mode for active workspace.
        
        Returns:
            "grid" or "list", defaults to "grid" if no active workspace.
        """
        workspace = self.get_active_workspace()
        if not workspace:
            return "grid"
        return workspace.view_mode

