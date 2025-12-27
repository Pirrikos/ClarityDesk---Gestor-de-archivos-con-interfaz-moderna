# REVISIÓN VISUAL Y UX - ClarityDesk Pro

**Fecha:** 2025-01-XX  
**Objetivo:** Mejorar claridad visual, coherencia y percepción profesional de la aplicación

---

## RESUMEN EJECUTIVO

La aplicación tiene una base visual sólida con estilo oscuro tipo Raycast, pero presenta **inconsistencias visuales** y **falta de feedback** en estados críticos que reducen la claridad y profesionalismo. Se identificaron **12 problemas principales** clasificados por prioridad.

---

## 1. CLARIDAD VISUAL - ¿Dónde está el usuario?

### 🔴 ALTA PRIORIDAD

#### 1.1 Falta indicación visual del tab activo en el sidebar
**Problema:** No hay forma visual de saber qué carpeta está activa en el `FolderTreeSidebar`. El usuario puede estar viendo una carpeta pero no sabe cuál es.

**Ubicación:** `app/ui/widgets/folder_tree_delegate.py` (línea 229-328)

**Solución propuesta:**
- Añadir un **indicador visual sutil** (línea vertical izquierda de 3px, color `#3B82F6`) en el ítem del sidebar que corresponde al tab activo
- Alternativamente: fondo sutil `rgba(59, 130, 246, 0.15)` en el ítem activo
- El indicador debe actualizarse cuando cambia el tab activo (`activeTabChanged` signal)

**Por qué mejora:** Elimina confusión sobre qué carpeta está abierta. Es un patrón estándar en navegadores y exploradores de archivos.

---

#### 1.2 Toolbar con fondo blanco rompe coherencia visual
**Problema:** El `ViewToolbar` tiene fondo blanco (`#ffffff`) mientras el resto de la app es oscuro (`#111318`). Genera contraste excesivo y sensación de desconexión.

**Ubicación:** `app/ui/widgets/view_toolbar.py` (línea 41-46)

**Solución propuesta:**
- Cambiar fondo del toolbar a `#1A1D22` (similar al sidebar)
- Mantener borde inferior sutil `rgba(255,255,255,0.08)` para separación
- Ajustar colores de texto si es necesario para mantener contraste

**Por qué mejora:** Unifica la identidad visual oscura y reduce distracción visual.

---

### 🟡 MEDIA PRIORIDAD

#### 1.3 Breadcrumb oculto reduce contexto
**Problema:** El `FocusHeaderPanel` está oculto (`container._focus_panel.hide()`), eliminando información de contexto sobre la ruta actual.

**Ubicación:** `app/ui/widgets/file_view_setup.py` (línea 85)

**Solución propuesta:**
- Mostrar breadcrumb de forma compacta (solo nombre de carpeta activa, no ruta completa)
- Posicionarlo en el toolbar o como texto discreto sobre el contenido
- Estilo: texto `#8e92a0`, tamaño 12px, sin fondo

**Por qué mejora:** Proporciona contexto mínimo sin ocupar espacio excesivo.

---

## 2. JERARQUÍA VISUAL

### 🔴 ALTA PRIORIDAD

#### 2.1 Selección de tiles poco visible
**Problema:** La selección en `FileTile` solo muestra un borde azul de 2px (`#4A90E2`). Con muchos tiles seleccionados, es difícil distinguirlos rápidamente.

**Ubicación:** `app/ui/widgets/file_tile_paint.py` (línea 34-36)

**Solución propuesta:**
- Añadir fondo translúcido `rgba(59, 130, 246, 0.12)` además del borde
- Mantener borde de 2px pero aumentar opacidad a `rgba(59, 130, 246, 0.9)`
- Aplicar mismo estilo en vista Grid y Lista

**Por qué mejora:** Mejora visibilidad de selección múltiple y reduce errores al operar con archivos.

---

### 🟡 MEDIA PRIORIDAD

#### 2.2 Botones de navegación (Back/Forward) poco destacados
**Problema:** Los botones Back/Forward tienen estilo muy sutil y pueden pasar desapercibidos.

**Ubicación:** `app/ui/widgets/toolbar_button_styles.py` (línea 46-69)

**Solución propuesta:**
- Aumentar tamaño de fuente de 16px a 18px
- Añadir hover state más visible: `rgba(255,255,255,0.15)` en lugar de transparente
- Iconos más claros o añadir iconos SVG en lugar de solo texto

**Por qué mejora:** Facilita descubrimiento de funcionalidad de navegación.

---

## 3. ESTADOS Y FEEDBACK

### 🔴 ALTA PRIORIDAD

#### 3.1 Drag & Drop sin feedback visual de destino válido/inválido
**Problema:** Al arrastrar archivos, no hay indicación visual clara de:
- Qué carpetas aceptan el drop (válido)
- Qué carpetas rechazan el drop (inválido)
- Qué acción se realizará (mover vs copiar)

