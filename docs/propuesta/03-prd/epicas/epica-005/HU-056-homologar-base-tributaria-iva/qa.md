# Casos de Prueba — HU-056: Homologar la base tributaria (IVA) y marcar comparaciones incompletas

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la homologación de valores a precio final con IVA, la conversión de valores sin IVA solo con IVA o tarifa explícitos en el documento, el tratamiento de valores sin IVA sin tarifa explícita y de bases indeterminadas (incluida la TVEC mientras INV-01 no se resuelva), el estado tributario de la comparación y los parámetros. Queda fuera el cálculo estadístico (HU-057/T505) y la confianza (HU-061).

## Precondiciones y Datos Base

- `base_tributaria_tvec` = `indeterminada`; `b1_minimo_observaciones` = 5; `b2_minimo_observaciones` = 3; `b2_minimo_fuentes` = 2.
- No existe tarifa general de IVA por defecto: ningún valor sin IVA se convierte si el documento no declara el IVA o la tarifa.
- Ítem objetivo IO-3: SECOP II, contrato CO1.PCCNTR.6660001, Samsung UN65CU7000, precio unitario 2.000.000 COP.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-03 con IVA / RN-06.4 | QA-01 |
| Escenario 2 / RN-03 sin tarifa explícita / RN-05 / RN-06.1 | QA-02 |
| Escenario 3 / RN-03 IVA explícito / evidencia | QA-03 |
| Escenario 4 / RN-03 tarifa explícita / redondeo / tarifa no válida | QA-04 |
| Escenario 5 / RN-06.1 / RN-07 | QA-05 |
| Escenario 6 / RN-02 TVEC / RN-05 / RN-06.2 | QA-06 |
| Escenario 7 / RN-05 exclusión | QA-07 |
| RN-05 Benchmark 2 con fuentes | QA-08 |
| RN-06 combinación 1 + 2 | QA-09 |
| Escenario 8 / RN-02 TVEC `sin_iva` / RN-04 | QA-10 |
| Escenario 9 / RN-02 retail | QA-11 |
| Escenario 10 / RN-01 | QA-12 |
| RN-04 parámetro inválido | QA-13 |
| RN-08 registro | QA-14 |

---

## Casos de Prueba

### QA-01: Todos con IVA, comparación completa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio contratado | 2.380.000 COP, con IVA | |
  | Observaciones | 5 SECOP II con IVA | |

- **Pasos:**
  1. Ejecutar la homologación.
- **Resultado esperado:** Valores sin cambio; estado "Completa – precio final con IVA".

### QA-02: Valor sin IVA sin tarifa explícita no se convierte

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03 / RN-05 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio contratado | 2.000.000 COP sin IVA | Documento sin IVA ni tarifa declarados |
  | Observaciones | 5 SECOP II con IVA | |
  | Variante: precio contratado | 2.380.000 COP, con IVA | |
  | Variante: observaciones | 6 SECOP II con IVA + 2 SECOP II sin IVA sin tarifa explícita | Determinadas ≥ 5 |

- **Pasos:**
  1. Ejecutar la homologación con el dato base.
  2. Ejecutar la homologación con la variante.
- **Resultado esperado:** Dato base: el precio contratado no se convierte (sigue en 2.000.000 COP; no se obtiene 2.380.000 ni se aplica ninguna tarifa), queda tratado como indeterminado, estado "Incompleta / no confiable: base tributaria indeterminada del precio contratado" y se muestra el motivo "Valor sin IVA sin tarifa explícita en el documento: no se convierte (posibles exenciones o tarifas diferenciales, ej. San Andrés)". Variante: las 2 observaciones sin IVA quedan "excluida por base tributaria indeterminada" con el mismo motivo; se usan las 6 con IVA y el estado es "Completa – precio final con IVA".

### QA-03: Conversión con IVA unitario explícito

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio contratado | 2.000.000 COP sin IVA | |
  | IVA unitario explícito | 380.000 COP | Del documento, CO1.PCCNTR.6660001, página 3 |

