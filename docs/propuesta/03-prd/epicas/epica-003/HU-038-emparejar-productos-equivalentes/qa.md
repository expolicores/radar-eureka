# Casos de Prueba — HU-038: Emparejar productos equivalentes por características técnicas

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la evaluación de pares contra las reglas de equivalencia vigentes: criterios obligatorios y "solo si ambos conocidos", tolerancias, desconocidos, decisión sin puntaje parcial, prerrequisito del objetivo, prohibición de relajación, referencias distintas, exclusión de pares mismo modelo o en conflicto, categoría sin reglas, resultado por ítem, recálculo e idempotencia. Queda fuera la configuración de reglas (HU-037) y la visualización (HU-040).

## Precondiciones y Datos Base

- Reglas `televisor` v1 vigentes (configuración inicial de RN-02).
- Productos vigentes y activos, categoría `televisor`:

| id_origen | tipo | marca | modelo | tamaño | resolución | tecnología | Smart | generación |
|---|---|---|---|---|---|---|---|---|
| SEC-2501-I1 | SECOP_II | nula | nulo | 65 | 4K | LED | SI | nula |
| TVEC-1501 | TVEC | SAMSUNG | UN65DU8000KXZL | 65 | 4K | LED | SI | 2024 |
| TVEC-1502 | TVEC | SAMSUNG | UN55DU8000KXZL | 55 | 4K | LED | SI | 2024 |
| RET-3501 | RETAIL | LG | 65UA7300PSB | 65 | 4K | nula | SI | 2024 |
| TVEC-1503 | TVEC | LG | 55UA7300PSB | 55 | 4K | LED | SI | 2023 |
| RET-3502 | RETAIL | LG | 55UA7300PSA | 55 | 4K | LED | SI | 2024 |
| RET-3503 | RETAIL | SAMSUNG | UN55AU7000KXZL | 55 | 4K | LED | SI | 2021 |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-03, RN-08 | QA-01 |
| Escenario 2 / RN-03, RN-04 | QA-02 |
| Escenario 3 / RN-03 (desconocido obligatorio) | QA-03 |
| Escenario 4 / RN-03 (solo si ambos) | QA-04 |
| Escenario 5 / RN-03 (tolerancia) | QA-05 |
| Escenario 6 / RN-07 | QA-06 |
| Escenario 7 / RN-05 | QA-07 |
| Escenario 8 / RN-06, RN-09 | QA-08 |
| Escenario 9 / RN-01 | QA-09 |
| Escenario 10 / RN-02 | QA-10 |
| Escenario 11 / RN-11 | QA-11, QA-12 |
| RN-03 (NO_EVALUADO configurado) | QA-13 |
| RN-10 | QA-14 |
| RN-11 (errores) | QA-15 |

---

## Casos de Prueba

### QA-01: Par equivalente con criterios no evaluados

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-08
- **Resultado esperado:** par {SEC-2501-I1, TVEC-1501} `EQUIVALENTE`, `version_reglas = 1`; tamaño, resolución, tecnología y Smart `CUMPLE` con sus valores; generación y marca `NO_EVALUADO`; `modelos_distintos = no` (modelo del objetivo nulo).

### QA-02: Criterio obligatorio distinto descarta el par

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03, RN-04
- **Resultado esperado:** no existe par `EQUIVALENTE` {SEC-2501-I1, TVEC-1502}; el conteo de descartes de SEC-2501-I1 incluye `tamano_pulgadas`.

### QA-03: Desconocido en criterio obligatorio descarta el par

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-03
- **Resultado esperado:** no existe par `EQUIVALENTE` {SEC-2501-I1, RET-3501}; descarte contado como `tecnologia (desconocido)`.

### QA-04: Marca o generación conocidas y distintas

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Par | TVEC-1502 (SAMSUNG) vs TVEC-1503 (LG) | Marca distinta |
  | Par | TVEC-1502 (2024) vs RET-3503 (2021, SAMSUNG) | Diferencia 3 > 1 |

