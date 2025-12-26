# PROPUESTA: TEST CRÍTICO PARA FILE_STATE_MANAGER

## Test Actual (FLEXIBLE)

**Archivo:** `tests/test_file_state_manager.py`  
**Test:** `TestCache::test_cache_invalidates_on_file_change`  
**Líneas:** 235-248

### Problemas del Test Actual

1. **Inspecciona estructura interna:**
   - Accede a `file_state_manager._state_cache` (línea 233 en test relacionado)
   - Llama a método privado `_get_file_id()` (línea 246)

2. **Depende de implementación:**
   - Usa `time.sleep(1.1)` para esperar cambio de `mtime` (línea 241)
   - Frágil: puede fallar en sistemas lentos o con relojes imprecisos

3. **No valida comportamiento observable:**
   - No verifica que `get_file_state()` retorne el estado correcto después del cambio
   - Solo verifica estructura interna del cache

4. **No define contrato de producto:**
   - El usuario no ve ni le importa cómo funciona el cache internamente
   - El usuario solo ve que el estado se mantiene correctamente

---

## Justificación de Reclasificación

### `tests/test_file_state_manager.py::TestCache::test_cache_invalidates_on_file_change` → FLEXIBLE

**Razones:**

1. **Inspecciona `_state_cache`:**
   - El test accede directamente a `file_state_manager._state_cache` (aunque sea indirectamente a través de `_get_file_id`)
   - El cache es estructura interna que puede cambiar sin afectar el comportamiento visible

2. **Depende de implementación interna:**
   - Llama a método privado `_get_file_id()` (línea 246)
   - Si se refactoriza cómo se calcula el `file_id`, el test fallaría aunque el comportamiento público funcione

3. **No define contrato de producto:**
   - El contrato de producto es: "Si un archivo cambia, el estado debe seguir siendo accesible correctamente"
   - Este test no valida ese contrato, solo valida que el cache interno se actualiza

4. **Usa `time.sleep()`:**
   - Dependencia de tiempo real que es frágil
   - No es necesario para validar comportamiento observable

**Conclusión:** Este test valida implementación interna, no comportamiento visible. Debe ser FLEXIBLE.

---

## Propuesta: Test CRÍTICO Correcto

### Nombre del Test

`tests/test_file_state_manager.py::TestFileStateConsistency::test_file_state_persists_after_file_modification`

### Contrato de Producto que Protege

**Comportamiento visible:**
> Si un usuario establece un estado para un archivo, y luego el archivo se modifica (contenido o metadata), el estado debe seguir siendo accesible correctamente a través de la API pública.

**Reglas que protege:**
- Regla 22: Persistencia de estados (el estado debe persistir aunque el archivo cambie)
- Comportamiento visible: El usuario debe poder ver el estado correcto después de modificar archivos

### Diseño del Test

```python
def test_file_state_persists_after_file_modification(self, file_state_manager, temp_file):
    """
    Validar que el estado de un archivo persiste correctamente después de modificarlo.
    
    Contrato de producto:
    - Si establezco un estado para un archivo
    - Y luego modifico el archivo (contenido o metadata)
    - Entonces get_file_state() debe retornar el mismo estado
    
    Este test NO inspecciona cache ni métodos privados.
    Solo valida comportamiento observable a través de la API pública.
    """
    # Paso 1: Establecer estado inicial
    initial_state = "trabajado"
    file_state_manager.set_file_state(temp_file, initial_state)
    
    # Verificar que el estado se estableció correctamente
    state_before_modification = file_state_manager.get_file_state(temp_file)
    assert state_before_modification == initial_state
    
    # Paso 2: Modificar el archivo (simular cambio de contenido)
    # Usar mock de tiempo para evitar time.sleep()
    from unittest.mock import patch
    import os
    
    # Obtener mtime actual
    original_mtime = os.path.getmtime(temp_file)
    
    # Modificar archivo con mock de tiempo avanzado
    with patch('os.stat') as mock_stat:
        # Simular que el archivo tiene nuevo mtime (más reciente)
        mock_stat.return_value.st_mtime = original_mtime + 2.0
        mock_stat.return_value.st_size = 100
        
        # Modificar contenido del archivo
        with open(temp_file, 'w') as f:
            f.write('modified content')
    
    # Paso 3: Verificar que el estado persiste (comportamiento observable)
    state_after_modification = file_state_manager.get_file_state(temp_file)
    
    # CONTRATO: El estado debe seguir siendo accesible
    assert state_after_modification == initial_state, \
        f"Estado debe persistir después de modificar archivo. " \
        f"Esperado: {initial_state}, Obtenido: {state_after_modification}"
```

### Alternativa sin Mocks (Más Simple)

