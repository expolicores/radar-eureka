# Casos de Prueba — HU-033: Identificar el código de modelo en el registro de origen

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la identificación del modelo original: prioridad campo estructurado / texto libre, no-valores, forma de los candidatos, exclusiones, calificadores, ambigüedad, referencias del pliego, códigos internos, trazabilidad, versiones y configuración. Queda fuera la normalización sintáctica del código (HU-034) y el emparejamiento.

## Precondiciones y Datos Base

- Configuración inicial (`version_reglas = 1`) de RN-03 a RN-08: longitud 6–20, no-valores, exclusiones, calificadores, expresiones de referencia y patrón interno `AMEPIE` + dígitos.
- Usuarios: `admin.po` (Administrador), `analista.piloto1` (Analista).
- Productos normalizados vigentes y activos:

| id_origen | tipo | marca | Campo modelo | Texto libre |
|---|---|---|---|---|
| TVEC-1201 | TVEC | SAMSUNG | — | `GSF01-TELEVISOR SAMSUNG UN55DU8000KXZL CRYSTAL UHD 55"` |
| TVEC-1202 | TVEC | LG | — | `TELEVISOR LG REF: 55UA7300PSB SMART 4K 3840X2160` |
| SEC-2201-I1 | SECOP_II | SAMSUNG | `UN 55DU8000 KXZL` | `Televisor 55 pulgadas` |
| RET-3201 | RETAIL | LG | `55UA7300PSA` | `Televisor LG 55" UHD` |
| TVEC-1203 | TVEC | LG | — | `AMEPIE0377 TELEVISOR LG 43"` |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-04, RN-09 | QA-01 |
| Escenario 2 / RN-05 | QA-02 |
| Escenario 3 / RN-02 | QA-03 |
| Escenario 4 / RN-03, RN-06 | QA-04 |
| Escenario 5 / RN-07 | QA-05 |
| Escenario 6 / RN-08 | QA-06 |
| Escenario 7 / RN-06 | QA-07 |
| Escenario 8 / RN-06 | QA-08 |
| Escenario 9 / RN-04 (exclusiones, forma) | QA-09, QA-10 |
| Escenario 10 / RN-10 | QA-11, QA-12 |
| RN-01 (inactivos) | QA-13 |
| RN-11 (error en un registro) | QA-14 |

---

## Casos de Prueba

### QA-01: Identifica el modelo en la descripción TVEC

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04, RN-09
- **Pasos:**
  1. Ejecutar la identificación sobre TVEC-1201.
- **Resultado esperado:** `modelo_original = UN55DU8000KXZL`, `campo_origen = descripcion_tvec`, `regla_aplicada = RN-04-token`; `GSF01-`, `55"` y `UHD` no son candidatos.

### QA-02: Candidato con calificador y descarte de resolución

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-05
- **Pasos:**
  1. Identificar el modelo de TVEC-1202.
- **Resultado esperado:** `modelo_original = 55UA7300PSB`, `regla_aplicada = RN-05-calificador`; `3840X2160` en `candidatos_descartados` con motivo "resolución".

### QA-03: El campo estructurado prevalece y se guarda completo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-02
- **Pasos:**
  1. Identificar el modelo de SEC-2201-I1 y RET-3201.
- **Resultado esperado:** `UN 55DU8000 KXZL` (con espacios) y `55UA7300PSA`, con `campo_origen` = `modelo_extraido` y `modelo_retail`; no se busca en el texto.

### QA-04: No-valores en el campo de modelo

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-03, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Modelo extraído | `N/A` | No-valor |
  | Modelo extraído | ` No aplica ` | Espacios y minúsculas |
  | Modelo retail | `Genérico` | Con tilde |
  | Modelo extraído | vacío | Vacío |
  | Texto libre (todos) | `Televisor 50 pulgadas` | Sin candidatos |
  | Modelo extraído `N/A` + texto `TV SAMSUNG UN50DU7000KXZL` | — | Cae a texto → `UN50DU7000KXZL` |

- **Resultado esperado:** los cuatro primeros con `modelo_original` nulo y `MODELO_NO_INFORMADO`; el último con `modelo_original = UN50DU7000KXZL`.

### QA-05: Referencia del pliego

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Modelo extraído | `UN55DU8000 o equivalente` | Campo estructurado |
  | Texto libre | `TELEVISOR TIPO 55UA7300PSB` | Expresión antes |
  | Texto libre | `TELEVISOR 55UA7300PSB O SIMILAR` | Expresión dentro de 3 palabras |

