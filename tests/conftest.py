"""
Fixtures compartidas para tests de ClarityDesk Pro.

Este archivo define fixtures comunes que se usan en múltiples tests.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """QApplication compartida para todos los tests de Qt."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # No hacer quit() aquí porque puede afectar otros tests


@pytest.fixture
def temp_folder():
    """Crear carpeta temporal para tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    
    try:
        shutil.rmtree(temp_path)
    except OSError:
        pass


@pytest.fixture
def temp_storage():
    """Crear archivo de almacenamiento temporal."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_path = temp_file.name
    temp_file.close()
    
    yield temp_path
    
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def temp_file():
    """Crear archivo temporal para tests."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(b'test content')
        temp_path = f.name
    
    yield temp_path
    
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def temp_files():
    """Crear múltiples archivos temporales.
    
    Retorna tupla (files, temp_dir) donde:
    - files: lista de rutas de archivos creados
    - temp_dir: directorio temporal donde se crearon
    """
    temp_dir = tempfile.mkdtemp()
    files = []
    
    for i in range(3):
        file_path = os.path.join(temp_dir, f'test_file_{i}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'content {i}')
        files.append(file_path)
    
    yield files, temp_dir
    
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass

