# Casos de Prueba — HU-003: Ingesta inicial e incremental de ítems de la TVEC

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la carga inicial e incremental de ítems TVEC: mapeo y lista blanca, prefiltro, ventana, deduplicación por identificador y por clave natural, resultado por registro, rechazos, trazabilidad, fecha de corte, reintentos, errores, exclusión mutua, fuente vacía y dataset alterno.

Queda fuera: relación con órdenes y entidades (HU-004), validaciones de precio, cantidad y total (HU-005) y marcación de candidatos (HU-009).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`. Fecha de referencia: 2026-10-02.
- Configuración: dataset `usqp-5nsn`; `fecha_inicio_historico = 2023-01-01`; términos "TELEVISOR", "SMART TV", "TV"; página 1.000; solape 24 h; 3 reintentos (2, 4, 8 s).
- Ítems semilla en la API simulada:

  | :id | orden | fecha | item | precio | cantidad | total | id_entidad | :updated_at |
  |---|---|---|---|---|---|---|---|---|
  | row-aaa1 | 112233 | 2024-05-10 | TELEVISOR SAMSUNG 55" UN55CU7000 | 2150000 | 4 | 8600000 | 701 | 2024-05-11T08:00:00 |
  | row-aaa2 | 112233 | 2024-05-10 | GSF01-SMART TV LG 43LR6500PSA | 1450000 | 2 | 2900000 | 701 | 2024-05-11T08:00:00 |
  | row-aaa3 | 445566 | 2025-11-20 | TV LED 32 PULGADAS KALLEY | 690000 | 10 | 6900000 | 902 | 2025-11-21T09:30:00 |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-03, RN-04, RN-05, RN-09 | QA-01, QA-02 |
| Escenario 2 / RN-11 | QA-03 |
| Escenario 3 / RN-07 | QA-04 |
| Escenario 4 / RN-08 | QA-05 |
| Escenario 5 / RN-06 | QA-06 |
| Escenario 6 / RN-13, RN-12 | QA-07 |
| Escenario 7 / RN-13 | QA-08 |
| Escenario 8 / RN-11 | QA-09 |
| Escenario 9 / RN-15 | QA-10 |
| Escenario 10 | QA-11 |
| Escenario 11 / RN-01, RN-02 | QA-12 |
| RN-10 | QA-13 |
| RN-11 (frecuencia) | QA-14 |
| RN-14, RN-16 | QA-15 |

---

## Casos de Prueba

### QA-01: Carga inicial exitosa con trazabilidad

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-04, RN-05, RN-09
- **Pasos:**
  1. Ejecutar la carga inicial TVEC con los 3 ítems semilla.
- **Resultado esperado:** la consulta pide `:id`, `:updated_at`, el prefiltro sobre `item` y `fecha` ≥ 2023-01-01. 3 ítems guardados con los campos internos de RN-02, `dataset_origen = usqp-5nsn`, `url_referencia = https://www.datos.gov.co/resource/usqp-5nsn.json?orden=112233` (y 445566), `fecha_corte`, `fecha_ingesta`, `id_ejecucion` y candidatura "Pendiente de marcación". Resumen "Carga inicial TVEC ítems finalizada. Leídos: 3. Nuevos: 3. Actualizados: 0. Sin cambios: 0. Rechazados: 0."

### QA-02: Campos fuera del mapeo no se persisten

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-03
- **Pasos:**
  1. Agregar a row-aaa1 los campos `nombre_contacto = Persona Ficticia` y `telefono_contacto = 3000000000` y ejecutar la carga.
- **Resultado esperado:** ninguno de los dos valores aparece en base de datos ni logs.

### QA-03: Incremental trae solo lo modificado y avanza la marca de agua

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-11
- **Precondiciones:** carga inicial "Exitosa"; marca de agua 2026-10-01T02:00:00.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem nuevo row-bbb1 :updated_at | 2026-10-01T18:00:00 | TELEVISOR LG 65" 65UR8750PSA, orden 778899 |

- **Pasos:**
  1. Ejecutar la incremental programada a las 02:30 del 2026-10-02.
- **Resultado esperado:** consulta con `:updated_at` > 2026-09-30T02:00:00; row-bbb1 "Nuevo"; estado "Exitosa"; marca de agua 2026-10-01T18:00:00.

### QA-04: Cambio de descripción vs. cambio de precio

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | row-aaa1.item | TELEVISOR SAMSUNG 55" UN55CU7000KXZL | descripción cambiada |
  | row-aaa3.precio | 710000 | solo precio cambiado |

- **Pasos:**
  1. Ejecutar la incremental.
- **Resultado esperado:** ambos "Actualizado" con `actualizado_en_fuente = sí`; row-aaa1 vuelve a "Pendiente de marcación"; row-aaa3 conserva su candidatura.

### QA-05: Rechazos por identificador y fecha

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | :id | (nulo) | "Identificador de origen ausente" |
  | fecha | (nula) | "Fecha ausente" |
  | fecha | 10-05-2024 | "Fecha con formato inválido" |
  | fecha | 2022-12-31 | mín − 1 → "Fecha fuera de la ventana histórica" |
  | fecha | 2023-01-01 | mín → se guarda |
  | fecha | 2026-10-03 | futuro → "Fecha fuera de la ventana histórica" |