- **Resultado esperado:** los tres con `modelo_original` nulo, motivo `MODELO_REFERENCIAL` y texto conservado.

### QA-06: Código interno del catálogo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Texto TVEC-1203 | `AMEPIE0377 TELEVISOR LG 43"` | Solo código interno |
  | Texto TVEC-1204 | `AMEPIE0412 TELEVISOR LG 43LM6370PSB` | Interno + modelo |

- **Resultado esperado:** TVEC-1203: `codigo_interno_detectado = AMEPIE0377`, `modelo_original` nulo, `MODELO_CODIGO_INTERNO`. TVEC-1204: `codigo_interno_detectado = AMEPIE0412`, `modelo_original = 43LM6370PSB`.

### QA-07: Varios candidatos distintos, con y sin calificador

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Texto | `TV UN55DU8000KXZL UN50DU7000KXZL` | Sin calificador |
  | Texto | `TV UN55DU8000KXZL MODELO UN50DU7000KXZL` | Un calificador |
  | Texto | `TV UN55DU8000KXZL REF UN55DU8000KXZL` | Iguales |

- **Resultado esperado:** primero nulo con `MODELO_AMBIGUO` y ambos candidatos registrados; segundo `UN50DU7000KXZL`; tercero `UN55DU8000KXZL`.

### QA-08: Sin candidatos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Texto | `TELEVISOR SAMSUNG LED 50 PULGADAS SMART` | Sin códigos |

- **Resultado esperado:** `modelo_original` nulo con `MODELO_NO_ENCONTRADO`.

### QA-09: Tokens excluidos no son modelo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Texto | `TV 55" 120HZ HDMI2.1 DVB-T2 7702040123456 2160P` | Todos excluidos |
  | Texto | `TV SAMSUNG SAMSUNG55` | Igual a la marca + dígitos: candidato válido `SAMSUNG55` (no es igual a la marca) |

- **Resultado esperado:** primero `MODELO_NO_ENCONTRADO` con los cinco tokens en `candidatos_descartados` y su motivo; segundo `modelo_original = SAMSUNG55`.

### QA-10: Límites de longitud y composición del candidato

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Token | `AB123` | 5 caracteres → no candidato |
  | Token | `AB1234` | 6 → candidato |
  | Token | `AB12345678901234567X` | 20 → candidato |
  | Token | `AB123456789012345678X` | 21 → no candidato |
  | Token | `A12345` | 1 letra → no candidato |
  | Token | `ABCDE1` | 1 dígito → no candidato |
  | Token | `UN-55-DU8000` | Sin guiones 11 → candidato, original con guiones |

- **Resultado esperado:** solo los marcados como candidatos se toman como `modelo_original` (cada uno probado en un texto donde es el único token con forma de código); el último se guarda como `UN-55-DU8000`.

### QA-11: Corrección del origen genera nueva versión

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-10
- **Pasos:**
  1. Identificar SEC-2201-I1; ejecutar de nuevo sin cambios.
  2. Corregir el modelo extraído a `UN55DU8000KXZL` y ejecutar.
- **Resultado esperado:** paso 1 no crea versiones; paso 2 crea versión vigente con el nuevo valor y conserva la anterior como histórica.

### QA-12: Cambios de configuración: auditoría, permisos y validación

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `admin.po` agrega patrón interno | códigos que empiezan por `CCE` + dígitos | Válido |
  | `analista.piloto1` agrega patrón | cualquiera | Sin permiso |
  | `admin.po` define longitud | mínimo 12, máximo 8 | Inválido |
  | `admin.po` agrega patrón | `[A-` (no interpretable) | Inválido |

- **Resultado esperado:** el primero se aplica, queda auditado y sube `version_reglas`; un producto con `CCE12345 TV LG 43"` pasa a `MODELO_CODIGO_INTERNO` en la siguiente ejecución. El del Analista se rechaza por permiso. Los inválidos se rechazan con "Configuración inválida: {detalle}".

### QA-13: Productos inactivos no se procesan

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-01
- **Precondiciones:** TVEC-1205 con `activo = no`.
- **Resultado esperado:** su modelo y su versión no cambian.

### QA-14: Un error en un registro no detiene el lote

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Ejecutar un lote con TVEC-1201, TVEC-1202 y TVEC-1999 (error simulado).
- **Resultado esperado:** los dos primeros procesados; error registrado para TVEC-1999 y reintento en la siguiente ejecución.

---

**Total de casos:** 14