- **Pasos:**
  1. Ejecutar la homologación.
- **Resultado esperado:** 2.380.000 COP marcado "Convertido desde sin IVA (IVA explícito del documento)"; el registro guarda el IVA usado (380.000 COP) y la evidencia "CO1.PCCNTR.6660001, página 3".

### QA-04: Conversión con tarifa explícita en el documento y redondeo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio contratado | 2.000.000 COP sin IVA, "IVA 19 %" en página 3 | Esperado 2.380.000 |
  | Observación SECOP II | 1.234.567 COP sin IVA, tarifa 19 % explícita | 1.469.134,73 → 1.469.135 |
  | Observación SECOP II | 1.000.002 COP sin IVA, tarifa 19 % explícita | 1.190.002,38 → 1.190.002 |
  | Observación SECOP II | 1.000.000 COP sin IVA, tarifa 5 % explícita | Esperado 1.050.000 |
  | Observación SECOP II | 1.000.000 COP sin IVA, "exento – tarifa 0 %" explícito | Esperado 1.000.000 |
  | Observación SECOP II | 1.000.000 COP sin IVA, IVA unitario 190.000 y tarifa 5 % | Prevalece el IVA unitario: 1.190.000 |
  | Observación SECOP II | 1.000.000 COP sin IVA, tarifa declarada "119 %" | Tarifa no válida |

- **Pasos:**
  1. Ejecutar la homologación.
- **Resultado esperado:** Valores homologados 2.380.000, 1.469.135, 1.190.002, 1.050.000, 1.000.000 y 1.190.000 COP; los convertidos por tarifa quedan marcados "Convertido desde sin IVA (tarifa {t} % explícita en el documento)" con t = 19, 19, 19, 5 y 0, y el de IVA unitario "Convertido desde sin IVA (IVA explícito del documento)"; cada uno registra la tarifa o IVA usados y su evidencia. La observación con "119 %" no se convierte, queda indeterminada con el motivo de RN-03 y el log registra "Tarifa de IVA no válida '119 %' en {identificador}; se trata como no declarada". Como las 5 observaciones determinadas alcanzan el mínimo del Benchmark 1, esa observación queda "excluida por base tributaria indeterminada" y el estado es "Completa – precio final con IVA (incluye valores convertidos)".

### QA-05: Precio contratado indeterminado

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-06 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio contratado | 2.000.000 COP, indeterminada | |
  | Observaciones | 5 con IVA | |

- **Pasos:**
  1. Ejecutar la homologación y el cálculo posterior.
- **Resultado esperado:** El precio no se convierte; estado "Incompleta / no confiable: base tributaria indeterminada del precio contratado"; la comparación sigue calculándose con la marca.

### QA-06: TVEC indeterminada sin observaciones determinadas suficientes

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-02 / RN-05 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Observaciones TVEC | 6 (órdenes 120101–120106) | Base por parámetro: indeterminada |
  | Observaciones SECOP II | 2 con IVA | No alcanzan 5 |

- **Pasos:**
  1. Ejecutar la homologación del Benchmark 1.
- **Resultado esperado:** Se usan las 8 observaciones; estado "Incompleta / no confiable: base tributaria indeterminada en 6 de 8 observaciones".

### QA-07: Exclusión de indeterminadas cuando las determinadas alcanzan el mínimo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Determinadas | 6 SECOP II con IVA | ≥ 5 |
  | Indeterminadas | 2 TVEC | |
  | Variante límite | 5 determinadas + 3 indeterminadas | Exactamente el mínimo |

- **Pasos:**
  1. Ejecutar con cada variante.
- **Resultado esperado:** Se usan solo las determinadas (6 y 5); las indeterminadas quedan "excluida por base tributaria indeterminada"; estado "Completa".

### QA-08: Regla de exclusión en el Benchmark 2 considera el mínimo de fuentes

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Determinadas | 3 Alkosto con IVA | 1 fuente: no alcanza |
  | Indeterminada | 1 Falabella sin información de IVA | |

