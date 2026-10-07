# Casos de Prueba — HU-054: Seleccionar comparables públicos del Benchmark 1 con ventana temporal configurable

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la selección automática del conjunto de comparables públicos (SECOP II + TVEC) de un ítem objetivo: elegibilidad, exclusiones, selección escalonada por tipo de emparejamiento y ventana, límites de ventana, parámetros configurables y registro del origen de cada observación. Queda fuera: el cálculo de mediana, cuartiles y desviación (HU-057), la homologación de IVA (HU-056) y la presentación en pantalla (HU-063).

## Precondiciones y Datos Base

- Configuración inicial: `b1_ventana_inicial_meses` = 6, `b1_ventana_maxima_meses` = 12, `b1_minimo_observaciones` = 5.
- **Ítem objetivo IO-1:** SECOP II, contrato CO1.PCCNTR.5550001, televisor Samsung UN55CU7000 (55", 4K, LED, Smart), fecha de firma 2025-06-15, precio unitario explícito 2.450.000 COP, estado "validado por revisor".
- **Producto equivalente de referencia:** LG 55UR8750 (55", 4K, LED, Smart), clasificado "producto equivalente" frente a IO-1.
- **Producto insuficiente:** "Televisor 55 pulgadas" sin resolución ni tecnología, clasificado "insuficiente/no confiable" frente a IO-1.
- Comparables TVEC con número de orden 120001 a 120020 y comparables SECOP II con contratos CO1.PCCNTR.5550100 en adelante, todos "incluidos" y aceptados, salvo que el caso indique otra cosa.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-07 paso 1 / RN-09 | QA-01 |
| Escenario 2 / RN-07 paso 2 | QA-02 |
| Escenario 3 / RN-07 pasos 3–4 / RN-08 | QA-03 |
| Escenario 4 / RN-07 sin mínimo | QA-04 |
| Escenario 5 / RN-07 conjunto vacío | QA-05 |
| Escenario 6 / RN-03 | QA-06 |
| Escenario 7 / RN-01, RN-04, RN-11 | QA-07 |
| Escenario 8 / RN-01 motivos | QA-08 |
| Escenario 9 / RN-05, RN-12 | QA-09 |
| RN-05 parámetro inválido | QA-10 |
| Escenario 10 / RN-06 límites | QA-11 |
| RN-06 fin de mes | QA-12 |
| RN-02 fecha de compra TVEC | QA-13 |
| RN-10 sin ponderación | QA-14 |

---

## Casos de Prueba

### QA-01: Selección con mismo modelo suficiente en ventana inicial y origen identificado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-07 paso 1 / RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables mismo modelo | 4 TVEC (órdenes 120001–120004) + 2 SECOP II (CO1.PCCNTR.5550100, 5550101) | Fechas entre 2025-01-10 y 2025-11-30 |

- **Pasos:**
  1. Ejecutar la selección de comparables del Benchmark 1 para IO-1.
- **Resultado esperado:** Conjunto de 6 observaciones; paso usado 1; ventana "±6 meses"; tipo "Mismo modelo"; cada observación muestra origen "Contratación pública – TVEC" o "Contratación pública – SECOP II" con su identificador, entidad, fecha, precio unitario, tipo de precio y base tributaria declarada.

### QA-02: Ampliación a ±12 meses con mismo modelo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-07 paso 2
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Mismo modelo en ±6 meses | 3 (2025-02-01, 2025-08-20, 2025-10-05) | |
  | Mismo modelo adicionales en ±12 meses | 2 (2024-07-01, 2026-05-30) | Fuera de ±6, dentro de ±12 |

- **Pasos:**
  1. Ejecutar la selección para IO-1.
- **Resultado esperado:** Conjunto de 5 observaciones; paso 2; ventana "±12 meses (ampliada)"; tipo "Mismo modelo"; no marcado por debajo del mínimo.

### QA-03: Incorporación de equivalentes y tipo de conjunto "Producto equivalente"

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-07 pasos 3–4 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Mismo modelo en ±12 meses | 2 | |
  | Equivalentes LG 55UR8750 en ±6 meses | 2 | Paso 3 = 4 observaciones |
  | Equivalentes adicionales en ±12 meses | 3 | Paso 4 = 7 observaciones |

- **Pasos:**
  1. Ejecutar la selección para IO-1.
- **Resultado esperado:** Conjunto de 7 observaciones; paso 4; ventana "±12 meses (ampliada)"; tipo del conjunto "Producto equivalente"; cada observación conserva su tipo individual (2 "Mismo modelo", 5 "Producto equivalente").

### QA-04: Ningún paso alcanza el mínimo; se usa mismo modelo en ventana máxima

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Mismo modelo en ±12 meses | 2 | |
  | Mismo modelo + equivalentes en ±12 meses | 4 | |
  | Caso alterno: mismo modelo en ±12 | 0; equivalentes en ±12 = 3 | Debe usar paso 4 |

- **Pasos:**
  1. Ejecutar la selección para IO-1 con el primer conjunto de datos.
  2. Repetir con el caso alterno.
- **Resultado esperado:** (1) Conjunto de 2 observaciones de mismo modelo, ventana "±12 meses (ampliada)", marcado "Por debajo del mínimo configurado (2 de 5)". (2) Conjunto de 3 observaciones, tipo "Producto equivalente", marcado "Por debajo del mínimo configurado (3 de 5)".

### QA-05: Sin comparables en la ventana máxima

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables más cercanos | 2024-06-14 y 2026-06-16 | Fuera de ±12 meses |

- **Pasos:**
  1. Ejecutar la selección para IO-1.
- **Resultado esperado:** Conjunto vacío con estado "Sin comparables públicos en la ventana máxima (±12 meses)"; la ejecución termina sin error.

### QA-06: Exclusión del propio ítem y de su mismo contrato u orden

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Otro ítem en CO1.PCCNTR.5550001 | Samsung UN55CU7000, 2.400.000 COP | Mismo contrato que IO-1 |
  | Ítem objetivo TVEC alterno | Orden 120050, línea 1 | La línea 2 de la misma orden es mismo modelo |

- **Pasos:**
  1. Ejecutar la selección para IO-1.
  2. Ejecutar la selección para la línea 1 de la orden 120050.
- **Resultado esperado:** En ningún conjunto aparece el propio ítem ni otro ítem del mismo contrato u orden; el registro cuenta 1 descarte por "mismo contrato/orden" en cada caso.

### QA-07: Exclusión de insuficientes, no incluidos y pendientes/rechazados con conteo de descartes

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-01, RN-04, RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem "Televisor 55 pulgadas" | Emparejamiento insuficiente | Debe descartarse |
  | Ítem videowall | Clasificación "excluido" | Debe descartarse |
  | Ítem en "requiere revisión" | Clasificación pendiente | Debe descartarse |
  | Ítem con precio "pendiente de revisión" | Extracción baja confianza | Debe descartarse |
  | Ítem "rechazado" por revisor | | Debe descartarse |

- **Pasos:**
  1. Ejecutar la selección para IO-1 con estos ítems dentro de ±6 meses.
- **Resultado esperado:** Ninguno entra al conjunto; el registro muestra 1 descarte por emparejamiento insuficiente, 2 por no incluido, 2 por pendiente/rechazado.

### QA-08: Ítem objetivo no elegible por cada motivo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio unitario | nulo / ítem "información insuficiente" | "Sin precio unitario" |
  | Precio unitario | 0 y −1.000 | "Precio unitario inválido" |
  | Estado de datos | pendiente de revisión | "Datos pendientes de revisión" |
  | Fecha de firma | nula | "Sin fecha de compra" |
  | Producto normalizado | insuficiente/no confiable | "Emparejamiento insuficiente" |
  | Precio nulo y fecha nula a la vez | | Debe reportar "Sin precio unitario" (orden de RN-01) |

- **Pasos:**
  1. Ejecutar la selección para cada variante de IO-1.
- **Resultado esperado:** No se construye conjunto; estado "Benchmark 1 no calculado" con el motivo exacto indicado en la tabla.

### QA-09: Uso de parámetros modificados y registro de parámetros

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-05, RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `b1_ventana_inicial_meses` | 4 | Cambiado por el Administrador |
  | `b1_minimo_observaciones` | 6 | |
  | Mismo modelo en ±4 meses | 6 | Comparable de 2025-11-10 queda fuera de ±4 |

- **Pasos:**
  1. Cambiar los parámetros.
  2. Ejecutar el recálculo.
- **Resultado esperado:** Se usa ventana ±4 y mínimo 6; el registro guarda ventana inicial 4, ventana máxima 12 y mínimo 6.

### QA-10: Parámetro fuera de rango usa la configuración inicial y deja advertencia

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `b1_ventana_inicial_meses` | 0 | Fuera de rango (mín 1) |
  | `b1_ventana_maxima_meses` | 3 con inicial 6 | Menor que la inicial |
  | `b1_minimo_observaciones` | vacío | Falta |

- **Pasos:**
  1. Configurar cada valor inválido y ejecutar la selección.
- **Resultado esperado:** Se usa el valor inicial (6, 12 o 5 según el caso) y el log registra "Parámetro {nombre} inválido; se usó el valor inicial {valor}".

### QA-11: Límites inclusivos de la ventana

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparable A | 2024-12-15 | Límite inferior ±6: entra |
  | Comparable B | 2024-12-14 | Un día antes: no entra en ±6 |
  | Comparable C | 2025-12-15 | Límite superior ±6: entra |
  | Comparable D | 2025-12-16 | No entra en ±6 |

- **Pasos:**
  1. Ejecutar la selección para IO-1 (fecha 2025-06-15) y revisar el paso 1.
- **Resultado esperado:** En el paso 1 entran A y C; B y D solo entran si se evalúa la ventana ±12.

### QA-12: Ventana sobre fin de mes inexistente

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Fecha de compra | 2025-08-31 | |
  | Comparable | 2026-02-28 | Límite superior ±6 = 2026-02-28 |

- **Pasos:**
  1. Ejecutar la selección con ventana ±6.
- **Resultado esperado:** La ventana es [2025-02-28, 2026-02-28] y el comparable del 2026-02-28 entra.

### QA-13: Fecha de compra TVEC tomada de la orden

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem objetivo TVEC | Orden 120060, fecha de orden 2025-03-10 | |

- **Pasos:**
  1. Ejecutar la selección para el ítem de la orden 120060.
- **Resultado esperado:** La ventana ±6 se calcula sobre 2025-03-10: [2024-09-10, 2025-09-10].

### QA-14: Cada línea cuenta como una observación sin importar la cantidad

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Línea TVEC orden 120007 | cantidad 40 | |
  | Línea TVEC orden 120008 | cantidad 1 | |

- **Pasos:**
  1. Ejecutar la selección para IO-1.
- **Resultado esperado:** El conjunto cuenta 2 observaciones (una por línea), sin ponderar por cantidad.

---

**Total de casos:** 14
