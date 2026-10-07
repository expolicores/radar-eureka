# Casos de Prueba — HU-032: Normalizar tecnología de pantalla, Smart y generación del televisor

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la normalización de tecnología de pantalla, Smart y generación sobre productos normalizados vigentes: sinónimos, precedencia y consumo de texto, subsunción de `LED`, negación de Smart, ambigüedades, nulos con motivo, fuentes de la generación y su rango, recálculo del estado, versiones y configuración. Queda fuera: marca, tamaño, resolución, modelo y EAN (otras HUs).

## Precondiciones y Datos Base

- Configuración inicial (`version_reglas = 1`) con las tablas de RN-04, RN-05 y RN-06; tabla de reglas de generación vacía; rango de años 2010–2027 (año actual 2026 + 1).
- Usuarios: `admin.po` (Administrador), `analista.piloto1` (Analista).
- Productos normalizados vigentes y activos (creados por la normalización del esquema común):

| id_origen | tipo | Texto o campos de origen | marca / modelo normalizado |
|---|---|---|---|
| TVEC-1101 | TVEC | `GSF01-TELEVISOR SAMSUNG FLAT LED CRYSTAL UHD SMART TV 55" MODELO 2024` | SAMSUNG / nulo |
| RET-3101 | RETAIL | `Televisor Samsung 65" Neo QLED 4K Smart TV pantalla LED` | SAMSUNG / `QN65QN90DAKXZL` |
| TVEC-1102 | TVEC | `TELEVISOR KALLEY 32" HD` | KALLEY / nulo |
| TVEC-1103 | TVEC | `TELEVISOR CHALLENGER 32" LED NO SMART` | CHALLENGER / nulo |
| SEC-2101-I1 | SECOP_II | funciones Smart extraído `Sí, Android TV` | nulo / nulo |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-07 | QA-01 |
| Escenario 2 / RN-03, RN-04 (subsunción) | QA-02 |
| Escenario 3 / RN-04 (ambigua) | QA-03 |
| Escenario 4 / RN-04 (no encontrada) | QA-04 |
| Escenario 5 / RN-05 (negación) | QA-05 |
| Escenario 6 / RN-05 (ambiguo, ausente) | QA-06 |
| Escenario 7 / RN-05 (booleano / campo extraído) | QA-07 |
| Escenario 8 / RN-06 (regla de código) | QA-08 |
| Escenario 9 / RN-06 (sin evidencia, no usa fechas) | QA-09 |
| Escenario 10 / RN-06 (sin calificador, ambiguo, rango) | QA-10, QA-11 |
| Escenario 11 / RN-06 (conflicto) | QA-12 |
| Escenario 12 / RN-08 | QA-13 |
| Escenario 13 / RN-09, RN-10 | QA-14, QA-15 |
| RN-01 (inactivos) | QA-16 |
| RN-02 (conflicto de origen) | QA-17 |
| RN-11 (error en un registro) | QA-18 |

---

## Casos de Prueba

### QA-01: Normaliza tecnología, Smart y generación desde la descripción TVEC

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-07
- **Pasos:**
  1. Ejecutar la normalización sobre TVEC-1101.
- **Resultado esperado:** `tecnologia = LED`, `smart = SI`, `generacion = 2024`; valores originales `FLAT LED` / `CRYSTAL UHD`, `SMART TV`, `MODELO 2024`; `campo_origen = descripcion_tvec`; regla aplicada registrada en cada atributo.

### QA-02: "Neo QLED" se reconoce como MINI_LED y el "LED" genérico se subsume

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Nombre RET-3101 | `Televisor Samsung 65" Neo QLED 4K Smart TV pantalla LED` | Esperado MINI_LED |
  | Nombre RET-3102 | `Televisor LG 55" QLED pantalla LED` | Esperado QLED |
  | Nombre RET-3103 | `Televisor Sony 65" QD-OLED` | Guion → espacio → OLED |

- **Resultado esperado:** `MINI_LED`, `QLED` y `OLED` respectivamente, sin motivo de ambigüedad; en RET-3101 `smart = SI`.

### QA-03: Tecnologías contradictorias producen nulo ambiguo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | `TELEVISOR 55" OLED QLED` | OLED + QLED |
  | Descripción | `TELEVISOR 65" OLED LED` | OLED + LED (no se subsume) |

- **Resultado esperado:** ambos con `tecnologia` nula y motivo `TECNOLOGIA_AMBIGUA`.

### QA-04: Sin términos de tecnología

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-04
- **Pasos:**
  1. Normalizar TVEC-1102.
- **Resultado esperado:** `tecnologia` nula con motivo `TECNOLOGIA_NO_ENCONTRADA`.

### QA-05: Negación de Smart se evalúa antes que "SMART"

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción TVEC-1103 | `TELEVISOR CHALLENGER 32" LED NO SMART` | NO SMART |
  | Descripción | `TELEVISOR CONVENCIONAL 24" LED` | TELEVISOR CONVENCIONAL |

- **Resultado esperado:** `smart = NO` en ambos, sin motivo `SMART_AMBIGUO`.

### QA-06: Smart contradictorio y Smart ausente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | `TELEVISOR 43" SMART TV SIN SMART` | Contradicción |
  | Descripción TVEC-1102 | `TELEVISOR KALLEY 32" HD` | Sin términos |

- **Resultado esperado:** primero `smart` nulo con `SMART_AMBIGUO`; segundo `smart` nulo con `SMART_NO_ENCONTRADO` (no `NO`).

