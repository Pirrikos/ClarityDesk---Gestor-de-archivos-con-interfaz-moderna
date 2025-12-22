# REVISIÓN DE CÓDIGO - Sistema de Preview con Barra Espaciadora

## Archivos Modificados en Esta Conversación

1. `app/ui/windows/main_window.py`
2. `app/ui/widgets/folder_tree_sidebar.py`
3. `app/ui/windows/quick_preview_window.py`
4. `app/ui/windows/quick_preview_loader.py`
5. `app/ui/windows/quick_preview_cache.py`
6. `app/ui/windows/quick_preview_ui_setup.py`
7. `app/services/preview_pdf_service.py`
8. `app/services/pdf_renderer.py`
9. `requirements.txt`

---

## PROBLEMAS DETECTADOS

### 🔴 CRÍTICO: Duplicación de Extensiones de Archivo (Regla 4 - DRY)

**Problema:** Las extensiones de archivo están definidas en múltiples lugares:

1. `app/services/preview_pdf_service.py` (líneas 179, 187-188)
2. `app/ui/windows/quick_preview_cache.py` (líneas 72-75)
3. `app/ui/windows/main_window_file_handler.py` (líneas 41-46)
4. `app/services/preview_service.py` (línea 81)

**Impacto:** 
- Violación de DRY (Regla 4)
- Mantenimiento difícil (cambiar extensiones requiere tocar 4+ archivos)
- Inconsistencias potenciales
- Desperdicio de tokens

**Propuesta:**
```python
# Crear app/services/preview_file_extensions.py
"""Extensiones de archivo para preview."""

PREVIEW_IMAGE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.ico', '.svg'
}

PREVIEW_TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
    '.yaml', '.yml', '.ini', '.log', '.csv', '.rtf'
}

PREVIEW_PDF_DOCX_EXTENSIONS = {'.pdf', '.docx'}

PREVIEWABLE_EXTENSIONS = (
    PREVIEW_IMAGE_EXTENSIONS | 
    PREVIEW_TEXT_EXTENSIONS | 
    PREVIEW_PDF_DOCX_EXTENSIONS
)
```

**Archivos a modificar:**
- `preview_pdf_service.py`: Importar constantes
- `quick_preview_cache.py`: Importar constantes
- `main_window_file_handler.py`: Importar constantes
- `preview_service.py`: Ya tiene su propia lógica, mantener separado si es necesario

---

### 🔴 CRÍTICO: Acceso a Atributos Privados (Violación de Encapsulación)

**Problema:** `quick_preview_loader.py` accede a atributos privados:

```python
# Línea 43: Acceso a atributo privado
preview_service = self._cache._preview_service

# Líneas 48, 52: Acceso directo a diccionarios internos
self._cache._cache[index] = pixmap
self._cache._cache_mtime[index] = os.path.getmtime(current_path)
```

**Impacto:**
- Violación de encapsulación
- Acoplamiento fuerte
- Difícil de mantener
- Rompe abstracción

**Propuesta:**
Agregar métodos públicos en `QuickPreviewCache`:

```python
# En quick_preview_cache.py
def update_cache_entry(self, index: int, path: str, pixmap: QPixmap) -> None:
    """Update cache entry with pixmap and mtime."""
    self._cache[index] = pixmap
    try:
        if os.path.exists(path):
            self._cache_mtime[index] = os.path.getmtime(path)
        else:
            self._cache_mtime[index] = 0
    except (OSError, ValueError):
        self._cache_mtime[index] = 0

@property
def preview_service(self):
    """Get preview service."""
    return self._preview_service
```

**Archivo a modificar:**
- `quick_preview_loader.py`: Usar métodos públicos en lugar de atributos privados

---

### 🟡 MEDIO: Logging Inconsistente (Regla 10 - Error Handling)

**Problema 1:** `pdf_renderer.py` usa `print()` en lugar de logger:

