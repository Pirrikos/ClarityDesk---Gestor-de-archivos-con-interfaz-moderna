# Backup - Implementación Vistas por Estado

**Fecha**: 2025-12-26 19:39:00
**Motivo**: Backup antes de implementar vistas por estado (Finder-like)

## Archivos Respaldados

### Services
- `app/services/path_utils.py` - Añadir helpers para detectar contextos de estado
- `app/services/state_label_storage.py` - Extender para persistir orden de estados

### Managers
- `app/managers/state_label_manager.py` - Extender con métodos de orden
- `app/managers/file_state_manager.py` - Añadir método get_items_by_state()
- `app/managers/tab_manager.py` - Extender con contexto de estado
- `app/managers/tab_manager_actions.py` - Rechazar paths virtuales en add_tab/select_tab

### UI Widgets
- `app/ui/widgets/folder_tree_sidebar.py` - Integrar sección ESTADOS
- `app/ui/widgets/file_drop_handler.py` - Rechazar drag en vistas por estado
- `app/ui/widgets/drag_common.py` - Similar

### Storage
- `storage/state_labels.json` - Extender schema con orden de estados

## Archivos Nuevos que se Crearán

- `app/services/file_state_storage_query.py` - Servicio para consultar archivos por estado
- `app/ui/widgets/state_section_widget.py` - Widget para sección ESTADOS en sidebar

## Cómo Restaurar

Para restaurar los archivos respaldados:

```powershell
cd "C:\Users\pirri\PROYECTOS\PROY ORDEN PC\ACTIVO\ClarityDesk_29-11-25"
$backupDir = "backups\backup_vistas_estado_2025-12-26_19-39-00"
Copy-Item "$backupDir\app\*" -Destination "app\" -Recurse -Force
Copy-Item "$backupDir\storage\*" -Destination "storage\" -Recurse -Force
```

## Cambios Principales

1. **Separación estricta**: Contextos de estado NO son paths
2. **Tabs solo paths físicos**: Los estados nunca entran en tabs
3. **set_state_context() simplificado**: No pasa por validaciones/watchers
4. **Visual**: Estados muestran color a la izquierda en sidebar

## Notas

- Los archivos nuevos creados durante la implementación NO están en este backup
- Si necesitas restaurar, elimina primero los archivos nuevos creados:
  - `app/services/file_state_storage_query.py`
  - `app/ui/widgets/state_section_widget.py`

