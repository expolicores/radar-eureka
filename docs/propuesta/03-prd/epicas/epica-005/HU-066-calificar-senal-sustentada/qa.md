# Casos de Prueba — HU-066: Calificar una señal como suficientemente sustentada para merecer revisión

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el registro de la calificación de una señal por un Analista: valores, comentario, unicidad y cambio, calificación por versión, elegibilidad (vigente y versión más reciente), rol, privacidad entre Analistas, errores y doble envío. Queda fuera el cálculo del KPI.

## Precondiciones y Datos Base

- Analistas "analista.piloto1" y "analista.piloto2"; Administrador "admin.po".
- SG-1 vigente, versión 1; SG-3 "No vigente"; SG-9 con versiones 1 y 2 (vigente la 2).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01 / RN-07 / RN-08 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-01 | QA-03 |
| Escenario 4 / RN-02 límites | QA-04 |
| RN-02 solo espacios | QA-05 |
| Escenario 5 / RN-03 | QA-06 |
| Escenario 6 / RN-03 versión | QA-07 |
| Escenario 7 / RN-04 | QA-08 |
| Escenario 8 / RN-05 | QA-09 |
| Escenario 9 / RN-03, RN-08 | QA-10 |
| Escenario 10 / RN-06 | QA-11 |
| RN-06 consulta del Administrador | QA-12 |

---

## Casos de Prueba

### QA-01: Calificar como sustentada con comentario

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-07 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Calificación | Suficientemente sustentada para merecer revisión | |
  | Comentario | "Mismo modelo, 7 compras TVEC cercanas" | |

- **Pasos:**
  1. Como "analista.piloto1", abrir SG-1, elegir la opción, escribir el comentario y guardar.
- **Resultado esperado:** Mensaje "Tu calificación quedó registrada."; bloque "Tu calificación: Suficientemente sustentada para merecer revisión" con fecha 02/10/2026 y comentario; registro con señal, versión 1, benchmark, Analista, valor, comentario y fechas.

### QA-02: Calificar sin comentario

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2 / RN-02
- **Pasos:**
  1. Como "analista.piloto2", elegir "No suficientemente sustentada" en SG-1 y guardar sin comentario.
- **Resultado esperado:** Se guarda con comentario vacío.

### QA-03: Guardar sin elegir opción

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-01
- **Pasos:**
  1. Escribir un comentario sin elegir opción y pulsar "Guardar calificación".
- **Resultado esperado:** "Selecciona una calificación."; no se guarda nada.

### QA-04: Límites del comentario

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comentario | 1.000 caracteres | Se guarda; contador "1000/1.000" |
  | Comentario | 1.001 caracteres | Rechazado |
  | Comentario | 1.000 caracteres + 3 espacios al final | Se guarda (espacios recortados) |

- **Pasos:**
  1. Intentar guardar cada variante.
- **Resultado esperado:** Según la tabla; con 1.001 aparece "El comentario admite máximo 1.000 caracteres.".

### QA-05: Comentario solo con espacios

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-02
- **Pasos:**
  1. Elegir una opción, escribir "     " y guardar.
- **Resultado esperado:** Se guarda con comentario vacío.

### QA-06: Cambiar la calificación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-03
- **Pasos:**
  1. Con la calificación de QA-02, cambiar a "Suficientemente sustentada para merecer revisión" y guardar.
- **Resultado esperado:** Una sola calificación vigente de "analista.piloto2" para SG-1 versión 1 con el nuevo valor; el historial conserva el valor anterior y la fecha-hora del cambio.

### QA-07: Nueva versión de la señal

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-03
- **Pasos:**
  1. "analista.piloto1" calificó SG-9 versión 1 como "No suficientemente sustentada".
  2. Abrir SG-9 (vigente versión 2).
- **Resultado esperado:** Mensaje "Calificaste la versión anterior: No suficientemente sustentada. La señal cambió; puedes calificar la versión actual."; formulario vacío; la calificación de la versión 1 sigue registrada.

### QA-08: Señal no vigente o versión anterior

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-04
- **Pasos:**
  1. Abrir SG-3.
  2. Abrir SG-9 y seleccionar la versión 1 en el historial.
- **Resultado esperado:** (1) Sin formulario y "Esta señal ya no está vigente; no se puede calificar." (2) Sin formulario y "Solo se califica la versión más reciente de la señal.".

### QA-09: El Administrador no califica

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-05
- **Pasos:**
  1. Como "admin.po", abrir SG-1.
  2. Enviar una calificación por otro medio (solicitud directa).
- **Resultado esperado:** No se ve el formulario; la solicitud se rechaza con "Solo los analistas pueden calificar señales.".

### QA-10: Error al guardar y doble envío

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-03 / RN-08
- **Pasos:**
  1. Simular falla de guardado y guardar.
  2. Restaurar y pulsar "Guardar calificación" dos veces seguidas.
- **Resultado esperado:** (1) "No pudimos guardar tu calificación. Intenta de nuevo." con la opción y el comentario conservados. (2) Una sola calificación registrada.

### QA-11: Privacidad entre Analistas

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-06
- **Pasos:**
  1. Con las calificaciones de QA-01 y QA-02, abrir SG-1 como "analista.piloto1".
- **Resultado esperado:** Solo ve su propia calificación; no ve la de "analista.piloto2".

### QA-12: Consulta de calificaciones por el Administrador

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Como "admin.po", consultar las calificaciones de SG-1 por el medio de consulta disponible.
- **Resultado esperado:** Se obtienen las calificaciones de ambos Analistas con versión, valor, comentario y fechas.

---

**Total de casos:** 12