```python
# Líneas 17, 22, 23, 28, 30
print(f"[PDF_RENDERER] ...")
```

**Problema 2:** `preview_pdf_service.py` crea logger en cada método:

```python
# Líneas 151-152, 160-161
import logging
logger = logging.getLogger(__name__)
```

**Impacto:**
- Inconsistencia con el resto del código
- No sigue el patrón establecido (`get_logger()` del core)
- Prints no van a archivo de log

**Propuesta:**
```python
# En pdf_renderer.py - Reemplazar prints con logger
from app.core.logger import get_logger
logger = get_logger(__name__)

# En preview_pdf_service.py - Logger a nivel de módulo
from app.core.logger import get_logger
logger = get_logger(__name__)
```

**Archivos a modificar:**
- `pdf_renderer.py`: Reemplazar prints con logger
- `preview_pdf_service.py`: Mover logger a nivel de módulo

---

### 🟡 MEDIO: Código Duplicado en Invalidación de Cache

**Problema:** `quick_preview_cache.py` tiene lógica duplicada para invalidar cache:

```python
# Líneas 53-55, 58-61, 64-67 - Mismo patrón repetido 3 veces
del self._cache[index]
if index in self._cache_mtime:
    del self._cache_mtime[index]
```

**Propuesta:**
```python
def _invalidate_cache_entry(self, index: int) -> None:
    """Invalidate cache entry for given index."""
    if index in self._cache:
        del self._cache[index]
    if index in self._cache_mtime:
        del self._cache_mtime[index]
```

**Archivo a modificar:**
- `quick_preview_cache.py`: Extraer método privado

---

### 🟡 MEDIO: Manejo de Errores Genérico

**Problema:** Varios `except Exception:` sin logging específico:

```python
# preview_pdf_service.py línea 258
except Exception:
    return QPixmap()
```

**Propuesta:**
```python
except Exception as e:
    logger.warning(f"Failed to render text preview for {path}: {e}")
    return QPixmap()
```

**Archivos a modificar:**
- `preview_pdf_service.py`: Agregar logging en excepciones
- `quick_preview_cache.py`: Ya tiene logging, está bien

---

### 🟢 MENOR: Type Hints Incompletos

**Problema:** Algunos métodos tienen type hints incompletos:

```python
# quick_preview_loader.py línea 26
def load_preview(self, paths: list[str], index: int, image_label: QLabel,
                use_crossfade: bool, animations) -> tuple[Optional[QPixmap], str]:
    # 'animations' sin type hint
```

**Propuesta:**
```python
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from app.ui.windows.quick_preview_animations import QuickPreviewAnimations

def load_preview(
    self, 
    paths: list[str], 
    index: int, 
    image_label: QLabel,
    use_crossfade: bool, 
    animations: 'QuickPreviewAnimations'
) -> tuple[Optional[QPixmap], str]:
```

**Archivos a modificar:**
- `quick_preview_loader.py`: Completar type hints

---

### 🟢 MENOR: Importaciones Dentro de Métodos

**Problema:** Varias importaciones dentro de métodos en lugar de nivel de módulo:

```python
# preview_pdf_service.py líneas 181, 195
from app.services.icon_renderer import render_image_preview
from app.services.icon_render_service import IconRenderService

# quick_preview_cache.py línea 70
from pathlib import Path
```

**Propuesta:** Mover imports a nivel de módulo (mejor rendimiento, más claro)

**Archivos a modificar:**
- `preview_pdf_service.py`: Mover imports a nivel de módulo
- `quick_preview_cache.py`: Ya tiene Path importado, pero se importa dentro del método

---

## RESUMEN DE VIOLACIONES DE REGLAS

