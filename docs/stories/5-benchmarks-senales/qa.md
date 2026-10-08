# Casos de Prueba — Historia #5: Benchmarks simulados y generación de señales

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-07

## Alcance de las Pruebas

**Se prueba:** selección de comparables y ventanas, estadísticos, regla híbrida de señal, precios bajos, estados explícitos, Benchmark 2, confianza, versionado de solo inserción, código de señal y exploración con estados y filtro de señal.
**Queda fuera:** API y pantalla de señales, detalle, carga manual de mercado.

## Precondiciones y Datos Base

| Dato | Valor | Nota |
| ---- | ----- | ---- |
| Configuración | `analitica-v1` | Ventanas 6/12 meses y 30 días; mínimos 5 y 3/2; k = 1,5; umbrales 30 % / 50 % |
| Ítem objetivo | 65", 4K, LED, Smart · $4.950.000 IVA incluido · 2026-08-14 | Compra de referencia del mockup |
| Comparables públicos (mockup) | 14 precios entre $2.350.000 y $3.600.000 (mar–sep 2026) | Mediana $2.860.000 · Q3 $3.115.000 · umbral $3.867.500 en el mockup |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1: comparables, ventana, estadísticos | QA-01, QA-02, QA-03 |
| Escenario 2: regla híbrida y bajos | QA-04, QA-05, QA-06 |
| Escenario 3: estados explícitos | QA-07 |
| Escenario 4: Benchmark 2 | QA-08 |
| Escenario 5: confianza | QA-09 |
| Escenario 6: versionado | QA-10 |
| Escenario 7: exploración | QA-11 |
| Regla: código de señal | QA-12 |

---

## Casos de Prueba

### QA-01: Solo cuentan comparables equivalentes, de otras compras, con IVA incluido y en ventana

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Datos de prueba:**

  | Candidato | ¿Comparable? |
  | --------- | ------------ |
  | 65" 4K LED, IVA incluido, 3 meses antes | Sí |
  | 55" 4K LED | No (otro tamaño) |
  | 65" 4K QLED | No (otro panel) |
  | 65" 4K LED, IVA indeterminado | No |
  | 65" 4K LED, 8 meses antes | No (fuera de ±6) |
  | Otro ítem de la misma compra | No |
  | 65" 4K LED con precio en revisión | No |

- **Resultado esperado:** solo el primero.

### QA-02: La ventana se amplía a ±12 meses cuando hay menos de 5 comparables

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Resultado esperado:** con 3 en ±6 meses y 3 más entre 6 y 12 meses, se usan 6 a ±12 meses y se registra la penalización «ventana ampliada».

### QA-03: Cuartiles, mediana y umbral reproducen el mockup

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Resultado esperado:** con los 14 precios del mockup: Q1 $2.630.000, mediana $2.860.000, Q3 $3.125.000 (interpolación lineal), umbral $3.867.500; desviación de $4.950.000 frente a la mediana +73,1 %.

### QA-04: Con muestra homogénea, la señal usa el umbral Q3 + 1,5 × RIC

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Resultado esperado:** $4.950.000 frente a los 14 comparables genera señal; un precio igual o menor al umbral no.

### QA-05: Con muestra pequeña o heterogénea, la señal usa el umbral porcentual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Datos de prueba:** 6 comparables con mediana $2.000.000.

  | Emparejamiento | Precio | ¿Señal? |
  | -------------- | ------ | ------- |
  | Mismo modelo | $2.600.000 (+30 %) | Sí |
  | Mismo modelo | $2.580.000 (+29 %) | No |
  | Equivalente | $3.000.000 (+50 %) | Sí |
  | Equivalente | $2.900.000 (+45 %) | No |

### QA-06: Los precios anormalmente bajos van a revisión de calidad, no a señal

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Resultado esperado:** un precio por debajo de Q1 − 1,5 × RIC queda `quality_review_low_price`, sin señal.

### QA-07: Los datos faltantes nunca generan señal

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3
- **Datos de prueba:** sin precio; precio en revisión; IVA indeterminado; IVA excluido; 4 comparables a ±12 meses.
- **Resultado esperado:** `no_unit_price`, `quality_review`, `vat_incomplete`, `vat_incomplete`, `insufficient_comparables`; ninguno con señal.

### QA-08: Benchmark 2 con referencia, evidencia limitada o no disponible

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4
- **Datos de prueba:**

  | Observaciones en ±30 días | Estado | Referencia |
  | ------------------------- | ------ | ---------- |
  | 3 de 2 tiendas | `reference` | mediana |
  | 2 de 2 tiendas | `limited` | la más alta |
  | 4 de 1 tienda | `limited` | la más alta |
  | 0 (o solo de vendedor tercero, con condición especial o fuera de ±30 días) | `unavailable` | — |

### QA-09: La confianza resta las penalizaciones y asigna el nivel

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Datos de prueba:** equivalente + B2 limitado + 14 comparables → 70 (media); mismo modelo + B2 con referencia + 12 comparables → 100 (alta); equivalente + derivado + B2 no disponible + 6 comparables + porcentual → 35 (baja).

### QA-10: El recálculo inserta una nueva versión y solo la última es vigente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6
- **Resultado esperado:** tras dos recálculos hay dos resultados por ítem, uno vigente; los dos llevan `config_version_id = analitica-v1`; los comparables quedan vinculados.

### QA-11: La exploración muestra el estado de señal y filtra

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 7
- **Resultado esperado:** `CO1.PCCNTR.0000142` aparece «con señal»; `has_signal=true` devuelve solo compras con señal y `false` solo sin señal.

### QA-12: El código de señal es estable y legible

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Regla de código
- **Datos de prueba:** `CO1.PCCNTR.0000142` (2026) → `SG-2026-0142`; orden TVEC `163772` (2025) → `SG-2025-T163772`.

---

**Total de casos:** 12
