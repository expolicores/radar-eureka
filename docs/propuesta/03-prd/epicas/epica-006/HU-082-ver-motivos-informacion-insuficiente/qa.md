# Casos de Prueba — HU-082: Ver los motivos de información insuficiente del contrato en la ficha

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la sección "Motivos de información insuficiente": catálogo de textos y categorías, motivos de contrato y de ítem, documento relacionado, motivos desconocidos, IVA indeterminado, falta de comparables, agrupación y orden, estados sin motivos y en procesamiento, navegación desde "Ver motivos", cobertura, lenguaje, rendimiento y accesibilidad. Queda fuera el registro de los motivos por otros procesos.

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (Analista).
- **Registros semilla:**

  | Registro | Motivos registrados |
  | -------- | ------------------- |
  | M1 (SECOP II) | ítem I1: `solo_valor_global` (documento "Contrato.pdf", con URL); ítem I2: `extraccion_no_encontrada`; ítem I3: `iva_indeterminado`; ítems I4 e I5: `sin_comparables` |
  | M2 (SECOP II) | contrato: `sin_documentos` |
  | M3 (SECOP II) | contrato: `documento_en_blanco` (documento "Formato propuesta.docx", sin URL) |
  | M4 (SECOP II) | ítem I1: código `lote_ambiguo` con texto "No se identificó el lote del televisor"; ítem I2: código `xyz` sin texto |
  | M5 (SECOP II) | sin motivos; procesamiento completo |
  | M6 (SECOP II) | sin motivos; extracción en curso |
  | M7 (SECOP II) | `error_descarga`, `error_lectura`, `extraccion_pendiente_revision`, `oferta_no_publicada`, `sin_cantidad`, `precio_no_derivable` en distintos ítems |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-04 / RN-05 | QA-01 |
| Escenario 2 | QA-02 |
| Escenario 3 / RN-06 | QA-03 |
| Escenario 4 / RN-03 | QA-04 |
| Escenario 5 | QA-01 |
| Escenario 6 / RN-04 agrupación | QA-01 |
| RN-02 catálogo completo | QA-05 |
| Escenario 7 / RN-07 | QA-06 |
| Escenario 8 / RN-07 | QA-07 |
| Escenario 9 | QA-08 |
| RN-07 cobertura | QA-09 |
| RN-08 | QA-10 |
| RN-09 | QA-11 |

---

## Casos de Prueba

### QA-01: Motivos de ítems agrupados por categoría

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenarios 1, 5 y 6 / RN-01 / RN-04 / RN-05
- **Pasos:**
  1. Abrir la ficha de M1 en "Motivos de información insuficiente".
- **Resultado esperado:** "Limitación de la fuente (3)": `solo_valor_global` (I1, documento "Contrato.pdf"), "No se pudo determinar si el precio incluye IVA; la comparación se marca como incompleta." (I3) y "No hay compras públicas comparables en la ventana de comparación." una sola vez con ítems I4 e I5; "Limitación del procesamiento (1)": "No se lograron extraer la cantidad y el precio unitario de los documentos procesados." (I2). Dentro de cada grupo, por orden del ítem.

### QA-02: Motivo de todo el contrato

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Pasos:**
  1. Abrir la ficha de M2.
- **Resultado esperado:** "Limitación de la fuente (1)": "La fuente no ha publicado documentos para este proceso." con alcance "Todo el contrato".

### QA-03: Documento relacionado con y sin URL

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-06
- **Pasos:**
  1. En M1 activar "Abrir en SECOP II" del motivo de I1.
  2. Abrir la ficha de M3.
- **Resultado esperado:** paso 1 abre "Contrato.pdf" en pestaña nueva; paso 2 muestra "Documento: Formato propuesta.docx" sin acción de apertura.

### QA-04: Motivos no catalogados

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-03
- **Pasos:**
  1. Abrir la ficha de M4.
- **Resultado esperado:** en "Limitación del procesamiento": "Motivo registrado: No se identificó el lote del televisor" (I1) y "Motivo registrado sin descripción" (I2).

### QA-05: Textos y categorías del catálogo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-02
- **Pasos:**
  1. Abrir la ficha de M7.
- **Resultado esperado:** `oferta_no_publicada`, `sin_cantidad` y `precio_no_derivable` aparecen en "Limitación de la fuente"; `error_descarga`, `error_lectura` y `extraccion_pendiente_revision` en "Limitación del procesamiento"; cada uno con el texto exacto de la tabla RN-02.

### QA-06: Sin motivos y procesamiento completo

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-07
- **Pasos:**
  1. Abrir la ficha de M5.
- **Resultado esperado:** "No hay motivos de información insuficiente registrados para este contrato."

### QA-07: Sin motivos y en procesamiento

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-07
- **Pasos:**
  1. Abrir la ficha de M6.
- **Resultado esperado:** "El contrato aún está en procesamiento; los motivos de información insuficiente, si los hay, aparecerán al terminar."

### QA-08: Llegar desde "Ver motivos"

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Pasos:**
  1. En M1 activar "Ver motivo" en la tarjeta de I2.
  2. En M2 activar "Ver motivos" en el estado de procesamiento.
- **Resultado esperado:** paso 1 desplaza a la sección, resalta el motivo de I2 y pone el foco en ella; paso 2 desplaza a la sección.

### QA-09: Sección presente en todas las fichas

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Pasos:**
  1. Abrir automáticamente todas las fichas del universo visible.
- **Resultado esperado:** el 100 % muestra la sección con motivos o con uno de los dos mensajes de estado.

### QA-10: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-08
- **Pasos:**
  1. Buscar los términos prohibidos en las secciones de M1 a M7.
- **Resultado esperado:** 0 apariciones de "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".

### QA-11: Rendimiento, accesibilidad y móvil

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Precondiciones:** 20 sesiones concurrentes.
- **Pasos:**
  1. Abrir fichas durante 10 minutos; leer la sección con lector de pantalla; verla a 360 px.
- **Resultado esperado:** ficha en ≤ 3 s (p95); los grupos se anuncian con su título y conteo; a 360 px cada motivo es una tarjeta.

---

**Total de casos:** 11
