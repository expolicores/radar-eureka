# Casos de Prueba — HU-058: Calcular el Benchmark 2 – Mercado con degradación a "no disponible"

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban los estados del Benchmark 2 (estadística, disponible, no disponible), los cálculos de mediana, cuartiles y desviación, el lenguaje permitido, la degradación sin afectar al Benchmark 1, las marcas heredadas y el vínculo con observaciones. Queda fuera la selección de observaciones (HU-055) y la homologación (HU-056).

## Precondiciones y Datos Base

- `b2_minimo_observaciones` = 3; `b2_minimo_fuentes` = 2; `b2_ventana_dias` = 30.
- Ítem objetivo IO-5: SECOP II CO1.PCCNTR.7770001, LG 50UR7800, fecha de firma 2026-08-20; Benchmark 1 con "Referencia estadística" (7 comparables, mediana 2.100.000).
- Valores ya homologados, COP.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-03, RN-04 | QA-01 |
| Escenario 2 / RN-02 fuentes / RN-05 | QA-02 |
| RN-02 límite de observaciones | QA-03 |
| Escenario 3 / RN-07 manual | QA-04 |
| Escenario 4 / RN-06 | QA-05 |
| Escenario 5 | QA-06 |
| Escenario 6 / RN-06 error | QA-07 |
| Escenario 7 / RN-07 | QA-08 |
| Escenario 8 / RN-07 | QA-09 |
| RN-05 términos prohibidos | QA-10 |
| RN-08 / RN-09 recalculo | QA-11 |

---

## Casos de Prueba

### QA-01: Referencia estadística de mercado con cuartiles

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02 a RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Observaciones | 1.799.900 (Alkosto), 1.849.900 (Alkosto), 1.899.900 (Falabella), 1.949.900 (Falabella) | 4 de 2 fuentes |
  | Precio contratado | 2.300.000 | |

- **Pasos:**
  1. Ejecutar el cálculo del Benchmark 2.
- **Resultado esperado:** Estado "Referencia estadística de mercado (4 observaciones de 2 fuentes)"; mediana 1.874.900; Q1 1.837.400; Q3 1.912.400; IQR 75.000; desviación "+22,7 %".

### QA-02: Referencia disponible por una sola fuente

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Observaciones | 1.800.000, 1.850.000, 1.900.000 (Alkosto) | 3 de 1 fuente |
  | Precio contratado | 2.405.000 | |

- **Pasos:**
  1. Ejecutar el cálculo.
- **Resultado esperado:** Estado "Referencia de mercado disponible – evidencia limitada (3 observaciones de 1 fuente; mínimo 3 de 2 fuentes)"; referencia 1.850.000; desviación "+30,0 %"; sin cuartiles; texto "Evidencia limitada: no es una referencia estadística robusta".

### QA-03: Límite de observaciones con dos fuentes

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Conjunto A | 1.800.000 (Alkosto), 1.900.000 (Falabella) | 2 de 2 fuentes |
  | Conjunto B | A + 1.850.000 (Alkosto) | 3 de 2 fuentes |

- **Pasos:**
  1. Ejecutar con A y con B.
- **Resultado esperado:** A → "Referencia de mercado disponible – evidencia limitada (2 observaciones de 2 fuentes; mínimo 3 de 2 fuentes)", referencia 1.850.000. B → "Referencia estadística de mercado (3 observaciones de 2 fuentes)", mediana 1.850.000.

### QA-04: Una observación manual

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Observación | Alkosto 2.000.000, método manual | |
  | Precio contratado | 2.300.000 | |

- **Pasos:**
  1. Ejecutar el cálculo.
- **Resultado esperado:** Estado "Referencia de mercado disponible – evidencia limitada (1 observación de 1 fuente; mínimo 3 de 2 fuentes)"; indicador "Manual"; desviación "+15,0 %".

### QA-05: Benchmark 2 no disponible sin afectar al Benchmark 1

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-06
- **Pasos:**
  1. Dejar vacío el conjunto del Benchmark 2 de IO-5.
  2. Ejecutar el cálculo de ambos benchmarks.
- **Resultado esperado:** Benchmark 2 "No disponible / evidencia insuficiente – sin observaciones de mercado en la ventana (±30 días)", sin referencia ni desviación; Benchmark 1 con "Referencia estadística", mediana 2.100.000 y su desviación, idéntico al cálculo sin Benchmark 2.

### QA-06: Ítem no elegible para el Benchmark 2

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Motivo | "Sin fecha de compra" | |

- **Pasos:**
  1. Ejecutar el cálculo.
- **Resultado esperado:** "No disponible / evidencia insuficiente – Sin fecha de compra".

### QA-07: Error del Benchmark 2 no bloquea el Benchmark 1 ni sus señales

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Falla simulada | Error inesperado en el cálculo del Benchmark 2 de IO-5 | |
  | Precio contratado IO-5 | 2.750.000 | Cumple condición de señal en Benchmark 1 |

- **Pasos:**
  1. Provocar la falla y ejecutar el proceso completo.
- **Resultado esperado:** Benchmark 2 "No disponible / evidencia insuficiente – error de cálculo"; el log registra identificador de IO-5, fecha-hora y descripción; Benchmark 1 calculado y la señal del Benchmark 1 publicada normalmente.

### QA-08: Marca tributaria heredada

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-07
- **Pasos:**
  1. Calcular con QA-01 marcando 1 observación con base indeterminada (no alcanzan el mínimo las determinadas).
- **Resultado esperado:** El resultado conserva "Incompleta / no confiable: base tributaria indeterminada en 1 de 4 observaciones".

### QA-09: Vínculo y método de cada observación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-07
- **Pasos:**
  1. Ejecutar QA-01 (1 observación manual, 3 por sitemap-datos estructurados) y consultar el resultado.
- **Resultado esperado:** 4 observaciones con identificador, "Retail – Alkosto"/"Retail – Falabella", fecha, precio original y homologado, base, método e indicador "Manual" solo en la manual.

### QA-10: Ninguna etiqueta usa "precio de mercado"

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-05
- **Pasos:**
  1. Generar los tres estados (QA-01, QA-02, QA-05) y revisar todas las etiquetas generadas.
- **Resultado esperado:** Ningún texto contiene "precio de mercado"; solo las etiquetas de RN-02.

### QA-11: Recalculo reemplaza el resultado vigente

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-08 / RN-09
- **Pasos:**
  1. Calcular con QA-02.
  2. Registrar una observación Falabella 1.880.000 dentro de la ventana y esperar el recálculo.
- **Resultado esperado:** El resultado vigente pasa a "Referencia estadística de mercado (4 observaciones de 2 fuentes)" con nueva fecha-hora y parámetros usados.

---

**Total de casos:** 11
