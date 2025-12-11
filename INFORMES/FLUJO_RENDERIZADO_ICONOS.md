# FLUJO COMPLETO DE RENDERIZADO DE ICONOS
## ClarityDesk Pro - Trazado Exacto del Pipeline

---

## RESUMEN EJECUTIVO

Este documento traza el flujo COMPLETO desde que un widget solicita un icono hasta que se renderiza en pantalla.

**Punto de entrada:** `FileTile._add_icon_zone()` o `FileStackTile._add_icon_zone()`
**Punto de salida:** `QLabel.setPixmap()` + `QLabel.paintEvent()` (interno de Qt)

---

## FLUJO PASO A PASO

### FASE 1: SOLICITUD DESDE WIDGET

#### PASO 1.1: FileTile._add_icon_zone()
**Archivo:** `app/ui/widgets/file_tile.py`
**Línea:** 100
**Código:**
```python
pixmap = self._icon_service.get_file_preview(self._file_path, QSize(96, 96))
```
**Parámetros:**
- `self._file_path`: Ruta completa del archivo (ej: `C:\Users\...\archivo.txt`)
- `QSize(96, 96)`: Tamaño objetivo del icono

**Retorna:** `QPixmap` (puede ser null o visualmente vacío)

**Siguiente paso:** Verificación con `safe_pixmap()` (PASO 1.3)

---

#### PASO 1.2: FileStackTile._add_icon_zone()
**Archivo:** `app/ui/widgets/file_stack_tile.py`
**Línea:** 89
**Código:**
```python
first_file = self._file_stack.files[0] if self._file_stack.files else None
if first_file:
    pixmap = self._icon_service.get_file_preview(first_file, QSize(96, 96))
```
**Parámetros:**
- `first_file`: Primer archivo del stack (ej: `C:\Users\...\archivo.txt`)
- `QSize(96, 96)`: Tamaño objetivo del icono

**Retorna:** `QPixmap` (puede ser null o visualmente vacío)

**Siguiente paso:** Verificación con `safe_pixmap()` (PASO 1.3)

---

#### PASO 1.3: Verificación con safe_pixmap()
**Archivo:** `app/ui/widgets/icon_fallback_helper.py`
**Línea:** 105-130
**Código:**
```python
pixmap = safe_pixmap(pixmap, icon_width, ext)
```

**Proceso interno:**
1. Verifica si `pixmap` es `None` o `isNull()` → Si es así, llama `get_default_icon()` (PASO 1.4)
2. Llama `is_pixmap_visually_empty()` para detectar:
   - Alpha < 50 en el centro
   - Brightness > 240 y saturation < 15
   - Muestra de píxeles: si `visible_points <= 1` → vacío
3. Si está vacío → llama `get_default_icon()` (PASO 1.4)
4. Si es válido → retorna el pixmap original

**Retorna:** `QPixmap` válido o fallback

**Siguiente paso:** Asignación a `self._icon_pixmap` y creación de `QLabel` (PASO 1.5)

---

#### PASO 1.4: Fallback con get_default_icon()
**Archivo:** `app/ui/widgets/icon_fallback_helper.py`
**Línea:** 133-182
**Código:**
```python
pixmap = get_default_icon(icon_width, ext)
```

**Proceso interno:**
1. Obtiene `svg_name` desde `get_svg_for_extension(ext)` → retorna nombre SVG (ej: `"generic.svg"`, `"archive.svg"`)
2. Llama `render_svg_icon(svg_name, target_size, ext)` (PASO 2.1)
3. Verifica que el pixmap resultante tenga `alpha > 0` en el centro
4. Si falla → intenta con `"generic.svg"`
5. Si todo falla → retorna pixmap gris sólido `QColor(200, 200, 200)`

**Retorna:** `QPixmap` con icono SVG o gris sólido

**Siguiente paso:** Asignación a `self._icon_pixmap` y creación de `QLabel` (PASO 1.5)

---

#### PASO 1.5: Creación de QLabel y asignación de pixmap
**Archivo:** `app/ui/widgets/file_tile.py` (líneas 132-145) o `file_stack_tile.py` (líneas 127-145)
**Código:**
```python
self._icon_pixmap = pixmap  # Guarda referencia

self._icon_label = QLabel()
self._icon_label.setFixedSize(icon_width, icon_height)  # 96x96
self._icon_label.setPixmap(pixmap)  # ← AQUÍ SE ASIGNA EL PIXMAP
self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
self._icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

if pixmap and not pixmap.isNull():
    self._icon_label.setVisible(True)  # ← FORZAR VISIBILIDAD

# Aplicar sombra
self._icon_shadow = QGraphicsDropShadowEffect(self._icon_label)
# ... configuración de sombra ...

layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
```

