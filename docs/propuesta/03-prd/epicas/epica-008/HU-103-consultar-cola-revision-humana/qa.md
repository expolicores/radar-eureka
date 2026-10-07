# Casos de Prueba — HU-103: Consultar la cola de revisión humana

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban el resumen, el listado, los filtros, el orden, la paginación, la exportación, la unicidad de elementos, el reflejo de resoluciones, los estados vacíos, los mensajes y los permisos de la cola. Queda fuera: las acciones de resolución (FR-016, FR-032) y los procesos que generan los elementos.

## Precondiciones y Datos Base

- Fecha de referencia: **2026-10-02**.
- Usuarios: `admin.po@prueba.co` (Administrador/Revisor); `analista1@prueba.co` (Analista).
- Cola semilla (12 pendientes y 2 resueltos):

  | Id | Tipo | Fuente | Contrato / orden | Campo | Confianza | Ingreso |
  | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
  | Q-01…Q-03 | Clasificación dudosa | SECOP II | CO1.PCCNTR.4946355, .5017737, .5375159 | — | — | 2026-09-23, 09-25, 09-28 |
  | Q-04…Q-09 | Extracción de baja confianza | SECOP II (5) / TVEC (1: Q-09) | CO1.PCCNTR.5030063 (Q-04, precio unitario) y otros | precio unitario, cantidad, tamaño, modelo | 0,41; 0,55; 0,60; 0,62; incierta; 0,30 | 2026-09-24 a 2026-10-01 |
  | Q-10, Q-11 | Inconsistencia aritmética | SECOP II | CO1.PCCNTR.4838434 | — | — | 2026-09-29, 09-30 |
  | Q-12 | Precio anormalmente bajo | TVEC | orden TVEC 98765 | — | — | 2026-10-01 |
  | Q-13 | Extracción de baja confianza (Resuelto, "Corregido", 2026-09-30, admin.po) | SECOP II | CO1.PCCNTR.4838434 | cantidad | 0,52 | 2026-09-20 |
  | Q-14 | Inconsistencia aritmética (Resuelto, "Validado") | SECOP II | CO1.PCCNTR.6000001 | — | — | 2026-09-18 |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-08 | QA-01 |
| Escenario 2, RN-03, RN-06, RN-07 | QA-02 |
| Escenario 3, RN-05 | QA-03 |
| RN-05 (rango de fechas inclusivo, contrato exacto) | QA-04 |
| Escenario 4, RN-06 | QA-05 |
| Escenario 5, RN-02 | QA-06 |
| Escenario 6, RN-02 | QA-07 |
| Escenario 7, RN-04 | QA-08 |
| Escenario 8, RN-04 | QA-09 |
| Escenario 9 | QA-10 |
| Escenario 10 | QA-11 |
| Escenario 11, RN-07, RN-10 | QA-12 |
| Escenario 12, RN-07 | QA-13 |
| Escenario 13 | QA-14 |
| RN-09 (lenguaje) | QA-15 |

---

## Casos de Prueba

### QA-01: Resumen con conteos por tipo y antigüedad

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-08
- **Pasos:**
  1. Consultar el resumen.
- **Resultado esperado:** total 12; Clasificación dudosa 3, Extracción de baja confianza 6, Inconsistencia aritmética 2, Precio anormalmente bajo 1; "elemento pendiente más antiguo: 9 días" (Q-01, 2026-09-23). Q-13 y Q-14 no cuentan.

### QA-02: Listado por defecto, orden y paginación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-03, RN-06, RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Tamaño de página | (por defecto) | 50 |
  | Tamaño de página | 5 | página 1: 5 elementos; página 3: 2 elementos |

- **Pasos:**
  1. Consultar la cola sin filtros.
  2. Consultar con página de 5, páginas 1 y 3.
- **Resultado esperado:** solo los 12 pendientes, del más antiguo al más reciente (empates por id), con todos los campos de RN-03 ("—" donde no aplica; antigüedad en días completos); paginación según la tabla.

### QA-03: Filtros combinados por tipo y fuente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-05
- **Pasos:**
  1. Filtrar tipo "Extracción de baja confianza" y fuente "SECOP II".
- **Resultado esperado:** 5 elementos (Q-04…Q-08); Q-09 (TVEC) queda fuera.

### QA-04: Rango de fechas inclusivo y contrato exacto

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Rango | 2026-09-23 a 2026-09-23 | incluye Q-01 |
  | Rango | 2026-09-29 a 2026-09-30 | incluye Q-10 y Q-11 (y extracción en esas fechas) |
  | Contrato | CO1.PCCNTR.4838434 | Q-10, Q-11 (pendientes) |
  | Contrato | CO1.PCCNTR.48384 | sin resultados (no es coincidencia parcial) |
  | Fecha | 2026/09/23 | "La fecha '2026/09/23' no tiene el formato AAAA-MM-DD." |