- **Pasos:**
  1. Ejecutar la carga con un ítem por fila.
- **Resultado esperado:** solo se guarda el de 2023-01-01; los demás se cuentan como rechazados con el motivo indicado y la carga continúa.

### QA-06: Republicación con nuevo identificador de fila no duplica

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-06
- **Pasos:**
  1. Devolver row-aaa1 con `:id = row-zzz9` y los mismos orden, descripción, precio, cantidad y fecha.
  2. Devolver en la orden 112233 dos líneas idénticas nuevas "CONTROL TV" con `:id` row-ccc1 y row-ccc2.
- **Resultado esperado:** (1) sigue habiendo un único ítem; su `id_origen_item = row-zzz9` y `ids_origen_anteriores` contiene row-aaa1; cuenta "Actualizado". (2) Se crean 2 ítems con ocurrencia 1 y 2.

### QA-07: Reintentos y falla persistente

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-13, RN-12
- **Pasos:**
  1. Inyectar HTTP 429 una vez y ejecutar.
  2. Inyectar HTTP 502 permanente en la página 2 de 1.800 ítems y ejecutar; luego quitar la falla y re-ejecutar.
- **Resultado esperado:** (1) se procesa tras una espera de 2 s, sin duplicados. (2) 4 intentos, "Fallida", 1.000 ítems guardados, marca de agua sin avanzar y mensaje "La carga TVEC ítems falló en la página 2: …"; la re-ejecución deja 1.800 ítems sin duplicados.

### QA-08: Error no recuperable

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-13
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Respuesta | HTTP 400 | |
  | Respuesta | HTTP 404 | dataset `zzzz-0000` |

- **Pasos:**
  1. Ejecutar con cada respuesta.
- **Resultado esperado:** un intento, "Fallida", mensaje "La API de datos.gov.co rechazó la consulta (HTTP {código}). Verifique el identificador del dataset, la consulta y el app token."

### QA-09: Incremental sin carga inicial

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-11
- **Pasos:**
  1. Sin carga inicial exitosa, ejecutar la incremental.
- **Resultado esperado:** "Omitida"; mensaje "No existe una carga inicial exitosa de ítems TVEC. Ejecute primero la carga inicial."; la API no recibe solicitudes.

### QA-10: Concurrencia

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-15
- **Pasos:**
  1. Con una carga en curso, intentar una manual y llegar a la hora programada.
- **Resultado esperado:** la manual se rechaza con "Ya existe una carga en curso para TVEC ítems (ejecución {id_ejecucion}). Espere a que termine."; la programada queda "Omitida".

### QA-11: Fuente sin registros

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 10
- **Pasos:**
  1. API vacía; ejecutar la carga inicial.
- **Resultado esperado:** "Exitosa", contadores en 0, mensaje "La fuente no devolvió ítems TVEC para la ventana y el prefiltro configurados."

### QA-12: Dataset alterno 3hdv-smhz

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-01, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | orden_de_compra | 112233 | |
  | price / qty / line_total | 2150000 / 4 / 8600000 | |
  | entidad | No definido | |

- **Pasos:**
  1. Configurar `3hdv-smhz` y ejecutar la carga.
- **Resultado esperado:** ítem guardado con `dataset_origen = 3hdv-smhz`, `precio_unitario = 2.150.000,00`, `cantidad = 4`, `valor_total_item = 8.600.000,00` e `id_entidad_origen` nulo.

### QA-13: Fecha de corte

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** RN-10
- **Pasos:**
  1. Ejecutar con metadatos `rowsUpdatedAt = 1790722800`.
  2. Ejecutar con metadatos en HTTP 500.
- **Resultado esperado:** (1) `fecha_corte` = conversión a America/Bogota, `fecha_corte_aproximada = no`. (2) `fecha_corte` = inicio de la ejecución y `fecha_corte_aproximada = sí`.

### QA-14: Validación de frecuencia y solape

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Frecuencia | 1 / 168 | aceptados |
  | Frecuencia | 0 / 169 / 2.5 / vacío | rechazados |
  | Solape | 0 / 168 | aceptados |
  | Solape | -1 / 169 | rechazados |

- **Pasos:**
  1. Configurar cada valor.
- **Resultado esperado:** los aceptados se aplican; los de frecuencia rechazados muestran "La frecuencia de ingesta debe ser un número entero de horas entre 1 y 168"; todo valor rechazado conserva el anterior.

### QA-15: Sin token, sin IA y sin eliminación

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-14, RN-16
- **Pasos:**
  1. Quitar el app token y ejecutar la incremental cuando la fuente ya no devuelve row-aaa3.
- **Resultado esperado:** advertencia "Ejecución sin app token: la API puede aplicar límites más estrictos"; row-aaa3 sigue guardado; no se crea ninguna solicitud de extracción con IA ni de clasificación.

---

**Total de casos:** 15
