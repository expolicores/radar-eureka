# Historia #003: Ingesta inicial e incremental de ítems de la TVEC

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Ingestar Órdenes de la TVEC  
**Prioridad:** Crítica  
**FRs relacionados:** FR-004, FR-002, FR-003, FR-008, FR-009

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** cargar desde la API oficial de datos.gov.co el histórico de ítems de órdenes de compra de la Tienda Virtual del Estado Colombiano (TVEC) relacionados con televisores y mantenerlo actualizado de forma incremental,  
**Para** contar con compras públicas que ya traen descripción, precio unitario y cantidad estructurados, que son la base principal del Benchmark 1.

## Descripción

La TVEC publica cada ítem comprado con su descripción, precio unitario, cantidad, total, fecha y orden de compra. Esta historia trae esos ítems desde el dataset oficial de ítems por la API Socrata de datos.gov.co, solo para los ítems cuya descripción cumple el **prefiltro de televisores**, dentro de la ventana histórica configurada, y luego los mantiene al día con cargas incrementales basadas en la fecha de última actualización del registro.

Cada ítem se guarda con su identificador de origen, la orden de compra, una referencia pública reproducible a la fuente y la fecha de corte. La carga no ejecuta extracción con IA (la TVEC no la necesita) ni clasificación: deja cada ítem en candidatura "Pendiente de marcación" para la HU-009. La relación con la orden y la entidad se resuelve en la HU-004.

Se inicia por comando (carga inicial) y por programación (incremental); no requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Carga inicial exitosa de ítems TVEC

- **Dado** que la configuración tiene el dataset de ítems `usqp-5nsn`, `fecha_inicio_historico = 2023-01-01` y los términos "TELEVISOR", "SMART TV" y "TV"
- **Cuando** el Administrador ejecuta el comando de carga inicial de la TVEC
- **Entonces** el sistema guarda cada ítem devuelto cuya `fecha` esté entre 2023-01-01 y la fecha de ejecución, con `id_origen_item`, `orden`, `descripcion_item`, `precio_unitario`, `cantidad`, `unidad_medida`, `valor_total_item`, `id_entidad_origen`, `url_referencia`, `fecha_corte`, `fecha_ingesta`, `id_ejecucion` y candidatura "Pendiente de marcación", y muestra "Carga inicial TVEC ítems finalizada. Leídos: {n}. Nuevos: {n}. Actualizados: {n}. Sin cambios: {n}. Rechazados: {n}."

### Escenario 2: Carga incremental de ítems nuevos o modificados

- **Dado** que existe una carga inicial "Exitosa" de ítems TVEC y su marca de agua es 2026-10-01T02:00:00
- **Cuando** se ejecuta la carga incremental programada
- **Entonces** se piden solo los ítems con fecha de actualización del registro posterior a la marca de agua menos el solape, se crean los nuevos, se actualizan los modificados, y la marca de agua avanza solo si la ejecución termina "Exitosa"

### Escenario 3: Ítem modificado en descripción

- **Dado** que un ítem guardado cambió su descripción en la fuente
- **Cuando** la carga incremental lo procesa
- **Entonces** se actualiza, se cuenta como "Actualizado", queda `actualizado_en_fuente = sí` y su candidatura vuelve a "Pendiente de marcación"; si cambió solo precio, cantidad, total o unidad de medida, se actualiza sin cambiar la candidatura

### Escenario 4: Ítem sin identificador, sin fecha o fuera de la ventana

- **Dado** que la API devuelve un ítem sin identificador de fila, con `fecha` nula, con formato no válido, anterior a `fecha_inicio_historico` o posterior a la fecha de ejecución
- **Cuando** se procesa el registro
- **Entonces** no se guarda, se cuenta como rechazado con el motivo "Identificador de origen ausente", "Fecha ausente", "Fecha con formato inválido" o "Fecha fuera de la ventana histórica", y la carga continúa

### Escenario 5: Mismo ítem con identificador de fila distinto

- **Dado** que la fuente republica un ítem ya guardado con un identificador de fila nuevo pero con la misma clave natural (orden, descripción normalizada, precio, cantidad, fecha y ocurrencia dentro de la orden)
- **Cuando** se procesa el registro
- **Entonces** no se crea un ítem nuevo: se actualiza el identificador de origen del ítem existente, se conserva el anterior en `ids_origen_anteriores` y se cuenta como "Actualizado"

### Escenario 6: Falla transitoria y persistente de la API

- **Dado** que una solicitud falla por tiempo de espera, HTTP 429 o HTTP 5xx
- **Cuando** el sistema reintenta hasta 3 veces con espera exponencial
- **Entonces** si se recupera, la página se procesa sin duplicados; si no, la ejecución queda "Fallida", lo ya escrito se conserva, la marca de agua no avanza y se muestra "La carga TVEC ítems falló en la página {n}: {detalle}. Puede volver a ejecutarla; los registros ya cargados no se duplicarán."

### Escenario 7: Error no recuperable

- **Dado** que la API responde HTTP 400, 401, 403 o 404
- **Cuando** se recibe la respuesta
- **Entonces** no se reintenta, la ejecución queda "Fallida" y se muestra "La API de datos.gov.co rechazó la consulta (HTTP {código}). Verifique el identificador del dataset, la consulta y el app token."

### Escenario 8: Incremental sin carga inicial

- **Dado** que no existe una carga inicial "Exitosa" de ítems TVEC
- **Cuando** se dispara la incremental
- **Entonces** se registra "Omitida" y se muestra "No existe una carga inicial exitosa de ítems TVEC. Ejecute primero la carga inicial."

### Escenario 9: Ejecución concurrente

- **Dado** que hay una carga de ítems TVEC "En curso"
- **Cuando** se intenta iniciar otra (manual o programada)
- **Entonces** la manual se rechaza con "Ya existe una carga en curso para TVEC ítems (ejecución {id_ejecucion}). Espere a que termine." y la programada se registra "Omitida"

### Escenario 10: Fuente sin registros

- **Dado** que la consulta no devuelve ítems
- **Cuando** termina la ejecución
- **Entonces** queda "Exitosa" con contadores en 0, la marca de agua no cambia y se muestra "La fuente no devolvió ítems TVEC para la ventana y el prefiltro configurados."

### Escenario 11: Dataset alterno configurado

- **Dado** que el Administrador configura el dataset de ítems `3hdv-smhz` con su mapeo de campos
- **Cuando** se ejecuta la carga
- **Entonces** el sistema usa ese dataset con el mismo procesamiento, guarda el dataset de origen en cada ítem y deja `id_entidad_origen` nulo cuando la fuente traiga la entidad como "No definido"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO). La incremental la ejecuta el sistema por programación.
- **Permisos requeridos:** rol Administrador para ejecutar y configurar.
- **Valor de negocio:** la TVEC aporta ~1.150 líneas de televisores (2023–2026) con precio unitario estructurado, sin costo de IA; es la base principal del Benchmark 1 y de la comparación de mismo modelo.

### Reglas de Negocio

- **RN-01 Fuente:** API SODA `https://www.datos.gov.co/resource/{dataset}.json`. Dataset de ítems configurable (valor inicial: `usqp-5nsn`, porque incluye `id_entidad`; alternativa admitida: `3hdv-smhz`). Sin scraping de la tienda.
- **RN-02 Mapeo de campos (configurable por dataset):** valor inicial para `usqp-5nsn`:

  | Campo origen | Campo interno | Tipo |
  |---|---|---|
  | `:id` (identificador de fila Socrata) | `id_origen_item` | Texto (obligatorio) |
  | `:updated_at` (fecha de actualización de fila Socrata) | `ultima_actualizacion_fuente` | Fecha y hora |
  | `orden` | `orden` | Texto |
  | `fecha` | `fecha_item` | Fecha (obligatorio) |
  | `item` | `descripcion_item` | Texto |
  | `precio` | `precio_unitario` | Decimal COP, 2 decimales |
  | `cantidad` | `cantidad` | Decimal, hasta 4 decimales |
  | `unidad_de_medida` | `unidad_medida` | Texto |
  | `total` | `valor_total_item` | Decimal COP, 2 decimales |
  | `id_entidad` | `id_entidad_origen` | Texto |

  Para `3hdv-smhz` el mapeo inicial es `orden_de_compra`→`orden`, `price`→`precio_unitario`, `qty`→`cantidad`, `line_total`→`valor_total_item`, y no trae `id_entidad`. La consulta solicita explícitamente los campos de sistema `:id` y `:updated_at`.
- **RN-03 Lista blanca:** solo se conservan los campos del mapeo. Todo otro campo se descarta en memoria y no se persiste ni se registra en logs. La respuesta cruda no se persiste.
- **RN-04 Prefiltro:** `upper(item)` contiene alguno de los términos configurados (valor inicial: "TELEVISOR", "SMART TV", "TV"). La marcación precisa la hace la HU-009; cada ítem queda con candidatura "Pendiente de marcación".
- **RN-05 Ventana:** `fecha` ≥ `fecha_inicio_historico` (configurable, valor inicial 2023-01-01, el mismo parámetro de SECOP II) y ≤ fecha de ejecución.
- **RN-06 Clave y deduplicación:** `id_origen_item` es la clave de origen. Además se calcula una clave natural: `orden` + `descripcion_item` normalizada (mayúsculas, sin tildes, espacios colapsados) + `precio_unitario` + `cantidad` + `fecha_item` + número de ocurrencia de esa combinación dentro de la orden (1, 2…). Si llega un `id_origen_item` desconocido con una clave natural existente, se trata como el mismo ítem (Escenario 5).
- **RN-07 Resultado por registro:** nuevo → "Nuevo"; existente con algún campo mapeado distinto → "Actualizado" con `actualizado_en_fuente = sí`; si cambió `descripcion_item`, además candidatura "Pendiente de marcación"; sin diferencias → "Sin cambios" (se actualizan solo `ultima_actualizacion_fuente`, `fecha_corte` e `id_ejecucion`).
- **RN-08 Rechazos propios:** `id_origen_item` nulo ("Identificador de origen ausente"); `fecha` nula ("Fecha ausente"), no interpretable como ISO 8601 ("Fecha con formato inválido") o fuera de la ventana ("Fecha fuera de la ventana histórica"). Un ítem ya guardado no se borra por un rechazo. Las validaciones de calidad de precio, cantidad y total se aplican en la HU-005.
- **RN-09 Trazabilidad:** cada ítem guarda `dataset_origen`, `id_origen_item`, `orden` y `url_referencia` = `https://www.datos.gov.co/resource/{dataset}.json?orden={orden}` (o con el campo de orden del dataset alterno). Si `orden` es nula, `url_referencia` = `https://www.datos.gov.co/resource/{dataset}.json?$where=:id='{id_origen_item}'`.
- **RN-10 Fecha de corte:** `rowsUpdatedAt` de `https://www.datos.gov.co/api/views/{dataset}.json` convertido a America/Bogota; si no está disponible, fecha y hora de inicio con `fecha_corte_aproximada = sí`.
- **RN-11 Incremental:** requiere carga inicial "Exitosa" (si no, "Omitida"). Consulta `:updated_at` > (marca de agua − solape) con el prefiltro y la ventana. Solape configurable, entero 0–168 h (valor inicial: 24). La marca de agua es la mayor `:updated_at` procesada y solo avanza con ejecución "Exitosa". Frecuencia configurable en horas enteras de 1 a 168 (valor inicial: 24, diaria) con hora de referencia 02:30 America/Bogota (configurable); valor inválido → "La frecuencia de ingesta debe ser un número entero de horas entre 1 y 168" y se conserva el anterior.
- **RN-12 Paginación e idempotencia:** orden `:id` ascendente, página configurable (valor inicial: 1.000). Ningún ítem se duplica por reintentos o re-ejecuciones.
- **RN-13 Reintentos:** tiempo de espera (valor inicial 60 s), HTTP 429 o 5xx → hasta 3 reintentos (configurable) con esperas 2, 4 y 8 s (valores iniciales). HTTP 400, 401, 403, 404 → sin reintento, "Fallida".
- **RN-14 App token:** encabezado `X-App-Token` desde secreto o variable de entorno; si falta, advertencia "Ejecución sin app token: la API puede aplicar límites más estrictos".
- **RN-15 Exclusión mutua:** una sola ejecución de ítems TVEC "En curso"; abandono tras 6 horas sin actividad (configurable).
- **RN-16 Separación:** la ingesta no ejecuta extracción con IA ni clasificación, y nunca elimina ítems guardados.
- **RN-17 Estados y tipos:** tipos "Inicial", "Incremental programada", "Incremental manual"; estados "En curso", "Exitosa", "Fallida", "Omitida".

### Interfaz

No requiere interfaz gráfica: comando para la carga inicial y la incremental manual; programación por configuración. Resumen final en consola o log como en el Escenario 1, con estado y marca de agua.

### Sistemas Externos (Si aplica)

- **API Socrata de datos.gov.co**, datasets TVEC `usqp-5nsn` (inicial) o `3hdv-smhz` (alterno), JSON y SoQL; metadatos en `/api/views/{dataset}.json`. Proveedor: Colombia Compra Eficiente. App token opcional.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-004 (órdenes TVEC y relación ítem ↔ orden ↔ entidad), HU-005 (validaciones de calidad), HU-006 (bitácora), HU-009 (marcación de candidatos TVEC).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El PRD nombra dos datasets de ítems (`usqp-5nsn` / `3hdv-smhz`) con el mismo contenido → resuelto: `usqp-5nsn` por defecto (trae entidad), `3hdv-smhz` como alterno configurable (RN-01).
- Los datasets TVEC no documentan un campo de fecha de actualización del negocio → resuelto con el campo de sistema `:updated_at` de Socrata (RN-02, RN-11).
- El identificador de fila podría cambiar si la fuente republica el dataset → resuelto con clave natural de deduplicación (RN-06).
- La TVEC no publica una URL pública por ítem → resuelto con una referencia reproducible a la API oficial (RN-09).
- La ventana histórica de 3 años de FR-002 se aplica también a la TVEC, con el mismo parámetro (RN-05).

---

## Validación INVEST

- [x] **Independiente:** Esta HU puede implementarse sin dependencias bloqueantes de otras HU
- [x] **Negociable:** Describe QUÉ se necesita, no CÓMO implementarlo (detalles técnicos son negociables)
- [x] **Valiosa:** Aporta valor tangible al negocio o usuario final (beneficio claro)
- [x] **Estimable:** El equipo puede estimar esfuerzo (scope claro, no ambiguo)
- [x] **Pequeña:** Completable en pocos días/persona (no excede 1 sprint)
- [x] **Testeable:** Criterios de aceptación permiten verificar cuándo está terminada

## Validación Anti-Ambigüedad

- [x] **Auto-contenida:** Un desarrollador puede implementar esta HU leyendo SOLO este archivo
- [x] **Reglas completas:** Todas las reglas de negocio incluyen formatos, rangos, límites y comportamiento ante nulos
- [x] **Errores explícitos:** El comportamiento ante cada tipo de error está documentado (mensaje, acción, redirección)
- [x] **Edge cases cubiertos:** Criterios de aceptación incluyen casos borde y estados vacíos
- [x] **Supuestos resueltos:** No quedan supuestos pendientes de validación
- [x] **Datos claros:** Origen, formato y proveedor de cada dato están especificados

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes de usuario implementados
- [ ] Pruebas funcionales pasando

---

## Registro de Cambios

| Fecha | Versión | Descripción | Autor |
|-------|---------|-------------|-------|
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-001 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
