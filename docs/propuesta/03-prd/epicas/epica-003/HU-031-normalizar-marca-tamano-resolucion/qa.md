# Casos de Prueba — HU-031: Normalizar marca, tamaño y resolución al esquema común

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la creación del producto normalizado en el esquema común y la normalización de marca, tamaño en pulgadas y resolución para registros de SECOP II, TVEC y retail: trazabilidad por atributo, nulos con motivo, ambigüedades, rango, conflictos de origen, estado de normalización, versiones, idempotencia y cambios de configuración. Queda fuera: tecnología, Smart, generación, modelo y EAN (otras HUs), la clasificación de categoría y la ingesta de los registros de origen.

## Precondiciones y Datos Base

- Configuración inicial cargada (`version_reglas = 1`): prefijo de catálogo "tres letras + dos dígitos + guion"; alias de marca SAMSUNG, LG (`LG ELECTRONICS`), TCL, KALLEY, CHALLENGER, HISENSE, SONY, PHILIPS, XIAOMI, PANASONIC, JVC, HYUNDAI, AIWA; expresiones de referencia `O EQUIVALENTE`, `O SIMILAR`, `TIPO`, `REFERENCIA`, `SIMILAR A`; rango de tamaño 10–120; sinónimos de resolución de RN-08.
- Usuarios: `admin.po` (Administrador) y `analista.piloto1` (Analista).
- Registros de origen semilla:

| id_origen | tipo | clasificación | Datos |
|---|---|---|---|
| TVEC-1001 | TVEC | incluido | `GSF01-TELEVISOR SAMSUNG FLAT LED CRYSTAL UHD SMART TV 55"` |
| SEC-2001-I1 | SECOP_II | incluido | marca `lg`, tamaño `65 pulg.`, resolución `Ultra HD 3840 x 2160` |
| RET-3001 | RETAIL | — | marca `Exclusiv`, nombre `Televisor Exclusiv 32" HD` |
| TVEC-1002 | TVEC | incluido | `TELEVISOR LED 43 PULGADAS FULL HD` |
| SEC-2002-I1 | SECOP_II | incluido | marca `Samsung o equivalente`, tamaño `50"` |
| TVEC-1003 | TVEC | excluido | `SOPORTE PARA TELEVISOR 32-70` |
| TVEC-1004 | TVEC | requiere revisión | `PANTALLA 55 PULGADAS` |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-03, RN-05 | QA-01 |
| Escenario 2 / RN-04 | QA-02 |
| Escenario 3 / RN-06 (marca no catalogada) | QA-03 |
| Escenario 4 / RN-06 (no reconocida, palabra completa) | QA-04 |
| Escenario 5 / RN-06 (referencial) | QA-05 |
| Escenario 6 / RN-06 (ambigua) | QA-06 |
| Escenario 7 / RN-07 (redondeo, cm) | QA-07 |
| Escenario 8 / RN-07 (ambiguo) | QA-08 |
| Escenario 9 / RN-07 (rango) | QA-09 |
| Escenario 10 / RN-08 | QA-10, QA-11 |
| Escenario 11 / RN-04 (conflicto) | QA-12 |
| Escenario 12 / RN-09 | QA-13 |
| Escenario 13 / RN-01 | QA-14 |
| Escenario 14 / RN-10 | QA-15 |
| Escenario 15 / RN-12 | QA-16, QA-17 |
| RN-11 (sin IA) | QA-18 |
| RN-13 (error en un registro) | QA-19 |

---

## Casos de Prueba

### QA-01: Normaliza un ítem TVEC desde su descripción y elimina el prefijo de catálogo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-03, RN-05
- **Pasos:**
  1. Ejecutar la normalización con TVEC-1001 pendiente.
  2. Consultar su producto normalizado.
- **Resultado esperado:** un único producto con `tipo_origen = TVEC`, `id_origen = TVEC-1001`, `categoria = televisor`, `marca = SAMSUNG`, `tamano_pulgadas = 55`, `resolucion = 4K`; valores originales `SAMSUNG`, `55"`, `CRYSTAL UHD`; `campo_origen = descripcion_tvec`; regla aplicada registrada en cada atributo; ningún valor normalizado contiene `GSF01-`; el texto original de TVEC-1001 no cambia; tecnología, Smart, generación, modelo y EAN con motivo `NO_PROCESADO`.