- **Pasos:**
  1. Aplicar cada filtro.
- **Resultado esperado:** el resultado indicado en la nota.

### QA-05: Orden por confianza con valores inciertos al final

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-06
- **Pasos:**
  1. Filtrar "Extracción de baja confianza" y ordenar por confianza ascendente.
- **Resultado esperado:** 0,30; 0,41; 0,55; 0,60; 0,62; incierta.

### QA-06: Consultar resueltos con datos de resolución

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-02
- **Pasos:**
  1. Filtrar estado "Resuelto".
  2. Filtrar estado "Todos".
- **Resultado esperado:** paso 1: Q-13 (2026-09-30, admin.po@prueba.co, "Corregido") y Q-14 ("Validado"); paso 2: 14 elementos.

### QA-07: Resolución externa saca el elemento de pendientes

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-02
- **Pasos:**
  1. Mediante el flujo de corrección de clasificación, confirmar Q-01.
  2. Consultar el resumen y la cola por defecto.
- **Resultado esperado:** Q-01 queda Resuelto ("Confirmado") con fecha y usuario; total pendiente 11, Clasificación dudosa 2; antigüedad máxima pasa a la de Q-04 o el siguiente más antiguo.

### QA-08: Nueva detección no duplica un pendiente

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Nueva detección | CO1.PCCNTR.5030063, ítem 1, precio unitario, valor 2.974.255, confianza 0,48, 2026-10-02 | Q-04 existe pendiente |

- **Pasos:**
  1. Registrar la nueva detección.
- **Resultado esperado:** sigue habiendo un solo elemento (Q-04) con valor 2.974.255, confianza 0,48, última detección 2026-10-02 y fecha de ingreso original sin cambio; total pendiente sigue en 12.

### QA-09: Reingreso después de una resolución

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-04
- **Pasos:**
  1. Registrar una nueva inconsistencia aritmética del ítem de Q-14 (CO1.PCCNTR.6000001).
- **Resultado esperado:** se crea un elemento Pendiente nuevo con ingreso 2026-10-02; Q-14 sigue Resuelto e idéntico.

### QA-10: Cola vacía

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Precondiciones:** todos los elementos resueltos.
- **Pasos:**
  1. Consultar la cola y el resumen.
- **Resultado esperado:** "No hay elementos pendientes de revisión."; resumen con total 0, los 4 tipos en 0 y "elemento pendiente más antiguo: —".

### QA-11: Filtros sin resultados

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 10
- **Pasos:**
  1. Filtrar fuente "TVEC" y tipo "Inconsistencia aritmética".
- **Resultado esperado:** "No hay elementos que cumplan los filtros."

### QA-12: Filtros y paginación inválidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-07, RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Tipo | Sobreprecio | tipo inválido |
  | Rango | 2026-09-30 a 2026-09-01 | inicio > fin |
  | Página | 0 / 501 / 600 | inválidos |
  | Página | 1 / 500 | válidos |

- **Pasos:**
  1. Consultar con cada valor.
- **Resultado esperado:** mensajes exactos de RN-10 para los inválidos ("El tipo 'Sobreprecio' no es válido. Tipos válidos: …", "La fecha inicial no puede ser posterior a la fecha final.", "El tamaño de página debe estar entre 1 y 500."); los válidos devuelven resultados.

### QA-13: Exportación CSV sin paginar

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-07
- **Precondiciones:** cargar 130 pendientes de "Extracción de baja confianza".
- **Pasos:**
  1. Filtrar por ese tipo y exportar.
- **Resultado esperado:** archivo CSV UTF-8, separador coma, encabezado con los campos de RN-03 y 136 filas de datos (130 + Q-04…Q-09); tildes legibles (ej. "Extracción").

### QA-14: Analista sin acceso a la cola

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 13
- **Pasos:**
  1. Como `analista1@prueba.co`, consultar el resumen, la cola y exportar.
- **Resultado esperado:** las tres operaciones devuelven "Acción no permitida: esta operación requiere el rol Administrador." sin datos.

### QA-15: Lenguaje no acusatorio en la cola

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Exportar la cola con estado "Todos".
  2. Buscar "sobreprecio", "corrupción", "fraude" y "hallazgo fiscal".
- **Resultado esperado:** ningún término aparece en motivos, tipos ni textos.

---

**Total de casos:** 15
