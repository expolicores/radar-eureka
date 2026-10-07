# Casos de Prueba — HU-023: Determinar si cada precio extraído es con IVA, sin IVA o de base indeterminada

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la clasificación determinística de la base tributaria por valor (precio unitario y total), las expresiones configurables, la estructura subtotal-IVA-total, la prioridad por especificidad, las contradicciones, la ausencia de declaración, la evidencia obligatoria, las exenciones, el valor y la tasa de IVA, y la configuración. Las declaraciones se suministran como salida simulada de HU-022. Queda fuera: el uso de la base en las comparaciones (épica de señales).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Ítem base `CO1.PCCNTR.7654321-01`: cantidad 8; documento "Propuesta_economica_ganador.pdf" (versión 1).
- Expresiones configuradas según RN-03, RN-04 y RN-05.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-03, RN-07 | QA-01 |
| Escenario 2 / RN-01, RN-04, RN-11 | QA-02 |
| Escenario 3 / RN-06 | QA-03, QA-04 |
| Escenario 4 / RN-09 | QA-05 |
| Escenario 5 / RN-09 | QA-06 |
| Escenario 6 / RN-05 | QA-07 |
| Escenario 7 / RN-07 | QA-08, QA-09 |
| Escenario 8 / RN-08 | QA-10 |
| Escenario 9 / RN-10 | QA-11 |
| Escenario 10 / RN-01 | QA-12 |
| RN-11 (tasa fuera de rango) | QA-13 |
| RN-12 | QA-14 |
| RN-13 | QA-15 |
| RN-14 / Permisos | QA-16 |
| RN-15 | QA-17 |

---

## Casos de Prueba

### QA-01: Expresiones de IVA incluido

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-07
- **Datos de prueba:**

  | Declaración (encabezado de columna, página 2) |
  | --------------------------------------------- |
  | "Valor unitario IVA incluido" |
  | "VALOR UNITARIO (INCLUYE IVA)" |
  | "Precio final con IVA" |

- **Pasos:**
  1. Determinar la base con cada declaración.
- **Resultado esperado:** precio unitario `con_iva` con evidencia "Propuesta_economica_ganador.pdf, versión 1, página 2" y el texto literal.

### QA-02: Precio unitario sin IVA y total con IVA

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-01, RN-04, RN-11
- **Datos de prueba:**

  | Campo | Valor | Declaración |
  | ----- | ----- | ----------- |
  | Precio unitario | 1.806.723 | "Valor unitario antes de IVA" |
  | IVA | 2.747.000 | "IVA 19 %" |
  | Total del ítem | 17.200.000 | "Valor total con IVA" |

- **Pasos:**
  1. Determinar la base.
- **Resultado esperado:** precio unitario `sin_iva`; total `con_iva`; valor de IVA 2.747.000 y tasa 19 % registrados con evidencia.

### QA-03: Estructura subtotal-IVA-total

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-06
- **Pasos:**
  1. Determinar la base de un total 17.200.000 extraído de la fila "Total" en "Subtotal $ 14.453.782 / IVA $ 2.746.218 / Total $ 17.200.000"; repetir con un valor extraído de la fila "Subtotal".
- **Resultado esperado:** el total queda `con_iva`; el subtotal queda `sin_iva`.

### QA-04: Columna de IVA separada en la fila

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Encabezados | Fila |
  | ----------- | ---- |
  | Valor unitario \| IVA \| Valor total | 1.806.723 \| 343.277 \| 2.150.000 |
  | Valor unitario IVA incluido \| IVA \| Valor total | 2.150.000 \| 343.277 \| 2.150.000 |

- **Pasos:**
  1. Determinar la base del valor unitario en cada caso.
- **Resultado esperado:** primer caso `sin_iva` (columna IVA separada); segundo caso `con_iva` (el encabezado lo dice explícitamente).

### QA-05: Sin declaración

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-09
- **Pasos:**
  1. Determinar la base de "Valor unitario $ 2.150.000" sin ninguna mención de IVA en el documento.
- **Resultado esperado:** `indeterminada`, motivo "sin declaración tributaria en el documento".

### QA-06: Coincidencia aritmética no determina la base

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-09
- **Datos de prueba:**

  | Precio unitario | Total | Cálculo | Observación esperada |
  | --------------- | ----- | ------- | -------------------- |
  | 1.806.723 | 17.200.000 | 8 × 1.806.723 × 1,19 = 17.199...., dentro de 0,5 % | Sí |
  | 1.806.723 | 18.000.000 | Fuera de 0,5 % | No |

