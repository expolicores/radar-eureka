# Casos de Prueba — HU-078: Ver los benchmarks de cada ítem con la distribución de precios comparables en la ficha

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la sección "Benchmarks" de la ficha: Benchmark 1 con referencia estadística, evidencia limitada y sin comparables; ventana inicial y ampliada; visualización, tabla y resumen textual; base tributaria indeterminada; Benchmark 2 agregado, limitado y no disponible; marcas de observación manual y condición especial; ítems sin comparación; navegación a observaciones; lenguaje, formatos, rendimiento y accesibilidad. Queda fuera el cálculo de benchmarks y la configuración de sus parámetros.

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (Analista).
- **Parámetros usados en el cálculo (valores iniciales):** B1 ventana ±6 meses, ampliable a ±12; mínimo B1 = 5; B2 ventana ±30 días; mínimo B2 = 3 observaciones de 2 fuentes.
- **Contrato C1 (SECOP II, fecha de compra 15/09/2026):**

  | Ítem | Precio contratado | Benchmark 1 | Benchmark 2 |
  | ---- | ----------------- | ----------- | ----------- |
  | I1 Samsung UN65CU7000 65" | $ 3.900.000 (con IVA) | 7 obs. (2 SECOP II, 5 TVEC), mismo modelo, ventana ±6 meses; precios $ 2.600.000, $ 2.750.000, $ 2.820.000, $ 2.884.000, $ 2.950.000, $ 3.050.000, $ 3.200.000; mediana $ 2.884.000; desviación +35,2 % | 3 obs.: Alkosto $ 3.099.900 (sitemap-datos estructurados), Alkosto $ 3.149.900 (manual), Falabella $ 3.199.900 (extracción web); además 1 obs. Alkosto $ 2.899.900 con precio sujeto a tarjeta específica (listada, no usada en la referencia); mediana $ 3.149.900; desviación +23,8 % |
  | I2 LG 55UR8750 55" | $ 2.950.000 (base indeterminada, derivado) | 3 obs. TVEC, producto equivalente (55", 4K UHD, LED, Smart), ventana ampliada ±12 meses | 1 obs. Alkosto $ 2.099.900 |
  | I3 Kalley K-TV32HD 32" | $ 1.300.000 | 0 obs. en ±12 meses | no disponible |
  | I4 Televisor 50" | sin precio unitario | — | — |
  | I5 Challenger 43" | $ 1.100.000 | comparación pendiente | — |

- **Orden TVEC 2023 (fecha de compra 10/02/2023):** ítem con B1 de 6 obs. y B2 no disponible.
- **Ítem con 250 observaciones de B1** en un contrato de prueba C9.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-04 / RN-07 / RN-09 | QA-01 |
| Escenario 2 / RN-10 | QA-02, QA-14 |
| Escenario 3 / RN-11 | QA-03 |
| Escenario 4 / RN-04 | QA-04 |
| Escenario 5 / RN-03 | QA-04 |
| Escenario 6 | QA-05 |
| Escenario 7 / RN-08 | QA-06 |
| Escenario 8 / RN-05 / RN-06 | QA-07 |
| Escenario 9 / RN-05 | QA-08 |
| Escenario 10 | QA-09 |
| Escenario 11 / RN-08 | QA-07 |
| Escenario 12 / RN-12 | QA-10 |
| Escenario 13 | QA-11 |
| RN-07 insuficiente / no confiable | QA-12 |
| RN-13 | QA-13 |
| RN-14 | QA-15 |
| RN-15 | QA-16 |

---

## Casos de Prueba

### QA-01: Benchmark 1 con referencia estadística

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02 / RN-04 / RN-07 / RN-09
- **Pasos:**
  1. Abrir la ficha de C1 en "Benchmarks", bloque de I1.
  2. Activar "Ver fórmula".
- **Resultado esperado:** "Benchmark 1 – Compras públicas", mediana "$ 2.884.000", "7 observaciones: 2 SECOP II, 5 TVEC", "±6 meses desde la fecha de compra", "Mismo modelo", base "con IVA", "+35,2 % frente a la mediana"; la fórmula muestra "($ 3.900.000 − $ 2.884.000) / $ 2.884.000 × 100 = +35,2 %".

### QA-02: Distribución con mediana, Q1–Q3 y precio contratado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-10
- **Pasos:**
  1. Observar la visualización de I1.
- **Resultado esperado:** 7 puntos en el eje de precio; marca de mediana en $ 2.884.000; banda Q1–Q3; marca distinta (forma y etiqueta) "Precio contratado: $ 3.900.000"; la escala incluye $ 2.600.000 y $ 3.900.000.

### QA-03: Tabla equivalente y resumen textual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-11
- **Pasos:**
  1. Activar "Ver como tabla" en I1.
  2. Escuchar la visualización con lector de pantalla.
- **Resultado esperado:** tabla con 7 filas ordenadas de $ 2.600.000 a $ 3.200.000, con fuente, entidad, fecha, precio, emparejamiento y desviación del precio contratado frente a cada una; resumen "Precio contratado $ 3.900.000; mediana $ 2.884.000; 7 observaciones entre $ 2.600.000 y $ 3.200.000".