| Regla | Violación | Archivo | Severidad |
|-------|-----------|---------|-----------|
| Regla 4 (DRY) | Duplicación de extensiones | 4 archivos | 🔴 CRÍTICO |
| Regla 5 (DI) | Acceso a atributos privados | `quick_preview_loader.py` | 🔴 CRÍTICO |
| Regla 10 (Error Handling) | Logging inconsistente | `pdf_renderer.py`, `preview_pdf_service.py` | 🟡 MEDIO |
| Regla 4 (DRY) | Código duplicado en cache | `quick_preview_cache.py` | 🟡 MEDIO |
| Regla 8 (Type Hints) | Type hints incompletos | `quick_preview_loader.py` | 🟢 MENOR |
| Regla 12 (Imports) | Imports dentro de métodos | Varios | 🟢 MENOR |

---

## PROPUESTAS DE REFACTORIZACIÓN

### Propuesta 1: Centralizar Extensiones de Archivo (PRIORIDAD ALTA)

**Archivo nuevo:** `app/services/preview_file_extensions.py`

```python
"""Extensiones de archivo para preview."""

PREVIEW_IMAGE_EXTENSIONS = frozenset({
    '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.ico', '.svg'
})

PREVIEW_TEXT_EXTENSIONS = frozenset({
    '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
    '.yaml', '.yml', '.ini', '.log', '.csv', '.rtf'
})

PREVIEW_PDF_DOCX_EXTENSIONS = frozenset({'.pdf', '.docx'})

PREVIEWABLE_EXTENSIONS = (
    PREVIEW_IMAGE_EXTENSIONS | 
    PREVIEW_TEXT_EXTENSIONS | 
    PREVIEW_PDF_DOCX_EXTENSIONS
)

def is_previewable_image(ext: str) -> bool:
    """Check if extension is a previewable image."""
    return ext.lower() in PREVIEW_IMAGE_EXTENSIONS

def is_previewable_text(ext: str) -> bool:
    """Check if extension is a previewable text file."""
    return ext.lower() in PREVIEW_TEXT_EXTENSIONS

def is_previewable_pdf_docx(ext: str) -> bool:
    """Check if extension is PDF or DOCX."""
    return ext.lower() in PREVIEW_PDF_DOCX_EXTENSIONS

def is_previewable(ext: str) -> bool:
    """Check if extension is previewable."""
    return ext.lower() in PREVIEWABLE_EXTENSIONS
```

**Beneficios:**
- ✅ Elimina duplicación (Regla 4)
- ✅ Un solo lugar para mantener extensiones
- ✅ Funciones helper para claridad
- ✅ Reduce tokens en futuras lecturas

---

### Propuesta 2: Mejorar Encapsulación de QuickPreviewCache (PRIORIDAD ALTA)

**Modificar:** `app/ui/windows/quick_preview_cache.py`

```python
def update_cache_entry(self, index: int, path: str, pixmap: QPixmap) -> None:
    """Update cache entry with pixmap and mtime."""
    self._cache[index] = pixmap
    try:
        if os.path.exists(path):
            self._cache_mtime[index] = os.path.getmtime(path)
        else:
            self._cache_mtime[index] = 0
    except (OSError, ValueError):
        self._cache_mtime[index] = 0

def _invalidate_cache_entry(self, index: int) -> None:
    """Invalidate cache entry for given index."""
    if index in self._cache:
        del self._cache[index]
    if index in self._cache_mtime:
        del self._cache_mtime[index]
```

**Modificar:** `app/ui/windows/quick_preview_loader.py`

```python
# Reemplazar líneas 43-56 con:
if max_size:
    preview_service = self._cache._preview_service  # Cambiar a método público
    pixmap = preview_service.get_quicklook_pixmap(current_path, max_size)
    if not pixmap.isNull():
        header_text = Path(current_path).name
        self._cache.update_cache_entry(index, current_path, pixmap)
        return pixmap, header_text
```

**Beneficios:**
- ✅ Mejor encapsulación
- ✅ Interfaz clara
- ✅ Más fácil de testear

---

### Propuesta 3: Estandarizar Logging (PRIORIDAD MEDIA)

**Modificar:** `app/services/pdf_renderer.py`

