"""Tests for TabsController."""

from app.controllers.tabs_controller import TabsController


class StubTabManager:
    """Stub for TabManager."""
    
    def __init__(self):
        self._tabs = []
        self._select_tab_called = False
        self._select_tab_index = None
        self._go_back_called = False
        self._go_forward_called = False
        self._can_go_back_value = False
        self._can_go_forward_value = False
    
    def get_tabs(self) -> list[str]:
        """Return tabs list."""
        return self._tabs.copy()
    
    def select_tab(self, index: int) -> bool:
        """Track select_tab calls."""
        self._select_tab_called = True
        self._select_tab_index = index
        return True
    
    def go_back(self) -> bool:
        """Track go_back calls."""
        self._go_back_called = True
        return True
    
    def go_forward(self) -> bool:
        """Track go_forward calls."""
        self._go_forward_called = True
        return True
    
    def can_go_back(self) -> bool:
        """Return can_go_back value."""
        return self._can_go_back_value
    
    def can_go_forward(self) -> bool:
        """Return can_go_forward value."""
        return self._can_go_forward_value


def test_activate_tab_calls_select_tab():
    """Test that activate_tab() calls select_tab."""
    tab_manager = StubTabManager()
    tab_manager._tabs = ["/path1", "/path2", "/path3"]
    controller = TabsController(tab_manager)
    
    controller.activate_tab(1)
    
    assert tab_manager._select_tab_called is True
    assert tab_manager._select_tab_index == 1


def test_activate_tab_validates_index():
    """Test that activate_tab() validates index range."""
    tab_manager = StubTabManager()
    tab_manager._tabs = ["/path1"]
    controller = TabsController(tab_manager)
    
    # Invalid index should not call select_tab
    tab_manager._select_tab_called = False
    controller.activate_tab(5)
    assert tab_manager._select_tab_called is False
    
    # Negative index should not call select_tab
    controller.activate_tab(-1)
    assert tab_manager._select_tab_called is False


def test_go_back_calls_manager():
    """Test that go_back() calls manager go_back."""
    tab_manager = StubTabManager()
    controller = TabsController(tab_manager)
    
    controller.go_back()
    
    assert tab_manager._go_back_called is True


def test_go_forward_calls_manager():
    """Test that go_forward() calls manager go_forward."""
    tab_manager = StubTabManager()
    controller = TabsController(tab_manager)
    
    controller.go_forward()
    
    assert tab_manager._go_forward_called is True


def test_can_go_back_returns_manager_value():
    """Test that can_go_back() returns manager value."""
    tab_manager = StubTabManager()
    controller = TabsController(tab_manager)
    
    tab_manager._can_go_back_value = True
    assert controller.can_go_back() is True
    
    tab_manager._can_go_back_value = False
    assert controller.can_go_back() is False


def test_can_go_forward_returns_manager_value():
    """Test that can_go_forward() returns manager value."""
    tab_manager = StubTabManager()
    controller = TabsController(tab_manager)
    
    tab_manager._can_go_forward_value = True
    assert controller.can_go_forward() is True
    
    tab_manager._can_go_forward_value = False
    assert controller.can_go_forward() is False

