# Casos de Prueba — HU-104: Marcar contratos y documentos de la muestra de validación manual

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban el marcado de contratos y documentos (individual y en lote), los rechazos, el no doble conteo, el retiro con y sin resultados, la composición con su indicador de mínimo y advertencias, la auditoría y los permisos. Queda fuera: el registro de valores verificados (HU-105) y el cálculo de KPIs (HU-106, HU-107).

## Precondiciones y Datos Base

- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Universo SECOP II candidato: incluye CO1.PCCNTR.4838434 (2023, con resultados de validación tras marcarlo), CO1.PCCNTR.5030063 (con documentos DOC-30610 y DOC-30611), CO1.PCCNTR.4946355, CO1.PCCNTR.5375159, CO1.PCCNTR.5100200 (con DOC-30542).
- TVEC: orden 98765. Inexistente: CO1.PCCNTR.9999999, DOC-00000.
- Configuración: mínimo de muestra 50; umbral de concentración 50,0 %.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-01, RN-03, RN-07 | QA-01 |
| Escenario 2, RN-01 | QA-02 |
| Escenario 3, RN-04 | QA-03 |
| Escenario 4, RN-01 | QA-04 |
| Escenario 5, RN-04 | QA-05 |
| Escenario 6, RN-05 | QA-06 |
| Escenario 7, RN-03 | QA-07 |
| Escenario 8, RN-06 | QA-08 |
| Escenario 9, RN-06 | QA-09 |
| RN-06 (motivo, no marcado) | QA-10 |
| Escenario 10, RN-08 | QA-11 |
| Escenario 11, RN-08 (límite del mínimo) | QA-12 |
| Escenario 12, RN-09 | QA-13 |
| Escenario 13 | QA-14 |
| RN-07 (falla de auditoría) | QA-15 |
| RN-10 (sin efectos colaterales) | QA-16 |
| Escenario 14 | QA-17 |

---

## Casos de Prueba

### QA-01: Marcar contratos en lote con auditoría

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-03, RN-07
- **Pasos:**
  1. Marcar CO1.PCCNTR.4838434, CO1.PCCNTR.5030063 y CO1.PCCNTR.4946355 con lote "D4-4".
- **Resultado esperado:** los tres "Marcado", tipo contrato, lote "D4-4", usuario y fecha; un evento "Marcado de muestra de validación" con los tres ids.

### QA-02: Marcar un documento individual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-01
- **Pasos:**
  1. Marcar DOC-30542 con lote "2026-10-S1".
- **Resultado esperado:** "Marcado", tipo documento.

### QA-03: Lote con resultados mixtos e ids repetidos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Ids | CO1.PCCNTR.4838434, CO1.PCCNTR.9999999, CO1.PCCNTR.5375159, CO1.PCCNTR.5375159 | el último repetido |

- **Pasos:**
  1. Marcar con lote "D4-4".
- **Resultado esperado:** "Ya en la muestra"; "Rechazado: el contrato 'CO1.PCCNTR.9999999' no existe en el universo de candidatos SECOP II."; "Marcado" (una sola vez para CO1.PCCNTR.5375159).

### QA-04: Rechazo de TVEC y de documento inexistente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Id | 98765 (orden TVEC) | "Rechazado: solo contratos o documentos de SECOP II sujetos a extracción pueden integrar la muestra." |
  | Id | DOC-00000 | "Rechazado: el documento 'DOC-00000' no existe o no pertenece a un contrato candidato SECOP II." |

- **Pasos:**
  1. Marcar cada id.
- **Resultado esperado:** el mensaje indicado; nada se marca.

### QA-05: Documento ya cubierto por su contrato

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-04
- **Pasos:**
  1. Con CO1.PCCNTR.5030063 marcado, marcar DOC-30610.
- **Resultado esperado:** "Ya en la muestra: el documento DOC-30610 está incluido a través del contrato CO1.PCCNTR.5030063."; sin registro nuevo.

### QA-06: Contrato y documento marcados no duplican campos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-05
- **Pasos:**
  1. Con DOC-30542 marcado, marcar CO1.PCCNTR.5100200.
  2. Consultar la composición.
- **Resultado esperado:** ambos marcados; DOC-30542 deja de contar como "documento individual" en elementos de muestra (lo cubre su contrato) y sus campos se cuentan una sola vez.