### QA-04: Evidencia limitada con ventana ampliada

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / Escenario 5 / RN-03 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Observaciones B1 de I2 | 3 | mínimo − 2 |
  | Observaciones B1 del ítem TVEC 2023 | 6 | mínimo + 1 |

- **Pasos:**
  1. Revisar el bloque de I2.
  2. Revisar el ítem de la orden TVEC 2023.
- **Resultado esperado:** I2 muestra "±12 meses (ampliada por falta de comparables en ±6 meses)" y "Referencia disponible — evidencia limitada (3 de 5 observaciones requeridas para una referencia estadística)", sin mediana ni Q1–Q3, con desviación por observación en la tabla; el ítem TVEC con 6 observaciones muestra mediana.

### QA-05: Sin comparables en compras públicas

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:**
  1. Revisar el bloque de I3.
- **Resultado esperado:** "Benchmark 1 – Compras públicas: sin observaciones comparables en la ventana de ±12 meses." sin visualización.

### QA-06: Base tributaria indeterminada

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Revisar el Benchmark 1 de I2.
- **Resultado esperado:** marca "Comparación incompleta / no confiable: base tributaria (IVA) indeterminada".

### QA-07: Benchmark 2 agregado con marcas de manual y condición especial

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / Escenario 11 / RN-05 / RN-06 / RN-08
- **Pasos:**
  1. Revisar el Benchmark 2 de I1.
- **Resultado esperado:** "Benchmark 2 – Mercado", mediana "$ 3.149.900", "3 observaciones de 2 fuentes", "±30 días desde la fecha de compra", "+23,8 %"; lista con fuente, fecha, precio efectivo y método; la observación manual muestra "Observación manual"; la observación de $ 2.899.900 aparece con "Precio con condición especial (tarjeta)" y "No se usa como precio general de mercado", y no cuenta entre las 3 observaciones de la referencia.

### QA-08: Referencia de mercado disponible con evidencia limitada

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-05
- **Pasos:**
  1. Revisar el Benchmark 2 de I2.
- **Resultado esperado:** "Referencia de mercado disponible — evidencia limitada (1 observaciones de 1 fuentes)" con la observación de Alkosto; el texto "precio de mercado" no aparece.

### QA-09: Benchmark 2 no disponible con Benchmark 1 visible

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10
- **Pasos:**
  1. Revisar el ítem de la orden TVEC 2023.
- **Resultado esperado:** "Benchmark 2 – Mercado: no disponible / evidencia insuficiente. No se usan precios actuales para juzgar compras antiguas."; el Benchmark 1 se muestra completo.

### QA-10: Ítems sin precio y con comparación pendiente

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 12 / RN-12
- **Pasos:**
  1. Revisar los bloques de I4 e I5.
- **Resultado esperado:** I4 muestra "Sin comparación: el ítem no tiene precio unitario disponible."; I5 muestra "Comparación pendiente".

### QA-11: Navegar a las observaciones

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 13
- **Pasos:**
  1. En la tabla de I1 activar una observación TVEC.
  2. En el Benchmark 2 de I1 activar la observación manual.
- **Resultado esperado:** paso 1 abre la ficha de la orden TVEC de origen; paso 2 abre el detalle de la observación con fuente, referencia, fecha y captura.

### QA-12: Emparejamiento insuficiente no muestra desviación

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Precondiciones:** un ítem cuya comparación quedó clasificada "Insuficiente / no confiable".
- **Pasos:**
  1. Revisar su Benchmark 1.
- **Resultado esperado:** se muestra "Insuficiente / no confiable" sin desviación porcentual.

### QA-13: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-13
- **Pasos:**
  1. Buscar los términos prohibidos en la sección de C1.
- **Resultado esperado:** 0 apariciones de "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".

### QA-14: Muchas observaciones

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Pasos:**
  1. Abrir la ficha de C9 (250 observaciones).
- **Resultado esperado:** los puntos se superponen con transparencia, la mediana y el precio contratado siguen visibles y la tabla lista las 250 observaciones.

### QA-15: Formatos y rendimiento

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-14
- **Precondiciones:** 20 sesiones concurrentes.
- **Pasos:**
  1. Abrir la ficha de C1 repetidamente durante 10 minutos.
- **Resultado esperado:** ficha completa con benchmarks en ≤ 3 s (p95); valores en formato "$ 2.884.000", "+35,2 %" y fechas DD/MM/AAAA.

### QA-16: Accesibilidad y móvil

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-15
- **Pasos:**
  1. Verificar contraste de las marcas gráficas y abrir "Ver como tabla" con teclado.
  2. Ver la sección a 360 px.
- **Resultado esperado:** contraste ≥ 3:1 en marcas; la tabla se abre con teclado; a 360 px la visualización se ajusta al ancho y la tabla se desplaza horizontalmente con todas sus columnas.

---

**Total de casos:** 16
