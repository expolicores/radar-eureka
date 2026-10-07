# Casos de Prueba — HU-083: Mostrar la fecha de actualización de los datos en la exploración y en la ficha

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la indicación de fecha de actualización en "Exploración", "Señales" y la ficha: fechas de corte por fuente, fecha de corte del registro, última actualización en la fuente, fecha de cálculo, fuente sin carga, cálculo pendiente, carga fallida, ayuda, formatos, ubicación, actualización por carga de vista y accesibilidad. Queda fuera la ejecución de ingestas y cálculos.

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (Analista).
- **Registro de ejecuciones:**

  | Fuente / proceso | Ejecuciones |
  | ---------------- | ----------- |
  | SECOP II | exitosa con corte 01/10/2026; fallida el 02/10/2026 |
  | TVEC | exitosa con corte 01/10/2026 |
  | Cálculo de comparaciones | terminado el 02/10/2026 06:45 |

- **Registros:** contrato F1 (SECOP II) con fecha de corte del registro 30/09/2026, `ultima_actualizacion` 28/09/2026, ítems comparados el 02/10/2026 06:45 (uno) y 01/10/2026 06:40 (otro); orden F2 (TVEC) sin fecha de última actualización publicada, corte 01/10/2026, comparada el 02/10/2026 06:45; contrato F3 sin ítems comparados.
- **Ambiente vacío** para los casos sin cargas ni cálculos.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-04 / RN-05 / RN-07 | QA-01 |
| Escenario 2 | QA-02 |
| Escenario 3 / RN-02 / RN-03 / RN-04 | QA-03 |
| Escenario 4 / RN-03 / RN-06 | QA-04 |
| Escenario 5 / RN-06 | QA-05 |
| Escenario 6 / RN-06 | QA-05, QA-06 |
| Escenario 7 / RN-01 | QA-07 |
| Escenario 8 | QA-08 |
| RN-08 | QA-09 |
| RN-07 móvil / RN-09 | QA-10 |

---

## Casos de Prueba

### QA-01: Indicación en la exploración

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-04 / RN-05 / RN-07
- **Pasos:**
  1. Abrir "Exploración" a 1366 × 768 px.
- **Resultado esperado:** sin desplazamiento se ve "Datos actualizados al: SECOP II 01/10/2026 · TVEC 01/10/2026 · Comparaciones calculadas el 02/10/2026 06:45".

### QA-02: Indicación en la lista de señales

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Pasos:**
  1. Abrir "Señales".
- **Resultado esperado:** la misma indicación de QA-01 aparece sobre la lista.

### QA-03: Fechas en la ficha SECOP II

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-02 / RN-03 / RN-04
- **Pasos:**
  1. Abrir la ficha de F1.
- **Resultado esperado:** "Fecha de corte de los datos: 30/09/2026", "Última actualización en la fuente: 28/09/2026" y "Comparación calculada el: 02/10/2026 06:45" (la más reciente de sus ítems).

### QA-04: Ficha TVEC sin última actualización publicada

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-03 / RN-06
- **Pasos:**
  1. Abrir la ficha de F2.
- **Resultado esperado:** "Fecha de corte de los datos: 01/10/2026" y "Comparación calculada el: 02/10/2026 06:45"; no aparece la línea "Última actualización en la fuente".

### QA-05: Ambiente sin cargas ni cálculos

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenarios 5 y 6 / RN-06
- **Pasos:**
  1. En el ambiente vacío abrir "Exploración".
- **Resultado esperado:** "SECOP II: sin datos cargados todavía · TVEC: sin datos cargados todavía · Comparaciones: pendientes de cálculo".

### QA-06: Ficha sin comparación

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-06
- **Pasos:**
  1. Abrir la ficha de F3.
- **Resultado esperado:** "Comparación: pendiente".

### QA-07: Una carga fallida no cambia la fecha

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-01
- **Pasos:**
  1. Abrir "Exploración" después de la carga fallida de SECOP II del 02/10/2026.
- **Resultado esperado:** SECOP II sigue mostrando "01/10/2026".

### QA-08: Ayuda sobre las fechas

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** Escenario 8
- **Pasos:**
  1. Activar con teclado el ícono "Información sobre las fechas".
- **Resultado esperado:** se abre la ayuda con el texto exacto del Escenario 8.

### QA-09: La indicación se actualiza al recargar la vista

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-08
- **Pasos:**
  1. Con "Exploración" abierta, completar una nueva carga exitosa de TVEC con corte 02/10/2026.
  2. Observar la vista sin recargar; luego recargar.
- **Resultado esperado:** sin recargar sigue "TVEC 01/10/2026"; tras recargar muestra "TVEC 02/10/2026".

### QA-10: Móvil y accesibilidad

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-07 / RN-09
- **Pasos:**
  1. Abrir "Exploración" y la ficha de F1 a 360 px con lector de pantalla.
- **Resultado esperado:** la indicación aparece compacta debajo del título, se lee completa con el lector y la ayuda se abre con teclado; las vistas siguen cargando en ≤ 3 s (p95).

---

**Total de casos:** 10