### QA-07: Validaciones de lote y lista

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Lote | (vacío) / "D4" | "Debe indicar una etiqueta de lote de 3 a 50 caracteres." |
  | Lote | "D44" / 50 caracteres | aceptados |
  | Lote | 51 caracteres | rechazado |
  | Ids | (ninguno) | "Debe indicar al menos un identificador." |
  | Ids | 200 / 201 | aceptado / "Se permiten como máximo 200 identificadores por operación." |

- **Pasos:**
  1. Marcar con cada combinación.
- **Resultado esperado:** el resultado indicado; en los rechazos no se marca ninguno.

### QA-08: Retiro de un elemento sin resultados

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-06
- **Pasos:**
  1. Retirar CO1.PCCNTR.5375159 con motivo "Marcado por error, es un contrato de mantenimiento duplicado".
- **Resultado esperado:** "CO1.PCCNTR.5375159 fue retirado de la muestra."; evento "Retiro de muestra de validación" con usuario, fecha, id y motivo.

### QA-09: Retiro bloqueado por resultados existentes

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-06
- **Precondiciones:** CO1.PCCNTR.4838434 tiene 1 resultado de validación.
- **Pasos:**
  1. Intentar retirarlo con motivo válido.
- **Resultado esperado:** "No se puede retirar CO1.PCCNTR.4838434 de la muestra: ya tiene resultados de validación registrados."; sigue marcado.

### QA-10: Retiro con motivo inválido o de elemento no marcado

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Motivo | "Error" (5) | "Debe indicar un motivo de retiro de 10 a 500 caracteres." |
  | Id | CO1.PCCNTR.4946355 retirado dos veces | segunda vez: "CO1.PCCNTR.4946355 no está en la muestra." |

- **Pasos:**
  1. Ejecutar cada retiro.
- **Resultado esperado:** el mensaje indicado.

### QA-11: Composición con distribución completa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10, RN-08
- **Precondiciones:** muestra de 45 contratos y 8 documentos individuales cuyos contratos no están marcados.
- **Pasos:**
  1. Consultar la composición.
- **Resultado esperado:** elementos 53; contratos 45; documentos individuales 8; "Muestra mínima: 53/50 — Cumple"; distribuciones por año, entidad, tipo de documento, OCR/multimodal, resultado del extractor y estado de validación con conteo y porcentaje con 1 decimal; lotes con su cantidad.

### QA-12: Límite del mínimo de muestra

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Elementos | 49 | "Muestra mínima: 49/50 — No cumple" |
  | Elementos | 50 | "Muestra mínima: 50/50 — Cumple" |
  | Elementos | 30 | "Muestra mínima: 30/50 — No cumple" |

- **Pasos:**
  1. Ajustar la muestra a cada tamaño y consultar.
- **Resultado esperado:** el indicador de la nota.

### QA-13: Advertencias de diversidad y su umbral

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Contratos 2023 | 31 de 45 (68,9 %), ninguno "información insuficiente"/"sin precio" | dos advertencias |
  | Contratos de la misma entidad | 25 de 50 (50,0 %) | sin advertencia (no supera) |
  | Contratos de la misma entidad | 26 de 50 (52,0 %) | advertencia de entidad |

- **Pasos:**
  1. Consultar la composición con cada muestra.
- **Resultado esperado:** "La muestra está concentrada: 68,9 % de los contratos corresponde a año de firma 2023." y "La muestra no incluye contratos con información insuficiente o sin precio extraído." en el primer caso; ninguna advertencia de concentración con 50,0 %; advertencia de entidad con 52,0 %.

### QA-14: Muestra vacía

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 13
- **Pasos:**
  1. Sin elementos, consultar la composición.
- **Resultado esperado:** "La muestra de validación está vacía." y "Muestra mínima: 0/50 — No cumple"; sin advertencias.

### QA-15: Falla de auditoría impide marcar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Precondiciones:** log de auditoría no disponible (simulado).
- **Pasos:**
  1. Marcar CO1.PCCNTR.4946355.
- **Resultado esperado:** "No fue posible registrar la auditoría; la operación no se aplicó. Intente de nuevo."; no queda marcado.

### QA-16: Marcar y retirar no alteran otros datos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-10
- **Pasos:**
  1. Tomar una instantánea de datos extraídos, cola y señales de CO1.PCCNTR.5030063.
  2. Marcarlo y luego retirarlo.
- **Resultado esperado:** la instantánea no cambia.

### QA-17: Analista sin acceso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 14
- **Pasos:**
  1. Como `analista1@prueba.co`, marcar, retirar y consultar la composición.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador." en las tres; nada cambia.

---

**Total de casos:** 17
