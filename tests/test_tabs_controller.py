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
    """Verifica que go_back() devuelve True cuando el handler retorna índice."""
    tm = TabManager()

    class NavStub:
        def go_back(self):
            return 0

    monkeypatch.setattr(tm, "_nav_handler", NavStub())
    assert tm.go_back() is True


def test_go_forward_calls_manager(monkeypatch):
    """Verifica que go_forward() devuelve True cuando el handler retorna índice."""
    tm = TabManager()

    class NavStub:
        def go_forward(self):
            return 1

    monkeypatch.setattr(tm, "_nav_handler", NavStub())
    assert tm.go_forward() is True


def test_can_go_back_returns_manager_value(monkeypatch):
    """Verifica que can_go_back() refleja el valor del handler."""
    tm = TabManager()

    class NavStubTrue:
        def can_go_back(self):
            return True

    class NavStubFalse:
        def can_go_back(self):
            return False

    monkeypatch.setattr(tm, "_nav_handler", NavStubTrue())
    assert tm.can_go_back() is True

    monkeypatch.setattr(tm, "_nav_handler", NavStubFalse())
    assert tm.can_go_back() is False


def test_can_go_forward_returns_manager_value(monkeypatch):
    """Verifica que can_go_forward() refleja el valor del handler."""
    tm = TabManager()

    class NavStubTrue:
        def can_go_forward(self):
            return True

    class NavStubFalse:
        def can_go_forward(self):
            return False

    monkeypatch.setattr(tm, "_nav_handler", NavStubTrue())
    assert tm.can_go_forward() is True

    monkeypatch.setattr(tm, "_nav_handler", NavStubFalse())
    assert tm.can_go_forward() is False

