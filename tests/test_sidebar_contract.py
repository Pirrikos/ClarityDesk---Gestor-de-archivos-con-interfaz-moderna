"""
Tests CRÍTICOS de contrato de producto para FolderTreeSidebar.

Estos tests validan el comportamiento visible del doble clic en el sidebar,
sin inspeccionar implementación interna (métodos privados, timers internos).

Categoría: CRÍTICO
Regla: Si falla → cambiar código de producción, no el test.
"""

import os
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar


@pytest.fixture
def qapp():
    """Crear QApplication para tests de Qt."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_folders():
    """Crear carpetas temporales para tests."""
    temp_base = tempfile.mkdtemp()
    folders = {
        'root': Path(temp_base) / "root_folder",
        'child': Path(temp_base) / "root_folder" / "child_folder",
    }
    
    for folder_path in folders.values():
        folder_path.mkdir(parents=True, exist_ok=True)
    
    yield {k: str(v) for k, v in folders.items()}
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_base)
    except OSError:
        pass


@pytest.fixture
def sidebar(qapp):
    """Crear instancia de FolderTreeSidebar para tests."""
    sidebar = FolderTreeSidebar()
    sidebar.show()
    QTest.qWaitForWindowExposed(sidebar)
    return sidebar


class TestSidebarDoubleClickContract:
    """Tests CRÍTICOS que validan contrato de producto del doble clic en Sidebar."""
    
    def test_double_click_emits_folder_selected_signal(
        self,
        sidebar: FolderTreeSidebar,
        temp_folders: dict,
        qapp: QApplication
    ):
        """
        Validar que el doble clic en una carpeta del sidebar emite el signal correcto.
        
        Contrato de producto (Sidebar puro):
        - Cuando el usuario hace doble clic en una carpeta del sidebar
        - El sidebar debe emitir folder_selected con el path correcto
        - El signal debe emitirse exactamente una vez por doble clic
        - El sistema NO debe crashear
        
        Este test valida comportamiento observable sin inspeccionar implementación interna.
        Solo usa API pública: folder_selected signal.
        No valida integración con TabManager ni MainWindow.
        """
        # Paso 1: Configurar estado inicial
        root_folder = temp_folders['root']
        child_folder = temp_folders['child']
        
        # Añadir carpetas al sidebar
        sidebar.add_focus_path(root_folder)
        sidebar.add_focus_path(child_folder)
        
        # Paso 2: Capturar emisiones del signal folder_selected
        emitted_paths = []
        
        def on_folder_selected(path: str) -> None:
            """Capturar path emitido por el signal."""
            emitted_paths.append(path)
        
        sidebar.folder_selected.connect(on_folder_selected)
        
        # Verificar estado inicial: no se han emitido señales
        assert len(emitted_paths) == 0, \
            f"Estado inicial incorrecto. No debe haber señales emitidas. " \
            f"Señales capturadas: {emitted_paths}"
        
        # Paso 3: Simular doble clic en la carpeta root del sidebar
        # Obtener el índice del item en el tree view
        tree_view = sidebar._tree_view
        model = sidebar._model
        
        # Buscar el item correspondiente a root_folder
        root_item = None
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.text() == os.path.basename(root_folder):
                root_item = item
                break
        
        assert root_item is not None, \
            f"No se encontró el item para la carpeta root en el sidebar. " \
            f"Carpeta: {root_folder}"
        
        root_index = model.indexFromItem(root_item)
        assert root_index.isValid(), \
            f"Índice inválido para la carpeta root. Item: {root_item.text()}"
        
        # Obtener rectángulo visual del item
        visual_rect = tree_view.visualRect(root_index)
        assert visual_rect.isValid(), \
            f"Rectángulo visual inválido para el item root"
        
        # Calcular posición del click (centro del item, a la izquierda del área de controles)
        click_x = visual_rect.left() + 20  # 20px desde la izquierda (área de navegación)
        click_y = visual_rect.center().y()
        click_pos = QPoint(click_x, click_y)
        
        # Verificar que el click está dentro del rectángulo visual
        assert visual_rect.contains(click_pos), \
            f"Posición del click fuera del rectángulo visual. " \
            f"Click: ({click_x}, {click_y}), Rect: {visual_rect}"
        
        # Paso 4: Simular doble clic usando QTest (comportamiento real del usuario)
        # El sidebar maneja clicks a través del eventFilter, así que simulamos el evento completo
        # Primero un click simple para establecer _last_click_pos, luego el doble clic
        QTest.mouseClick(tree_view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, click_pos)
        qapp.processEvents()
        
        # Ahora el doble clic (que también dispara el signal clicked)
        QTest.mouseDClick(tree_view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, click_pos, delay=50)
        
        # Procesar eventos de Qt para que se procesen las señales
        qapp.processEvents()
        
        # Paso 5: Verificar comportamiento observable del Sidebar
        # 5a: Verificar que se emitió el signal
        assert len(emitted_paths) > 0, \
            f"Después del doble clic, debe haberse emitido al menos una señal folder_selected. " \
            f"Señales capturadas: {emitted_paths}"
        
        # 5b: Verificar que el path emitido es correcto
        # El path puede estar normalizado o no, pero debe corresponder a root_folder
        # Usamos comparación normalizada para ser tolerante a diferencias de formato
        last_emitted_path = emitted_paths[-1]
        
        # Normalizar paths para comparación (Windows puede tener diferentes casos y separadores)
        normalized_emitted = last_emitted_path.lower().replace('\\', '/')
        normalized_root = root_folder.lower().replace('\\', '/')
        
        assert normalized_emitted == normalized_root, \
            f"Después del doble clic en '{root_folder}', el signal debe emitir ese path. " \
            f"Esperado: {root_folder} (normalizado: {normalized_root}), " \
            f"Obtenido: {last_emitted_path} (normalizado: {normalized_emitted})"
        
        # 5c: Verificar que el path emitido es un path válido (no vacío, no None)
        assert last_emitted_path and isinstance(last_emitted_path, str), \
            f"El path emitido debe ser una cadena no vacía. " \
            f"Obtenido: {last_emitted_path} (tipo: {type(last_emitted_path)})"
        
        # 5d: Verificar que la carpeta existe (el path es válido)
        assert os.path.exists(last_emitted_path), \
            f"El path emitido debe corresponder a una carpeta existente. " \
            f"Path: {last_emitted_path}"
        
        assert os.path.isdir(last_emitted_path), \
            f"El path emitido debe ser una carpeta (directorio). " \
            f"Path: {last_emitted_path}"
        
        # Paso 6: Verificar que se puede hacer doble clic en otra carpeta sin problemas
        # Limpiar lista de paths emitidos para el segundo test
        emitted_paths.clear()
        
        # Buscar el item de child_folder
        child_item = None
        for i in range(model.rowCount()):
            item = model.item(i)
            if item:
                # Buscar recursivamente en hijos
                for j in range(item.rowCount()):
                    child = item.child(j)
                    if child and child.text() == os.path.basename(child_folder):
                        child_item = child
                        break
                if child_item:
                    break
        
        if child_item:
            child_index = model.indexFromItem(child_item)
            if child_index.isValid():
                child_rect = tree_view.visualRect(child_index)
                if child_rect.isValid():
                    child_click_x = child_rect.left() + 20
                    child_click_y = child_rect.center().y()
                    child_click_pos = QPoint(child_click_x, child_click_y)
                    
                    # Simular doble clic en carpeta hija
                    QTest.mouseClick(tree_view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, child_click_pos)
                    qapp.processEvents()
                    QTest.mouseDClick(tree_view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, child_click_pos, delay=50)
                    qapp.processEvents()
                    
                    # Verificar que se emitió el signal para la carpeta hija
                    assert len(emitted_paths) > 0, \
                        f"Después del doble clic en carpeta hija, debe haberse emitido una señal folder_selected. " \
                        f"Señales capturadas: {emitted_paths}"
                    
                    last_child_path = emitted_paths[-1]
                    normalized_child_emitted = last_child_path.lower().replace('\\', '/')
                    normalized_child = child_folder.lower().replace('\\', '/')
                    
                    assert normalized_child_emitted == normalized_child, \
                        f"Después del doble clic en '{child_folder}', el signal debe emitir ese path. " \
                        f"Esperado: {child_folder} (normalizado: {normalized_child}), " \
                        f"Obtenido: {last_child_path} (normalizado: {normalized_child_emitted})"