### QA-07: Campo extraído o estructurado de Smart

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Smart extraído SEC-2101-I1 | `Sí, Android TV` | Texto → SI |
  | Smart estructurado RET-3104 | `true` | Booleano → SI |
  | Smart extraído SEC-2102-I1 | `No` | Booleano → NO |
  | Smart extraído SEC-2103-I1 | `0` | Booleano → NO |

- **Resultado esperado:** SI, SI, NO y NO respectivamente, con `campo_origen` del campo específico.

### QA-08: Generación por regla de código de modelo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-06
- **Precondiciones:** `admin.po` carga la regla `GEN-001` {marca SAMSUNG, patrón "modelo normalizado que empieza por `QN` y contiene `QN90D`", año 2024}.
- **Pasos:**
  1. Normalizar RET-3101 (sin año explícito).
  2. Normalizar un producto con marca nula y el mismo modelo.
- **Resultado esperado:** RET-3101 con `generacion = 2024` y `regla_aplicada = GEN-001`; el segundo con `generacion` nula y motivo `GENERACION_NO_DETERMINADA` (la regla exige marca).

### QA-09: Generación sin evidencia no usa fechas de compra

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción TVEC-1102 | `TELEVISOR KALLEY 32" HD` | Sin año |
  | Fecha de la orden TVEC-1102 | 2025-03-14 | No debe usarse |

- **Resultado esperado:** `generacion` nula con motivo `GENERACION_NO_DETERMINADA`; ningún valor 2025.

### QA-10: Año sin calificador y años distintos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | `CONTRATO 2023 TELEVISOR 50"` | Sin calificador |
  | Descripción | `TELEVISOR MODELO 2022 MODELO 2023` | Dos años |
  | Descripción | `TELEVISOR AÑO: 2023` | Calificador con dos puntos → 2023 |

- **Resultado esperado:** `GENERACION_NO_DETERMINADA`, `GENERACION_AMBIGUA` y `generacion = 2023` respectivamente.

### QA-11: Valores límite del rango de años

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | `MODELO 2009` | Mín−1 → nulo |
  | Descripción | `MODELO 2010` | Mínimo → 2010 |
  | Descripción | `MODELO 2027` | Máximo (2026 + 1) → 2027 |
  | Descripción | `MODELO 2028` | Máx+1 → nulo |

- **Resultado esperado:** 2010 y 2027 se guardan; 2009 y 2028 quedan nulos con `GENERACION_FUERA_DE_RANGO`.

### QA-12: Conflicto entre año explícito y regla de código

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-06
- **Precondiciones:** regla `GEN-001` cargada (año 2024).
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Nombre RET-3105 | `Samsung QN65QN90D MODELO 2023` | Explícito 2023 vs. regla 2024 |
  | Nombre RET-3106 | `Samsung QN65QN90D MODELO 2024` | Coinciden |

- **Resultado esperado:** RET-3105 con `generacion` nula, `GENERACION_EN_CONFLICTO` y ambos valores registrados; RET-3106 con `generacion = 2024` y ambas reglas registradas.

### QA-13: El estado pasa a COMPLETA cuando los 7 atributos quedan llenos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 12 / RN-08
- **Precondiciones:** RET-3101 tiene marca, modelo, tamaño y resolución no nulos y `estado_normalizacion = PARCIAL`; regla `GEN-001` cargada.
- **Resultado esperado:** tras normalizar, `tecnologia = MINI_LED`, `smart = SI`, `generacion = 2024` y `estado_normalizacion = COMPLETA`.

### QA-14: Cambio de configuración genera nueva versión; reejecución sin cambios no

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 13 / RN-09, RN-10
- **Pasos:**
  1. Normalizar RET-3107 `Televisor LG 55" QNED 4K` → tecnología nula.
  2. Con `admin.po`, agregar `QNED` a QLED.
  3. Ejecutar la normalización dos veces.
- **Resultado esperado:** cambio auditado (usuario, fecha y hora, anterior, nuevo) y `version_reglas = 2`; tras la primera ejecución RET-3107 tiene nueva versión con `tecnologia = QLED` y la anterior queda histórica; la segunda ejecución no crea versiones.

### QA-15: Validaciones y permisos de la configuración

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Usuario | `analista.piloto1` agrega sinónimo | Sin permiso |
  | Sinónimo | `QLED` asignado también a OLED | Duplicado |
  | Regla de generación | marca SAMSUNG, patrón vacío, año 2024 | Sin patrón |
  | Regla de generación | marca LG, patrón `55UT`, año 2030 | Año fuera de rango |
  | Rango de años | 2020–2015 | Inicio > fin |

- **Resultado esperado:** el cambio del Analista se rechaza por falta de permiso; los demás se rechazan con "Configuración inválida: {detalle}"; `version_reglas` no cambia.

### QA-16: Productos inactivos no se procesan

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-01
- **Precondiciones:** TVEC-1104 con `activo = no`.
- **Resultado esperado:** su versión y atributos no cambian tras la ejecución.

### QA-17: Conflicto entre campo estructurado y nombre comercial

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Característica estructurada RET-3108 | tecnología `OLED` | Campo específico |
  | Nombre RET-3108 | `Televisor LG 55" QNED` + `LED` | Texto libre → LED |

- **Resultado esperado:** `tecnologia = OLED`, `conflicto_origen = sí`, con ambos valores originales.

### QA-18: Un error en un registro no detiene el lote

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Ejecutar un lote con TVEC-1101, TVEC-1102 y TVEC-1999 (error de procesamiento simulado).
- **Resultado esperado:** TVEC-1101 y TVEC-1102 procesados; error registrado con `id_origen = TVEC-1999`, que se reintenta en la siguiente ejecución.

---

**Total de casos:** 18
