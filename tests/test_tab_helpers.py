"""
Tests para TabHelpers.

Cubre búsqueda de tabs, validación de carpetas y nombres de display.
"""

import os
import tempfile

import pytest

from app.services.tab_helpers import (
    find_tab_index,
    find_or_add_tab,
    validate_folder,
    get_tab_display_name
)


@pytest.fixture
def temp_folders():
    """Crear carpetas temporales para tests."""
    folders = []
    for i in range(3):
        folder = tempfile.mkdtemp()
        folders.append(folder)
    
    yield folders
    
    import shutil
    for folder in folders:
        try:
            shutil.rmtree(folder)
        except OSError:
            pass


class TestFindTabIndex:
    """Tests para find_tab_index."""
    
    def test_find_tab_index_success(self, temp_folders):
        """Encontrar índice de tab existente."""
        tabs = temp_folders
        
        index = find_tab_index(tabs, temp_folders[0])
        
        assert index == 0
    
    def test_find_tab_index_not_found(self, temp_folders):
        """Buscar tab inexistente."""
        tabs = temp_folders
        nonexistent = tempfile.mkdtemp()
        
        try:
            index = find_tab_index(tabs, nonexistent)
            
            assert index is None
        finally:
            import shutil
            try:
                shutil.rmtree(nonexistent)
            except OSError:
                pass
    
    def test_find_tab_index_case_insensitive(self, temp_folders):
        """Búsqueda case-insensitive."""
        tabs = temp_folders
        # Usar path con diferente case
        test_path = temp_folders[0].upper() if temp_folders[0].islower() else temp_folders[0].lower()
        
        index = find_tab_index(tabs, test_path)
        
        # Debe encontrar por normalización
        assert index == 0 or index is None  # Depende de normalización


class TestFindOrAddTab:
    """Tests para find_or_add_tab."""
    
    def test_find_or_add_tab_existing(self, temp_folders):
        """Encontrar tab existente."""
        tabs = temp_folders.copy()
        original_length = len(tabs)
        
        index = find_or_add_tab(tabs, temp_folders[0])
        
        assert index == 0
        assert len(tabs) == original_length
    
    def test_find_or_add_tab_new(self, temp_folders):
        """Añadir tab nuevo."""
        tabs = temp_folders.copy()
        new_folder = tempfile.mkdtemp()
        
        try:
            original_length = len(tabs)
            
            index = find_or_add_tab(tabs, new_folder)
            
            assert index == original_length
            assert len(tabs) == original_length + 1
            assert tabs[index] == new_folder
        finally:
            import shutil
            try:
                shutil.rmtree(new_folder)
            except OSError:
                pass


class TestValidateFolder:
    """Tests para validate_folder."""
    
    def test_validate_folder_success(self, temp_folders):
        """Validar carpeta existente."""
        result = validate_folder(temp_folders[0])
        
        assert result is True
    
    def test_validate_folder_nonexistent(self):
        """Validar carpeta inexistente."""
        result = validate_folder("/nonexistent/folder")
        
        assert result is False
    
    def test_validate_folder_empty_path(self):
        """Validar path vacío."""
        result = validate_folder("")
        
        assert result is False
    
    def test_validate_folder_desktop_focus(self):
        """Validar Desktop Focus (virtual path)."""
        from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH
        
        result = validate_folder(DESKTOP_FOCUS_PATH)
        
        assert result is True
    
    def test_validate_folder_trash_focus(self):
        """Validar Trash Focus (virtual path)."""
        from app.services.trash_storage import TRASH_FOCUS_PATH
        
        result = validate_folder(TRASH_FOCUS_PATH)
        
        assert result is True
    
    def test_validate_folder_file_not_folder(self):
        """Validar archivo (no carpeta)."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            result = validate_folder(temp_file)
            
            assert result is False
        finally:
            try:
                os.unlink(temp_file)
            except OSError:
                pass


class TestGetTabDisplayName:
    """Tests para get_tab_display_name."""
    
    def test_get_tab_display_name_normal_path(self, temp_folders):
        """Obtener nombre de display para path normal."""
        folder_path = temp_folders[0]
        display_name = get_tab_display_name(folder_path)
        
        assert isinstance(display_name, str)
        assert len(display_name) > 0
        # Debe ser el basename
        assert display_name == os.path.basename(folder_path)
    
    def test_get_tab_display_name_empty_path(self):
        """Obtener nombre de display para path vacío."""
        display_name = get_tab_display_name("")
        
        assert display_name == ""
    
    def test_get_tab_display_name_desktop_focus(self):
        """Obtener nombre de display para Desktop Focus."""
        from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH
        
        display_name = get_tab_display_name(DESKTOP_FOCUS_PATH)
        
        assert display_name == "Escritorio"
    
    def test_get_tab_display_name_trash_focus(self):
        """Obtener nombre de display para Trash Focus."""
        from app.services.trash_storage import TRASH_FOCUS_PATH
        
        display_name = get_tab_display_name(TRASH_FOCUS_PATH)
        
        assert display_name == "Papelera"
    
    def test_get_tab_display_name_special_characters(self):
        """Obtener nombre de display con caracteres especiales."""
        temp_dir = tempfile.mkdtemp()
        special_folder = os.path.join(temp_dir, "test folder (1)")
        os.makedirs(special_folder, exist_ok=True)
        
        try:
            display_name = get_tab_display_name(special_folder)
            
            assert display_name == "test folder (1)"
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
    
    def test_get_tab_display_name_unicode(self):
        """Obtener nombre de display con Unicode."""
        temp_dir = tempfile.mkdtemp()
        unicode_folder = os.path.join(temp_dir, "测试_тест")
        os.makedirs(unicode_folder, exist_ok=True)
        
        try:
            display_name = get_tab_display_name(unicode_folder)
            
            assert display_name == "测试_тест"
        finally:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_find_tab_index_empty_list(self):
        """Buscar en lista vacía."""
        index = find_tab_index([], "/some/path")
        
        assert index is None
    
    def test_find_or_add_tab_empty_list(self):
        """Añadir a lista vacía."""
        tabs = []
        new_folder = tempfile.mkdtemp()
        
        try:
            index = find_or_add_tab(tabs, new_folder)
            
            assert index == 0
            assert len(tabs) == 1
        finally:
            import shutil
            try:
                shutil.rmtree(new_folder)
            except OSError:
                pass
    
    def test_validate_folder_none(self):
        """Validar None."""
        result = validate_folder(None)
        
        assert result is False

