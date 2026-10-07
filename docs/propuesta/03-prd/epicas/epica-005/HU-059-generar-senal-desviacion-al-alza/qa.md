# Casos de Prueba — HU-059: Generar la «señal que merece revisión» por desviación al alza con regla híbrida configurable

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la decisión de generar o no una señal por (ítem, benchmark): aplicabilidad de la regla de atípicos (suficiencia y homogeneidad), regla de umbrales por tipo de emparejamiento, límites exactos, solo al alza, estados sin referencia, parámetros, ciclo de vida y versionado, y lenguaje. Queda fuera la confianza (HU-061), la evidencia (HU-062) y los precios bajos (HU-060).

## Precondiciones y Datos Base

- Parámetros iniciales: atípicos habilitada, factor 1,5, umbral mismo modelo 30, umbral equivalente 50; `b1_minimo_observaciones` = 5.
- **S7** (mismo modelo, base completa): 1.800.000 … 2.400.000 (paso 100.000). Q1 1.950.000, mediana 2.100.000, Q3 2.250.000, IQR 300.000, límite de atípicos 2.700.000.
- Ítem IO-6: SECOP II CO1.PCCNTR.8880001, Samsung UN55CU7000.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-04 / RN-07 | QA-01 |
| Escenario 2 / RN-04 límite | QA-02 |
| Escenario 3 / RN-05 mismo modelo | QA-03 |
| Escenario 4 / RN-05 límite | QA-04 |
| Escenario 5 / RN-05 equivalente | QA-05 |
| Escenario 6 / RN-03.2 | QA-06 |
| RN-03.4 IQR = 0 / RN-03.5 deshabilitada | QA-07 |
| Escenario 7 / RN-03.3 | QA-08 |
| Escenario 8 / RN-02 | QA-09 |
| Escenario 9 / RN-01 | QA-10 |
| Escenario 10 | QA-11 |
| RN-06 parámetros | QA-12 |
| Escenario 11 / RN-08 no vigente | QA-13 |
| Escenario 12 / RN-08 versiones | QA-14 |
| RN-08 reactivación y no comparable | QA-15 |
| RN-09 lenguaje | QA-16 |

---

## Casos de Prueba

### QA-01: Señal por regla de atípicos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | S7 | |
  | Precio contratado | 2.750.000 | > 2.700.000 |

- **Pasos:**
  1. Ejecutar la evaluación de señales.
- **Resultado esperado:** Señal "Vigente", versión 1, "Señal que merece revisión", "Benchmark 1 – Contratación pública", regla "Valor atípico: precio > Q3 + 1,5 × IQR (límite 2.700.000 COP)", desviación "+31,0 %", referencia 2.100.000.

### QA-02: Precio igual al límite de atípicos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio contratado | 2.700.000 | = límite |
  | Precio contratado | 2.700.001 | > límite |

- **Pasos:**
  1. Evaluar cada precio.
- **Resultado esperado:** 2.700.000 → sin señal; 2.700.001 → señal.

### QA-03: Umbral de mismo modelo con evidencia limitada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | 1.900.000, 2.000.000, 2.100.000 mismo modelo | Referencia 2.000.000 |
  | Precio contratado | 2.600.000 | +30,0 % |

- **Pasos:**
  1. Evaluar.
- **Resultado esperado:** Señal con regla "Umbral porcentual provisional: mismo modelo ≥ +30 %" y motivo "Regla de atípicos no aplicable: muestra insuficiente".

### QA-04: Desviación justo bajo el umbral y redondeo

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio | 2.598.900 | +29,9 %: sin señal |
  | Precio | 2.599.000 | 29,95 → +30,0 %: señal |

- **Pasos:**
  1. Evaluar cada precio con referencia 2.000.000.
- **Resultado esperado:** Según la tabla.

### QA-05: Umbral de producto equivalente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Conjunto | 3 equivalentes, referencia 2.000.000 | |
  | Precio | 3.000.000 | +50,0 % |
  | Precio | 2.990.000 | +49,5 % |
  | Precio | 2.700.000 | +35,0 %: no alcanza 50 aunque supera 30 |

- **Pasos:**
  1. Evaluar cada precio.
- **Resultado esperado:** Solo 3.000.000 genera señal, con regla "Umbral porcentual provisional: producto equivalente ≥ +50 %".

### QA-06: Muestra suficiente pero mezclada

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | S7: 4 mismo modelo + 3 equivalentes | Tipo del conjunto: equivalente |
  | Precio | 2.750.000 | +31,0 %: supera atípicos pero no 50 % |
  | Precio | 3.150.000 | +50,0 % |

- **Pasos:**
  1. Evaluar cada precio.
