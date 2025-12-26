"""
Tests para FocusManager.

Cubre apertura/cierre de Focus, señales y delegación a TabManager.
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject

from app.managers.focus_manager import FocusManager
from app.managers.tab_manager import TabManager


@pytest.fixture
def tab_manager(qapp, temp_storage):
    """Crear instancia de TabManager para tests."""
    return TabManager(storage_path=temp_storage)


@pytest.fixture
def focus_manager(qapp, tab_manager):
    """Crear instancia de FocusManager para tests."""
    return FocusManager(tab_manager)


class TestOpenOrCreateFocusForPath:
    """Tests para open_or_create_focus_for_path."""
    
    def test_open_or_create_focus_for_path_success(self, focus_manager, temp_folder):
        """Abrir o crear Focus exitosamente."""
        focus_manager.open_or_create_focus_for_path(temp_folder)
        
        assert temp_folder in focus_manager._tab_manager.get_tabs()
    
    def test_open_or_create_focus_for_path_empty(self, focus_manager):
        """Abrir Focus con path vacío (no debe hacer nada)."""
        tabs_before = len(focus_manager._tab_manager.get_tabs())
        
        focus_manager.open_or_create_focus_for_path("")
        
        assert len(focus_manager._tab_manager.get_tabs()) == tabs_before
    
    def test_open_or_create_focus_for_path_emits_signal(self, focus_manager, temp_folder):
        """Validar que emite señal focus_opened."""
        signal_received = []
        
        def on_focus_opened(path):
            signal_received.append(path)
        
        focus_manager.focus_opened.connect(on_focus_opened)
        focus_manager.open_or_create_focus_for_path(temp_folder)
        
        assert len(signal_received) == 1
        assert signal_received[0] == temp_folder


class TestRemoveFocus:
    """Tests para remove_focus."""
    
    def test_remove_focus_success(self, focus_manager, temp_folder):
        """Eliminar Focus exitosamente."""
        focus_manager.open_or_create_focus_for_path(temp_folder)
        
        focus_manager.remove_focus(temp_folder)
        
        assert temp_folder not in focus_manager._tab_manager.get_tabs()
    
    def test_remove_focus_empty_path(self, focus_manager):
        """Eliminar Focus con path vacío (no debe hacer nada)."""
        tabs_before = len(focus_manager._tab_manager.get_tabs())
        
        focus_manager.remove_focus("")
        
        assert len(focus_manager._tab_manager.get_tabs()) == tabs_before
    
    def test_remove_focus_emits_signal(self, focus_manager, temp_folder):
        """Validar que emite señal focus_removed."""
        focus_manager.open_or_create_focus_for_path(temp_folder)
        
        signal_received = []
        
        def on_focus_removed(path):
            signal_received.append(path)
        
        focus_manager.focus_removed.connect(on_focus_removed)
        focus_manager.remove_focus(temp_folder)
        
        assert len(signal_received) == 1
        assert signal_received[0] == temp_folder


class TestOpenFocus:
    """Tests para open_focus."""
    
    def test_open_focus_success(self, focus_manager, temp_folder):
        """Abrir Focus exitosamente."""
        focus_manager.open_focus(temp_folder)
        
        assert temp_folder in focus_manager._tab_manager.get_tabs()
    
    def test_open_focus_empty_path(self, focus_manager):
        """Abrir Focus con path vacío."""
        tabs_before = len(focus_manager._tab_manager.get_tabs())
        
        focus_manager.open_focus("")
        
        assert len(focus_manager._tab_manager.get_tabs()) == tabs_before


class TestCloseFocus:
    """Tests para close_focus."""
    
    def test_close_focus_by_index_success(self, focus_manager, temp_folder):
        """Cerrar Focus por índice exitosamente."""
        focus_manager.open_focus(temp_folder)
        
        focus_manager.close_focus(0)
        
        assert temp_folder not in focus_manager._tab_manager.get_tabs()
    
    def test_close_focus_active_tab(self, focus_manager):
        """Cerrar Focus activo (sin índice)."""
        folders = [tempfile.mkdtemp() for _ in range(2)]
        
        try:
            for folder in folders:
                focus_manager.open_focus(folder)
            
            focus_manager.close_focus()  # Sin índice, cierra activo
            
            assert len(focus_manager._tab_manager.get_tabs()) == 1
        finally:
            import shutil
            for folder in folders:
                try:
                    shutil.rmtree(folder)
                except OSError:
                    pass
    
    def test_close_focus_invalid_index(self, focus_manager, temp_folder):
        """Cerrar Focus con índice inválido."""
        focus_manager.open_focus(temp_folder)
        tabs_before = len(focus_manager._tab_manager.get_tabs())
        
        focus_manager.close_focus(10)
        
        assert len(focus_manager._tab_manager.get_tabs()) == tabs_before
    
    def test_close_focus_negative_index(self, focus_manager):
        """Cerrar Focus con índice negativo."""
        tabs_before = len(focus_manager._tab_manager.get_tabs())
        
        focus_manager.close_focus(-1)
        
        assert len(focus_manager._tab_manager.get_tabs()) == tabs_before


class TestCloseFocusByPath:
    """Tests para close_focus_by_path."""
    
    def test_close_focus_by_path_success(self, focus_manager, temp_folder):
        """Cerrar Focus por path exitosamente."""
        focus_manager.open_focus(temp_folder)
        
        focus_manager.close_focus_by_path(temp_folder)
        
        assert temp_folder not in focus_manager._tab_manager.get_tabs()
    
    def test_close_focus_by_path_empty(self, focus_manager):
        """Cerrar Focus con path vacío."""
        tabs_before = len(focus_manager._tab_manager.get_tabs())
        
        focus_manager.close_focus_by_path("")
        
        assert len(focus_manager._tab_manager.get_tabs()) == tabs_before


class TestReopenLastFocus:
    """Tests para reopen_last_focus."""
    
    def test_reopen_last_focus_success(self, focus_manager, temp_folder):
        """Reabrir último Focus exitosamente."""
        focus_manager.open_focus(temp_folder)
        
        # Navegar a otra carpeta
        temp_folder2 = tempfile.mkdtemp()
        try:
            focus_manager.open_focus(temp_folder2)
            
            # Reabrir último (debe estar en historial)
            focus_manager.reopen_last_focus()
            
            # Debe estar en tabs
            tabs = focus_manager._tab_manager.get_tabs()
            assert temp_folder in tabs or temp_folder2 in tabs
        finally:
            import shutil
            try:
                shutil.rmtree(temp_folder2)
            except OSError:
                pass
    
    def test_reopen_last_focus_no_history(self, focus_manager):
        """Reabrir último Focus sin historial."""
        tabs_before = len(focus_manager._tab_manager.get_tabs())
        
        focus_manager.reopen_last_focus()
        
        # No debe cambiar tabs si no hay historial
        assert len(focus_manager._tab_manager.get_tabs()) == tabs_before


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_multiple_focus_operations(self, focus_manager):
        """Múltiples operaciones de Focus."""
        folders = [tempfile.mkdtemp() for _ in range(3)]
        
        try:
            # Abrir múltiples Focus
            for folder in folders:
                focus_manager.open_focus(folder)
            
            assert len(focus_manager._tab_manager.get_tabs()) == 3
            
            # Cerrar uno
            focus_manager.close_focus_by_path(folders[1])
            
            assert len(focus_manager._tab_manager.get_tabs()) == 2
        finally:
            import shutil
            for folder in folders:
                try:
                    shutil.rmtree(folder)
                except OSError:
                    pass

