# Casos de Prueba — HU-060: Dirigir los precios anormalmente bajos a la cola de revisión de calidad

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la detección de precios anormalmente bajos (regla de atípicos inferior y umbrales), la creación, actualización y cierre automático del elemento en la cola de revisión, la ausencia de señal y la marca en el benchmark. Queda fuera la resolución manual del elemento por el Revisor.

## Precondiciones y Datos Base

- Parámetros iniciales: atípicos habilitada, factor 1,5, umbrales 30 y 50.
- **S7** mismo modelo, base completa: Q1 1.950.000, IQR 300.000, límite inferior 1.500.000, mediana 2.100.000.
- Ítem IO-7: TVEC orden 140001, línea 1, LG 50UR7800. Usuario Administrador "admin.po".

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-03 / RN-06 / RN-09 | QA-01 |
| Escenario 2 / RN-03 límite | QA-02 |
| RN-03 límite ≤ 0 | QA-03 |
| Escenario 3 / RN-04 mismo modelo | QA-04 |
| Escenario 4 / RN-04 equivalente | QA-05 |
| RN-02 no homogénea | QA-06 |
| RN-05 parámetros | QA-07 |
| Escenario 5 / RN-07 | QA-08 |
| Escenario 6 / RN-08 | QA-09 |
| Escenario 7 / RN-01 | QA-10 |
| Escenario 8 / RN-09 | QA-11 |
| Permisos | QA-12 |

---

## Casos de Prueba

### QA-01: Precio bajo por atípicos crea elemento y no señal

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03 / RN-06 / RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio contratado | 1.450.000 | < 1.500.000 |

- **Pasos:**
  1. Ejecutar la evaluación.
  2. Consultar la cola de revisión y las señales del ítem.
- **Resultado esperado:** Elemento "Abierto" de tipo "Precio anormalmente bajo frente a referencia" con regla "Valor atípico inferior: precio < Q1 − 1,5 × IQR (límite 1.500.000 COP)", desviación "−31,0 %", orden 140001 y el texto de posibles causas; ninguna señal.

### QA-02: Precio igual al límite inferior

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio | 1.500.000 | = límite: sin elemento |
  | Precio | 1.499.999 | < límite: elemento |

- **Pasos:**
  1. Evaluar cada precio.
- **Resultado esperado:** Según la tabla.

### QA-03: Límite inferior no positivo

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | 1.000.000, 1.200.000, 2.000.000, 2.800.000, 3.000.000 | Q1 1.200.000, Q3 2.800.000, IQR 1.600.000, límite −1.200.000 |
  | Precio | 300.000 | Desviación −85,0 % |

- **Pasos:**
  1. Evaluar.
- **Resultado esperado:** No se crea elemento por la regla de atípicos (límite ≤ 0); como la regla aplicable es la de atípicos (muestra homogénea), no se crea elemento.

### QA-04: Umbral de mismo modelo

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Referencia | 2.000.000 (3 obs., mismo modelo) | |
  | Precio | 1.400.000 | −30,0 %: elemento |
  | Precio | 1.402.000 | −29,9 %: sin elemento |

- **Pasos:**
  1. Evaluar cada precio.
- **Resultado esperado:** Según la tabla; la regla registrada es "Umbral porcentual: mismo modelo ≤ −30 %".

### QA-05: Umbral de equivalente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio | 1.000.000 | −50,0 %: elemento |
  | Precio | 1.300.000 | −35,0 %: sin elemento |

- **Pasos:**
  1. Evaluar con referencia equivalente 2.000.000.
- **Resultado esperado:** Según la tabla.

### QA-06: Muestra no homogénea usa umbrales

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | S7 con 2 equivalentes | Tipo del conjunto: equivalente |
  | Precio | 1.450.000 | −31,0 %: no llega a −50 % |

- **Pasos:**
  1. Evaluar.
- **Resultado esperado:** Sin elemento (aplica umbral de equivalente).

### QA-07: Parámetros independientes e inválidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `calidad_bajo_umbral_mismo_modelo` | 20 | −21,0 % crea elemento |
  | `senal_umbral_mismo_modelo` | 30 | No cambia |
  | `calidad_bajo_umbral_equivalente` | 100 | Inválido → 50 |

- **Pasos:**
  1. Configurar y evaluar.
- **Resultado esperado:** El umbral 20 se aplica sin afectar la regla de señal; el inválido usa 50 con advertencia "Parámetro calidad_bajo_umbral_equivalente inválido; se usó el valor inicial 50".

### QA-08: Sin duplicados en recálculos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-07
- **Pasos:**
  1. Ejecutar QA-01.
  2. Agregar un comparable de 2.450.000 y recalcular (sigue cumpliendo).
- **Resultado esperado:** Sigue existiendo un único elemento abierto para (IO-7, Benchmark 1), con referencia, desviación y fecha de última evaluación actualizadas.

### QA-09: Cierre automático

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-08
- **Pasos:**
  1. Con el elemento de QA-01 abierto, corregir el precio del ítem a 1.900.000 y recalcular el 2026-10-02.
- **Resultado esperado:** Elemento cerrado con resolución "Cerrado automáticamente: ya no cumple la condición tras el recálculo del 2026-10-02".

### QA-10: Sin referencia no evalúa

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Benchmark 1 | "Sin comparables públicos" | |
  | Benchmark 2 | "No disponible / evidencia insuficiente" | |

- **Pasos:**
  1. Evaluar.
- **Resultado esperado:** Ningún elemento.

### QA-11: Marca visible en el benchmark

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-09
- **Pasos:**
  1. Con el elemento de QA-01 abierto, consultar el Benchmark 1 del ítem.
- **Resultado esperado:** Se muestra "En revisión de calidad: precio anormalmente bajo frente a la referencia" y ninguna señal; al cerrarse el elemento (QA-09) la marca desaparece.

### QA-12: Solo el Administrador ve la cola

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Consultar la cola con "admin.po" y con un Analista "analista.piloto1".
- **Resultado esperado:** El Administrador ve el elemento; el Analista no tiene acceso a la cola.

---

**Total de casos:** 12
