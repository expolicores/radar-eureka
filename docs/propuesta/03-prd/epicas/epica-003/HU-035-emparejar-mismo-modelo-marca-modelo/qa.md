# Casos de Prueba — HU-035: Emparejar como mismo modelo por marca y modelo normalizado

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la generación de pares `MISMO_MODELO` por marca y modelo normalizado: selección de objetivos y candidatos, igualdad exacta, nulos, control de conflicto, registro del par, resultado por ítem, independencia de precio/fecha, recálculo, idempotencia y configuración. Queda fuera el emparejamiento por EAN (HU-036), la equivalencia (HU-038) y la visualización (HU-040).

## Precondiciones y Datos Base

- Configuración inicial: atributos de control `tamano_pulgadas`, `resolucion`, `tecnologia`.
- Usuarios: `admin.po` (Administrador), `analista.piloto1` (Analista).
- Productos normalizados vigentes y activos, categoría `televisor`:

| id_origen | tipo | marca | modelo_normalizado | tamaño | resolución | tecnología |
|---|---|---|---|---|---|---|
| TVEC-1301 | TVEC | SAMSUNG | UN55DU8000KXZL | 55 | 4K | LED |
| RET-3301 | RETAIL | SAMSUNG | UN55DU8000KXZL | 55 | 4K | LED |
| SEC-2301-I1 | SECOP_II | SAMSUNG | UN55DU8000KXZL | 55 | nula | nula |
| TVEC-1302 | TVEC | LG | 55UA7300PSB | 55 | 4K | LED |
| RET-3302 | RETAIL | LG | 55UA7300PSA | 55 | 4K | LED |
| RET-3303 | RETAIL | SAMSUNG | UN55DU8000KXZL | 65 | 4K | LED |
| RET-3304 | RETAIL | EXCLUSIV | UN55DU8000KXZL | 55 | 4K | LED |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-04 | QA-01 |
| Escenario 2 / RN-01 | QA-02 |
| Escenario 3 / RN-02 (exactitud) | QA-03 |
| Escenario 4 / RN-05 | QA-04 |
| Escenario 5 / RN-02 | QA-05 |
| Escenario 6 / RN-03 | QA-06 |
| Escenario 7 / RN-03 (NO_EVALUADO) | QA-07 |
| Escenario 8 / RN-05 | QA-08 |
| Escenario 9 / RN-01 | QA-09 |
| Escenario 10 / RN-07 | QA-10, QA-11 |
| RN-01 (retail no es objetivo, categoría) | QA-12 |
| RN-06 | QA-13 |
| RN-08 | QA-14 |
| RN-09 | QA-15 |

---

## Casos de Prueba

### QA-01: Par mismo modelo entre TVEC y retail

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-04
- **Pasos:**
  1. Ejecutar el emparejamiento.
  2. Consultar los pares vigentes de TVEC-1301.
- **Resultado esperado:** par {TVEC-1301, RET-3301} con `tipo = MISMO_MODELO`, `criterio = MARCA_MODELO`, criterios evaluados con tamaño, resolución y tecnología en `CUMPLE`, versiones de ambos productos, `version_reglas`, `fecha_calculo` y `vigente = sí`.

### QA-02: Par entre dos compras públicas en ambos sentidos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-01
- **Resultado esperado:** existen los pares vigentes {SEC-2301-I1, TVEC-1301} y {TVEC-1301, SEC-2301-I1}, ambos `MISMO_MODELO`.

### QA-03: Sufijo distinto no genera mismo modelo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-02
- **Resultado esperado:** no existe par `MISMO_MODELO` entre TVEC-1302 (`55UA7300PSB`) y RET-3302 (`55UA7300PSA`).

### QA-04: Objetivo con marca o modelo nulo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | TVEC-1303 | marca nula, modelo `UN55DU8000KXZL` | Sin marca |
  | TVEC-1304 | marca SAMSUNG, modelo nulo | Sin modelo |