### QA-02: Normaliza un ítem SECOP II desde sus campos extraídos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-04, RN-08
- **Pasos:**
  1. Ejecutar la normalización con SEC-2001-I1.
- **Resultado esperado:** `marca = LG`, `tamano_pulgadas = 65`, `resolucion = 4K` (tras quitar espacios alrededor de la X); `campo_origen` = `marca_extraida`, `tamano_extraido`, `resolucion_extraida`.

### QA-03: Guarda una marca de campo estructurado que no está en la tabla

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-06
- **Pasos:**
  1. Normalizar RET-3001.
- **Resultado esperado:** `marca = EXCLUSIV`, `marca_no_catalogada = sí`, `tamano_pulgadas = 32`, `resolucion = HD`.

### QA-04: Deja la marca nula cuando el texto libre no contiene un alias como palabra completa

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción TVEC-1002 | `TELEVISOR LED 43 PULGADAS FULL HD` | Sin marca |
  | Descripción TVEC-1005 | `TELEVISOR 40" FUNDA ALGODON` | `LG` aparece dentro de `ALGODON` |

- **Pasos:**
  1. Normalizar ambos registros.
- **Resultado esperado:** en ambos `marca` nula con motivo `MARCA_NO_RECONOCIDA`; TVEC-1002 con `tamano_pulgadas = 43` y `resolucion = FHD`.

### QA-05: Marca de referencia del pliego queda nula

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Marca extraída SEC-2002-I1 | `Samsung o equivalente` | Expresión `O EQUIVALENTE` |
  | Marca extraída SEC-2003-I1 | `tipo LG` | Expresión `TIPO` |

- **Resultado esperado:** `marca` nula con motivo `MARCA_REFERENCIAL` y valor original conservado en ambos.

### QA-06: Dos marcas distintas en el texto producen marca ambigua

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción TVEC-1006 | `TELEVISOR SAMSUNG O LG 50"` | Dos marcas |

- **Resultado esperado:** `marca` nula con motivo `MARCA_AMBIGUA`; `tamano_pulgadas = 50`.

### QA-07: Redondeo del tamaño nominal y conversión desde centímetros

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | `TV 54,6"` | Esperado 55 |
  | Descripción | `TV 64.5 PULGADAS` | 0,5 sube → 65 |
  | Descripción | `TV 42,4 IN` | Esperado 42 |
  | Descripción | `TV 139 CM` | 54,72 → 55 |
  | Descripción | `TV 108 CM 43"` | Hay pulgadas: se ignora cm → 43 |

- **Resultado esperado:** los tamaños esperados de la columna Nota, con la regla aplicada (`pulgadas` o `cm`) registrada.

### QA-08: Dos tamaños distintos producen tamaño ambiguo; el mismo tamaño repetido no

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | `TELEVISOR 50" Y 55" SMART` | Ambiguo |
  | Descripción | `TELEVISOR 55" PANTALLA 55 PULGADAS` | Mismo tamaño |

- **Resultado esperado:** la primera con `tamano_pulgadas` nulo y motivo `TAMANO_AMBIGUO`; la segunda con `tamano_pulgadas = 55`.

### QA-09: Valores límite del rango de tamaño

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Tamaño | `9"` | Mín−1 → nulo |
  | Tamaño | `10"` | Mínimo → 10 |
  | Tamaño | `120"` | Máximo → 120 |
  | Tamaño | `121"` | Máx+1 → nulo |
  | Tamaño | `9,6"` | Redondea a 10 → válido |

- **Resultado esperado:** los valores dentro del rango se guardan; los de fuera quedan nulos con motivo `TAMANO_FUERA_DE_RANGO`.

### QA-10: Resolución ambigua y resolución no encontrada

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | `TELEVISOR 55" FULL HD 4K` | Dos resoluciones |
  | Descripción | `TELEVISOR SAMSUNG 32"` | Sin resolución |

- **Resultado esperado:** primera: `resolucion` nula, `RESOLUCION_AMBIGUA`; segunda: `resolucion` nula, `RESOLUCION_NO_ENCONTRADA`.

### QA-11: Precedencia de sinónimos largos y palabra completa en resolución

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción | `TV 43" FULL HD` | FHD, no HD |
  | Descripción | `TV 50" ULTRA HD` | 4K, no HD |
  | Descripción | `TV 55" 4K UHD` | Dos sinónimos de 4K → 4K |
  | Descripción | `TV 32" HD READY` | HD |

