# Casos de Prueba — HU-034: Normalizar sintácticamente el código de modelo

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el cálculo de `modelo_normalizado` desde `modelo_original`: separadores, mayúsculas, etiquetas, marca antepuesta, conservación de sufijos, no sustitución de caracteres parecidos, validaciones de caracteres y longitud, nulos heredados, versiones, idempotencia y configuración. Queda fuera la identificación del modelo original (HU-033) y el emparejamiento.

## Precondiciones y Datos Base

- Configuración inicial (`version_reglas = 1`): etiquetas `MODELO`, `MOD`, `REF`, `REFERENCIA`, `MODEL`; separadores espacio, `-`, `_`, `.`, `/`, `\`; longitud 4–25.
- Usuarios: `admin.po` (Administrador), `analista.piloto1` (Analista).
- Productos normalizados vigentes y activos con `marca` y `modelo_original` según cada caso.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02 (pasos 1, 2, 5) | QA-01 |
| Escenario 2 / RN-03 (sufijos) | QA-02 |
| Escenario 3 / RN-02 (pasos 3, 5) | QA-03 |
| Escenario 4 / RN-02 (paso 4) | QA-04 |
| Escenario 5 / RN-02 (paso 6) | QA-05 |
| Escenario 6 / RN-03 (sin sustitución) | QA-06 |
| Escenario 7 / RN-02 (paso 7) | QA-07 |
| Escenario 8 / RN-04 | QA-08 |
| Escenario 9 / RN-06 | QA-09, QA-10 |
| RN-05 (trazabilidad) | QA-01 |
| RN-07 (configuración) | QA-11 |
| RN-08 (error en un registro) | QA-12 |

---

## Casos de Prueba

### QA-01: Espacios, guiones y minúsculas producen el mismo código

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | modelo_original | ` UN 55DU8000 KXZL ` | Espacios internos y extremos |
  | modelo_original | `un55du8000kxzl` | Minúsculas |
  | modelo_original | `UN-55DU8000-KXZL` | Guiones |

- **Resultado esperado:** los tres con `modelo_normalizado = UN55DU8000KXZL` y la lista de pasos aplicados registrada (ej. `mayusculas`, `quitar_separadores`).

### QA-02: Sufijos regionales se conservan

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | modelo_original | `55UA7300PSA` | Sufijo PSA |
  | modelo_original | `55UA7300PSB` | Sufijo PSB |
  | modelo_original | `UN85DU8000KXZL` | Sufijo KXZL |

- **Resultado esperado:** `55UA7300PSA`, `55UA7300PSB` y `UN85DU8000KXZL`, sin pérdida de caracteres; los dos primeros son distintos entre sí.

### QA-03: Separadores equivalentes y etiqueta inicial

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | modelo_original | `55.UA7300.PSB` | Puntos |
  | modelo_original | `55UA7300/PSB` | Barra |
  | modelo_original | `55UA7300_PSB` | Guion bajo |
  | modelo_original | `55UA7300\PSB` | Barra invertida |
  | modelo_original | `Modelo: 55UA7300PSB` | Etiqueta con dos puntos |
  | modelo_original | `REF. 55UA7300PSB` | Etiqueta con punto |

- **Resultado esperado:** todos con `modelo_normalizado = 55UA7300PSB`.

### QA-04: Marca antepuesta con y sin separador

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | marca / modelo_original | SAMSUNG / `SAMSUNG UN55DU8000KXZL` | Con espacio → se quita |
  | marca / modelo_original | LG / `LG-55UA7300PSB` | Con guion → se quita |
  | marca / modelo_original | SAMSUNG / `SAMSUNGUN55DU8000` | Pegada → se conserva |
  | marca / modelo_original | nula / `SAMSUNG UN55DU8000KXZL` | Sin marca → no se quita |

- **Resultado esperado:** `UN55DU8000KXZL`, `55UA7300PSB`, `SAMSUNGUN55DU8000` y `SAMSUNGUN55DU8000KXZL` respectivamente.

### QA-05: Caracteres no válidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | modelo_original | `55UA7300(PSB)` | Paréntesis |
  | modelo_original | `55UA7300+` | Signo más |
  | modelo_original | `55UA7300Ñ` | Ñ |

- **Resultado esperado:** `modelo_normalizado` nulo con `MODELO_CARACTERES_NO_VALIDOS`; `modelo_original` sin cambios.

### QA-06: Caracteres parecidos no se sustituyen

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | modelo_original | `55UA73OOPSB` | Letras O |
  | modelo_original | `55UA7300PSB` | Ceros |
  | modelo_original | `43LM637OPSB` | Letra O final |

- **Resultado esperado:** `55UA73OOPSB`, `55UA7300PSB` y `43LM637OPSB` sin cambios de caracteres; los dos primeros distintos.

### QA-07: Límites de longitud

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | modelo_original | `A1B` | 3 → nulo |
  | modelo_original | `A1-B2` | 4 tras quitar guion → válido |
  | modelo_original | 25 caracteres alfanuméricos `UN55DU8000KXZLABCDEFGHIJK` | Máximo → válido |
  | modelo_original | 26 caracteres `UN55DU8000KXZLABCDEFGHIJKL` | Máx+1 → nulo |

- **Resultado esperado:** los válidos se guardan; los inválidos quedan nulos con `MODELO_LONGITUD_INVALIDA`.

### QA-08: Modelo original nulo

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | modelo_original / motivo | nulo / `MODELO_NO_ENCONTRADO` | — |
  | modelo_original / motivo | nulo / `MODELO_CODIGO_INTERNO` | — |

- **Resultado esperado:** `modelo_normalizado` nulo con el mismo motivo en cada caso.

### QA-09: Idempotencia

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-06
- **Pasos:**
  1. Normalizar `UN 55DU8000 KXZL`; ejecutar de nuevo sin cambios.
  2. Aplicar la normalización al resultado `UN55DU8000KXZL`.
- **Resultado esperado:** no se crean versiones nuevas; el paso 2 devuelve `UN55DU8000KXZL`.

### QA-10: Nueva versión ante cambio del modelo original

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-06
- **Pasos:**
  1. Cambiar el `modelo_original` de `55UA7300PSA` a `55UA7300PSB` y ejecutar.
- **Resultado esperado:** nueva versión vigente con `55UA7300PSB`; la anterior queda histórica con fecha de reemplazo.

### QA-11: Configuración: permisos, auditoría y validaciones

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `admin.po` agrega separador | `,` | Válido |
  | `analista.piloto1` agrega separador | `,` | Sin permiso |
  | `admin.po` agrega separador | `A` | Letra → inválido |
  | `admin.po` define longitud | mínimo 0 | Menor que 1 → inválido |
  | `admin.po` define longitud | mínimo 10, máximo 5 | Inválido |

- **Resultado esperado:** el primero se aplica, queda auditado (usuario, fecha y hora, anterior, nuevo), sube `version_reglas` y `55UA7300,PSB` pasa a `55UA7300PSB` en la siguiente ejecución; el del Analista se rechaza por permiso; los inválidos se rechazan con "Configuración inválida: {detalle}".

### QA-12: Un error en un registro no detiene el lote

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-08
- **Pasos:**
  1. Ejecutar un lote con tres productos, uno con error simulado.
- **Resultado esperado:** los otros dos procesados; el error queda registrado con su `id_origen` y se reintenta en la siguiente ejecución.

---

**Total de casos:** 12