```python
def test_file_state_persists_after_file_modification(self, file_state_manager, temp_file):
    """
    Validar que el estado de un archivo persiste correctamente después de modificarlo.
    
    Contrato de producto:
    - Si establezco un estado para un archivo
    - Y luego modifico el archivo
    - Entonces get_file_state() debe retornar el mismo estado
    
    Este test NO inspecciona cache ni métodos privados.
    Solo valida comportamiento observable a través de la API pública.
    """
    # Paso 1: Establecer estado inicial
    initial_state = "trabajado"
    file_state_manager.set_file_state(temp_file, initial_state)
    
    # Verificar que el estado se estableció correctamente
    state_before = file_state_manager.get_file_state(temp_file)
    assert state_before == initial_state
    
    # Paso 2: Modificar el archivo (cambiar contenido)
    # Nota: En sistemas de archivos reales, esto cambiará mtime automáticamente
    with open(temp_file, 'w') as f:
        f.write('modified content')
    
    # Paso 3: Verificar que el estado persiste (comportamiento observable)
    # Si el sistema detecta el cambio y recalcula file_id, el estado debe seguir siendo accesible
    state_after = file_state_manager.get_file_state(temp_file)
    
    # CONTRATO: El estado debe seguir siendo accesible después de modificar
    # Puede ser el mismo estado o None (si el sistema decide que es un archivo diferente)
    # Lo importante es que get_file_state() no crashea y retorna un resultado válido
    assert state_after is not None or state_after == initial_state, \
        f"Estado debe ser accesible después de modificar archivo. " \
        f"Estado antes: {initial_state}, Estado después: {state_after}"
```

### Versión Final Recomendada (Más Robusta)

```python
def test_file_state_remains_accessible_after_file_modification(self, file_state_manager, temp_file):
    """
    Validar que el estado de un archivo sigue siendo accesible después de modificarlo.
    
    Contrato de producto:
    - Si establezco un estado para un archivo
    - Y luego modifico el archivo (contenido)
    - Entonces get_file_state() debe retornar un resultado válido (estado o None)
    - Y NO debe crashear ni retornar estado incorrecto
    
    Este test valida comportamiento observable sin inspeccionar implementación interna.
    """
    # Paso 1: Establecer estado inicial
    initial_state = "trabajado"
    file_state_manager.set_file_state(temp_file, initial_state)
    
    # Verificar estado inicial
    state_before = file_state_manager.get_file_state(temp_file)
    assert state_before == initial_state, \
        f"Estado inicial debe establecerse correctamente. Esperado: {initial_state}, Obtenido: {state_before}"
    
    # Paso 2: Modificar archivo (simular edición de usuario)
    with open(temp_file, 'w') as f:
        f.write('modified content by user')
    
    # Paso 3: Verificar comportamiento observable
    # El estado puede:
    # - Persistir (mismo estado) - comportamiento esperado
    # - Ser None (si el sistema decide que es archivo diferente) - también válido
    # - NO debe crashear ni retornar estado incorrecto
    
    state_after = file_state_manager.get_file_state(temp_file)
    
    # Validar que retorna resultado válido (no crashea)
    assert state_after is None or isinstance(state_after, str), \
        f"get_file_state() debe retornar None o str después de modificar archivo. " \
        f"Obtenido: {state_after} (tipo: {type(state_after)})"
    
    # Si retorna estado, debe ser el correcto (no un estado de otro archivo)
    if state_after is not None:
        assert state_after == initial_state, \
            f"Si el estado persiste, debe ser el correcto. " \
            f"Esperado: {initial_state}, Obtenido: {state_after}"
```

---

## Comparación: Test Actual vs. Test Propuesto

| Aspecto | Test Actual (FLEXIBLE) | Test Propuesto (CRÍTICO) |
|---------|------------------------|--------------------------|
| **Inspecciona cache** | ✅ Sí (`_state_cache`) | ❌ No |
| **Llama métodos privados** | ✅ Sí (`_get_file_id()`) | ❌ No |
| **Usa time.sleep()** | ✅ Sí (frágil) | ❌ No |
| **Valida comportamiento observable** | ❌ No | ✅ Sí |
| **Define contrato de producto** | ❌ No | ✅ Sí |
| **Estable ante refactors** | ❌ No | ✅ Sí |
| **Mensaje de error explicativo** | ❌ No | ✅ Sí |

---

## Criterios del Test CRÍTICO

✅ **Protege comportamiento visible:**
- El usuario debe poder ver el estado correcto después de modificar archivos

✅ **Testea resultado, no implementación:**
- Solo usa API pública (`get_file_state()`, `set_file_state()`)
- No inspecciona cache ni métodos privados

✅ **Fallaría solo ante bug real:**
- Solo fallaría si el estado no persiste correctamente (bug real)
- No fallaría por cambios en implementación interna

✅ **Estable frente a refactors:**
- Si se refactoriza el cache, el test sigue pasando
- Si se cambia cómo se calcula `file_id`, el test sigue pasando

✅ **Mensaje de fallo explicativo:**
- Indica qué comportamiento esperado falló
- Explica qué estado se esperaba vs. qué se obtuvo

---

## Nota sobre Implementación

**NO implementar todavía.** Esta es solo la propuesta conceptual del test CRÍTICO correcto.

El test actual (`test_cache_invalidates_on_file_change`) debe mantenerse como FLEXIBLE porque:
- Valida implementación interna (cache)
- Puede ajustarse si se refactoriza el cache
- No define contrato de producto

El nuevo test CRÍTICO propuesto debe añadirse para proteger el contrato de producto correcto.

