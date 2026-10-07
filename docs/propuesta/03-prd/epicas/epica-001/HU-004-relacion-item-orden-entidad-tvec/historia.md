# Historia #004: Relacionar cada ítem TVEC con su orden de compra, entidad y fecha

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Ingestar Órdenes de la TVEC  
**Prioridad:** Crítica  
**FRs relacionados:** FR-004, FR-005, FR-003, FR-008, FR-009

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** traer las órdenes de compra de la TVEC a las que pertenecen los ítems de televisor ingeridos y relacionar cada ítem con su orden, su entidad compradora y su fecha,  
**Para** que cada compra de la TVEC pueda compararse y mostrarse con su contexto (quién compró, a quién y cuándo) y trazarse hasta la fuente oficial.

## Descripción

Los ítems de la TVEC (HU-003) traen el número de orden, pero el detalle de la orden (entidad compradora, proveedor, valor total, instrumento de agregación) está en el dataset de **Consolidado de órdenes** (`rgxm-mmea`). La relación `ítem.orden ↔ orden.identificador_de_la_orden` **no fue verificada** en el spike D1, por lo que esta historia la establece con reglas explícitas y deja visible el estado de la relación de cada ítem.

El sistema solo consulta las órdenes referenciadas por ítems ya guardados (no el dataset completo), las actualiza de forma incremental y vuelve a intentar la relación de los ítems cuya orden aún no se encuentra. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Relación exitosa ítem ↔ orden ↔ entidad

- **Dado** que existen ítems TVEC guardados con `orden = 112233` y la API de órdenes devuelve la orden con `identificador_de_la_orden = 112233`
- **Cuando** se ejecuta la carga de órdenes TVEC
- **Entonces** la orden se guarda con su identificador, fecha, entidad, NIT de la entidad, proveedor, valor total, agregación, estado, URL de referencia, fecha de corte e id de ejecución, y cada ítem de esa orden queda con `estado_relacion = Relacionado`, `entidad_nombre`, `entidad_nit`, `proveedor_nombre`, `fecha_compra` (la fecha del ítem) y el vínculo a la orden

### Escenario 2: Orden no encontrada

- **Dado** que un ítem tiene `orden = 999001` y la API no devuelve ninguna orden con ese identificador
- **Cuando** termina la carga de órdenes
- **Entonces** el ítem queda con `estado_relacion = Orden no encontrada`, conserva `id_entidad_origen` y `fecha_compra` desde el propio ítem, y la siguiente ejecución vuelve a buscar su orden

### Escenario 3: Ítem sin número de orden

- **Dado** que un ítem guardado tiene `orden` nula o vacía
- **Cuando** se ejecuta la carga de órdenes
- **Entonces** el ítem queda con `estado_relacion = Sin número de orden`, no se consulta la API por él y su fecha y entidad provienen solo del ítem

### Escenario 4: Fecha del ítem inconsistente con la orden

- **Dado** que la fecha del ítem difiere de la fecha de la orden en más de 31 días
- **Cuando** se relaciona el ítem
- **Entonces** el ítem queda con `estado_relacion = Relación inconsistente`, motivo "La fecha del ítem difiere de la fecha de la orden en {n} días", conserva la fecha del ítem como `fecha_compra` y los datos de entidad y proveedor de la orden

### Escenario 5: Más de una orden con el mismo identificador

- **Dado** que la API devuelve dos o más registros con el mismo `identificador_de_la_orden`
- **Cuando** se procesa la respuesta
- **Entonces** se conserva el registro con la fecha de actualización de fila más reciente, los demás se cuentan como rechazados con el motivo "Orden duplicada en la fuente", y si los registros difieren en entidad, los ítems de esa orden quedan "Relación inconsistente" con el motivo "La orden tiene más de un registro con entidades distintas en la fuente"

### Escenario 6: Actualización incremental de órdenes

- **Dado** que una orden ya guardada cambió en la fuente (ej. su estado) después de la marca de agua menos el solape
- **Cuando** se ejecuta la carga de órdenes
- **Entonces** la orden se actualiza, se cuenta como "Actualizada", sus ítems relacionados reciben los nuevos datos de entidad y proveedor, y la marca de agua avanza solo si la ejecución termina "Exitosa"

### Escenario 7: Falla de la API de órdenes

- **Dado** que la API falla de forma persistente después de 3 reintentos con espera exponencial
- **Cuando** se agotan los reintentos
- **Entonces** la ejecución queda "Fallida", las órdenes y relaciones ya escritas se conservan, la marca de agua no avanza y los ítems sin relacionar conservan su estado para la siguiente ejecución; ante HTTP 400, 401, 403 o 404 no se reintenta

### Escenario 8: No hay ítems pendientes ni órdenes modificadas

- **Dado** que todos los ítems están relacionados y ninguna orden cambió
- **Cuando** se ejecuta la carga de órdenes
- **Entonces** termina "Exitosa" con contadores en 0 y se muestra "No hay órdenes TVEC pendientes de relacionar ni modificadas."

### Escenario 9: Indicador de relación de la ejecución

- **Dado** que la carga de órdenes terminó
- **Cuando** se escribe el resumen
- **Entonces** el resumen muestra "Ítems relacionados: {n} de {total} ({porcentaje} %). Orden no encontrada: {n}. Sin número de orden: {n}. Relación inconsistente: {n}."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO); el sistema ejecuta la carga programada.
- **Permisos requeridos:** rol Administrador para ejecución manual y configuración.
- **Valor de negocio:** sin entidad y fecha confiables, una compra TVEC no puede filtrarse, compararse en la ventana temporal ni mostrarse con contexto al Analista.

