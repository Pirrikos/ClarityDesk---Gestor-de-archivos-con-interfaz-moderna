"""
WorkspaceManager - Manager for workspace containers.

Manages workspace list, active workspace, and coordinates state persistence.
WorkspaceManager is the owner of workspace state - it decides what to save and when.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import QObject, Signal, QModelIndex

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
        
        if not self._workspaces:
            default_workspace = self.create_workspace("Default")
            self._active_workspace_id = default_workspace.id
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
            expanded_nodes=[]
        )
        
        self._workspaces.append(workspace)
        self._save_workspaces_metadata()
        save_workspace_state(workspace_id, {
            'tabs': [],
            'active_tab': None,
            'focus_tree_paths': [],
            'expanded_nodes': []
        })
        
        self.workspace_created.emit(workspace_id)
        logger.info(f"Created workspace: {name} ({workspace_id})")
        
        return workspace
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete a workspace.
        
        Args:
            workspace_id: ID of workspace to delete.
        
        Returns:
            True if deleted, False if not found or is active workspace.
        """
        if workspace_id == self._active_workspace_id:
            logger.warning("Cannot delete active workspace")
            return False
        
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        self._workspaces = [w for w in self._workspaces if w.id != workspace_id]
        self._save_workspaces_metadata()
        
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
        
        # Cargar estado en TabManager sin emitir señales
        tab_manager.load_workspace_state({
            'tabs': tabs,
            'active_tab': active_tab
        }, emit_signals=False)
        
        # Reconstruir sidebar explícitamente una sola vez desde aquí
        # (El reseteo visual se hace dentro de restore_tree con señales bloqueadas)
        sidebar.load_workspace_state(focus_paths, expanded_nodes)
        
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
    
    def save_current_state(self, tab_manager: 'TabManager', sidebar: 'FolderTreeSidebar') -> None:
        """
        Save current workspace state.
        
        WorkspaceManager recopila estado de TabManager y Sidebar, luego persiste.
        
        Args:
            tab_manager: TabManager instance to get current state.
            sidebar: FolderTreeSidebar instance to get current state.
        """
        if not self._active_workspace_id:
            return
        
        # Recopilar estado de TabManager
        tab_state = tab_manager.get_current_state()
        
        # Recopilar estado de Sidebar
        sidebar_paths, sidebar_expanded = sidebar.get_current_state()
        
        # Construir estado completo
        state = {
            'tabs': tab_state.get('tabs', []),
            'active_tab': tab_state.get('active_tab'),
            'focus_tree_paths': sidebar_paths,
            'expanded_nodes': sidebar_expanded
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
            'expanded_nodes': state.get('expanded_nodes', [])
        }