**Ubicación:** `app/ui/widgets/file_tile_drag.py`, `app/ui/widgets/file_tile_paint.py`

**Solución propuesta:**
- **Destino válido:** Añadir overlay verde translúcido `rgba(59, 165, 93, 0.2)` + borde verde `#3BA55D` de 2px en `dragMoveEvent` cuando `event.accept()`
- **Destino inválido:** Overlay rojo translúcido `rgba(239, 68, 68, 0.15)` + borde rojo `#EF4444` cuando `event.ignore()`
- **Cursor:** Cambiar a `Qt.CursorShape.DragMoveCursor` sobre destino válido, `Qt.CursorShape.ForbiddenCursor` sobre inválido
- Aplicar mismo patrón en `FolderTreeSidebar` para drops en carpetas del árbol

**Por qué mejora:** Reduce errores de drop y mejora comprensión inmediata de acciones permitidas.

---

#### 3.2 Falta hover state en FileTile
**Problema:** Los `FileTile` no tienen estado hover visible, reduciendo feedback de interactividad.

**Ubicación:** `app/ui/widgets/file_tile_paint.py`, `app/ui/widgets/file_tile_controller.py`

**Solución propuesta:**
- Añadir hover state: fondo translúcido `rgba(255, 255, 255, 0.08)` en `mouseEnterEvent`
- Remover en `mouseLeaveEvent`
- No aplicar si el tile está seleccionado (priorizar selección)

**Por qué mejora:** Mejora percepción de interactividad y clarifica qué elementos son clickeables.

---

### 🟡 MEDIA PRIORIDAD

#### 3.3 Transiciones abruptas al cambiar de vista (Grid ↔ Lista)
**Problema:** El cambio entre Grid y Lista es instantáneo, puede desorientar.

**Ubicación:** `app/ui/widgets/file_view_sync.py` (probablemente)

**Solución propuesta:**
- Añadir fade transition de 150ms al cambiar entre vistas
- Usar `QPropertyAnimation` con opacidad del `QStackedWidget`

**Por qué mejora:** Transiciones suaves mejoran percepción de calidad y reducen sensación de "salto" visual.

---

#### 3.4 Estados de botones en toolbar poco claros
**Problema:** Los botones Grid/List tienen estados checked/unchecked pero la diferencia visual es sutil.

**Ubicación:** `app/ui/widgets/toolbar_button_styles.py` (línea 8-43)

**Solución propuesta:**
- Estado checked: mantener fondo `#1F2228` pero añadir borde sutil `rgba(255,255,255,0.2)`
- Estado unchecked: mantener transparente pero hover más visible
- Añadir iconos pequeños (cuadrícula/lista) para claridad

**Por qué mejora:** Clarifica qué vista está activa sin necesidad de interpretar colores.

---

## 4. CONSISTENCIA

### 🔴 ALTA PRIORIDAD

#### 4.1 Inconsistencia de hover entre sidebar y tiles
**Problema:** El sidebar tiene hover state (`#1F2228` con opacidad), pero los tiles no. Mismo patrón de interacción debería verse igual.

**Ubicación:** `app/ui/widgets/folder_tree_delegate.py` (línea 264-286) vs `app/ui/widgets/file_tile_paint.py`

**Solución propuesta:**
- Unificar hover state: usar mismo color `rgba(255, 255, 255, 0.08)` en ambos
- Mismo radio de borde (6px en sidebar, 14px en tiles - mantener proporcional)

**Por qué mejora:** Coherencia visual mejora percepción de calidad profesional.

---

### 🟡 MEDIA PRIORIDAD

#### 4.2 Vista Lista y Grid tienen estilos diferentes
**Problema:** La vista Lista tiene fondo transparente y estilos propios, mientras Grid usa fondo del contenedor. Deberían compartir más elementos visuales.

**Ubicación:** `app/ui/widgets/list_styles.py` vs `app/ui/widgets/file_view_setup.py`

**Solución propuesta:**
- Unificar colores de texto: ambas usan `#E6E7EA` (ya consistente)
- Unificar hover: `rgba(255,255,255,0.06)` en lista vs `rgba(255,255,255,0.08)` en grid → usar `0.08` en ambas
- Unificar selección: mismo color y opacidad en ambas vistas

**Por qué mejora:** Reduce confusión al alternar entre vistas.

---

#### 4.3 Espaciado inconsistente entre componentes
**Problema:** Diferentes márgenes y paddings entre toolbar (20px), sidebar (16px), y contenido.

**Ubicación:** Múltiples archivos de setup

**Solución propuesta:**
- Establecer sistema de espaciado: 8px (pequeño), 16px (medio), 24px (grande)
- Toolbar: padding horizontal 16px (reducir de 20px)
- Sidebar: mantener 16px
- Contenido: padding 16px desde bordes

**Por qué mejora:** Mejora ritmo visual y percepción de orden.

---

## 5. DISEÑO FUNCIONAL

### 🟡 MEDIA PRIORIDAD