### Reglas de Negocio

- **RN-01 Fuente:** API SODA `https://www.datos.gov.co/resource/{dataset}.json`, dataset de órdenes configurable (valor inicial: `rgxm-mmea`).
- **RN-02 Mapeo de campos (configurable; valor inicial):** `:id` → `id_origen_orden`; `:updated_at` → `ultima_actualizacion_fuente`; `identificador_de_la_orden` → `orden` (obligatorio); `fecha` → `fecha_orden`; `entidad` → `entidad_nombre`; `nit_entidad` → `entidad_nit`; `proveedor` → `proveedor_nombre`; `total` → `valor_total_orden` (decimal COP, 2 decimales); `agregacion` → `instrumento_agregacion`; `estado` → `estado_orden`. Solo se persisten los campos del mapeo; los demás se descartan en memoria. Si un campo mapeado no existe en la fuente, se guarda nulo y la ejecución registra una sola advertencia por campo: "El campo {campo} no existe en el dataset {dataset}".
- **RN-03 Órdenes a consultar:** (a) los números de orden de ítems con `estado_relacion` "Pendiente" u "Orden no encontrada"; (b) las órdenes ya guardadas con `:updated_at` > (marca de agua − solape). Las consultas por número se hacen en lotes (valor inicial: 100 identificadores por consulta). No se consulta el dataset completo.
- **RN-04 Comparación de identificadores:** `ítem.orden` y `orden.identificador_de_la_orden` se comparan como texto, sin espacios al inicio ni al final; no se eliminan ceros ni otros caracteres.
- **RN-05 Estados de relación del ítem:** "Pendiente" (estado inicial de todo ítem nuevo), "Relacionado", "Orden no encontrada", "Sin número de orden", "Relación inconsistente". El estado se recalcula en cada ejecución para los ítems afectados.
- **RN-06 Datos que recibe el ítem relacionado:** `entidad_nombre`, `entidad_nit` y `proveedor_nombre` de la orden; `fecha_compra` = `fecha_item` del ítem (si fuera nula, `fecha_orden`); vínculo a la orden. `id_entidad_origen` del ítem se conserva siempre.
- **RN-07 Inconsistencia de fecha:** si |`fecha_item` − `fecha_orden`| > tolerancia configurable en días (valor inicial: 31) → "Relación inconsistente" con el motivo del Escenario 4. Si alguna de las dos fechas es nula, no se evalúa.
- **RN-08 Orden duplicada:** regla del Escenario 5.
- **RN-09 Rechazo de órdenes:** orden con `identificador_de_la_orden` nulo o vacío → rechazada con "Identificador de origen ausente".
- **RN-10 Trazabilidad:** cada orden guarda `id_origen_orden`, `dataset_origen`, `url_referencia` = `https://www.datos.gov.co/resource/{dataset}.json?identificador_de_la_orden={orden}`, `fecha_corte` (de `rowsUpdatedAt` de `/api/views/{dataset}.json`; si no está disponible, inicio de la ejecución con `fecha_corte_aproximada = sí`), `fecha_ingesta` e `id_ejecucion`.
- **RN-11 Incremental y programación:** solape configurable entero 0–168 h (valor inicial: 24); marca de agua = mayor `:updated_at` procesada, avanza solo con ejecución "Exitosa"; programación configurable (valor inicial: diaria, 03:00 America/Bogota, después de la carga de ítems). Si hay una carga de ítems TVEC o de órdenes "En curso", la ejecución programada se registra "Omitida".
- **RN-12 Reintentos:** tiempo de espera (valor inicial 60 s), HTTP 429 o 5xx → hasta 3 reintentos (configurable) con esperas 2, 4 y 8 s; HTTP 400, 401, 403 y 404 sin reintento.
- **RN-13 Idempotencia:** clave de la orden = `orden`; re-ejecuciones no duplican órdenes ni vínculos.
- **RN-14 App token:** encabezado `X-App-Token` desde secreto; si falta, advertencia "Ejecución sin app token: la API puede aplicar límites más estrictos".
- **RN-15 Separación:** esta carga no ejecuta extracción con IA ni clasificación y no elimina órdenes ni ítems.

### Interfaz

No requiere interfaz gráfica. Comando "carga de órdenes TVEC" y programación por configuración. El resumen del Escenario 9 se escribe en consola o log junto con "Órdenes nuevas: {n}. Actualizadas: {n}. Sin cambios: {n}. Rechazadas: {n}."

### Sistemas Externos (Si aplica)

- **API Socrata de datos.gov.co**, dataset TVEC Consolidado de órdenes `rgxm-mmea` (JSON, SoQL) y metadatos `/api/views/rgxm-mmea.json`. Proveedor: Colombia Compra Eficiente.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-003 (ingesta de ítems TVEC), HU-006 (bitácora de ejecuciones).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La relación ítem ↔ orden no está verificada (D1) → resuelto con estados de relación explícitos y reintento (RN-05, RN-03), e indicador de relación por ejecución (Escenario 9).
- Los nombres de campos del dataset de órdenes no están confirmados → resuelto con mapeo configurable y advertencia por campo inexistente (RN-02).
- La fecha de la compra TVEC es la fecha del ítem; la de la orden solo valida coherencia → resuelto en RN-06 y RN-07 (tolerancia inicial 31 días, configurable).
- Solo se consultan las órdenes referenciadas por ítems ingeridos → resuelto en RN-03.

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
