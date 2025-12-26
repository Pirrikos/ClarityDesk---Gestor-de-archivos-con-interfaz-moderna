# Análisis: Eliminación de Workspace

## Flujo Actual de Eliminación

### 1. Usuario solicita eliminar workspace
**Ubicación:** `app/ui/widgets/workspace_selector.py:396-422`

```396:422:app/ui/widgets/workspace_selector.py
    def _on_delete_workspace_clicked(self) -> None:
        """Handle delete workspace action - show confirmation and delete."""
        if not self._workspace_manager:
            return
        
        active_workspace = self._workspace_manager.get_active_workspace()
        if not active_workspace:
            return
        
        workspace_name = active_workspace.name
        workspace_id = active_workspace.id
        
        # Diálogo de confirmación
        reply = QMessageBox.question(
            self,
            "Eliminar Workspace",
            f"¿Estás seguro de que quieres eliminar el workspace \"{workspace_name}\"?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Eliminar workspace (el manager manejará el cambio automático si es necesario)
        deleted = self._workspace_manager.delete_workspace(workspace_id)
```

### 2. WorkspaceManager.delete_workspace()
**Ubicación:** `app/managers/workspace_manager.py:143-193`

**Problemas identificados:**

#### ❌ PROBLEMA 1: No guarda estado antes de eliminar
Si el workspace activo se elimina, **NO se guarda el estado actual** antes de cambiar a otro workspace.

```143:193:app/managers/workspace_manager.py
    def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete a workspace.
        
        Si es el workspace activo, cambia automáticamente a otro workspace válido
        antes de eliminar. Si es el único workspace, crea uno por defecto.
        
        Args:
            workspace_id: ID of workspace to delete.
        
        Returns:
            True if deleted, False if not found.
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        is_active = workspace_id == self._active_workspace_id
        other_workspaces = [w for w in self._workspaces if w.id != workspace_id]
        
        # Si es el activo y hay otros workspaces, cambiar al primero antes de eliminar
        if is_active and other_workspaces:
            self._active_workspace_id = other_workspaces[0].id
            logger.info(f"Switched to workspace {other_workspaces[0].name} before deleting active workspace")
        # Si es el activo y es el único, resetear a None (se creará uno por defecto después)
        elif is_active and not other_workspaces:
            self._active_workspace_id = None
        
        # Eliminar workspace de la lista
        self._workspaces = [w for w in self._workspaces if w.id != workspace_id]
        
        # Si no quedan workspaces, crear uno por defecto
        if not self._workspaces:
            default_workspace = self.create_workspace("Default")
            self._active_workspace_id = default_workspace.id
        
        self._save_workspaces_metadata()
        
        # Eliminar archivo de estado
        try:
            from app.services.workspace_storage_service import get_workspace_state_file
            state_file = get_workspace_state_file(workspace_id)
            if state_file.exists():
                state_file.unlink()
        except Exception as e:
            logger.error(f"Error deleting workspace state file: {e}")
        
        self.workspace_deleted.emit(workspace_id)
        logger.info(f"Deleted workspace: {workspace_id}")
        
        return True
```

#### ❌ PROBLEMA 2: No llama a switch_workspace()
Cuando cambia el `_active_workspace_id`, **NO llama a `switch_workspace()`** para:
- Guardar el estado actual del workspace que se elimina
- Cargar el estado del nuevo workspace activo en TabManager y Sidebar

Solo actualiza el ID interno, pero TabManager y Sidebar siguen mostrando el estado del workspace eliminado.

#### ❌ PROBLEMA 3: Señal workspace_changed no carga estado
La señal `workspace_changed` se emite, pero el handler en MainWindow solo actualiza el view_mode:

```332:342:app/ui/windows/main_window.py
    def _on_workspace_changed(self, workspace_id: str) -> None:
        """Handle workspace change - actualizar UI con nuevo estado."""
        if not self._workspace_manager:
            return
        
        workspace = self._workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return
        
        view_mode = self._workspace_manager.get_view_mode()
        switch_view(self._file_view_container, view_mode)
```

**NO carga el estado del nuevo workspace en TabManager y Sidebar.**

## Escenarios de Eliminación

### Escenario 1: Eliminar workspace NO activo
✅ **Funciona correctamente**
- Solo se elimina de la lista
- Se elimina el archivo de estado
- No afecta el workspace activo

### Escenario 2: Eliminar workspace activo (hay otros workspaces)
❌ **PROBLEMA**
- Cambia `_active_workspace_id` al primer workspace disponible
- **NO guarda el estado actual** antes de cambiar
- **NO carga el estado del nuevo workspace** en TabManager/Sidebar
- TabManager y Sidebar siguen mostrando tabs/paths del workspace eliminado
- UI muestra el nombre del nuevo workspace pero con el contenido del eliminado