- **Resultado esperado:** ninguno tiene pares `MISMO_MODELO` por marca y modelo; ambos registran `MARCA_O_MODELO_NULO`.

### QA-05: Misma referencia con marca distinta

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-02
- **Resultado esperado:** no existe par `MISMO_MODELO` entre TVEC-1301 y RET-3304.

### QA-06: Conflicto de tamaño en mismo marca y modelo

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-03
- **Resultado esperado:** par {TVEC-1301, RET-3303} con `tipo = INSUFICIENTE_NO_CONFIABLE`, motivo `CONFLICTO_ATRIBUTOS`, detalle `tamano_pulgadas: 55 vs 65`; no se cuenta en el número de pares `MISMO_MODELO` de TVEC-1301 y sí en el de pares en conflicto.

### QA-07: Atributos nulos no bloquean

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-03
- **Resultado esperado:** par {TVEC-1301, SEC-2301-I1} `MISMO_MODELO`, con tamaño `CUMPLE` y resolución y tecnología `NO_EVALUADO`.

### QA-08: Objetivo sin candidatos

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | TVEC-1305 | HISENSE / `50A6KVXZ` | Único en la base |

- **Resultado esperado:** sin pares `MISMO_MODELO`; motivo `SIN_CANDIDATOS_MISMO_MODELO`.

### QA-09: Sin autoemparejamiento ni pares con históricos o inactivos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-01
- **Precondiciones:** TVEC-1301 tiene una versión histórica; RET-3305 (SAMSUNG / UN55DU8000KXZL) tiene `activo = no`.
- **Resultado esperado:** no hay pares de TVEC-1301 consigo mismo, con su versión histórica ni con RET-3305.

### QA-10: Recálculo al cambiar el modelo de un candidato

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-07
- **Pasos:**
  1. RET-3301 obtiene nueva versión con `modelo_normalizado = UN55DU7000KXZL`.
  2. Ejecutar el emparejamiento.
- **Resultado esperado:** el par {TVEC-1301, RET-3301} anterior queda `vigente = no` con fecha; no existe par `MISMO_MODELO` vigente entre ellos.

### QA-11: Reejecución sin cambios no duplica pares

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Pasos:**
  1. Ejecutar el emparejamiento dos veces sin cambios.
- **Resultado esperado:** el número de pares vigentes y totales no cambia.

### QA-12: Retail no es objetivo; categorías distintas no se emparejan

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-01
- **Precondiciones:** existe un producto de prueba de categoría `monitor` con SAMSUNG / UN55DU8000KXZL (solo para esta prueba).
- **Resultado esperado:** RET-3301 no tiene pares propios como objetivo; no hay pares con el producto de categoría `monitor`.

### QA-13: Precio y fecha no influyen

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Fecha de RET-3301 | 2023-01-10 | Muy anterior a TVEC-1301 (2026-05-02) |
  | Base tributaria de TVEC-1301 | indeterminada | — |

- **Resultado esperado:** el par {TVEC-1301, RET-3301} sigue siendo `MISMO_MODELO`.

### QA-14: Configuración de atributos de control

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `analista.piloto1` modifica la lista | quitar `tecnologia` | Sin permiso |
  | `admin.po` agrega atributo | `color` | No pertenece al esquema |
  | `admin.po` deja la lista vacía | sin justificación | Rechazo |
  | `admin.po` deja la lista vacía | justificación "Prueba controlada de la regla" | Aceptado |

- **Resultado esperado:** rechazos por permiso y con "Configuración inválida: {detalle}" en los dos primeros inválidos; el último se aplica, queda auditado y sube `version_reglas`; en la siguiente ejecución el par {TVEC-1301, RET-3303} pasa a `MISMO_MODELO`.

### QA-15: Error en un objetivo no detiene el lote

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Resultado esperado:** con un error simulado en TVEC-1302, los demás objetivos se emparejan y el error queda registrado para reintento.

---

**Total de casos:** 15