- **Pasos:**
  1. Determinar la base sin declaraciones.
- **Resultado esperado:** en ambos casos los dos valores `indeterminada`; solo el primero lleva "coincidencia aritmética con IVA 19 % sin declaración explícita".

### QA-07: Exención o exclusión

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-05
- **Datos de prueba:**

  | Declaración |
  | ----------- |
  | "Bienes exentos de IVA - Ley 1607 de 2012" |
  | "Excluido de IVA" |
  | "No causa IVA" |

- **Pasos:**
  1. Determinar la base con cada declaración junto al precio.
- **Resultado esperado:** `sin_iva`, indicador "exento o excluido de IVA: sí", anotación "el precio final al comprador coincide con este valor".

### QA-08: Declaración general del documento

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-07
- **Pasos:**
  1. Determinar la base de valores de la página 2 con la declaración "Todos los precios de la presente oferta incluyen IVA" en la página 1 del mismo documento.
- **Resultado esperado:** `con_iva`, con evidencia en la página 1.

### QA-09: Prioridad por especificidad y documento distinto

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-07
- **Datos de prueba:**

  | Caso | Declaración general | Declaración específica | Resultado esperado |
  | ---- | ------------------- | ---------------------- | ------------------ |
  | A | "Precios con IVA" (pág. 1) | Columna "Valor antes de IVA" (pág. 2) | `sin_iva` |
  | B | "Precios con IVA" en el contrato | Ninguna en la oferta de donde sale el valor | `indeterminada` (otro documento) |

- **Pasos:**
  1. Determinar la base en cada caso.
- **Resultado esperado:** el de la tabla.

### QA-10: Declaraciones contradictorias del mismo nivel

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-08
- **Pasos:**
  1. Determinar la base con nota de tabla "valores con IVA" y pie de la misma tabla "valores antes de IVA".
- **Resultado esperado:** `indeterminada`, motivo "declaraciones tributarias contradictorias", con ambas evidencias.

### QA-11: Base indicada sin evidencia

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-10
- **Pasos:**
  1. Suministrar una salida del extractor con base "con IVA" sin texto ni ubicación.
- **Resultado esperado:** `indeterminada`, motivo "declaración tributaria sin evidencia".

### QA-12: Valores nulos no tienen base

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** Escenario 10 / RN-01
- **Pasos:**
  1. Determinar la base de un ítem con precio unitario nulo y total nulo.
- **Resultado esperado:** ambas bases nulas, sin motivo.

### QA-13: Tasa de IVA fuera de rango

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-11
- **Datos de prueba:**

  | Tasa publicada | Resultado esperado |
  | -------------- | ------------------ |
  | 0 % | registrada |
  | 100 % | registrada |
  | 190 % | descartada, "tasa de IVA fuera de rango" |

- **Pasos:**
  1. Determinar la base con cada tasa.
- **Resultado esperado:** el de la tabla.

### QA-14: El precio derivado hereda la base del total

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-12
- **Pasos:**
  1. Para un ítem con total 17.200.000 `con_iva` y precio derivado 2.150.000 (HU-024), consultar la base del precio derivado.
- **Resultado esperado:** `con_iva`, con la misma evidencia del total.

### QA-15: La base no se infiere de otras fuentes

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Determinar la base de un precio sin declaración en un contrato cuyo proveedor tiene otros 3 contratos con precios `con_iva`.
- **Resultado esperado:** `indeterminada`, motivo "sin declaración tributaria en el documento".

### QA-16: Cambio de expresiones y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-14 / Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar agregar la expresión "valor neto" a `sin_iva`.
  2. Como `admin.po@piloto.test`, agregarla y solicitar la redeterminación del proceso de un ítem con "Valor neto $ 1.806.723".
- **Resultado esperado:** el Analista recibe acceso denegado; el cambio del Administrador queda registrado con usuario, fecha, valor anterior y nuevo; tras la redeterminación el valor queda `sin_iva`.

### QA-17: Funciona con la IA desactivada

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-15
- **Pasos:**
  1. Desactivar la extracción con IA y solicitar la redeterminación de QA-16.
- **Resultado esperado:** la base se recalcula sin llamadas al servicio de IA.

---

**Total de casos:** 17