**Eventos Qt que ocurren:**
- `QLabel.setPixmap()` → Internamente Qt llama `update()` → dispara `paintEvent()`
- `QLabel.paintEvent()` → Dibuja el pixmap en el widget

**Siguiente paso:** Renderizado por Qt (PASO 1.6)

---

#### PASO 1.6: Renderizado por Qt (paintEvent interno)
**Archivo:** Interno de Qt (no visible)
**Proceso:**
- Qt llama `QLabel.paintEvent()` automáticamente
- Dibuja el `QPixmap` en el área del `QLabel`
- Respeta `setVisible()`, `setStyleSheet()`, `setOpacity()`, etc.

**Resultado:** Icono visible en pantalla (o invisible si hay problemas)

---

### FASE 2: SERVICIO DE ICONOS (IconService)

#### PASO 2.1: IconService.get_file_preview()
**Archivo:** `app/services/icon_service.py`
**Línea:** 93-99
**Código:**
```python
def get_file_preview(self, path: str, size: QSize) -> QPixmap:
    if os.path.isdir(path):
        return self._get_folder_preview(path, size)
    else:
        raw_pixmap = get_file_preview(path, size, self._icon_provider)
        return apply_visual_normalization(raw_pixmap, size)
```

**Proceso:**
- Si es carpeta → llama `_get_folder_preview()` (PASO 2.2)
- Si es archivo → llama `preview_service.get_file_preview()` (PASO 3.1)
- Aplica normalización visual con `apply_visual_normalization()` (PASO 2.3)

**Retorna:** `QPixmap` normalizado

---

#### PASO 2.2: IconService._get_folder_preview() (solo carpetas)
**Archivo:** `app/services/icon_service.py`
**Línea:** 101-107
**Código:**
```python
def _get_folder_preview(self, path: str, size: QSize) -> QPixmap:
    high_res_size = QSize(256, 256)
    raw_pixmap = get_windows_shell_icon(path, high_res_size, self._icon_provider, scale_to_target=False)
    raw_pixmap = self._scale_folder_icon(raw_pixmap, size)
    raw_pixmap = self._apply_folder_fallbacks(path, raw_pixmap, size)
    return apply_visual_normalization(raw_pixmap, size)
```

**Proceso:**
1. Obtiene icono de alta resolución (256x256) desde Windows shell
2. Escala a tamaño objetivo
3. Aplica fallbacks si es necesario
4. Normaliza visualmente (PASO 2.3)

**Retorna:** `QPixmap` normalizado de carpeta

---

#### PASO 2.3: apply_visual_normalization()
**Archivo:** `app/services/icon_normalizer.py`
**Línea:** 11-30
**Código:**
```python
def apply_visual_normalization(raw_pixmap: QPixmap, target_size: QSize) -> QPixmap:
    # Crea canvas transparente
    canvas = QPixmap(target_size)
    canvas.fill(Qt.GlobalColor.transparent)
    
    # Escala a 90% y centra
    scaled_pixmap, x_offset, y_offset = scale_and_center_pixmap(raw_pixmap, target_size)
    
    # Aplica esquinas redondeadas y overlay blanco 5%
    apply_rounded_clip(painter, target_size)
    painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
    apply_white_overlay(painter, canvas)
    
    return canvas
```

**Efectos aplicados:**
- Escala a 90% del tamaño objetivo
- Centra el icono
- Esquinas redondeadas (radio 8px)
- Overlay blanco 5% para contraste

**Retorna:** `QPixmap` normalizado con efectos visuales

---

### FASE 3: SERVICIO DE PREVIEW (PreviewService)

#### PASO 3.1: preview_service.get_file_preview()
**Archivo:** `app/services/preview_service.py`
**Línea:** 32-38
**Código:**
```python
def get_file_preview(path: str, size: QSize, icon_provider) -> QPixmap:
    return _get_file_preview_impl(path, size, icon_provider)
```

**Proceso:**
- Llama `_get_file_preview_impl()` (PASO 3.2)

---

#### PASO 3.2: _get_file_preview_impl()
**Archivo:** `app/services/preview_service.py`
**Línea:** 41-49
**Código:**
```python
def _get_file_preview_impl(path: str, size: QSize, icon_provider) -> QPixmap:
    if not path or not os.path.exists(path):
        return QPixmap()
    
    if os.path.isdir(path):
        return _get_folder_preview_impl(path, size, icon_provider)
    
    return _get_file_preview_impl_helper(path, size, icon_provider)
```

