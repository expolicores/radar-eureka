# Casos de Prueba — HU-055: Seleccionar observaciones retail del Benchmark 2 cercanas a la fecha de la compra

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la selección automática de observaciones retail para el Benchmark 2: ventana temporal, validez de cada observación, deduplicación por tienda y producto, selección escalonada por emparejamiento, mínimos de observaciones y fuentes, parámetros y trazabilidad del origen y método de adquisición. Queda fuera el cálculo de la referencia y la degradación (HU-058) y la homologación de IVA (HU-056).

## Precondiciones y Datos Base

- Configuración inicial: `b2_ventana_dias` = 30, `b2_minimo_observaciones` = 3, `b2_minimo_fuentes` = 2, fuentes habilitadas Alkosto y Falabella.
- **Ítem objetivo IO-2:** TVEC, orden 130010, televisor LG 50UR7800 (50", 4K, LED, Smart), fecha de orden 2026-08-20, precio unitario 1.890.000 COP. Ventana ±30 días = [2026-07-21, 2026-09-19].
- **Observaciones base:** Alkosto SKU AK-50UR7800 (mismo modelo), Falabella SKU FB-50UR7800 (mismo modelo), Falabella SKU FB-50UQ7500 (producto equivalente). Vendedor = la tienda, precio efectivo > 0, sin condiciones, salvo indicación.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-07 paso 1 / RN-09 | QA-01 |
| Escenario 2 / RN-04 | QA-02 |
| Escenario 3 / regla temporal | QA-03 |
| Escenario 4 / RN-07 paso 2 / RN-08 | QA-04 |
| Escenario 5 / RN-07 sin mínimo / manual | QA-05 |
| RN-07 mínimo de fuentes | QA-06 |
| Escenario 6 / RN-03 | QA-07 |
| Escenario 7 / RN-06 | QA-08 |
| RN-06 identificación sin SKU | QA-09 |
| Escenario 8 / RN-01 | QA-10 |
| Escenario 9 / RN-04, RN-05 | QA-11 |
| RN-05 parámetro inválido | QA-12 |
| RN-07 conjunto vacío total | QA-13 |

---

## Casos de Prueba

### QA-01: Selección de mismo modelo con dos tiendas y trazabilidad completa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-07 / RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Alkosto AK-50UR7800 | 1.799.900 COP, 2026-08-12, método sitemap-datos estructurados | |
  | Alkosto (SKU AK-50UR7800-B, mismo modelo) | 1.849.900 COP, 2026-08-25, método manual | SKU distinto |
  | Falabella FB-50UR7800 | 1.899.900 COP, 2026-09-02, método manual | |

- **Pasos:**
  1. Ejecutar la selección del Benchmark 2 para IO-2.
- **Resultado esperado:** Conjunto de 3 observaciones de 2 fuentes, paso 1, tipo "Mismo modelo", ventana "±30 días", sin marca de "por debajo del mínimo"; cada observación muestra "Retail – Alkosto" o "Retail – Falabella", fecha, precio efectivo, método de adquisición, IVA registrado, URL/evidencia, y las 2 manuales con indicador "Manual".

### QA-02: Observación fuera de la ventana

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Única observación | Alkosto AK-50UR7800, 2026-09-25 | 36 días después |

- **Pasos:**
  1. Ejecutar la selección para IO-2.
- **Resultado esperado:** Conjunto vacío, estado "Sin observaciones de mercado en la ventana (±30 días)", 1 descarte "fuera de ventana".

### QA-03: Compra antigua sin histórico propio

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem objetivo | SECOP II CO1.PCCNTR.4440001, fecha de firma 2023-04-10 | |
  | Observaciones existentes | Todas desde 2026-09-01 | |

- **Pasos:**
  1. Ejecutar la selección para el ítem.
- **Resultado esperado:** Conjunto vacío, estado "Sin observaciones de mercado en la ventana (±30 días)"; ninguna observación de 2026 se usa.

### QA-04: Incorporación de equivalentes

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-07 paso 2 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Mismo modelo | 2 Alkosto (SKUs distintos) | 1 fuente: no alcanza |
  | Equivalentes | 2 Falabella (FB-50UQ7500 y FB-50CU7000) | |

- **Pasos:**
  1. Ejecutar la selección para IO-2.
- **Resultado esperado:** Conjunto de 4 observaciones de 2 fuentes, paso 2, tipo del conjunto "Producto equivalente"; cada observación conserva su tipo individual.

### QA-05: Por debajo del mínimo con una observación manual

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Observación | Alkosto AK-50UR7800, 1.799.900 COP, 2026-08-15, manual | Única |

- **Pasos:**
  1. Ejecutar la selección para IO-2.
- **Resultado esperado:** Conjunto de 1 observación marcado "Por debajo del mínimo configurado (1 observaciones de 1 fuentes; mínimo 3 de 2 fuentes)", con indicador "Manual".

### QA-06: Tres observaciones de una sola tienda no alcanzan el mínimo de fuentes

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Mismo modelo | 3 Alkosto con SKUs distintos | 3 observaciones, 1 fuente |
  | Equivalentes | ninguno | |

- **Pasos:**
  1. Ejecutar la selección para IO-2.
- **Resultado esperado:** Conjunto de 3 observaciones (paso 1) marcado "Por debajo del mínimo configurado (3 observaciones de 1 fuentes; mínimo 3 de 2 fuentes)".

### QA-07: Descarte de observaciones no válidas por cada motivo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Vendedor tercero en Falabella | "ElectroMundo SAS" | "vendedor no es la tienda" |
  | Precio con tarjeta específica | Alkosto, condicionado = sí | "precio condicionado" |
  | Precio efectivo | 0 COP | "precio inválido" |
  | Fecha de observación | nula | "sin fecha de observación" |
  | Producto "TV 50" | emparejamiento insuficiente | "emparejamiento insuficiente" |
  | Observación TVEC | fuente pública | "fuente no retail" |

- **Pasos:**
  1. Ejecutar la selección para IO-2 con todas en la ventana.
- **Resultado esperado:** Ninguna entra; el registro muestra 1 descarte por cada motivo indicado.

### QA-08: Una observación por tienda y producto, la más cercana

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Alkosto AK-50UR7800 | 2026-08-03, 08-10, 08-17, 08-24 | Semanales |
  | Variante empate | 2026-08-17 y 2026-08-23 | Ambas a 3 días |
  | Variante mismo día | Dos registros del 2026-08-17 | Registrados 09:00 y 15:00 |

- **Pasos:**
  1. Ejecutar la selección con cada variante.
- **Resultado esperado:** (1) Entra la del 2026-08-17; 3 descartes "repetida por tienda y producto". (2) Entra la del 2026-08-17 (anterior a la compra). (3) Entra la registrada a las 15:00.

### QA-09: Identificación del producto observado sin SKU

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Falabella obs. A | sin SKU, EAN 8806084100001, 2026-08-10 | |
  | Falabella obs. B | sin SKU, EAN 8806084100001, 2026-08-19 | Mismo EAN |
  | Falabella obs. C y D | sin SKU ni EAN, LG 50UR7800, 2026-08-05 y 2026-08-18 | Mismo marca+modelo |

- **Pasos:**
  1. Ejecutar la selección para IO-2.
- **Resultado esperado:** Entra B (por EAN) y D (por marca + modelo); A y C se descartan como "repetida por tienda y producto".

### QA-10: Ítem objetivo no elegible

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio unitario | nulo | "Sin precio unitario" |
  | Precio unitario | −5.000 | "Precio unitario inválido" |
  | Estado de datos | pendiente de revisión | "Datos pendientes de revisión" |
  | Fecha de orden | nula | "Sin fecha de compra" |
  | Producto | insuficiente/no confiable | "Emparejamiento insuficiente" |

- **Pasos:**
  1. Ejecutar la selección para cada variante.
- **Resultado esperado:** Estado "Benchmark 2 no calculado" con el motivo exacto indicado.

### QA-11: Límite de ventana y cambio del parámetro

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-04 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Observación A | 2026-07-21 | −30 días: entra |
  | Observación B | 2026-07-20 | −31 días: no entra con 30 |
  | Observación C | 2026-09-19 | +30 días: entra |
  | Nuevo `b2_ventana_dias` | 45 | |

- **Pasos:**
  1. Ejecutar con 30 días.
  2. Cambiar a 45 y ejecutar.
- **Resultado esperado:** (1) Entran A y C. (2) Entran A, B y C; el registro de cada ejecución guarda la ventana usada (30 y 45).

### QA-12: Parámetro inválido usa la configuración inicial

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `b2_ventana_dias` | 181 | Fuera de rango |
  | `b2_minimo_fuentes` | 0 | Fuera de rango |
  | `b2_fuentes_retail_habilitadas` | lista vacía | Inválida |

- **Pasos:**
  1. Configurar cada valor y ejecutar.
- **Resultado esperado:** Se usa 30, 2 o "Alkosto, Falabella" según el caso y se registra "Parámetro {nombre} inválido; se usó el valor inicial {valor}".

### QA-13: Sin observaciones de ningún tipo

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Base de observaciones | vacía para el modelo y sus equivalentes | |

- **Pasos:**
  1. Ejecutar la selección para IO-2.
- **Resultado esperado:** Conjunto vacío, estado "Sin observaciones de mercado en la ventana (±30 días)", sin error de proceso.

---

**Total de casos:** 13
