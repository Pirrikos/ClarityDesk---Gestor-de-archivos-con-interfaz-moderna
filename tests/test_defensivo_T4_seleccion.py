"""
Test defensivo T4 — Selección (grid / list)

Objetivo del contrato:
- La selección nunca queda corrupta.
- Cambiar de vista no mezcla estados (aquí verificamos consistencia básica).
- Ctrl/Shift no rompen lógica (probamos Ctrl, que es la ruta actual).
"""

from PySide6.QtCore import Qt

from app.ui.widgets.grid_selection_manager import handle_tile_selection


class StubTile:
    """
    Tile mínimo para pruebas de selección.
    - Solo mantiene estado 'selected' y es hashable para sets.
    """
    def __init__(self) -> None:
        self.selected = False
    def set_selected(self, value: bool) -> None:
        self.selected = value
    def __hash__(self) -> int:
        return id(self)


def test_seleccion_ctrl_toggle_y_click_simple():
    """
    Protege: que la selección con Ctrl alterna sin corromper el conjunto,
    y el click simple selecciona uno sólo.
    """
    selected = set()
    def clear():
        selected.clear()

    a = StubTile()
    b = StubTile()

    # Click simple en A → sólo A seleccionado
    handle_tile_selection(a, Qt.KeyboardModifier.NoModifier, selected, clear)
    assert a.selected is True and b.selected is False
    assert selected == {a}

    # Ctrl sobre B → añadir B sin perder A
    handle_tile_selection(b, Qt.KeyboardModifier.ControlModifier, selected, clear)
    assert a.selected is True and b.selected is True
    assert selected == {a, b}

    # Ctrl sobre A → deseleccionar A (toggle)
    handle_tile_selection(a, Qt.KeyboardModifier.ControlModifier, selected, clear)
    assert a.selected is False and b.selected is True
    assert selected == {b}