**Proceso:**
- Si no existe → retorna `QPixmap()` vacío
- Si es carpeta → llama `_get_folder_preview_impl()` (no usado en flujo principal)
- Si es archivo → llama `_get_file_preview_impl_helper()` (PASO 3.3)

---

#### PASO 3.3: _get_file_preview_impl_helper()
**Archivo:** `app/services/preview_service.py`
**Línea:** 74-98
**Código:**
```python
def _get_file_preview_impl_helper(path: str, size: QSize, icon_provider) -> QPixmap:
    ext = Path(path).suffix.lower()
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.ico'}
    
    # Si es imagen → renderizar directamente
    if ext in image_extensions:
        return render_image_preview(path, size)
    
    # Obtener icono de Windows shell
    pixmap = get_windows_shell_icon(path, size, icon_provider)
    
    # Verificar si tiene mucho espacio en blanco
    if not skip_svg_fallback and not pixmap.isNull() and has_excessive_whitespace(pixmap, threshold=0.4):
        svg_name = get_svg_for_extension(ext)
        svg_pixmap = render_svg_icon(svg_name, size, ext)
        if not svg_pixmap.isNull():
            return svg_pixmap
    
    # Escalar y retornar
    return scale_pixmap_to_size(pixmap, size)
```

**Proceso:**
1. Si es imagen → llama `render_image_preview()` (PIL/Pillow)
2. Obtiene icono de Windows shell con `get_windows_shell_icon()` (PASO 3.4)
3. Si tiene mucho espacio en blanco (>40%) → intenta fallback SVG (PASO 3.5)
4. Escala a tamaño objetivo y retorna

**Retorna:** `QPixmap` con icono de Windows o SVG fallback

---

#### PASO 3.4: get_windows_shell_icon()
**Archivo:** `app/services/preview_service.py`
**Línea:** 101-118
**Código:**
```python
def get_windows_shell_icon(path: str, size: QSize, icon_provider, scale_to_target: bool = True) -> QPixmap:
    icon_size = max(size.width(), size.height())
    
    # Intento 1: Via ImageList (más alta resolución)
    pixmap = get_icon_via_imagelist(path, icon_size, hicon_to_qpixmap_at_size)
    if not pixmap.isNull():
        return scale_if_needed(pixmap, size)
    
    # Intento 2: Via ExtractIcon
    pixmap = get_icon_via_extracticon(path, size, hicon_to_qpixmap_at_size)
    if not pixmap.isNull():
        return pixmap
    
    # Intento 3: Via QIcon (fallback)
    return get_icon_via_qicon(path, size, icon_provider)
```

**Proceso:**
- Intenta obtener icono nativo de Windows en orden de calidad descendente
- Puede retornar iconos transparentes o visualmente vacíos (problema conocido)

**Retorna:** `QPixmap` con icono de Windows (puede ser transparente/vacío)

---

#### PASO 3.5: render_svg_icon() (fallback SVG)
**Archivo:** `app/services/icon_renderer.py`
**Línea:** 119-172
**Código:**
```python
def render_svg_icon(svg_name: str, size: QSize, ext: str = "") -> QPixmap:
    # Leer SVG desde assets/icons/
    svg_path = base_path / svg_name
    
    # Obtener color específico para el tipo de archivo
    svg_color = SVG_COLOR_MAP.get(svg_name, SVG_COLOR_MAP.get("generic.svg", QColor(127, 140, 141)))
    color_hex = f"#{svg_color.red():02x}{svg_color.green():02x}{svg_color.blue():02x}"
    
    # Leer contenido SVG
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    # Reemplazar stroke="currentColor" con color hexadecimal
    svg_content_colored = svg_content.replace('stroke="currentColor"', f'stroke="{color_hex}"')
    
    # Crear renderer desde contenido modificado
    svg_bytes_colored = QByteArray(svg_content_colored.encode('utf-8'))
    renderer_colored = QSvgRenderer(svg_bytes_colored)
    
    # Renderizar directamente con el color aplicado
    painter = QPainter(pix)
    if painter.isActive():
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer_colored.render(painter)
    painter.end()
    
    return pix
```

**Proceso:**
1. Lee SVG desde `assets/icons/{svg_name}`
2. Obtiene color desde `SVG_COLOR_MAP` (ej: `generic.svg` → `QColor(127, 140, 141)`)
3. Reemplaza `stroke="currentColor"` con color hexadecimal (ej: `stroke="#7f8c8d"`)
4. Crea `QSvgRenderer` desde contenido modificado
5. Renderiza con `QPainter` sobre pixmap transparente

