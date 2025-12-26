"""
Tests para StateLabelManager.

Cubre gestión de etiquetas de estado, persistencia y señales Qt.
"""

import tempfile
from unittest.mock import patch, MagicMock

import pytest
from PySide6.QtCore import QObject

from app.managers.state_label_manager import StateLabelManager
from app.ui.widgets.state_badge_widget import (
    STATE_PENDING,
    STATE_DELIVERED,
    STATE_CORRECTED,
    STATE_REVIEW,
)


@pytest.fixture
def state_label_manager(qapp, monkeypatch):
    """Crear instancia de StateLabelManager para tests."""
    # Mockear storage para usar directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    # Mock de storage functions
    custom_labels = {}
    
    def mock_load_custom_labels():
        return custom_labels.copy()
    
    def mock_set_custom_label(state, label):
        custom_labels[state] = label
        return True
    
    def mock_get_custom_label(state):
        return custom_labels.get(state)
    
    def mock_remove_custom_label(state):
        if state in custom_labels:
            del custom_labels[state]
            return True
        return True
    
    monkeypatch.setattr(
        'app.services.state_label_storage.load_custom_labels',
        mock_load_custom_labels
    )
    monkeypatch.setattr(
        'app.services.state_label_storage.set_custom_label',
        mock_set_custom_label
    )
    monkeypatch.setattr(
        'app.services.state_label_storage.get_custom_label',
        mock_get_custom_label
    )
    monkeypatch.setattr(
        'app.services.state_label_storage.remove_custom_label',
        mock_remove_custom_label
    )
    
    manager = StateLabelManager()
    
    yield manager
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass


class TestGetLabel:
    """Tests para get_label."""
    
    def test_get_label_default(self, state_label_manager):
        """Obtener etiqueta por defecto."""
        label = state_label_manager.get_label(STATE_PENDING)
        
        assert isinstance(label, str)
        assert len(label) > 0
    
    def test_get_label_custom(self, state_label_manager):
        """Obtener etiqueta personalizada."""
        state_label_manager.rename_label(STATE_PENDING, "Personalizado")
        
        label = state_label_manager.get_label(STATE_PENDING)
        
        assert label == "Personalizado"
    
    def test_get_label_all_states(self, state_label_manager):
        """Obtener etiquetas para todos los estados."""
        labels = {
            STATE_PENDING: state_label_manager.get_label(STATE_PENDING),
            STATE_DELIVERED: state_label_manager.get_label(STATE_DELIVERED),
            STATE_CORRECTED: state_label_manager.get_label(STATE_CORRECTED),
            STATE_REVIEW: state_label_manager.get_label(STATE_REVIEW),
        }
        
        assert all(isinstance(label, str) and len(label) > 0 for label in labels.values())


class TestGetAllLabels:
    """Tests para get_all_labels."""
    
    def test_get_all_labels_success(self, state_label_manager):
        """Obtener todas las etiquetas exitosamente."""
        labels = state_label_manager.get_all_labels()
        
        assert isinstance(labels, dict)
        assert STATE_PENDING in labels
        assert STATE_DELIVERED in labels
        assert STATE_CORRECTED in labels
        assert STATE_REVIEW in labels
    
    def test_get_all_labels_includes_custom(self, state_label_manager):
        """Validar que incluye etiquetas personalizadas."""
        state_label_manager.rename_label(STATE_PENDING, "Custom Pending")
        
        labels = state_label_manager.get_all_labels()
        
        assert labels[STATE_PENDING] == "Custom Pending"


