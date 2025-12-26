"""Tests para TabManager (sustituye al antiguo TabsController)."""

from app.managers.tab_manager import TabManager


def test_activate_tab_calls_select_tab(monkeypatch):
    """Verifica que activate_tab() invoca select_tab con índice válido."""
    tm = TabManager()
    tm._tabs = ["/path1", "/path2", "/path3"]
    called = {"flag": False, "index": None}

    def fake_select(idx: int) -> bool:
        called["flag"] = True
        called["index"] = idx
        return True

    monkeypatch.setattr(tm, "select_tab", fake_select)

    tm.activate_tab(1)

    assert called["flag"] is True
    assert called["index"] == 1


def test_activate_tab_validates_index(monkeypatch):
    """Verifica que activate_tab() valida el rango de índice."""
    tm = TabManager()
    tm._tabs = ["/path1"]
    called = {"flag": False}

    def fake_select(idx: int) -> bool:
        called["flag"] = True
        return True

    monkeypatch.setattr(tm, "select_tab", fake_select)

    tm.activate_tab(5)
    assert called["flag"] is False

    tm.activate_tab(-1)
    assert called["flag"] is False


def test_go_back_calls_manager(monkeypatch):
    """Verifica que go_back() usa _history_manager correctamente."""
    tm = TabManager()
    tm._tabs = ["/path1", "/path2"]
    tm._active_index = 1

    class HistoryStub:
        def can_go_back(self):
            return True
        def get_back_path(self):
            return "/path1"
        def move_back(self):
            pass
        def set_navigating_flag(self, value):
            pass

    monkeypatch.setattr(tm, "_history_manager", HistoryStub())
    monkeypatch.setattr(tm, "select_tab", lambda idx: True)
    
    result = tm.go_back()
    assert result is True


def test_go_forward_calls_manager(monkeypatch):
    """Verifica que go_forward() usa _history_manager correctamente."""
    tm = TabManager()
    tm._tabs = ["/path1", "/path2"]
    tm._active_index = 0

    class HistoryStub:
        def can_go_forward(self):
            return True
        def get_forward_path(self):
            return "/path2"
        def move_forward(self):
            pass
        def set_navigating_flag(self, value):
            pass

    monkeypatch.setattr(tm, "_history_manager", HistoryStub())
    monkeypatch.setattr(tm, "select_tab", lambda idx: True)
    
    result = tm.go_forward()
    assert result is True


def test_can_go_back_returns_manager_value(monkeypatch):
    """Verifica que can_go_back() refleja el valor del _history_manager."""
    tm = TabManager()

    class HistoryStubTrue:
        def can_go_back(self):
            return True

    class HistoryStubFalse:
        def can_go_back(self):
            return False

    monkeypatch.setattr(tm, "_history_manager", HistoryStubTrue())
    assert tm.can_go_back() is True

    monkeypatch.setattr(tm, "_history_manager", HistoryStubFalse())
    assert tm.can_go_back() is False


def test_can_go_forward_returns_manager_value(monkeypatch):
    """Verifica que can_go_forward() refleja el valor del _history_manager."""
    tm = TabManager()

    class HistoryStubTrue:
        def can_go_forward(self):
            return True

    class HistoryStubFalse:
        def can_go_forward(self):
            return False

    monkeypatch.setattr(tm, "_history_manager", HistoryStubTrue())
    assert tm.can_go_forward() is True

    monkeypatch.setattr(tm, "_history_manager", HistoryStubFalse())
    assert tm.can_go_forward() is False

