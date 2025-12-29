"""
Test defensivo T5 — Cambio de workspace

Objetivo del contrato:
- No pierde archivos (estado básico consistente).
- No restaura estados inválidos.
- No deja selecciones fantasma (en este nivel, verificamos coherencia mínima).
"""

import tempfile
import shutil
from pathlib import Path

import pytest

from app.managers.workspace_manager import WorkspaceManager


def test_cambio_workspace_estado_coherente(qapp, monkeypatch):
    """
    Protege: que el cambio de workspace mantiene un estado coherente (ID activo válido).
    Estrategia: usar storage temporal para no afectar datos reales.
    """
    temp_dir = tempfile.mkdtemp()

    def mock_get_storage_dir():
        storage_path = Path(temp_dir) / "storage"
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    monkeypatch.setattr(
        "app.services.workspace_storage_service.get_storage_dir",
        mock_get_storage_dir,
    )

    manager = WorkspaceManager()
    w1 = manager.create_workspace("W1")
    w2 = manager.create_workspace("W2")

    # Cambiar al segundo workspace
    success = manager.switch_workspace(w2.id, None, None)
    assert success is True
    assert manager.get_active_workspace_id() == w2.id

    # Cambiar de vuelta al primero
    success_back = manager.switch_workspace(w1.id, None, None)
    assert success_back is True
    assert manager.get_active_workspace_id() == w1.id

    # Limpieza
    shutil.rmtree(temp_dir, ignore_errors=True)