- **Resultado esperado:** FHD, 4K, 4K y HD respectivamente, sin motivo de ambigüedad.

### QA-12: Conflicto entre campo estructurado y nombre comercial

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Tamaño estructurado RET-3002 | `50` | Campo específico |
  | Nombre RET-3002 | `Televisor LG 55" 4K` | Texto libre |

- **Resultado esperado:** `tamano_pulgadas = 50`, `conflicto_origen = sí` para el tamaño, con valores originales `50` y `55"` registrados; marca LG y resolución 4K sin conflicto.

### QA-13: Registro sin atributos mínimos y cálculo del estado

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 12 / RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Descripción TVEC-1007 | `TELEVISOR` | Sin datos |
  | Descripción TVEC-1008 | `TELEVISOR 40"` | Solo tamaño |

- **Resultado esperado:** TVEC-1007 crea producto con atributos nulos y motivos (`MARCA_NO_RECONOCIDA`, `TAMANO_NO_ENCONTRADO`, `RESOLUCION_NO_ENCONTRADA`, resto `NO_PROCESADO`) y `estado_normalizacion = SIN_ATRIBUTOS_MINIMOS`; TVEC-1008 queda `PARCIAL`.

### QA-14: No normaliza registros no incluidos e inactiva los que dejan de serlo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 13 / RN-01
- **Pasos:**
  1. Ejecutar la normalización con TVEC-1003 (excluido) y TVEC-1004 (requiere revisión).
  2. Cambiar la clasificación de TVEC-1001 (ya normalizado) a `excluido` y ejecutar de nuevo.
  3. Volver TVEC-1001 a `incluido` y ejecutar.
- **Resultado esperado:** paso 1: sin producto normalizado para TVEC-1003 ni TVEC-1004. Paso 2: el producto de TVEC-1001 queda `activo = no`, motivo `ORIGEN_NO_INCLUIDO`, con fecha, y sigue existiendo. Paso 3: se reactiva con una nueva normalización vigente.

### QA-15: Idempotencia y nueva versión ante corrección del origen

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 14 / RN-10
- **Pasos:**
  1. Normalizar SEC-2004-I1 con tamaño extraído `56"`.
  2. Ejecutar de nuevo sin cambios.
  3. Corregir el tamaño extraído a `65"` (corrección del Revisor) y ejecutar.
- **Resultado esperado:** paso 2: el número de productos y versiones no cambia. Paso 3: nueva versión vigente con `tamano_pulgadas = 65`; la versión con 56 queda `vigente = no` con fecha de reemplazo y su `version_reglas`.

### QA-16: Cambio válido de configuración por el Administrador

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 15 / RN-12
- **Pasos:**
  1. Con `admin.po`, agregar el alias `EXCLUSIV`.
  2. Ejecutar la normalización.
  3. Con `analista.piloto1`, intentar modificar la tabla de alias.
- **Resultado esperado:** paso 1: cambio registrado con usuario `admin.po`, fecha y hora, valor anterior y nuevo; `version_reglas = 2`. Paso 2: RET-3001 se recalcula con `marca = EXCLUSIV` y `marca_no_catalogada = no`. Paso 3: la modificación es rechazada por falta de permiso y la configuración no cambia.

### QA-17: Rechazo de configuración inválida

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Rango de tamaño | mínimo 80, máximo 40 | Mínimo > máximo |
  | Tabla de sinónimos de resolución | vacía | Tabla vacía |

- **Resultado esperado:** ambos cambios se rechazan con "Configuración inválida: {detalle}"; `version_reglas` no cambia.

### QA-18: La normalización funciona con la extracción con IA desactivada

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Desactivar la extracción con IA.
  2. Normalizar TVEC-1002.
- **Resultado esperado:** el producto se normaliza igual que en QA-04, sin errores.

### QA-19: Un error en un registro no detiene el lote

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Ejecutar un lote con TVEC-1001, TVEC-1002 y un registro TVEC-1999 cuya descripción provoca un error de procesamiento simulado.
  2. Corregir la causa y ejecutar de nuevo.
- **Resultado esperado:** paso 1: TVEC-1001 y TVEC-1002 quedan normalizados; se registra el error con `id_origen = TVEC-1999`. Paso 2: TVEC-1999 se procesa.

---

**Total de casos:** 19