- **Resultado esperado:** 2.750.000 → sin señal; 3.150.000 → señal con regla de equivalente y motivo "Regla de atípicos no aplicable: muestra no homogénea (tipos de emparejamiento mezclados)".

### QA-07: Dispersión nula y regla deshabilitada

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | 5 × 2.000.000 mismo modelo | IQR = 0 |
  | Precio | 2.100.000 | +5,0 % |
  | Precio | 2.600.000 | +30,0 % |
  | Variante | S7 con `senal_regla_atipicos_habilitada` = no, precio 2.750.000 | +31,0 % |

- **Pasos:**
  1. Evaluar cada caso.
- **Resultado esperado:** IQR = 0: 2.100.000 sin señal; 2.600.000 señal por umbral con motivo "dispersión nula (IQR = 0)". Variante: señal por umbral de mismo modelo con motivo "regla de atípicos deshabilitada".

### QA-08: Comparación tributaria incompleta

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comparables | 7 TVEC indeterminadas, mismo modelo, referencia 2.000.000 | |
  | Precio | 2.900.000 | +45,0 % |

- **Pasos:**
  1. Evaluar.
- **Resultado esperado:** Señal por umbral de mismo modelo, motivo "comparación tributaria incompleta", con la marca "Incompleta / no confiable" conservada.

### QA-09: Desviaciones negativas o nulas no generan señal

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Desviación | −35,0 % | |
  | Desviación | 0,0 % | |

- **Pasos:**
  1. Evaluar.
- **Resultado esperado:** Sin señal en ambos casos.

### QA-10: Benchmarks sin referencia

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Benchmark 1 | "Sin comparables públicos" | |
  | Benchmark 2 | "No disponible / evidencia insuficiente" | |
  | Benchmark 1 alterno | "Benchmark 1 no calculado – Sin precio unitario" | |

- **Pasos:**
  1. Evaluar.
- **Resultado esperado:** Ninguna señal.

### QA-11: Dos señales independientes

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Benchmark 1 | S7, precio 2.750.000 | Atípico |
  | Benchmark 2 | 4 obs. mismo modelo de 2 fuentes (1.799.900, 1.849.900, 1.899.900, 1.949.900), referencia 1.874.900, Q3 1.912.400, IQR 75.000 | Desviación +46,7 %; límite de atípicos 2.024.900 |

- **Pasos:**
  1. Evaluar.
- **Resultado esperado:** Dos señales con identificadores distintos: Benchmark 1 (regla de atípicos) y Benchmark 2 (regla aplicable a su muestra), cada una con su desviación.

### QA-12: Parámetros modificados e inválidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `senal_umbral_mismo_modelo` | 25 | Válido: +26,0 % genera señal |
  | `senal_factor_iqr` | 6,0 | Inválido → 1,5 |
  | `senal_umbral_equivalente` | 0 | Inválido → 50 |

- **Pasos:**
  1. Configurar y evaluar.
- **Resultado esperado:** El umbral 25 se aplica; los inválidos usan el valor inicial y dejan la advertencia "Parámetro {nombre} inválido; se usó el valor inicial {valor}"; la señal guarda los parámetros usados.

### QA-13: Señal que deja de cumplir pasa a No vigente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-08
- **Pasos:**
  1. Generar la señal de QA-01.
  2. Agregar comparables hasta que la desviación sea +12,0 % y recalcular el 2026-10-02.
- **Resultado esperado:** Estado "No vigente", motivo "Tras el recálculo del 2026-10-02, la desviación ya no cumple la regla configurada"; las versiones previas se conservan.

### QA-14: Versionado según cambios

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 12 / RN-08
- **Pasos:**
  1. Generar la señal de QA-01.
  2. Recalcular sin cambios en los datos.
  3. Cambiar un comparable para que la referencia sea 2.050.000 y recalcular.
- **Resultado esperado:** Paso 2: sigue versión 1, solo cambia la fecha de última evaluación. Paso 3: versión 2 con la nueva referencia y desviación.

### QA-15: Reactivación y ítem que deja de ser comparable

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-08
- **Pasos:**
  1. Con la señal "No vigente" de QA-13, retirar los comparables agregados y recalcular.
  2. Marcar luego el precio del ítem como "rechazado" por el revisor y recalcular.
- **Resultado esperado:** Paso 1: "Vigente" con nueva versión. Paso 2: "No vigente" con motivo "El ítem dejó de ser comparable: Benchmark 1 no calculado – Datos pendientes de revisión" o el motivo de elegibilidad que corresponda; la señal no se elimina.

### QA-16: Denominación y términos prohibidos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-09
- **Pasos:**
  1. Revisar los textos de las señales generadas en QA-01 a QA-15.
- **Resultado esperado:** Todas se denominan "Señal que merece revisión"; ningún texto contiene "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

---

**Total de casos:** 16