class TestRenameLabel:
    """Tests para rename_label."""
    
    def test_rename_label_success(self, state_label_manager):
        """Renombrar etiqueta exitosamente."""
        success, error = state_label_manager.rename_label(STATE_PENDING, "Nuevo Nombre")
        
        assert success is True
        assert error is None
        assert state_label_manager.get_label(STATE_PENDING) == "Nuevo Nombre"
    
    def test_rename_label_empty_name(self, state_label_manager):
        """Renombrar con nombre vacío."""
        success, error = state_label_manager.rename_label(STATE_PENDING, "")
        
        assert success is False
        assert error is not None
        assert "vacío" in error.lower()
    
    def test_rename_label_invalid_state(self, state_label_manager):
        """Renombrar con estado inválido."""
        success, error = state_label_manager.rename_label("invalid_state", "New Name")
        
        assert success is False
        assert error is not None
    
    def test_rename_label_duplicate(self, state_label_manager):
        """Renombrar con nombre duplicado."""
        state_label_manager.rename_label(STATE_PENDING, "Same Name")
        
        success, error = state_label_manager.rename_label(STATE_DELIVERED, "Same Name")
        
        assert success is False
        assert error is not None
        assert "existe" in error.lower()
    
    def test_rename_label_emits_signal(self, state_label_manager):
        """Validar que emite señal labels_changed."""
        signal_received = []
        
        def on_labels_changed():
            signal_received.append(True)
        
        state_label_manager.labels_changed.connect(on_labels_changed)
        state_label_manager.rename_label(STATE_PENDING, "New Name")
        
        assert len(signal_received) == 1


class TestResetLabel:
    """Tests para reset_label."""
    
    def test_reset_label_success(self, state_label_manager):
        """Resetear etiqueta exitosamente."""
        state_label_manager.rename_label(STATE_PENDING, "Custom")
        
        success = state_label_manager.reset_label(STATE_PENDING)
        
        assert success is True
        # Debe volver a etiqueta por defecto
        label = state_label_manager.get_label(STATE_PENDING)
        assert label != "Custom"
    
    def test_reset_label_no_custom(self, state_label_manager):
        """Resetear etiqueta sin personalización."""
        success = state_label_manager.reset_label(STATE_PENDING)
        
        assert success is True
    
    def test_reset_label_emits_signal(self, state_label_manager):
        """Validar que emite señal al resetear."""
        state_label_manager.rename_label(STATE_PENDING, "Custom")
        
        signal_received = []
        
        def on_labels_changed():
            signal_received.append(True)
        
        state_label_manager.labels_changed.connect(on_labels_changed)
        state_label_manager.reset_label(STATE_PENDING)
        
        assert len(signal_received) == 1


class TestHasCustomLabel:
    """Tests para has_custom_label."""
    
    def test_has_custom_label_true(self, state_label_manager):
        """Validar que tiene etiqueta personalizada."""
        state_label_manager.rename_label(STATE_PENDING, "Custom")
        
        assert state_label_manager.has_custom_label(STATE_PENDING) is True
    
    def test_has_custom_label_false(self, state_label_manager, monkeypatch):
        """Validar que no tiene etiqueta personalizada."""
        # Asegurar que no hay etiquetas personalizadas
        state_label_manager._custom_labels.clear()
        assert state_label_manager.has_custom_label(STATE_PENDING) is False
    
    def test_has_custom_label_after_reset(self, state_label_manager):
        """Validar que no tiene etiqueta personalizada después de reset."""
        state_label_manager.rename_label(STATE_PENDING, "Custom")
        state_label_manager.reset_label(STATE_PENDING)
        
        assert state_label_manager.has_custom_label(STATE_PENDING) is False


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_rename_multiple_labels(self, state_label_manager):
        """Renombrar múltiples etiquetas."""
        state_label_manager.rename_label(STATE_PENDING, "Pending Custom")
        state_label_manager.rename_label(STATE_DELIVERED, "Delivered Custom")
        
        assert state_label_manager.get_label(STATE_PENDING) == "Pending Custom"
        assert state_label_manager.get_label(STATE_DELIVERED) == "Delivered Custom"
    
    def test_case_insensitive_duplicate_check(self, state_label_manager):
        """Validar que la verificación de duplicados es case-insensitive."""
        state_label_manager.rename_label(STATE_PENDING, "Same Name")
        
        success, error = state_label_manager.rename_label(STATE_DELIVERED, "SAME NAME")
        
        assert success is False
        assert "existe" in error.lower()

