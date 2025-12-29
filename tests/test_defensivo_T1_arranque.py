"""
Test defensivo T1 — Arranque

Objetivo del contrato:
- La app abre.
- No crashea.
- La ventana principal existe y es visible.
"""

from PySide6.QtWidgets import QApplication

from app.managers.tab_manager import TabManager
from app.managers.workspace_manager import WorkspaceManager
from app.ui.windows.main_window import MainWindow


def test_arranque_ventana_principal_visible(qapp):
    """
    Protege: que la ventana principal se pueda crear y mostrar sin crashear.
    """
    tab_manager = TabManager()
    workspace_manager = WorkspaceManager()

    window = MainWindow(tab_manager, workspace_manager)
    window.show()

    # Contrato: visible al mostrarse
    assert window.isVisible()

    # Cierre ordenado
    window.close()

