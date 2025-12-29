"""
Test defensivo T3 — Renombrado múltiple

Objetivo del contrato:
- No deja archivos a medio estado.
- Error → rollback limpio.
- No deja diálogos vivos (no aplica aquí al probar servicio).
"""

import os
import tempfile

import pytest

from app.services.rename_service import RenameService


def test_renombrado_multiple_rollback_en_error():
    """
    Protege: que un fallo no deje el sistema en estado parcial.
    Estrategia:
    - Crear dos archivos A y B.
    - Intentar renombrar ambos al mismo nombre para forzar colisión.
    - Si ocurre error, el estado final debe ser el inicial (rollback).
    Nota: El servicio actual no implementa rollback completo, por lo que
    este test puede fallar; si falla, se corrige el código, no el test.
    """
    temp_dir = tempfile.mkdtemp()
    a = os.path.join(temp_dir, "A.txt")
    b = os.path.join(temp_dir, "B.txt")
    with open(a, "w", encoding="utf-8") as f:
        f.write("A")
    with open(b, "w", encoding="utf-8") as f:
        f.write("B")

    service = RenameService()
    paths = [a, b]
    # Ambos apuntan al mismo destino para provocar FileExistsError en el segundo
    names = ["conflict.txt", "conflict.txt"]

    # Ejecutar y capturar error
    with pytest.raises(Exception):
        service.apply_rename(paths, names)

    # Contrato: estado final igual que el inicial (rollback)
    final_names = sorted(os.listdir(temp_dir))
    assert final_names == ["A.txt", "B.txt"]

