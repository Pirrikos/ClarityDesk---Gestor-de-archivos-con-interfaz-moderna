"""
Tests CRÍTICOS de contrato de producto para FileStateManager.

Estos tests validan el comportamiento visible del sistema de estados de archivos,
sin inspeccionar implementación interna (cache, métodos privados).

Categoría: CRÍTICO
Regla: Si falla → cambiar código de producción, no el test.
"""

import os
import tempfile

import pytest
from PySide6.QtCore import QObject

from app.managers.file_state_manager import FileStateManager


@pytest.fixture
def file_state_manager(qapp):
    """Crear instancia de FileStateManager para tests."""
    manager = FileStateManager()
    return manager


@pytest.fixture
def temp_file():
    """Crear archivo temporal para tests."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(b'initial content')
        temp_path = f.name
    
    yield temp_path
    
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except OSError:
        pass


class TestFileStateContract:
    """Tests CRÍTICOS que validan contrato de producto de FileStateManager."""
    
    def test_file_state_remains_accessible_after_file_modification(
        self, 
        file_state_manager: FileStateManager, 
        temp_file: str
    ):
        """
        Validar que el estado de un archivo sigue siendo accesible después de modificarlo.
        
        Contrato de producto:
        - Si un usuario establece un estado para un archivo
        - Y luego modifica el archivo (contenido)
        - Entonces get_file_state() debe retornar un resultado válido (estado o None)
        - Y NO debe crashear ni retornar estado incorrecto
        
        Este test valida comportamiento observable sin inspeccionar implementación interna.
        Solo usa API pública: set_file_state() y get_file_state().
        """
        # Paso 1: Establecer estado inicial
        initial_state = "trabajado"
        file_state_manager.set_file_state(temp_file, initial_state)
        
        # Verificar que el estado se estableció correctamente
        state_before = file_state_manager.get_file_state(temp_file)
        assert state_before == initial_state, \
            f"Estado inicial debe establecerse correctamente. " \
            f"Esperado: {initial_state}, Obtenido: {state_before}"
        
        # Paso 2: Modificar archivo (simular edición de usuario)
        # Esto cambiará el contenido y potencialmente el mtime del archivo
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write('modified content by user')
        
        # Paso 3: Verificar comportamiento observable
        # El estado puede:
        # - Persistir (mismo estado) - comportamiento esperado si el sistema
        #   reconoce que es el mismo archivo
        # - Ser None (si el sistema decide que es un archivo diferente debido
        #   al cambio de metadata) - también válido, pero debe ser consistente
        # - NO debe crashear ni retornar estado incorrecto
        
        state_after = file_state_manager.get_file_state(temp_file)
        
        # Validar que retorna resultado válido (no crashea)
        assert state_after is None or isinstance(state_after, str), \
            f"get_file_state() debe retornar None o str después de modificar archivo. " \
            f"Obtenido: {state_after} (tipo: {type(state_after)})"
        
        # Si retorna estado, debe ser el correcto (no un estado de otro archivo)
        if state_after is not None:
            assert state_after == initial_state, \
                f"Si el estado persiste después de modificar archivo, debe ser el correcto. " \
                f"Esperado: {initial_state}, Obtenido: {state_after}"
        
        # Validar consistencia: múltiples llamadas deben retornar el mismo resultado
        state_after_repeated = file_state_manager.get_file_state(temp_file)
        assert state_after_repeated == state_after, \
            f"get_file_state() debe retornar resultado consistente en llamadas repetidas. " \
            f"Primera llamada: {state_after}, Segunda llamada: {state_after_repeated}"

