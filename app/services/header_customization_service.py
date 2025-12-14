"""
HeaderCustomizationService - Header customization configuration management.

Manages reading and writing persistent header customization to JSON storage.
Currently uses global configuration (same for all workspaces).
Design allows future extension to per-workspace configuration without major refactoring.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any


class HeaderCustomizationService:
    """Service for header customization configuration management."""
    
    # Lista cerrada de controles válidos
    VALID_CONTROLS = {
        # Navegación
        "back", "forward",
        # Vista y organización
        "view", "sort", "group",
        # Búsqueda
        "search",
        # Selección / acciones
        "states", "rename", "duplicate", "delete", "info", "share",
        # Creación
        "new_folder",
        # Paneles
        "breadcrumb", "preview_panel",
        # Estructura
        "separator", "flexible_space"
    }
    
    # Controles obligatorios mínimos (al menos uno debe estar presente)
    REQUIRED_NAVIGATION_CONTROLS = {"back", "forward"}
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize HeaderCustomizationService with storage path.
        
        Args:
            config_path: Optional path to config file. If None, uses default global path.
                        Can be extended in the future to include workspace_id.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'storage' / 'header_config.json'
        
        self._config_path = Path(config_path)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default header configuration.
        
        Returns:
            Default configuration dict with items and version.
        """
        return {
            "items": ["back", "forward", "view", "search", "states"],
            "version": 1
        }
    
    def load_header_config(self) -> Dict[str, Any]:
        """
        Load header configuration from JSON file.
        
        Validates configuration and falls back to default if invalid.
        
        Returns:
            Configuration dict with items and version.
        """
        if not self._config_path.exists():
            return self.get_default_config()
        
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar versión
            if data.get("version") != 1:
                return self.get_default_config()
            
            items = data.get("items", [])
            
            # Validar que todos los ítems pertenezcan a la lista cerrada
            if not all(item in self.VALID_CONTROLS for item in items):
                return self.get_default_config()
            
            # Validar no duplicados
            if len(items) != len(set(items)):
                return self.get_default_config()
            
            # Validar controles obligatorios mínimos
            if not self._has_required_navigation(items):
                return self.get_default_config()
            
            return data
        except (json.JSONDecodeError, IOError, OSError, KeyError, TypeError):
            return self.get_default_config()
    
    def save_header_config(self, config: Dict[str, Any]) -> bool:
        """
        Save header configuration to JSON file.
        
        Validates configuration before saving.
        
        Args:
            config: Configuration dict with items and version.
        
        Returns:
            True if saved successfully, False otherwise.
        """
        # Validar configuración antes de guardar
        if not self._validate_config(config):
            return False
        
        try:
            # Atomic write: escribir a archivo temporal y luego renombrar
            temp_path = self._config_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Renombrar atómicamente
            temp_path.replace(self._config_path)
            return True
        except (IOError, OSError):
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate header configuration.
        
        Args:
            config: Configuration dict to validate.
        
        Returns:
            True if valid, False otherwise.
        """
        # Validar estructura básica
        if not isinstance(config, dict):
            return False
        
        if "version" not in config or config["version"] != 1:
            return False
        
        if "items" not in config or not isinstance(config["items"], list):
            return False
        
        items = config["items"]
        
        # Validar lista cerrada
        if not all(item in self.VALID_CONTROLS for item in items):
            return False
        
        # Validar no duplicados
        if len(items) != len(set(items)):
            return False
        
        # Validar controles obligatorios mínimos
        if not self._has_required_navigation(items):
            return False
        
        return True
    
    def _has_required_navigation(self, items: List[str]) -> bool:
        """
        Check if configuration has at least one required navigation control.
        
        Args:
            items: List of control IDs.
        
        Returns:
            True if at least one navigation control is present.
        """
        return bool(self.REQUIRED_NAVIGATION_CONTROLS & set(items))
    
    def get_valid_control_ids(self) -> set:
        """
        Get set of valid control IDs.
        
        Returns:
            Set of valid control ID strings.
        """
        return self.VALID_CONTROLS.copy()
    
    def can_remove_control(self, control_id: str, current_items: List[str]) -> tuple[bool, Optional[str]]:
        """
        Check if a control can be removed from configuration.
        
        Args:
            control_id: ID of control to remove.
            current_items: Current list of items in configuration.
        
        Returns:
            Tuple of (can_remove: bool, error_message: Optional[str]).
        """
        if control_id not in current_items:
            return False, "Control no está en la configuración"
        
        # Verificar si es un control de navegación obligatorio
        if control_id in self.REQUIRED_NAVIGATION_CONTROLS:
            # Verificar si quedaría al menos uno después de remover
            remaining_items = [item for item in current_items if item != control_id]
            if not self._has_required_navigation(remaining_items):
                return False, "Debe permanecer al menos un control de navegación (Atrás o Adelante)"
        
        return True, None