```python
# Reemplazar prints con logger
from app.core.logger import get_logger

logger = get_logger(__name__)

# En lugar de print(), usar:
logger.info("PyMuPDF imported successfully...")
logger.error("Failed to import PyMuPDF...")
```

**Modificar:** `app/services/preview_pdf_service.py`

```python
# Mover logger a nivel de módulo
from app.core.logger import get_logger

logger = get_logger(__name__)

# Eliminar imports de logging dentro de métodos
```

**Beneficios:**
- ✅ Consistencia con el resto del código
- ✅ Logs van a archivo
- ✅ Mejor debugging

---

### Propuesta 4: Simplificar Lógica de Cache (PRIORIDAD MEDIA)

**Modificar:** `app/ui/windows/quick_preview_cache.py`

Extraer método `_invalidate_cache_entry()` y usarlo en los 3 lugares donde se repite.

**Beneficios:**
- ✅ Menos código duplicado
- ✅ Más fácil de mantener

---

## CÓDIGO MUERTO DETECTADO

### ❌ No se detectó código muerto

Todos los cambios realizados son funcionales y necesarios.

---

## VIOLACIONES DE ARQUITECTURA

### ✅ Separación de Capas: CORRECTO

- `services/` → Lógica de negocio (renderizado PDF, preview)
- `ui/windows/` → Componentes UI (ventanas, widgets)
- `managers/` → No se modificó

### ✅ Dependencias: CORRECTO

- Services no importan UI
- Managers no importan UI directamente
- Separación correcta

---

## MÉTRICAS DE CÓDIGO

| Archivo | Líneas | Responsabilidad | Estado |
|---------|--------|-----------------|--------|
| `quick_preview_loader.py` | 84 | Carga de previews | ✅ OK |
| `quick_preview_cache.py` | 144 | Cache de previews | ✅ OK |
| `preview_pdf_service.py` | 283 | Servicio de preview PDF | ✅ OK (< 800) |
| `pdf_renderer.py` | 177 | Renderizado PDF | ✅ OK |
| `quick_preview_window.py` | 221 | Ventana de preview | ✅ OK |

**Todas las clases cumplen límite de 800 líneas (Regla 3)**

---

## PRIORIDAD DE REFACTORIZACIÓN

### 🔴 ALTA PRIORIDAD (Hacer primero)

1. **Centralizar extensiones de archivo** (Propuesta 1)
   - Impacto: Elimina duplicación en 4 archivos
   - Esfuerzo: Bajo
   - Beneficio: Alto

2. **Mejorar encapsulación de cache** (Propuesta 2)
   - Impacto: Mejora mantenibilidad
   - Esfuerzo: Bajo
   - Beneficio: Medio-Alto

### 🟡 MEDIA PRIORIDAD (Hacer después)

3. **Estandarizar logging** (Propuesta 3)
   - Impacto: Consistencia
   - Esfuerzo: Bajo
   - Beneficio: Medio

4. **Simplificar lógica de cache** (Propuesta 4)
   - Impacto: Menos duplicación
   - Esfuerzo: Muy bajo
   - Beneficio: Medio

### 🟢 BAJA PRIORIDAD (Opcional)

5. **Completar type hints** (Mejora menor)
6. **Mover imports a nivel de módulo** (Optimización menor)

---

## CONCLUSIÓN

**Estado general:** ✅ El código cumple la mayoría de las reglas del proyecto.

**Problemas críticos encontrados:**
1. Duplicación de extensiones de archivo (4 lugares)
2. Acceso a atributos privados (violación de encapsulación)

**Recomendación:** 
- Aplicar Propuestas 1 y 2 (ALTA PRIORIDAD)
- Las demás son mejoras opcionales que pueden hacerse después

**Impacto en tokens:** 
- Las propuestas reducirán tokens futuros al centralizar constantes
- Mejorarán mantenibilidad sin aumentar complejidad

