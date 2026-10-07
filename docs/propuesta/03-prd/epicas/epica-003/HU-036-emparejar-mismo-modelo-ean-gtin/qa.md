# Casos de Prueba — HU-036: Emparejar como mismo modelo por EAN/GTIN

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la validación y normalización del EAN/GTIN (tipo de identificador, formato, longitud, dígito de control) y la generación de pares `MISMO_MODELO` por EAN: criterio combinado, conflicto, EAN distinto, EAN en un solo lado, recálculo e idempotencia. Queda fuera el emparejamiento por marca y modelo (HU-035) y la equivalencia.

## Precondiciones y Datos Base

- Atributos de control: `tamano_pulgadas`, `resolucion`, `tecnologia`.
- EAN válidos calculados con dígito de control GS1: `8806095512341` (EAN-13), `7702040123451` (EAN-13), `88016436` (EAN-8), `036000291452` (UPC-12).
- Productos normalizados vigentes y activos:

| id_origen | tipo | Identificador (tipo / valor) | marca / modelo | tamaño / resolución / tecnología |
|---|---|---|---|---|
| RET-3401 | RETAIL | EAN / `8806095512341` | SAMSUNG / nulo | 55 / 4K / LED |
| SEC-2401-I1 | SECOP_II | GTIN / `8806095512341` | nula / nulo | 55 / 4K / nula |
| TVEC-1401 | TVEC | — | SAMSUNG / UN55DU8000KXZL | 55 / 4K / LED |
| RET-3402 | RETAIL | EAN / `8806095512341` | SAMSUNG / UN55DU8000KXZL | 55 / 4K / LED |
| RET-3403 | RETAIL | SKU / `881234567` | LG / nulo | 50 / 4K / LED |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01, RN-02 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-02, RN-03 | QA-03, QA-04 |
| Escenario 4 / RN-01 | QA-05 |
| Escenario 5 / RN-05 | QA-06 |
| Escenario 6 / RN-05 | QA-07 |
| Escenario 7 / RN-06 | QA-08 |
| Escenario 8 / RN-07 | QA-09 |
| Escenario 9 | QA-10 |
| RN-04 (objetivos y candidatos) | QA-11 |
| RN-08 (recálculo, idempotencia) | QA-12 |
| RN-09 | QA-13 |

---

## Casos de Prueba

### QA-01: EAN-13 válido se guarda como GTIN-14

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01, RN-02
- **Resultado esperado:** RET-3401 con `ean = 08806095512341`, valor original `8806095512341` y campo de origen `identificador_retail`.

### QA-02: Formatos y longitudes válidas

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | EAN | `8806 0955 12341` | Espacios |
  | EAN | `8-806095-512341` | Guiones |
  | EAN | `08806095512341` | Ya GTIN-14 |
  | EAN | `88016436` | EAN-8 → `00000088016436` |
  | UPC | `036000291452` | UPC-12 → `00036000291452` |

- **Resultado esperado:** los tres primeros `08806095512341`; los dos últimos según la nota.

### QA-03: Dígito de control incorrecto

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | EAN | `8806095512346` | Control esperado 1 |
  | EAN | `7702040123450` | Control esperado 1 |

- **Resultado esperado:** `ean` nulo con `EAN_INVALIDO`; valor original conservado.

### QA-04: Longitud o caracteres no válidos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | EAN | `8801643` | 7 dígitos |
  | EAN | `880609551` | 9 dígitos |
  | EAN | `88060955123410` + `1` (15 dígitos) | Máx+1 |
  | EAN | `88O6095512341` | Letra O |
  | EAN | vacío | Sin valor → `EAN_NO_INFORMADO` |

- **Resultado esperado:** los cuatro primeros con `EAN_INVALIDO`; el vacío con `EAN_NO_INFORMADO`.

### QA-05: SKU y tipos no EAN

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | RET-3403 | SKU / `881234567` | SKU Falabella |
  | RET-3404 | sin tipo / `8806095512341` | Tipo no declarado |

- **Resultado esperado:** ambos con `ean` nulo y `IDENTIFICADOR_NO_ES_EAN`.

### QA-06: Par mismo modelo solo por EAN

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-05
- **Resultado esperado:** par {SEC-2401-I1, RET-3401} `MISMO_MODELO`, `criterio = EAN`; criterios con tamaño y resolución `CUMPLE`, tecnología `NO_EVALUADO`, marca `NO_EVALUADO`.

### QA-07: Coincidencia por EAN y por marca y modelo produce un solo par

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-05
- **Precondiciones:** TVEC-1402 con SAMSUNG / UN55DU8000KXZL y EAN de tipo GTIN `8806095512341`.
- **Resultado esperado:** un único par vigente {TVEC-1402, RET-3402} `MISMO_MODELO` con `criterio = MARCA_MODELO_Y_EAN`.

### QA-08: EAN igual con marca o atributo contradictorio

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | RET-3405 | EAN `8806095512341`, marca LG, 55 / 4K / LED | Marca distinta |
  | RET-3406 | EAN `8806095512341`, marca SAMSUNG, 65 / 4K / LED | Tamaño distinto |

- **Resultado esperado:** pares {SEC-2401-I1, RET-3406} y {TVEC-1402, RET-3405} como `INSUFICIENTE_NO_CONFIABLE`, `CONFLICTO_ATRIBUTOS`, con detalle `tamano_pulgadas: 55 vs 65` y `marca: SAMSUNG vs LG` respectivamente. {SEC-2401-I1, RET-3405} es `MISMO_MODELO` porque la marca de SEC-2401-I1 es nula.

### QA-09: EAN distinto con marca y modelo iguales

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | TVEC-1403 | SAMSUNG / UN55DU8000KXZL, GTIN `7702040123451` | EAN distinto al de RET-3402 |

- **Resultado esperado:** par {TVEC-1403, RET-3402} `MISMO_MODELO`, `criterio = MARCA_MODELO`, con `ean_distinto = sí` y ambos valores.

### QA-10: EAN en un solo lado

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Resultado esperado:** TVEC-1401 (sin EAN) y RET-3401 no forman par por EAN; no existe par `MISMO_MODELO` entre ellos porque RET-3401 no tiene modelo.

### QA-11: Retail no es objetivo; no hay autoemparejamiento

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-04
- **Resultado esperado:** RET-3401 y RET-3402 no tienen pares como objetivo entre sí; ningún producto se empareja consigo mismo.

### QA-12: Cambio de EAN y reejecución

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-08
- **Pasos:**
  1. Corregir el EAN de SEC-2401-I1 a `7702040123451` y ejecutar.
  2. Ejecutar otra vez sin cambios.
- **Resultado esperado:** paso 1: nueva versión del producto; el par {SEC-2401-I1, RET-3401} queda `vigente = no` con fecha. Paso 2: no se crean registros.

### QA-13: Error en un registro no detiene el lote

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Resultado esperado:** con un error simulado en un producto, los demás se procesan y el error queda registrado para reintento.

---

**Total de casos:** 13
