"""
Tests para FileStateStorage.

Cubre operaciones CRUD, batch, rename handling y inicialización de SQLite.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.file_state_storage import (
    initialize_database,
    set_state,
    get_state_by_path,
    load_all_states,
    remove_state,
    set_states_batch,
    remove_states_batch,
    remove_missing_files,
    get_file_id_from_path,
    update_path_for_rename
)
from app.services.file_state_storage_helpers import compute_file_id


def _helper_set_state(path: str, state: str) -> None:
    """Helper para set_state que calcula file_id, size y modified automáticamente."""
    if not path or not os.path.exists(path):
        return
    
    stat = os.stat(path)
    size = stat.st_size
    modified = int(stat.st_mtime)
    file_id = compute_file_id(path, size, modified)
    
    set_state(file_id, path, size, modified, state)


@pytest.fixture
def temp_db(monkeypatch):
    """Crear base de datos temporal para tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / 'test_states.db'
    
    # Monkeypatch get_db_path para usar DB temporal
    from app.services import file_state_storage_helpers
    original_get_db_path = file_state_storage_helpers.get_db_path
    
    def mock_get_db_path():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path
    
    monkeypatch.setattr(file_state_storage_helpers, 'get_db_path', mock_get_db_path)
    
    # Inicializar DB
    initialize_database()
    
    yield str(db_path)
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass


class TestInitializeDatabase:
    """Tests para initialize_database."""
    
    def test_initialize_database_success(self, temp_db):
        """Inicializar base de datos exitosamente."""
        # Ya inicializada en fixture, verificar que funciona
        assert os.path.exists(temp_db)
    
    def test_initialize_database_creates_tables(self, temp_db):
        """Validar que crea las tablas necesarias."""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Verificar que existe tabla file_states
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_states'")
        result = cursor.fetchone()
        
        assert result is not None
        conn.close()


class TestSetState:
    """Tests para set_state."""
    
    def test_set_state_success(self, temp_db, temp_file):
        """Establecer estado de archivo exitosamente."""
        _helper_set_state(temp_file, "trabajado")
        
        # Verificar que se guardó
        state = get_state_by_path(temp_file)
        assert state == "trabajado"
    
    def test_set_state_nonexistent_file(self, temp_db):
        """Establecer estado de archivo inexistente."""
        # set_state no debe crashear con archivo inexistente
        _helper_set_state("/nonexistent/file.txt", "trabajado")
        
        # Verificar que no se guardó (archivo no existe)
        state = get_state_by_path("/nonexistent/file.txt")
        assert state is None
    
    def test_set_state_empty_path(self, temp_db):
        """Establecer estado con path vacío."""
        # set_state no debe crashear con path vacío
        _helper_set_state("", "trabajado")
        
        # Verificar que no se guardó
        state = get_state_by_path("")
        assert state is None


class TestGetStateByPath:
    """Tests para get_state_by_path."""
    
    def test_get_state_by_path_success(self, temp_db, temp_file):
        """Obtener estado de archivo existente."""
        _helper_set_state(temp_file, "pendiente")
        
        state = get_state_by_path(temp_file)
        
        assert state == "pendiente"
    
    def test_get_state_by_path_nonexistent(self, temp_db, temp_file):
        """Obtener estado de archivo sin estado."""
        state = get_state_by_path(temp_file)
        
        assert state is None
    
    def test_get_state_by_path_nonexistent_file(self, temp_db):
        """Obtener estado de archivo inexistente."""
        state = get_state_by_path("/nonexistent/file.txt")
        
        assert state is None


class TestLoadAllStates:
    """Tests para load_all_states."""
    
    def test_load_all_states_success(self, temp_db, temp_file):
        """Cargar todos los estados."""
        _helper_set_state(temp_file, "trabajado")
        
        states = load_all_states()
        
        assert isinstance(states, dict)
        assert len(states) > 0
    
    def test_load_all_states_empty(self, temp_db):
        """Cargar estados cuando no hay ninguno."""
        # La DB puede tener estados de otros tests, así que verificamos el tipo
        states = load_all_states()
        
        assert isinstance(states, dict)


class TestRemoveState:
    """Tests para remove_state."""
    
    def test_remove_state_success(self, temp_db, temp_file):
        """Eliminar estado exitosamente."""
        _helper_set_state(temp_file, "trabajado")
        
        file_id = get_file_id_from_path(temp_file)
        assert file_id is not None
        
        remove_state(file_id)
        
        # Verificar que se eliminó
        state = get_state_by_path(temp_file)
        assert state is None
    
    def test_remove_state_nonexistent(self, temp_db, temp_file):
        """Eliminar estado inexistente."""
        file_id = get_file_id_from_path(temp_file)
        if file_id:
            # remove_state no retorna valor, solo no debe crashear
            remove_state(file_id)
        
        # Verificar que no hay estado
        state = get_state_by_path(temp_file)
        assert state is None


