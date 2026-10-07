# Casos de Prueba — HU-025: Marcar los ítems con información insuficiente indicando el motivo

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la condición de insuficiencia, la asignación de cada motivo del catálogo con su causa, los motivos múltiples, el efecto sobre la disponibilidad para comparación, el resumen por proceso, la reevaluación tras corrección, el historial y los contadores. Los resultados de HU-017, HU-020, HU-022 y HU-024 se suministran como datos simulados.

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Ítems de prueba sobre el contrato `CO1.PCCNTR.8234869` (proceso `CO1.BDOS.8234869`) salvo que el caso indique otro.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-02 | QA-01 |
| RN-02 (base indeterminada) | QA-02 |
| Escenario 2 / RN-03, RN-05 | QA-03 |
| Escenario 3 / RN-03 | QA-04 |
| Escenario 4 / RN-02, RN-05 | QA-05 |
| Escenario 5 / RN-03 | QA-06 |
| Escenario 6 / RN-03 | QA-07 |
| Escenario 7 / RN-03 | QA-08 |
| RN-03 (moneda, documentos no legibles) | QA-09 |
| Escenario 8 / RN-03 | QA-10 |
| RN-04 | QA-11, QA-12 |
| Escenario 9 / RN-06 | QA-13 |
| Escenario 10 / RN-01, RN-07 | QA-14 |
| RN-08 / RN-09 / Permisos | QA-15 |

---

## Casos de Prueba

### QA-01: Ítem completo es suficiente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02
- **Datos de prueba:**

  | Caso | Cantidad | Precio | Etapa |
  | ---- | -------- | ------ | ----- |
  | A | 8 | 2.150.000 explícito | adjudicado |
  | B | 8 | 2.150.000 derivado | contratado |

- **Pasos:**
  1. Evaluar cada ítem.
- **Resultado esperado:** ambos "información suficiente" y disponibles para comparación.

### QA-02: Base indeterminada no hace insuficiente al ítem

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Pasos:**
  1. Evaluar un ítem con cantidad 8, precio explícito 2.150.000 adjudicado y base `indeterminada`.
- **Resultado esperado:** "información suficiente".

### QA-03: Valor global mezcla bienes o servicios

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03, RN-05
- **Pasos:**
  1. Evaluar un ítem con cantidad 2, sin precio, con "condiciones de precio derivado no cumplidas: 2, 4".
- **Resultado esperado:** "información insuficiente" con "valor global mezcla bienes o servicios" (fuente) y "condiciones de precio derivado no cumplidas: 2, 4" (fuente); no disponible para comparación.

### QA-04: Oferta del adjudicatario no identificable

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-03
- **Pasos:**
  1. Evaluar un ítem con precio nulo y observación "oferta adjudicada no identificable".
- **Resultado esperado:** motivo "oferta del adjudicatario no publicada o no identificable" (fuente).

### QA-05: Solo precio de presupuesto

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-02, RN-05
- **Pasos:**
  1. Evaluar un ítem con cantidad 5 y precio 2.400.000 de etapa "presupuesto o cotización".
- **Resultado esperado:** "información insuficiente", motivo "solo precio de presupuesto o cotización" (fuente); el precio 2.400.000 sigue visible con su etapa y evidencia; no disponible para comparación.

### QA-06: Cantidad no documentada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-03
- **Pasos:**
  1. Evaluar un ítem con precio explícito 2.150.000 y cantidad nula sin observación de descarte.
- **Resultado esperado:** motivo "cantidad no documentada" (fuente).

### QA-07: Formato de oferta en blanco en el proceso

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-03
- **Datos de prueba:**

  | Caso | Documento económico del proceso | ¿Motivo presente? |
  | ---- | ------------------------------- | ----------------- |
  | A | "ANEXO 3 - FORMATO PROPUESTA ECONOMICA.xlsx" marcado formulario en blanco | Sí |
  | B | "Oferta economica.pdf" marcado archivo vacío | Sí |
  | C | Solo "Estudio previo.pdf" (no económico) sin datos | No |

