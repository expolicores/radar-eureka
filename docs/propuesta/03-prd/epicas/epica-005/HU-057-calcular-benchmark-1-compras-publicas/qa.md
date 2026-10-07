# Casos de Prueba — HU-057: Calcular el Benchmark 1 – Contratación pública y la desviación del precio contratado

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el cálculo de la distribución (n, mínimo, Q1, mediana, Q3, IQR, máximo), los estados del Benchmark 1, la desviación porcentual con su redondeo, las marcas heredadas y el vínculo con las observaciones. Queda fuera la selección de comparables (HU-054), la homologación de IVA (HU-056) y la señal (HU-059).

## Precondiciones y Datos Base

- `b1_minimo_observaciones` = 5. Todos los valores ya homologados a precio final con IVA, en COP.
- **Serie S7:** 1.800.000, 1.900.000, 2.000.000, 2.100.000, 2.200.000, 2.300.000, 2.400.000 (TVEC órdenes 120201–120205 y SECOP II CO1.PCCNTR.5550200–5550201).
- **Serie S6:** 1.800.000, 1.900.000, 2.000.000, 2.300.000, 2.400.000, 2.500.000.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-03, RN-04, RN-05 | QA-01 |
| Escenario 2 / RN-03 par | QA-02 |
| Escenario 3 / RN-06 | QA-03 |
| Escenario 4 / RN-05 negativa | QA-04 |
| RN-02 límite del mínimo | QA-05 |
| Escenario 5 | QA-06 |
| Escenario 6 | QA-07 |
| Escenario 7 / RN-07 | QA-08 |
| Escenario 8 / RN-08 | QA-09 |
| Escenario 9 / RN-10 | QA-10 |
| RN-05 redondeo y cero | QA-11 |
| RN-09 resultado almacenado | QA-12 |

---

## Casos de Prueba

### QA-01: Distribución y desviación con referencia estadística

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02 a RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | S7 | n = 7 |
  | Precio contratado | 2.450.000 COP | |

- **Pasos:**
  1. Ejecutar el cálculo del Benchmark 1.
- **Resultado esperado:** Estado "Referencia estadística"; mínimo 1.800.000; Q1 1.950.000; mediana 2.100.000; Q3 2.250.000; IQR 300.000; máximo 2.400.000; desviación "+16,7 %".

### QA-02: Mediana con número par

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | S6 | |
  | Precio contratado | 2.450.000 COP | |
  | Variante | 1.000.001 y 1.000.002 + 4 valores mayores | Mediana con 0,5 |

- **Pasos:**
  1. Ejecutar con S6.
  2. Ejecutar con la variante (1.000.001, 1.000.002, 1.000.003, 1.000.004, 1.000.005, 1.000.006).
- **Resultado esperado:** (1) Mediana 2.150.000; desviación "+14,0 %". (2) Mediana 1.000.003,5 → 1.000.004.

### QA-03: Referencia disponible por debajo del mínimo

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | 1.900.000, 2.000.000, 2.100.000 | n = 3 |
  | Precio contratado | 2.600.000 | |

- **Pasos:**
  1. Ejecutar el cálculo.
- **Resultado esperado:** Estado "Referencia disponible – evidencia limitada (3 de 5 observaciones mínimas)"; referencia 2.000.000; desviación "+30,0 %"; se listan las 3 observaciones; no aparecen Q1, Q3 ni IQR; texto "Evidencia limitada: no es una referencia estadística robusta".

### QA-04: Una sola observación con desviación negativa

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparable | 2.000.000 | n = 1 |
  | Precio contratado | 1.700.000 | |

- **Pasos:**
  1. Ejecutar el cálculo.
- **Resultado esperado:** Estado "Referencia disponible – evidencia limitada (1 de 5 observaciones mínimas)"; referencia 2.000.000; desviación "−15,0 %".

### QA-05: Límite del mínimo (4 y 5 observaciones)

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Conjunto A | 4 primeras de S7 | n = m − 1 |
  | Conjunto B | 5 primeras de S7 | n = m |

- **Pasos:**
  1. Ejecutar con A y con B.
- **Resultado esperado:** A → "Referencia disponible – evidencia limitada (4 de 5 observaciones mínimas)"; B → "Referencia estadística" con mediana 2.000.000, Q1 1.900.000, Q3 2.100.000.

### QA-06: Sin comparables

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 5
- **Pasos:**
  1. Ejecutar con conjunto vacío.
- **Resultado esperado:** Estado "Sin comparables públicos"; sin referencia ni desviación; sin error.

### QA-07: Ítem no elegible conserva su motivo

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Motivo | "Sin precio unitario" | |
  | Motivo | "Emparejamiento insuficiente" | |

- **Pasos:**
  1. Ejecutar el cálculo.
- **Resultado esperado:** Estado "Benchmark 1 no calculado – Sin precio unitario" / "– Emparejamiento insuficiente"; sin valores calculados.

### QA-08: Marca de comparación incompleta heredada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Estado tributario | "Incompleta / no confiable: base tributaria indeterminada en 6 de 8 observaciones" | |
  | Ventana | "±12 meses (ampliada)" | |
  | Tipo de conjunto | Producto equivalente | |

- **Pasos:**
  1. Ejecutar el cálculo con 8 observaciones.
- **Resultado esperado:** Se calculan distribución, referencia y desviación; el resultado conserva el estado tributario, la ventana ampliada y el tipo "Producto equivalente".

### QA-09: Vínculo con cada observación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-08
- **Pasos:**
  1. Ejecutar QA-01 y consultar el resultado.
- **Resultado esperado:** Se listan 7 observaciones con identificador, origen ("Contratación pública – TVEC" o "– SECOP II"), precio original, base original, precio homologado, tipo de emparejamiento y fecha.

### QA-10: Recalculo con nuevo mínimo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `b1_minimo_observaciones` | 8 | |

- **Pasos:**
  1. Cambiar el parámetro y recalcular con S7.
- **Resultado esperado:** Estado "Referencia disponible – evidencia limitada (7 de 8 observaciones mínimas)"; referencia 2.100.000; sin cuartiles.

### QA-11: Redondeo de la desviación y desviación nula

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Referencia 2.000.000, precio 2.599.000 | 29,95 % | Se muestra "+30,0 %" |
  | Referencia 2.000.000, precio 2.598.900 | 29,945 % | Se muestra "+29,9 %" |
  | Referencia 2.000.000, precio 1.401.000 | −29,95 % | Se muestra "−30,0 %" |
  | Referencia 2.000.000, precio 2.000.000 | 0 % | Se muestra "0,0 %" |

- **Pasos:**
  1. Ejecutar el cálculo para cada par.
- **Resultado esperado:** Desviaciones mostradas y almacenadas como indica la tabla.

### QA-12: Resultado almacenado con parámetros

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Ejecutar QA-01 y consultar el resultado almacenado; luego recalcular.
- **Resultado esperado:** Constan estado, n, mínimo configurado, estadísticos, referencia, desviación, marcas, parámetros y fecha-hora; tras recalcular, el resultado vigente se reemplaza con nueva fecha-hora.

---

**Total de casos:** 12
