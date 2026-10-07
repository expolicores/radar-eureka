# Casos de Prueba — HU-113: Consultar y exportar el log de auditoría

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban la búsqueda filtrada, el orden, la paginación, la historia de una entidad, el detalle de evento, la exportación y su límite, la nota de retención, los estados vacíos, las validaciones de filtros, el carácter de solo lectura y los permisos. Queda fuera: el registro de eventos y la depuración (HU-112).

## Precondiciones y Datos Base

- Fecha de referencia: **2026-10-02**.
- Usuarios: `admin.po@prueba.co` (Administrador); `revisor2@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Log semilla: eventos del 2025-10-02 al 2026-10-02 (retención 12 meses), entre ellos:
  - 3 eventos sobre el precio unitario del ítem 1 de CO1.PCCNTR.5030063 (2026-09-10 corrección, 2026-09-12 corrección, 2026-09-20 validación).
  - 12 eventos "Carga semiautomática de observación" con id de operación OP-0451.
  - Evento 1520 con valor anterior truncado.
  - 8 eventos "Cambio de configuración" de `admin.po@prueba.co` en septiembre de 2026 y 2 de `revisor2@prueba.co`.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-01 (por defecto), RN-02 | QA-01 |
| Escenario 2, RN-01 | QA-02 |
| Escenario 3, RN-03 | QA-03 |
| Escenario 4, RN-01 | QA-04 |
| Escenario 5, RN-04 | QA-05 |
| Escenario 6 | QA-06 |
| Escenario 7, RN-05 | QA-07 |
| Escenario 8, RN-05 (límite) | QA-08 |
| Escenario 9, RN-06 | QA-09 |
| Escenario 10 | QA-10 |
| Escenario 11, RN-07 | QA-11 |
| Escenario 12, RN-08 | QA-12 |
| Escenario 13 | QA-13 |

---

## Casos de Prueba

### QA-01: Consulta por defecto, orden y paginación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-02
- **Pasos:**
  1. Consultar sin filtros.
  2. Consultar con tamaño de página 1 y 500.
- **Resultado esperado:** solo eventos del 2026-09-03 al 2026-10-02 (30 días incluyendo hoy), del más reciente al más antiguo (empates por id descendente), 50 por página y con todos los campos; con 1 y 500 se respeta el tamaño.

### QA-02: Filtros combinados

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Tipo | Cambio de configuración | — |
  | Usuario | ADMIN.PO@prueba.co | mayúsculas ignoradas |
  | Rango | 2026-09-01 a 2026-09-30 | extremos incluidos |

- **Pasos:**
  1. Consultar con los tres filtros.
- **Resultado esperado:** los 8 eventos de `admin.po@prueba.co`; los 2 de `revisor2@prueba.co` quedan fuera.

### QA-03: Historia cronológica de una entidad

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Pasos:**
  1. Pedir la historia del ítem 1 de CO1.PCCNTR.5030063, campo precio unitario.
- **Resultado esperado:** 3 eventos en orden 2026-09-10, 2026-09-12, 2026-09-20, con valores anterior y nuevo.

### QA-04: Filtrar por id de operación

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-01
- **Pasos:**
  1. Filtrar por OP-0451 con un rango que incluya su fecha.
- **Resultado esperado:** 12 eventos.

### QA-05: Detalle con valor truncado

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-04
- **Pasos:**
  1. Pedir el detalle del evento 1520.
- **Resultado esperado:** todos los campos; el valor anterior con 4.000 caracteres, "[truncado]" y el hash del valor completo; valores enmascarados como "****".

### QA-06: Evento inexistente

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** Escenario 6
- **Pasos:**
  1. Pedir el detalle del evento 999999.
- **Resultado esperado:** "El evento 999999 no existe o fue depurado por la política de retención."

### QA-07: Exportación completa

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-05
- **Precondiciones:** filtro que devuelve 1.250 eventos.
- **Pasos:**
  1. Exportar.
- **Resultado esperado:** CSV UTF-8, separador coma, encabezado y 1.250 filas.

### QA-08: Límite de exportación

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Resultado del filtro | 100.000 eventos | se exporta |
  | Resultado del filtro | 100.001 / 120.000 eventos | "La exportación supera 100000 eventos; acote el rango de fechas u otros filtros." |

- **Pasos:**
  1. Exportar en cada situación.
- **Resultado esperado:** el resultado indicado.

### QA-09: Nota de período depurado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-06
- **Pasos:**
  1. Consultar 2025-06-01 a 2025-12-31.
- **Resultado esperado:** eventos desde 2025-10-02 y la nota "Los eventos anteriores a 2025-10-02 fueron depurados por la política de retención (12 meses)."

### QA-10: Sin resultados

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 10
- **Pasos:**
  1. Filtrar por tipo "Reactivación de fuente" en un rango sin reactivaciones.
- **Resultado esperado:** "No hay eventos de auditoría que cumplan los filtros."

### QA-11: Filtros inválidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-07
- **Datos de prueba:**

  | Campo | Valor | Resultado esperado |
  | ----- | ----- | ----- |
  | Tipo | Borrado de datos | "El tipo de evento 'Borrado de datos' no es válido." |
  | Fecha | 02/10/2026 | "La fecha '02/10/2026' no tiene el formato AAAA-MM-DD." |
  | Rango | 2026-09-30 a 2026-09-01 | "La fecha inicial no puede ser posterior a la fecha final." |
  | Rango | 2025-10-01 a 2026-10-02 (367 días) | "El rango de consulta no puede superar 366 días." |
  | Rango | 2025-10-02 a 2026-10-02 (366 días) | aceptado |
  | Página | 0 / 501 | "El tamaño de página debe estar entre 1 y 500." |

- **Pasos:**
  1. Consultar con cada valor.
- **Resultado esperado:** el resultado indicado.

### QA-12: Consultar no genera eventos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-08
- **Pasos:**
  1. Contar eventos; consultar, ver detalle, historia y exportar; volver a contar.
- **Resultado esperado:** el conteo no cambia.

### QA-13: Analista sin acceso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 13
- **Pasos:**
  1. Como `analista1@prueba.co`, consultar, pedir detalle, historia y exportar.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador." en todas.

---

**Total de casos:** 13