**PROBLEMA CONOCIDO:** El SVG se renderiza con `alpha=0` (invisible)

**Retorna:** `QPixmap` con SVG renderizado (puede ser transparente)

---

## MAPA DE FLUJO VISUAL

```
┌─────────────────────────────────────────────────────────────────┐
│ WIDGET LAYER                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FileTile._add_icon_zone()                                      │
│  └─> icon_service.get_file_preview()                           │
│      │                                                           │
│      ├─> [SI ES CARPETA]                                        │
│      │   └─> _get_folder_preview()                              │
│      │       └─> get_windows_shell_icon()                       │
│      │       └─> apply_visual_normalization()                   │
│      │                                                           │
│      └─> [SI ES ARCHIVO]                                        │
│          └─> preview_service.get_file_preview()                 │
│              └─> _get_file_preview_impl_helper()               │
│                  ├─> [SI ES IMAGEN]                             │
│                  │   └─> render_image_preview()                │
│                  │                                               │
│                  └─> [SI NO ES IMAGEN]                          │
│                      └─> get_windows_shell_icon()               │
│                      └─> [SI TIENE MUCHO BLANCO]                │
│                          └─> render_svg_icon()                  │
│                      └─> scale_pixmap_to_size()                 │
│          └─> apply_visual_normalization()                       │
│                                                                  │
│  └─> safe_pixmap()                                              │
│      ├─> [SI ES NULL/VACÍO]                                     │
│      │   └─> get_default_icon()                                 │
│      │       └─> render_svg_icon()                              │
│      │                                                           │
│      └─> [SI ES VÁLIDO]                                         │
│          └─> retorna pixmap original                            │
│                                                                  │
│  └─> QLabel.setPixmap(pixmap)                                   │
│      └─> Qt paintEvent() (interno)                             │
│          └─> RENDERIZADO EN PANTALLA                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PUNTOS CRÍTICOS DE FALLO

### 1. Iconos de Windows transparentes/vacíos
**Ubicación:** `get_windows_shell_icon()` → retorna pixmap con `alpha=0` o `brightness > 240`
**Detección:** `is_pixmap_visually_empty()` en `safe_pixmap()`
**Solución actual:** Fallback a SVG

### 2. SVG renderizado con alpha=0
**Ubicación:** `render_svg_icon()` → `QSvgRenderer.render()` sobre pixmap transparente
**Problema:** Qt no renderiza correctamente `stroke="currentColor"` aunque se reemplace con color hexadecimal
**Estado:** NO RESUELTO

### 3. QLabel no visible
**Ubicación:** `FileTile._add_icon_zone()` / `FileStackTile._add_icon_zone()`
**Solución actual:** `setVisible(True)` forzado después de `setPixmap()`

---

## ARCHIVOS INVOLUCRADOS

### Widgets (UI)
- `app/ui/widgets/file_tile.py` - Widget de archivo individual
- `app/ui/widgets/file_stack_tile.py` - Widget de stack de archivos
- `app/ui/widgets/icon_fallback_helper.py` - Helper de fallback

### Servicios (Core)
- `app/services/icon_service.py` - Servicio principal de iconos
- `app/services/preview_service.py` - Servicio de previews
- `app/services/icon_normalizer.py` - Normalización visual
- `app/services/icon_renderer.py` - Renderizado de SVG

### Otros
- `app/services/windows_icon_extractor.py` - Extracción de iconos Windows
- `app/services/windows_icon_converter.py` - Conversión HICON → QPixmap
- `app/services/icon_extraction_fallbacks.py` - Fallbacks de extracción
- `app/services/preview_scaling.py` - Escalado de previews

---

## NOTAS IMPORTANTES

1. **NO modificar servicios core** (`preview_service.py`, `icon_service.py`, `icon_normalizer.py`) según reglas del proyecto.

2. **Solo modificar widgets** (`file_tile.py`, `file_stack_tile.py`) y helpers (`icon_fallback_helper.py`).

3. **El problema principal** es que `render_svg_icon()` genera pixmaps con `alpha=0`, haciendo que los iconos sean invisibles.

4. **La detección de vacío visual** funciona correctamente (`is_pixmap_visually_empty()`), pero el fallback SVG también falla.

5. **Qt no renderiza correctamente** SVGs con `stroke` sobre fondo transparente, incluso con color explícito.

---

## FIN DEL DOCUMENTO