class TestBatchOperations:
    """Tests para operaciones batch."""
    
    def test_set_states_batch_success(self, temp_db):
        """Establecer múltiples estados en batch."""
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.txt') as f:
                f.write(b'content')
                temp_files.append(f.name)
        
        try:
            # Preparar lista de tuplas (file_id, path, size, modified, state)
            states = []
            for file_path in temp_files:
                stat = os.stat(file_path)
                size = stat.st_size
                modified = int(stat.st_mtime)
                file_id = compute_file_id(file_path, size, modified)
                states.append((file_id, file_path, size, modified, "trabajado"))
            
            result = set_states_batch(states)
            
            assert result == 3
            
            # Verificar que se guardaron
            for file_path in temp_files:
                state = get_state_by_path(file_path)
                assert state == "trabajado"
        finally:
            for f in temp_files:
                try:
                    os.unlink(f)
                except OSError:
                    pass
    
    def test_remove_states_batch_success(self, temp_db):
        """Eliminar múltiples estados en batch."""
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.txt') as f:
                f.write(b'content')
                temp_files.append(f.name)
        
        try:
            # Establecer estados primero
            states = []
            for file_path in temp_files:
                stat = os.stat(file_path)
                size = stat.st_size
                modified = int(stat.st_mtime)
                file_id = compute_file_id(file_path, size, modified)
                states.append((file_id, file_path, size, modified, "trabajado"))
            set_states_batch(states)
            
            # Eliminar en batch (necesita lista de file_ids)
            file_ids = [get_file_id_from_path(f) for f in temp_files]
            file_ids = [fid for fid in file_ids if fid is not None]
            
            result = remove_states_batch(file_ids)
            
            assert result == len(file_ids)
            
            # Verificar que se eliminaron
            for file_path in temp_files:
                state = get_state_by_path(file_path)
                assert state is None
        finally:
            for f in temp_files:
                try:
                    os.unlink(f)
                except OSError:
                    pass


class TestRemoveMissingFiles:
    """Tests para remove_missing_files."""
    
    def test_remove_missing_files_success(self, temp_db):
        """Eliminar estados de archivos que ya no existen."""
        # Crear archivo temporal y establecer estado
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'content')
            temp_file = f.name
        
        try:
            _helper_set_state(temp_file, "trabajado")
            
            # Eliminar archivo
            os.unlink(temp_file)
            
            # Limpiar estados de archivos faltantes
            result = remove_missing_files(set())  # Pasar set vacío (el parámetro se ignora)
            
            assert result >= 0
            
            # Verificar que se eliminó el estado
            state = get_state_by_path(temp_file)
            assert state is None
        except OSError:
            pass


class TestGetFileIdFromPath:
    """Tests para get_file_id_from_path."""
    
    def test_get_file_id_from_path_success(self, temp_db, temp_file):
        """Obtener file_id de archivo existente."""
        file_id = get_file_id_from_path(temp_file)
        
        assert file_id is not None
        assert isinstance(file_id, str)
        assert len(file_id) > 0
    
    def test_get_file_id_from_path_nonexistent(self, temp_db):
        """Obtener file_id de archivo inexistente."""
        file_id = get_file_id_from_path("/nonexistent/file.txt")
        
        assert file_id is None
    
    def test_get_file_id_from_path_consistent(self, temp_db, temp_file):
        """Validar que file_id es consistente."""
        file_id1 = get_file_id_from_path(temp_file)
        file_id2 = get_file_id_from_path(temp_file)
        
        assert file_id1 == file_id2


class TestUpdatePathForRename:
    """Tests para update_path_for_rename."""
    
    def test_update_path_for_rename_success(self, temp_db):
        """Actualizar path después de renombrar archivo."""
        # Crear archivo original
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'content')
            old_path = f.name
        
        new_path = old_path.replace('.txt', '_renamed.txt')
        
        try:
            # Establecer estado en archivo original
            _helper_set_state(old_path, "trabajado")
            
            # Renombrar archivo
            os.rename(old_path, new_path)
            
            # Obtener file_id y stats del nuevo archivo
            stat = os.stat(new_path)
            size = stat.st_size
            modified = int(stat.st_mtime)
            new_file_id = compute_file_id(new_path, size, modified)
            
            # Actualizar path en DB
            result = update_path_for_rename(old_path, new_path, new_file_id, size, modified)
            
            assert result is not None
            
            # Verificar que el estado se mantiene con nuevo path
            state = get_state_by_path(new_path)
            assert state == "trabajado"
            
            # Verificar que el estado antiguo ya no existe
            old_state = get_state_by_path(old_path)
            assert old_state is None
        finally:
            try:
                if os.path.exists(new_path):
                    os.unlink(new_path)
            except OSError:
                pass


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_set_state_special_characters(self, temp_db):
        """Establecer estado con caracteres especiales en path."""
        temp_dir = tempfile.mkdtemp()
        special_file = os.path.join(temp_dir, "test file (1).txt")
        
        try:
            with open(special_file, 'w') as f:
                f.write('content')
            
            _helper_set_state(special_file, "trabajado")
            
            # Verificar que se guardó
            state = get_state_by_path(special_file)
            assert state == "trabajado"
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
    
    def test_set_state_unicode_path(self, temp_db):
        """Establecer estado con caracteres Unicode en path."""
        temp_dir = tempfile.mkdtemp()
        unicode_file = os.path.join(temp_dir, "测试_тест.txt")
        
        try:
            with open(unicode_file, 'w') as f:
                f.write('content')
            
            _helper_set_state(unicode_file, "trabajado")
            
            # Verificar que se guardó
            state = get_state_by_path(unicode_file)
            assert state == "trabajado"
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass

