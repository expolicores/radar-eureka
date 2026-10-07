# Casos de Prueba — HU-004: Relacionar cada ítem TVEC con su orden de compra, entidad y fecha

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la carga de órdenes TVEC referenciadas por ítems y la relación ítem ↔ orden ↔ entidad: estados de relación, inconsistencias de fecha, órdenes duplicadas, actualización incremental, fallas, estado vacío e indicador de relación.

Queda fuera: la ingesta de ítems (HU-003) y la bitácora general (HU-006).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`. Configuración: dataset `rgxm-mmea`; lote de 100; tolerancia de fecha 31 días; solape 24 h; 3 reintentos.
- Ítems TVEC guardados (estado de relación "Pendiente"):

  | id_origen_item | orden | fecha_item | descripcion_item | id_entidad_origen |
  |---|---|---|---|---|
  | row-aaa1 | 112233 | 2024-05-10 | TELEVISOR SAMSUNG 55" UN55CU7000 | 701 |
  | row-aaa2 | 112233 | 2024-05-10 | GSF01-SMART TV LG 43LR6500PSA | 701 |
  | row-aaa3 | 445566 | 2025-11-20 | TV LED 32 PULGADAS KALLEY | 902 |
  | row-aaa4 | 999001 | 2026-02-01 | TELEVISOR TCL 50" 50P635 | 905 |
  | row-aaa5 | (nula) | 2026-03-15 | TELEVISOR HISENSE 58" | 906 |

- Órdenes en la API simulada:

  | identificador_de_la_orden | fecha | entidad | nit_entidad | proveedor | total | agregacion | estado |
  |---|---|---|---|---|---|---|---|
  | 112233 | 2024-05-09 | Gobernación de Prueba | 800000001-1 | Distribuidora Ficticia S.A.S. | 11500000 | Grandes Superficies | Emitida |
  | 445566 | 2025-09-30 | Alcaldía de Ensayo | 890000002-2 | Comercializadora Demo Ltda. | 6900000 | Grandes Superficies | Emitida |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-03, RN-04, RN-06, RN-10 | QA-01 |
| Escenario 2 / RN-05 | QA-02 |
| Escenario 3 / RN-05 | QA-03 |
| Escenario 4 / RN-07 | QA-04 |
| Escenario 5 / RN-08 | QA-05 |
| Escenario 6 / RN-11 | QA-06 |
| Escenario 7 / RN-12 | QA-07 |
| Escenario 8 | QA-08 |
| Escenario 9 | QA-01, QA-09 |
| RN-02 (campo inexistente) | QA-10 |
| RN-09 | QA-11 |
| RN-13 | QA-12 |
| RN-11 (concurrencia) | QA-13 |

---

## Casos de Prueba

### QA-01: Relación exitosa con datos de entidad, proveedor y fecha

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-03, RN-04, RN-06, RN-10
- **Pasos:**
  1. Ejecutar la carga de órdenes TVEC.
- **Resultado esperado:** la API recibe solo consultas por los números 112233, 445566 y 999001 (no por el dataset completo). Orden 112233 guardada con `url_referencia = https://www.datos.gov.co/resource/rgxm-mmea.json?identificador_de_la_orden=112233`. row-aaa1 y row-aaa2 quedan "Relacionado", `entidad_nombre = Gobernación de Prueba`, `entidad_nit = 800000001-1`, `proveedor_nombre = Distribuidora Ficticia S.A.S.`, `fecha_compra = 2024-05-10`, `id_entidad_origen = 701`.

### QA-02: Orden no encontrada y reintento posterior

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-05
- **Pasos:**
  1. Ejecutar la carga (999001 no existe en la API).
  2. Agregar a la API la orden 999001 (fecha 2026-02-01, entidad "Hospital de Prueba") y volver a ejecutar.
- **Resultado esperado:** (1) row-aaa4 queda "Orden no encontrada", `fecha_compra = 2026-02-01`, `id_entidad_origen = 905`. (2) La segunda ejecución consulta 999001 y row-aaa4 queda "Relacionado" con entidad "Hospital de Prueba".

### QA-03: Ítem sin número de orden

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-05
- **Pasos:**
  1. Ejecutar la carga.
- **Resultado esperado:** row-aaa5 queda "Sin número de orden"; ninguna consulta a la API lo incluye; su `fecha_compra = 2026-03-15`.

### QA-04: Tolerancia de fecha en los límites

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | row-aaa3 fecha_item vs fecha_orden 445566 | 2025-11-20 vs 2025-09-30 | 51 días → inconsistente |
  | Diferencia | 31 días | límite → Relacionado |
  | Diferencia | 32 días | límite + 1 → inconsistente |
  | fecha_orden | (nula) | no se evalúa → Relacionado |

- **Pasos:**
  1. Ejecutar la carga con cada variante de fecha de la orden.
- **Resultado esperado:** con 51 y 32 días: "Relación inconsistente", motivo "La fecha del ítem difiere de la fecha de la orden en {n} días", `fecha_compra` = fecha del ítem y entidad/proveedor de la orden. Con 31 días y con fecha nula: "Relacionado".

### QA-05: Orden duplicada en la fuente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | 112233 registro A :updated_at | 2024-05-11T08:00:00 | entidad Gobernación de Prueba |
  | 112233 registro B :updated_at | 2024-06-01T10:00:00 | entidad Gobernación de Prueba |
  | 112233 registro C (variante) | 2024-06-02T10:00:00 | entidad Municipio Distinto |

- **Pasos:**
  1. Ejecutar con A y B.
  2. Ejecutar con A, B y C.
- **Resultado esperado:** (1) se conserva B; A cuenta como rechazada "Orden duplicada en la fuente"; ítems "Relacionado". (2) Se conserva C; A y B rechazadas; row-aaa1 y row-aaa2 "Relación inconsistente" con "La orden tiene más de un registro con entidades distintas en la fuente".

### QA-06: Actualización incremental de una orden

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-11
- **Precondiciones:** QA-01 ejecutado; marca de agua 2026-10-01T03:00:00.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | 112233.proveedor | Distribuidora Ficticia Dos S.A.S. | :updated_at 2026-10-01T20:00:00 |

- **Pasos:**
  1. Ejecutar la carga programada a las 03:00 del 2026-10-02.
- **Resultado esperado:** orden "Actualizada"; row-aaa1 y row-aaa2 con el nuevo proveedor; marca de agua 2026-10-01T20:00:00.

### QA-07: Falla persistente y error no recuperable

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-12
- **Pasos:**
  1. Inyectar tiempo de espera agotado permanente en el segundo lote.
  2. Repetir con HTTP 401 en la primera consulta.
- **Resultado esperado:** (1) 4 intentos con esperas 2, 4 y 8 s, "Fallida", lo escrito del primer lote se conserva, la marca de agua no cambia y los ítems no relacionados conservan "Pendiente". (2) Un solo intento y "Fallida".

### QA-08: Sin pendientes ni cambios

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 8
- **Precondiciones:** todos los ítems "Relacionado" y sin órdenes modificadas.
- **Pasos:**
  1. Ejecutar la carga.
- **Resultado esperado:** "Exitosa", contadores en 0, mensaje "No hay órdenes TVEC pendientes de relacionar ni modificadas."

### QA-09: Indicador de relación de la ejecución

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Pasos:**
  1. Ejecutar la carga con los datos base (row-aaa3 con orden de fecha 2025-09-30).
- **Resultado esperado:** "Ítems relacionados: 2 de 5 (40 %). Orden no encontrada: 1. Sin número de orden: 1. Relación inconsistente: 1."

### QA-10: Campo mapeado inexistente en la fuente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Pasos:**
  1. Quitar `agregacion` de todas las órdenes de la API y ejecutar.
- **Resultado esperado:** órdenes guardadas con `instrumento_agregacion` nulo; una sola advertencia "El campo agregacion no existe en el dataset rgxm-mmea"; la ejecución termina "Exitosa".

### QA-11: Orden sin identificador

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Pasos:**
  1. Incluir en la respuesta una orden con `identificador_de_la_orden` vacío.
- **Resultado esperado:** rechazada con "Identificador de origen ausente"; no se guarda.

### QA-12: Re-ejecución sin duplicados

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Ejecutar la carga dos veces seguidas con los mismos datos.
- **Resultado esperado:** una sola orden 112233 y un solo vínculo por ítem; la segunda ejecución cuenta las órdenes como "Sin cambios".

### QA-13: Programada omitida por carga en curso

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-11
- **Pasos:**
  1. Mantener "En curso" una carga de ítems TVEC y llegar a las 03:00.
- **Resultado esperado:** la carga de órdenes se registra "Omitida".

---

**Total de casos:** 13
