# Contratos de Producto

Este documento define los contratos CRÍTICOS del sistema que garantizan el comportamiento correcto visible para el usuario. Estos contratos están protegidos por tests CRÍTICOS que nunca deben modificarse sin cambiar primero el código de producción.

---

## 1. Estado de Archivos

### Qué promete al usuario

Cuando un usuario marca un archivo con un estado (por ejemplo, "trabajado" o "pendiente") y luego edita ese archivo, el sistema debe seguir funcionando correctamente. El usuario debe poder consultar el estado del archivo sin que la aplicación se bloquee o muestre información incorrecta.

### Qué se considera comportamiento correcto

- Si un usuario establece un estado para un archivo y luego modifica el contenido del archivo, el sistema debe responder correctamente cuando se consulta el estado.
- La respuesta puede ser:
  - El mismo estado que se había establecido (si el sistema reconoce que es el mismo archivo)
  - Ningún estado (si el sistema decide que es un archivo diferente)
- Lo importante es que el sistema **nunca debe crashear** ni retornar un estado incorrecto (por ejemplo, el estado de otro archivo).
- Múltiples consultas del mismo archivo deben retornar resultados consistentes.

### Test CRÍTICO que lo protege

**Archivo:** `tests/test_file_state_contract.py`  
**Test:** `TestFileStateContract::test_file_state_remains_accessible_after_file_modification`

### Qué NO debe comprobar el test

- No inspecciona caches internas ni estructuras de datos privadas
- No llama métodos privados del sistema
- No verifica cómo se almacena el estado internamente
- No depende de tiempos específicos o delays artificiales
- Solo usa la API pública: `set_file_state()` y `get_file_state()`

### Qué significa que este test falle

Si este test falla, **siempre es un bug de producto**. El usuario ha experimentado un comportamiento incorrecto:
- La aplicación puede haber crasheado al consultar el estado de un archivo editado
- El sistema puede estar retornando estados incorrectos o inconsistentes
- El sistema puede estar en un estado inconsistente que afecta la experiencia del usuario

**Acción requerida:** Corregir el código de producción para que cumpla el contrato. **No modificar el test.**

---

## 2. Sidebar – Doble Clic

### Qué promete al usuario

Cuando un usuario hace doble clic en una carpeta visible en el sidebar, el sistema debe reconocer correctamente esa acción y comunicar la intención de navegar a esa carpeta. El sistema no debe crashear ni ignorar la acción del usuario.

### Qué se considera comportamiento correcto

- Cuando el usuario hace doble clic en una carpeta del sidebar, el sistema debe emitir una señal de navegación con el path correcto de esa carpeta.
- El path emitido debe corresponder exactamente a la carpeta en la que el usuario hizo clic.
- El sistema debe funcionar correctamente incluso si se hace doble clic en diferentes carpetas de forma consecutiva.
- El sistema **nunca debe crashear** al procesar un doble clic.

### Test CRÍTICO que lo protege

**Archivo:** `tests/test_sidebar_contract.py`  
**Test:** `TestSidebarDoubleClickContract::test_double_click_emits_folder_selected_signal`

### Qué NO debe comprobar el test

- No valida integración con otros componentes (TabManager, MainWindow, etc.)
- No verifica si se abrió una pestaña o se cambió la vista principal
- No inspecciona métodos privados del sidebar
- No verifica timers internos ni estructuras de datos privadas
- No depende de tiempos específicos o delays artificiales
- Solo valida que el sidebar emite correctamente la señal de navegación

### Qué significa que este test falle

Si este test falla, **siempre es un bug de producto**. El usuario ha experimentado un comportamiento incorrecto:
- El sidebar puede no estar respondiendo a dobles clics del usuario
- El sistema puede estar emitiendo paths incorrectos o no emitir nada
- El sistema puede crashear al procesar un doble clic
- La acción del usuario puede estar siendo ignorada

**Acción requerida:** Corregir el código de producción para que cumpla el contrato. **No modificar el test.**

---

## 3. Preview / Iconos (R16)

### Qué promete al usuario

Cuando el sistema necesita mostrar un icono o preview de un archivo en la interfaz, siempre debe mostrar algo válido. Incluso si el archivo es desconocido, no tiene icono asociado, o hay un error al obtenerlo, el sistema debe mostrar un icono de respaldo (fallback) en lugar de mostrar nada, un icono roto, o causar que la aplicación se bloquee.

### Qué se considera comportamiento correcto

- Cuando se solicita un icono o preview de un archivo, el sistema **nunca debe devolver un icono inválido** a la interfaz de usuario.
- Un icono válido es:
  - No nulo (existe)
  - Tiene dimensiones mayores que cero (tiene ancho y alto)
  - Puede ser mostrado correctamente en la interfaz
- Si la fuente original del icono falla o devuelve un icono inválido, el sistema debe aplicar automáticamente un icono de respaldo (fallback).
- El sistema debe funcionar correctamente incluso para:
  - Archivos con extensiones desconocidas
  - Archivos que no existen
  - Archivos que no tienen icono asociado en el sistema operativo
- El sistema **nunca debe crashear** al intentar obtener un icono.

### Test CRÍTICO que lo protege

**Archivo:** `tests/test_preview_icon_contract.py`  
**Test:** `TestPreviewIconContract::test_always_returns_valid_pixmap_on_failure`

### Qué NO debe comprobar el test

- No inspecciona caches internas de iconos
- No verifica qué método específico se usó para obtener el icono
- No llama métodos privados del servicio de iconos
- No verifica el contenido visual del icono (solo que es válido)
- No depende de tiempos específicos o delays artificiales
- Solo usa la API pública: `get_file_preview()`

### Qué significa que este test falle

Si este test falla, **siempre es un bug de producto**. El usuario ha experimentado un comportamiento incorrecto:
- La interfaz puede mostrar espacios vacíos donde deberían aparecer iconos
- La aplicación puede crashear al intentar mostrar un icono
- Pueden aparecer iconos rotos o inválidos en la interfaz
- La experiencia visual del usuario se ve afectada negativamente

**Acción requerida:** Corregir el código de producción para que cumpla el contrato. **No modificar el test.**

---

## Gobernanza de Tests CRÍTICOS

### Regla fundamental

**Si un test CRÍTICO falla, siempre se debe cambiar el código de producción, nunca el test.**

Los tests CRÍTICOS definen el contrato del producto. Modificarlos sin cambiar primero el código de producción rompe la garantía de calidad que proporcionan.

### Cuándo modificar un test CRÍTICO

Un test CRÍTICO solo debe modificarse si:
1. El contrato de producto ha cambiado oficialmente (requisito de negocio)
2. El test tiene un error lógico que no refleja el contrato real
3. Se ha refactorizado el código de producción y el test necesita ajustes menores para seguir validando el mismo contrato

En todos los casos, cualquier modificación debe ser revisada y aprobada antes de implementarse.

### Mantenimiento

Este documento debe actualizarse cada vez que:
- Se añade un nuevo contrato de producto CRÍTICO
- Se modifica un contrato existente
- Se cambia el test que protege un contrato

---

**Última actualización:** Diciembre 2024