- **Pasos:**
  1. Evaluar un ítem sin precio en cada caso.
- **Resultado esperado:** el de la tabla; cuando aplica, "formato de oferta en blanco o archivo vacío" (fuente).

### QA-08: Causas de procesamiento

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-03
- **Pasos:**
  1. Evaluar un ítem sin precio, con observación "dato sin evidencia válida descartado" en el precio y con el proceso anotado con 15 páginas "lectura visual omitida por límite".
- **Resultado esperado:** motivos "dato descartado por falta de evidencia válida" y "páginas no leídas por límite de lectura visual", ambos con causa procesamiento.

### QA-09: Moneda distinta y documentos económicos no legibles

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-03
- **Datos de prueba:**

  | Caso | Situación | Motivo esperado | Causa |
  | ---- | --------- | --------------- | ----- |
  | A | Precio descartado por "moneda distinta de COP" | moneda distinta de COP | fuente |
  | B | "Oferta economica.pdf" seleccionado quedó "archivo protegido" | documentos económicos no legibles | procesamiento |
  | C | "Evaluacion economica.pdf" quedó "descarga bloqueada" | documentos económicos no legibles | procesamiento |

- **Pasos:**
  1. Evaluar un ítem sin precio en cada caso.
- **Resultado esperado:** el de la tabla.

### QA-10: Sin precio ni total publicados

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-03
- **Pasos:**
  1. Evaluar un ítem con cantidad 4, precio y total nulos, sin otras observaciones.
- **Resultado esperado:** motivo "precio unitario no publicado" (fuente).

### QA-11: Varios motivos sin duplicados

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Pasos:**
  1. Evaluar un ítem con cantidad nula, precio nulo, observación "oferta adjudicada no identificable" en dos documentos y un formulario en blanco en el proceso.
- **Resultado esperado:** motivos "cantidad no documentada", "oferta del adjudicatario no publicada o no identificable" (una sola vez) y "formato de oferta en blanco o archivo vacío".

### QA-12: Motivo no identificado

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-04
- **Pasos:**
  1. Evaluar un ítem con cantidad 3, precio unitario nulo y valor total 6.000.000 sin resultado de evaluación del derivado ni observaciones.
- **Resultado esperado:** "información insuficiente" con "motivo no identificado" (procesamiento).

### QA-13: Resumen por proceso

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-06
- **Datos de prueba:**

  | Proceso | Situación | Resumen esperado |
  | ------- | --------- | ---------------- |
  | CO1.BDOS.5372563 | "sin documentos relevantes" | proceso sin ítems comparables: sin documentos relevantes |
  | CO1.BDOS.8234869 | 2 ítems insuficientes: "precio unitario no publicado" y "precio unitario no publicado" + "cantidad no documentada" | proceso sin ítems comparables: precio unitario no publicado; cantidad no documentada |
  | CO1.BDOS.7654321 | 1 suficiente y 1 insuficiente | no es "sin ítems comparables" |

- **Pasos:**
  1. Consultar el resumen de cada proceso.
- **Resultado esperado:** el de la tabla.

### QA-14: Reevaluación tras corrección y historial

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-01, RN-07
- **Pasos:**
  1. Partir del ítem de QA-06 (cantidad nula, precio 2.150.000).
  2. Como Administrador, corregir la cantidad a 6 con evidencia.
- **Resultado esperado:** el ítem pasa a "información suficiente"; el historial guarda "información insuficiente" con "cantidad no documentada", la fecha y `admin.po@piloto.test`.

### QA-15: Contadores, funcionamiento sin IA y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-08 / RN-09 / Permisos requeridos
- **Pasos:**
  1. Con la extracción con IA desactivada, reevaluar los ítems de QA-03 a QA-06.
  2. Como `analista1@piloto.test`, consultar estado y motivos de un ítem; como Administrador, consultar los contadores.
- **Resultado esperado:** la reevaluación funciona sin llamadas al servicio de IA; el Analista ve estado y motivos; los contadores muestran 4 insuficientes con su desglose por motivo y causa.

---

**Total de casos:** 15