### Escenario 3: Eliminar último workspace
⚠️ **PARCIALMENTE FUNCIONAL**
- Crea un workspace "Default" nuevo
- Cambia `_active_workspace_id` al nuevo workspace
- **NO carga el estado vacío** del nuevo workspace en TabManager/Sidebar
- TabManager y Sidebar siguen mostrando el estado del workspace eliminado

## Consecuencias

1. **Pérdida de estado**: Si eliminas el workspace activo, se pierde el estado actual (tabs, sidebar) porque no se guarda antes de cambiar.

2. **UI desincronizada**: La UI muestra el nombre del nuevo workspace pero con el contenido (tabs, sidebar) del workspace eliminado.

3. **Estado inconsistente**: TabManager y Sidebar tienen un estado que no corresponde al workspace activo.

4. **Persistencia incorrecta**: Si el usuario hace cambios después de eliminar, se guardarán en el workspace eliminado (que ya no existe) o se sobrescribirá el nuevo workspace con datos incorrectos.

## Solución Propuesta

### Opción A: Guardar estado y hacer switch completo
```python
def delete_workspace(self, workspace_id: str, tab_manager=None, sidebar=None, signal_controller=None) -> bool:
    workspace = self.get_workspace(workspace_id)
    if not workspace:
        return False
    
    is_active = workspace_id == self._active_workspace_id
    other_workspaces = [w for w in self._workspaces if w.id != workspace_id]
    
    # Si es el activo, guardar estado actual ANTES de cambiar
    if is_active and tab_manager is not None and sidebar is not None:
        self.save_current_state(tab_manager, sidebar)
    
    # Determinar nuevo workspace activo
    if is_active and other_workspaces:
        new_active_id = other_workspaces[0].id
    elif is_active and not other_workspaces:
        new_active_id = None  # Se creará uno por defecto
    else:
        new_active_id = self._active_workspace_id  # No cambia
    
    # Eliminar workspace de la lista
    self._workspaces = [w for w in self._workspaces if w.id != workspace_id]
    
    # Si no quedan workspaces, crear uno por defecto
    if not self._workspaces:
        default_workspace = self.create_workspace("Default")
        new_active_id = default_workspace.id
    
    # Cambiar al nuevo workspace activo (si cambió)
    if new_active_id != self._active_workspace_id:
        if tab_manager is not None and sidebar is not None:
            self.switch_workspace(new_active_id, tab_manager, sidebar, signal_controller)
        else:
            self._active_workspace_id = new_active_id
    
    self._save_workspaces_metadata()
    
    # Eliminar archivo de estado
    try:
        from app.services.workspace_storage_service import get_workspace_state_file
        state_file = get_workspace_state_file(workspace_id)
        if state_file.exists():
            state_file.unlink()
    except Exception as e:
        logger.error(f"Error deleting workspace state file: {e}")
    
    self.workspace_deleted.emit(workspace_id)
    logger.info(f"Deleted workspace: {workspace_id}")
    
    return True
```

### Opción B: Manejar en UI (workspace_selector)
Pasar TabManager y Sidebar desde `workspace_selector._on_delete_workspace_clicked()` y hacer el switch antes de eliminar.

## Recomendación

**Opción A** es mejor porque:
- Mantiene la lógica de workspace en WorkspaceManager
- Asegura que siempre se guarde el estado antes de cambiar
- Hace el switch completo (carga estado nuevo)
- Es más robusto y consistente

## ✅ Solución Implementada

**Cambios realizados:**

1. ✅ Modificado `delete_workspace()` en `WorkspaceManager` para aceptar `tab_manager`, `sidebar`, `signal_controller` como parámetros opcionales
2. ✅ Guarda estado actual ANTES de eliminar si es workspace activo
3. ✅ Llama a `switch_workspace()` completo si cambia el workspace activo (carga estado nuevo)
4. ✅ Actualizado `WorkspaceSelector` con métodos `set_tab_manager()`, `set_sidebar()`, `set_signal_controller()`
5. ✅ Actualizado `_on_delete_workspace_clicked()` para pasar estos parámetros
6. ✅ Configurado en `MainWindow._connect_signals()` para inyectar dependencias

**Archivos modificados:**
- `app/managers/workspace_manager.py` - Método `delete_workspace()` mejorado
- `app/ui/widgets/workspace_selector.py` - Métodos setter y actualización de `_on_delete_workspace_clicked()`
- `app/ui/windows/main_window.py` - Configuración de dependencias

**Tests:**
- ✅ Todos los tests de `TestDeleteWorkspace` pasan correctamente
- Los parámetros son opcionales, por lo que los tests existentes siguen funcionando

