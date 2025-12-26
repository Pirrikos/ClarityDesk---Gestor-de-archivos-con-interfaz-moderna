"""
Tests para TabHistoryManager.

Cubre gestión de historial de navegación, back/forward y actualización.
"""

import pytest

from app.services.tab_history_manager import TabHistoryManager


def normalize_path(path: str) -> str:
    """Función de normalización simple para tests."""
    return path.lower().replace('\\', '/')


@pytest.fixture
def history_manager():
    """Crear instancia de TabHistoryManager."""
    return TabHistoryManager()


class TestInitializeWithPath:
    """Tests para initialize_with_path."""
    
    def test_initialize_with_path_success(self, history_manager):
        """Inicializar con path exitosamente."""
        path = "/folder1"
        history_manager.initialize_with_path(path)
        
        assert len(history_manager.get_history()) == 1
        assert history_manager.get_history_index() == 0
        assert history_manager.get_history()[0] == path


class TestUpdateOnNavigate:
    """Tests para update_on_navigate."""
    
    def test_update_on_navigate_success(self, history_manager):
        """Actualizar historial al navegar exitosamente."""
        history_manager.initialize_with_path("/folder1")
        
        history_manager.update_on_navigate("/folder2", normalize_path)
        
        assert len(history_manager.get_history()) == 2
        assert history_manager.get_history_index() == 1
        assert history_manager.get_history()[1] == "/folder2"
    
    def test_update_on_navigate_same_path(self, history_manager):
        """No actualizar si navega al mismo path."""
        history_manager.initialize_with_path("/folder1")
        original_length = len(history_manager.get_history())
        
        history_manager.update_on_navigate("/folder1", normalize_path)
        
        assert len(history_manager.get_history()) == original_length
    
    def test_update_on_navigate_truncates_forward(self, history_manager):
        """Truncar historial forward al navegar."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        history_manager.update_on_navigate("/folder3", normalize_path)
        
        # Ir hacia atrás
        history_manager.move_back()
        
        # Navegar a nuevo path (debe truncar forward)
        history_manager.update_on_navigate("/folder4", normalize_path)
        
        assert len(history_manager.get_history()) == 3
        assert history_manager.get_history_index() == 2
        assert history_manager.get_history()[2] == "/folder4"
    
    def test_update_on_navigate_blocked_by_flag(self, history_manager):
        """No actualizar cuando flag de navegación está activo."""
        history_manager.initialize_with_path("/folder1")
        history_manager.set_navigating_flag(True)
        
        original_length = len(history_manager.get_history())
        history_manager.update_on_navigate("/folder2", normalize_path)
        
        assert len(history_manager.get_history()) == original_length


class TestCanGoBack:
    """Tests para can_go_back."""
    
    def test_can_go_back_true(self, history_manager):
        """Puede ir hacia atrás cuando hay historial."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        
        assert history_manager.can_go_back() is True
    
    def test_can_go_back_false_at_start(self, history_manager):
        """No puede ir hacia atrás al inicio."""
        history_manager.initialize_with_path("/folder1")
        
        assert history_manager.can_go_back() is False
    
    def test_can_go_back_false_empty(self, history_manager):
        """No puede ir hacia atrás con historial vacío."""
        assert history_manager.can_go_back() is False


class TestCanGoForward:
    """Tests para can_go_forward."""
    
    def test_can_go_forward_true(self, history_manager):
        """Puede ir hacia adelante cuando hay historial forward."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        history_manager.move_back()
        
        assert history_manager.can_go_forward() is True
    
    def test_can_go_forward_false_at_end(self, history_manager):
        """No puede ir hacia adelante al final."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        
        assert history_manager.can_go_forward() is False
    
    def test_can_go_forward_false_empty(self, history_manager):
        """No puede ir hacia adelante con historial vacío."""
        assert history_manager.can_go_forward() is False


class TestGetBackPath:
    """Tests para get_back_path."""
    
    def test_get_back_path_success(self, history_manager):
        """Obtener path hacia atrás exitosamente."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        
        back_path = history_manager.get_back_path()
        
        assert back_path == "/folder1"
    
    def test_get_back_path_error(self, history_manager):
        """Error al obtener path hacia atrás cuando no es posible."""
        history_manager.initialize_with_path("/folder1")
        
        with pytest.raises(IndexError):
            history_manager.get_back_path()


class TestGetForwardPath:
    """Tests para get_forward_path."""
    
    def test_get_forward_path_success(self, history_manager):
        """Obtener path hacia adelante exitosamente."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        history_manager.move_back()
        
        forward_path = history_manager.get_forward_path()
        
        assert forward_path == "/folder2"
    
    def test_get_forward_path_error(self, history_manager):
        """Error al obtener path hacia adelante cuando no es posible."""
        history_manager.initialize_with_path("/folder1")
        
        with pytest.raises(IndexError):
            history_manager.get_forward_path()


class TestMoveBack:
    """Tests para move_back."""
    
    def test_move_back_success(self, history_manager):
        """Mover hacia atrás exitosamente."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        
        path = history_manager.move_back()
        
        assert path == "/folder1"
        assert history_manager.get_history_index() == 0


class TestMoveForward:
    """Tests para move_forward."""
    
    def test_move_forward_success(self, history_manager):
        """Mover hacia adelante exitosamente."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        history_manager.move_back()
        
        path = history_manager.move_forward()
        
        assert path == "/folder2"
        assert history_manager.get_history_index() == 1


class TestRestoreHistory:
    """Tests para restore_history."""
    
    def test_restore_history_success(self, history_manager):
        """Restaurar historial exitosamente."""
        history = ["/folder1", "/folder2", "/folder3"]
        index = 1
        
        history_manager.restore_history(history, index)
        
        assert history_manager.get_history() == history
        assert history_manager.get_history_index() == index
    
    def test_restore_history_clamps_index(self, history_manager):
        """Ajustar índice fuera de rango al restaurar."""
        history = ["/folder1", "/folder2"]
        
        # Índice fuera de rango
        history_manager.restore_history(history, 10)
        assert history_manager.get_history_index() == 1
        
        # Índice negativo
        history_manager.restore_history(history, -5)
        assert history_manager.get_history_index() == 0
    
    def test_restore_history_empty(self, history_manager):
        """Restaurar historial vacío."""
        history_manager.restore_history([], -1)
        
        assert len(history_manager.get_history()) == 0
        assert history_manager.get_history_index() == -1


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_multiple_navigations(self, history_manager):
        """Múltiples navegaciones."""
        history_manager.initialize_with_path("/folder1")
        
        for i in range(5):
            history_manager.update_on_navigate(f"/folder{i+2}", normalize_path)
        
        assert len(history_manager.get_history()) == 6
        assert history_manager.get_history_index() == 5
    
    def test_back_and_forward_cycle(self, history_manager):
        """Ciclo completo de back y forward."""
        history_manager.initialize_with_path("/folder1")
        history_manager.update_on_navigate("/folder2", normalize_path)
        history_manager.update_on_navigate("/folder3", normalize_path)
        
        # Back
        history_manager.move_back()
        assert history_manager.get_history_index() == 1
        
        # Forward
        history_manager.move_forward()
        assert history_manager.get_history_index() == 2
        
        # Back again
        history_manager.move_back()
        assert history_manager.get_history_index() == 1