#### 5.1 Botón "+" del sidebar podría ser más descriptivo
**Problema:** El botón "+" no indica claramente que añade un nuevo Focus/tab.

**Ubicación:** `app/ui/widgets/folder_tree_sidebar.py` (línea 102)

**Solución propuesta:**
- Cambiar texto a "+ Añadir Focus" o mantener "+" pero añadir tooltip "Añadir carpeta como Focus"
- Tooltip aparece después de 500ms de hover

**Por qué mejora:** Reduce fricción para nuevos usuarios.

---

#### 5.2 Botón de menú (tres puntitos) poco visible
**Problema:** Los tres puntitos en carpetas raíz del sidebar tienen opacidad baja (180/255) y pueden pasar desapercibidos.

**Ubicación:** `app/ui/widgets/folder_tree_delegate.py` (línea 344)

**Solución propuesta:**
- Aumentar opacidad base a 220/255 (sin hover)
- Hover: 255/255 (ya implementado)
- Aumentar tamaño de puntos de 2px a 2.5px radius

**Por qué mejora:** Mejora descubribilidad de funcionalidad de menú contextual.

---

### 🟢 BAJA PRIORIDAD

#### 5.3 Animaciones de expansión del sidebar podrían ser más rápidas
**Problema:** Las animaciones de expansión/colapso (140-180ms) pueden sentirse lentas en uso repetido.

**Ubicación:** `app/ui/widgets/folder_tree_delegate.py` (línea 80-226)

**Solución propuesta:**
- Reducir duración de 140ms a 100ms para chevron
- Reducir de 180ms a 120ms para hijos
- Mantener easing `OutCubic` para suavidad

**Por qué mejora:** Mejora percepción de velocidad sin perder suavidad.

---

## 6. MICRO-UX

### 🟡 MEDIA PRIORIDAD

#### 6.1 Cursor no cambia al arrastrar archivos
**Problema:** El cursor permanece como flecha durante drag, no indica acción de arrastre.

**Ubicación:** `app/ui/widgets/tile_drag_handler.py` (probablemente)

**Solución propuesta:**
- Cambiar cursor a `Qt.CursorShape.DragMoveCursor` al iniciar drag
- Restaurar cursor normal al soltar o cancelar

**Por qué mejora:** Feedback inmediato de acción en curso.

---

#### 6.2 Falta indicador de carga al generar iconos
**Problema:** Cuando se generan iconos/previews, no hay feedback visual de progreso.

**Ubicación:** `app/services/icon_service.py` (probablemente)

**Solución propuesta:**
- Mostrar spinner discreto en tile mientras carga icono
- O: mostrar placeholder con opacidad reducida hasta que carga

**Por qué mejora:** Evita percepción de "congelamiento" durante carga.

---

### 🟢 BAJA PRIORIDAD

#### 6.3 Scrollbar del sidebar podría ser más discreta
**Problema:** La scrollbar es visible siempre, puede distraer.

**Ubicación:** `app/ui/widgets/folder_tree_styles.py` (línea 136-166)

**Solución propuesta:**
- Hacer scrollbar solo visible al hacer hover sobre sidebar
- O: reducir ancho de 8px a 6px y opacidad del handle

**Por qué mejora:** Reduce ruido visual cuando no se necesita.

---

## RESUMEN DE PRIORIDADES

### 🔴 ALTA PRIORIDAD (Implementar primero)
1. Indicación visual del tab activo en sidebar
2. Unificar fondo del toolbar con tema oscuro
3. Feedback visual de drag & drop (válido/inválido)
4. Añadir hover state a FileTile
5. Mejorar visibilidad de selección de tiles
6. Unificar hover states entre componentes

### 🟡 MEDIA PRIORIDAD (Implementar después)
7. Mostrar breadcrumb de forma compacta
8. Mejorar estados de botones en toolbar
9. Transiciones suaves al cambiar vista
10. Unificar estilos entre Lista y Grid
11. Mejorar visibilidad de botón de menú
12. Cambiar cursor durante drag

### 🟢 BAJA PRIORIDAD (Opcional)
13. Acelerar animaciones del sidebar
14. Scrollbar más discreta
15. Indicador de carga de iconos

---

## NOTAS DE IMPLEMENTACIÓN

- **No cambiar identidad visual:** Mantener paleta oscura tipo Raycast
- **Mantener accesibilidad:** Asegurar contraste suficiente en todos los cambios
- **Probar en ambos modos:** Grid y Lista deben verse coherentes
- **Considerar rendimiento:** Animaciones deben ser ligeras (<200ms, GPU-accelerated)

---

## MÉTRICAS DE ÉXITO

Después de implementar cambios de alta prioridad:
- ✅ Usuario puede identificar inmediatamente qué carpeta está activa
- ✅ Feedback visual claro durante drag & drop reduce errores
- ✅ Coherencia visual entre componentes mejora percepción profesional
- ✅ Hover states mejoran descubribilidad de interactividad

---

**Fin del informe**










