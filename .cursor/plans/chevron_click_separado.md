# Plan: Separar Click en Chevron vs Click en Item

## Objetivo

- Click en chevron (flecha) → expandir/colapsar
- Click en resto del item → navegar a carpeta (mostrar archivos)

## Implementación

### 1. Agregar método para calcular área del chevron

En `folder_tree_delegate.py`:
- Método `_get_chevron_rect(option, index)` que retorna QRect del área del chevron
- Basado en `indentation` del tree view y nivel del item

### 2. Interceptar clicks en eventFilter

En `folder_tree_sidebar.py`:
- Modificar `eventFilter` para detectar clicks en el viewport
- Calcular si el click fue en el área del chevron
- Si fue en chevron → expand/collapse
- Si fue en otra parte → navegar (folder_selected.emit)

### 3. Desconectar señal clicked actual

- Desconectar `self._tree_view.clicked.connect(self._on_tree_clicked)`
- Manejar todo manualmente en eventFilter

## Cálculo del área del chevron

```python
def _get_chevron_rect(self, option: QStyleOptionViewItem, index) -> QRect:
    """Calcular área del chevron basado en indentación."""
    depth = 0
    parent = index.parent()
    while parent.isValid():
        depth += 1
        parent = parent.parent()
    
    indentation = self._view.indentation()
    chevron_size = 12  # Área clickeable del chevron
    chevron_left = depth * indentation + 4  # Offset desde izquierda
    chevron_top = option.rect.top() + (option.rect.height() - chevron_size) // 2
    
    return QRect(chevron_left, chevron_top, chevron_size, chevron_size)
```

