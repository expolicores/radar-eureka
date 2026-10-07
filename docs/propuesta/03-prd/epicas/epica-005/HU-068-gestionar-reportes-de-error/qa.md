# Casos de Prueba — HU-068: Gestionar los reportes de error y registrar su resolución

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la consulta de reportes (abiertos, por estado, conteos, vacío), las transiciones de estado válidas e inválidas, la resolución obligatoria, la auditoría, la visibilidad del resultado para el Analista, los permisos, el reporte inexistente y la concurrencia. Queda fuera la corrección del dato en sí. Las pruebas son de caja negra sobre el medio de gestión que se implemente (consulta, script o interfaz mínima).

## Precondiciones y Datos Base

- Administrador "admin.po"; Analista "analista.piloto1".
- RE-000001: Recibido, 01/10/2026 09:00, creado por "analista.piloto1", SG-1 v1, "Dato del ítem: Cantidad", valor mostrado 80, sugerido 8.
- RE-000002: En revisión, 01/10/2026 11:00, SG-1 v1, "La señal completa".
- RE-000003: Corregido, 30/09/2026.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-04 | QA-01 |
| Escenario 2 / RN-04 | QA-02 |
| Escenario 3 / RN-02 / RN-05 | QA-03 |
| Escenario 4 / RN-03 / RN-07 | QA-04 |
| Escenario 5 / RN-02 Recibido → Descartado | QA-05 |
| Escenario 6 / RN-03 | QA-06 |
| Escenario 7 / RN-02 cerrado | QA-07 |
| RN-02 En revisión → Recibido | QA-08 |
| Escenario 8 / RN-08 | QA-09 |
| Escenario 9 / RN-04 vacío | QA-10 |
| Escenario 10 | QA-11 |
| RN-06 independencia | QA-12 |
| RN-09 concurrencia | QA-13 |

---

## Casos de Prueba

### QA-01: Consultar reportes abiertos en orden

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04
- **Pasos:**
  1. Como "admin.po", consultar los reportes abiertos.
- **Resultado esperado:** RE-000001 y luego RE-000002, con todos los campos registrados; RE-000003 no aparece.

### QA-02: Filtro por estado y conteos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2 / RN-04
- **Pasos:**
  1. Filtrar por "Corregido".
  2. Pedir el conteo por estado.
  3. Filtrar por "Descartado".
- **Resultado esperado:** (1) RE-000003. (2) "Recibido: 1, En revisión: 1, Corregido: 1, Descartado: 0". (3) "No hay reportes en estado Descartado.".

### QA-03: Pasar a En revisión con auditoría

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-02 / RN-05
- **Pasos:**
  1. Pasar RE-000001 a "En revisión" y consultar la auditoría.
- **Resultado esperado:** Estado "En revisión"; auditoría con "admin.po", fecha-hora, RE-000001, "Recibido" → "En revisión".

### QA-04: Cerrar como Corregido y visibilidad para el Analista

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-03 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Resolución | "Cantidad corregida a 8 según página 4 de la oferta" | |

- **Pasos:**
  1. Cerrar RE-000001 como "Corregido".
  2. Como "analista.piloto1", abrir SG-1.
- **Resultado esperado:** Reporte "Corregido" con resolución, fecha de cierre y usuario; auditoría registrada; el Analista lo ve en "Mis reportes en esta señal" y el aviso de la señal cuenta un reporte abierto menos.

### QA-05: Cerrar directamente desde Recibido como Descartado

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-02
- **Pasos:**
  1. Crear RE-000004 (Recibido) y cerrarlo como "Descartado" con "El comparable es de 55 pulgadas; el emparejamiento es correcto".
- **Resultado esperado:** Estado "Descartado" con resolución y fecha de cierre.

### QA-06: Resolución inválida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Resolución | vacía | Rechazo |
  | Resolución | "Corregido" (9) | Rechazo |
  | Resolución | "   ok   " | 2 tras recorte: rechazo |
  | Resolución | 1.001 caracteres | Rechazo |
  | Resolución | 10 y 1.000 caracteres | Aceptadas |

- **Pasos:**
  1. Intentar cerrar RE-000002 con cada valor.
- **Resultado esperado:** Rechazos con "La resolución es obligatoria y debe tener entre 10 y 1.000 caracteres." sin cambio de estado; los límites válidos se aceptan.

### QA-07: Reporte cerrado no cambia de estado

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-02
- **Pasos:**
  1. Intentar pasar RE-000003 a "En revisión" y a "Descartado".
- **Resultado esperado:** "El reporte ya está cerrado; no se puede cambiar su estado."; sigue "Corregido".

### QA-08: Transición hacia atrás no permitida

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-02
- **Pasos:**
  1. Intentar pasar RE-000002 de "En revisión" a "Recibido".
- **Resultado esperado:** "Transición no permitida de En revisión a Recibido."; sin cambio.

### QA-09: Analista sin permiso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-08
- **Pasos:**
  1. Como "analista.piloto1", consultar todos los reportes y cambiar el estado de RE-000002.
- **Resultado esperado:** Ambas acciones rechazadas con "Solo el Administrador puede gestionar reportes de error.".

### QA-10: Sin reportes abiertos

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 9 / RN-04
- **Pasos:**
  1. Cerrar todos los reportes abiertos y consultar los abiertos.
- **Resultado esperado:** Resultado vacío con "No hay reportes de error abiertos.".

### QA-11: Reporte inexistente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Pasos:**
  1. Intentar cambiar el estado de RE-999999.
- **Resultado esperado:** "El reporte RE-999999 no existe.".

### QA-12: Cerrar un reporte no modifica datos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Sin usar el mecanismo de corrección, cerrar un reporte sobre la cantidad como "Corregido".
  2. Consultar la cantidad del ítem y la señal.
- **Resultado esperado:** La cantidad y la señal no cambian (sin nueva versión).

### QA-13: Cambios simultáneos

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Pasos:**
  1. Enviar al mismo tiempo, sobre RE-000002 (En revisión), un cierre como "Corregido" y otro como "Descartado", ambos con resolución válida.
- **Resultado esperado:** Se aplica el primero que llega; el segundo se rechaza con "El reporte ya está cerrado; no se puede cambiar su estado."; la auditoría registra solo un cierre.

---

**Total de casos:** 13