- **Pasos:**
  1. Ejecutar la homologación del Benchmark 2.
- **Resultado esperado:** Se usan las 4; estado "Incompleta / no confiable: base tributaria indeterminada en 1 de 4 observaciones".

### QA-09: Precio contratado y observaciones indeterminados

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Precio contratado | TVEC, indeterminada | |
  | Observaciones | 7 TVEC indeterminadas | |

- **Pasos:**
  1. Ejecutar la homologación.
- **Resultado esperado:** Estado "Incompleta / no confiable: base tributaria indeterminada del precio contratado y de 7 de 7 observaciones".

### QA-10: Registro del resultado de INV-01

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-02 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `base_tributaria_tvec` | `con_iva` | Cambio del Administrador |
  | Variante A | `sin_iva`, órdenes sin IVA ni tarifa explícitos | No se convierte |
  | Variante B | `sin_iva`, orden 120101 con "IVA 19 %" en página 2 | Solo esa orden se convierte |

- **Pasos:**
  1. Cambiar el parámetro y ejecutar el recálculo del dato base de QA-06.
- **Resultado esperado:** Con `con_iva`: estado "Completa – precio final con IVA". Variante A: ningún valor TVEC se convierte ni se supone 19 %; las 6 órdenes muestran el motivo "Valor sin IVA sin tarifa explícita en el documento: no se convierte (posibles exenciones o tarifas diferenciales, ej. San Andrés)"; se usan las 8 observaciones y el estado es "Incompleta / no confiable: base tributaria indeterminada en 6 de 8 observaciones". Variante B: la orden 120101 queda "Convertido desde sin IVA (tarifa 19 % explícita en el documento)" con evidencia "120101, página 2"; las determinadas (3) no alcanzan 5, se usan las 8 y el estado es "Incompleta / no confiable: base tributaria indeterminada en 5 de 8 observaciones". En todos los casos el registro guarda el valor del parámetro usado.

### QA-11: Observación retail sin información de IVA

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-02 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Alkosto | campo IVA vacío | |
  | Falabella | "incluye IVA" | con_iva |
  | Falabella | "no incluye IVA", 1.000.000, sin tarifa | No se convierte |

- **Pasos:**
  1. Ejecutar la homologación.
- **Resultado esperado:** Alkosto queda `indeterminada`; la Falabella "incluye IVA" queda con IVA; la Falabella "no incluye IVA" no se convierte (se mantiene en 1.000.000, sin suponer 19 %), se trata como indeterminada y muestra el motivo de RN-03; se aplica RN-05.

### QA-12: Base no reconocida tratada como indeterminada

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Base | "IVA incluido parcial" | Fuera del dominio |
  | Base | nulo | Sin log |

- **Pasos:**
  1. Ejecutar la homologación.
- **Resultado esperado:** Ambos quedan `indeterminada`; solo el primero genera en log "Base tributaria no reconocida 'IVA incluido parcial' en {identificador}; tratada como indeterminada".

### QA-13: Parámetro inválido

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `base_tributaria_tvec` | "incluido" | No permitido |
  | `base_tributaria_tvec` | vacío | Faltante |

- **Pasos:**
  1. Configurar cada valor y ejecutar.
- **Resultado esperado:** Se usa `indeterminada`, con advertencia "Parámetro base_tributaria_tvec inválido; se usó el valor inicial indeterminada".

### QA-14: Registro de la homologación por valor y comparación

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-08
- **Pasos:**
  1. Ejecutar QA-04 y QA-02 y consultar el registro.
- **Resultado esperado:** Para cada valor constan base original, base final, valor original, valor homologado y método; en QA-04, la tarifa o IVA usados y su evidencia (documento y página/hoja/celda); en QA-02, el motivo de no conversión y ninguna tarifa aplicada. Para cada comparación, el estado, los parámetros y el conteo de excluidas (1 en QA-04; 0 en el dato base y 2 en la variante de QA-02).

---

**Total de casos:** 14