- **Resultado esperado:** ninguno es `EQUIVALENTE`; descartes por `marca` y `generacion` respectivamente.

### QA-05: Tolerancia de generación en el límite

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Par | TVEC-1503 (2023) vs RET-3502 (2024) | Diferencia 1 = tolerancia |
  | Par | TVEC-1503 (2023) vs RET-3504 (LG 55UA7300PSC, 2025, resto igual) | Diferencia 2 |

- **Resultado esperado:** el primero `CUMPLE` en generación; el segundo `NO_CUMPLE` y no es equivalente.

### QA-06: Referencias distintas equivalentes

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-07
- **Resultado esperado:** par {TVEC-1503, RET-3502} `EQUIVALENTE` (no `MISMO_MODELO`) con `modelos_distintos = sí`, modelos `55UA7300PSB` y `55UA7300PSA` registrados.

### QA-07: Objetivo sin atributo obligatorio

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | SEC-2502-I1 | tamaño nulo, Smart nulo, resto 4K / LED | Dos faltantes |

- **Resultado esperado:** 0 candidatos evaluados; resultado `ATRIBUTOS_OBLIGATORIOS_FALTANTES: tamano_pulgadas, smart`.

### QA-08: Sin equivalentes y sin relajación

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-06, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | SEC-2503-I1 | 43" / FHD / LED / SI | Ningún candidato 43" FHD en la base |

- **Pasos:**
  1. Ejecutar el emparejamiento.
  2. Revisar el registro de la ejecución.
- **Resultado esperado:** 0 pares `EQUIVALENTE`, motivo `SIN_CANDIDATOS_QUE_CUMPLAN`, conteo de descartes por atributo (ej. `tamano_pulgadas: 7`); hay una sola evaluación del objetivo por ejecución, con la `version_reglas` vigente, y ningún par generado con tolerancias u obligatoriedad distintas.

### QA-09: Pares mismo modelo o en conflicto no se evalúan

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-01
- **Precondiciones:** {TVEC-1502, TVEC-1504} tiene par vigente `MISMO_MODELO`; {TVEC-1502, RET-3505} tiene par vigente `INSUFICIENTE_NO_CONFIABLE` por conflicto.
- **Resultado esperado:** ninguno de los dos tiene además un par `EQUIVALENTE`.

### QA-10: Categoría sin reglas

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** Escenario 10 / RN-02
- **Precondiciones:** objetivo de prueba de categoría `computador` sin reglas.
- **Resultado esperado:** sin pares equivalentes; motivo `SIN_REGLAS_EQUIVALENCIA`.

### QA-11: Recalculo con nueva versión de reglas

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-11
- **Pasos:**
  1. Crear la versión 2 de reglas con tolerancia de generación 0.
  2. Ejecutar el emparejamiento.
- **Resultado esperado:** el par {TVEC-1503, RET-3502} (2023 vs 2024) de v1 queda `vigente = no` con `version_reglas = 1`; no existe par vigente entre ellos con v2.

### QA-12: Reejecución sin cambios

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Resultado esperado:** dos ejecuciones seguidas sin cambios dejan el mismo número de pares vigentes y totales.

### QA-13: Criterio configurado como no evaluado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-03
- **Precondiciones:** versión de reglas con marca `NO_EVALUADO`.
- **Resultado esperado:** {TVEC-1502, TVEC-1503 con tamaño 55 y generación 2024} es `EQUIVALENTE` y la marca no aparece como `CUMPLE` en los criterios.

### QA-14: Precio y fecha no influyen

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Fecha de TVEC-1501 | 2023-02-01 | 3 años antes del objetivo |
  | Base tributaria | indeterminada | — |

- **Resultado esperado:** el par {SEC-2501-I1, TVEC-1501} sigue siendo `EQUIVALENTE`.

### QA-15: Error en un objetivo no detiene el lote

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-11
- **Resultado esperado:** con un error simulado en SEC-2501-I1, los demás objetivos se procesan; el error queda registrado para reintento.

---

**Total de casos:** 15
