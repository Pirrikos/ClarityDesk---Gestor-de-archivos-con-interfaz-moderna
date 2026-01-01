"""
StateLabelManager - Manager for custom state label names.

Orchestrates state label management: persistence + UI updates.
Emits signals to notify UI of label changes.
"""

from typing import Dict, List, Optional

from PySide6.QtCore import QObject, Signal

from app.services.state_label_storage import (
    get_custom_label,
    load_custom_labels,
    load_state_order,
    remove_custom_label,
    save_state_order,
    set_custom_label,
)
from app.ui.widgets.state_badge_widget import (
    STATE_CORRECTED,
    STATE_DELIVERED,
    STATE_LABELS,
    STATE_PENDING,
    STATE_REVIEW,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class StateLabelManager(QObject):
    """Manager for custom state label names with persistence and UI updates."""
    
    # Valid state constants (centralized to avoid duplication)
    _VALID_STATES = [STATE_PENDING, STATE_DELIVERED, STATE_CORRECTED, STATE_REVIEW]
    
    # Signal emitted when labels change
    labels_changed = Signal()  # Emitted when any label is renamed
    state_label_changed = Signal(str)  # Emitted when a specific state label is renamed (state_id)
    
    def __init__(self):
        """Initialize manager and load custom labels and order."""
        super().__init__()
        self._custom_labels: Dict[str, str] = {}
        self._state_order: List[str] = []
        self._load_custom_labels()
        self._load_state_order()
    
    def _load_custom_labels(self) -> None:
        """Load custom labels from storage."""
        self._custom_labels = load_custom_labels()
    
    def _load_state_order(self) -> None:
        """Load state order from storage."""
        self._state_order = load_state_order()
    
    def get_label(self, state: str) -> str:
        """
        Get display label for a state constant.
        
        Args:
            state: State constant (e.g., STATE_PENDING).
            
        Returns:
            Custom label if exists, otherwise default label.
        """
        if state in self._custom_labels:
            return self._custom_labels[state]
        return STATE_LABELS.get(state, state.upper())
    
    def get_all_labels(self) -> Dict[str, str]:
        """
        Get all state labels (custom + defaults).
        
        Returns:
            Dictionary mapping state constants to display labels.
        """
        result = {}
        for state in self._VALID_STATES:
            result[state] = self.get_label(state)
        return result
    
    def rename_label(self, state: str, new_label: str) -> tuple[bool, Optional[str]]:
        """
        Rename a state label.
        
        Args:
            state: State constant to rename.
            new_label: New label name.
            
        Returns:
            Tuple of (success, error_message).
            error_message is None on success.
        """
        # Validate state constant
        if state not in self._VALID_STATES:
            return False, f"Estado inválido: {state}"
        
        # Validate label not empty
        new_label = new_label.strip()
        if not new_label:
            return False, "El nombre de la etiqueta no puede estar vacío."
        # Validate length <= 15 (including spaces)
        if len(new_label) > 15:
            return False, "El nombre de la etiqueta debe tener como máximo 15 caracteres."
        
        # Check for duplicate labels (case-insensitive)
        current_labels = self.get_all_labels()
        for other_state, other_label in current_labels.items():
            if other_state != state and other_label.lower() == new_label.lower():
                return False, f"Ya existe una etiqueta con el nombre '{other_label}'."
        
        # Save custom label
        if not set_custom_label(state, new_label):
            return False, "Error al guardar la etiqueta personalizada."
        
        # Update cache
        self._custom_labels[state] = new_label
        
        # Emit signals for UI update
        self.labels_changed.emit()
        self.state_label_changed.emit(state)
        
        logger.info(f"State label renamed: {state} -> {new_label}")
        return True, None
    
    def reset_label(self, state: str) -> bool:
        """
        Reset a state label to default.
        
        Args:
            state: State constant to reset.
            
        Returns:
            True if reset successfully, False otherwise.
        """
        if state not in self._custom_labels:
            return True  # Already using default
        
        if not remove_custom_label(state):
            return False
        
        # Update cache
        self._custom_labels.pop(state, None)
        
        # Emit signals for UI update
        self.labels_changed.emit()
        self.state_label_changed.emit(state)
        
        logger.info(f"State label reset to default: {state}")
        return True
    
    def has_custom_label(self, state: str) -> bool:
        """Check if state has a custom label."""
        return state in self._custom_labels
    
    def refresh_from_storage(self) -> bool:
        """
        Reload custom labels from storage and emit signal if changed.
        
        Returns:
            True if labels changed, False otherwise.
        """
        old_labels = self._custom_labels.copy()
        old_order = self._state_order.copy()
        self._load_custom_labels()
        self._load_state_order()
        
        if old_labels != self._custom_labels or old_order != self._state_order:
            self.labels_changed.emit()
            logger.info("State labels refreshed from storage")
            return True
        return False
    
    def get_states_in_order(self) -> List[str]:
        """
        Get all states in their display order.
        
        Returns:
            List of state constants in display order.
        """
        return self._state_order.copy()
    
    def reorder_states(self, new_order: List[str]) -> bool:
        """
        Reorder states and persist the new order.
        
        Args:
            new_order: List of state constants in new display order.
            
        Returns:
            True if reordered successfully, False otherwise.
        """
        # Validar que todos los estados están presentes
        if set(new_order) != set(self._VALID_STATES):
            logger.error("Invalid state order: missing or extra states")
            return False
        
        # Guardar nuevo orden
        if not save_state_order(new_order):
            return False
        
        # Actualizar cache
        self._state_order = new_order.copy()
        
        # Emitir signal para actualizar UI
        self.labels_changed.emit()
        
        logger.info(f"State order updated: {new_order}")
        return True
