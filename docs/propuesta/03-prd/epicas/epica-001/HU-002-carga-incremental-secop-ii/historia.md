# Historia #002: Carga incremental periódica de contratos SECOP II

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Ingestar Contratos SECOP II  
**Prioridad:** Crítica  
**FRs relacionados:** FR-003, FR-006, FR-008, FR-009

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema traiga automáticamente, con la frecuencia configurada, solo los contratos SECOP II nuevos o modificados desde la última carga exitosa,  
**Para** mantener el universo de televisores actualizado sin reprocesar todo el histórico ni disparar de nuevo la extracción con IA de documentos ya procesados.

## Descripción

Después de la carga inicial, el universo SECOP II se mantiene al día con cargas incrementales programadas. Cada carga usa la **fecha de última actualización del registro** (`ultima_actualizacion`) para pedir a la API de datos.gov.co solo los contratos que cambiaron desde la última carga exitosa (marca de agua), con un solape de seguridad para no perder registros publicados con retraso.

La carga incremental aplica las mismas protecciones de la carga inicial: lista blanca de campos (los campos personales sensibles nunca se persisten), identificador de origen y URL pública, fecha de corte, reintentos y escritura idempotente.

La ingesta está **separada** del procesamiento documental: actualizar un contrato no descarga documentos, no ejecuta extracción con IA y no modifica ítems ya extraídos ni clasificaciones existentes. Solo deja marcado que el contrato cambió en la fuente y, si cambiaron los campos que definen la candidatura, lo devuelve a "Pendiente de marcación" para que la HU-008 lo reevalúe.

---

## Criterios de Aceptación

### Escenario 1: Carga incremental programada con contratos nuevos

- **Dado** que existe una carga inicial "Exitosa", la marca de agua es 2026-10-01T02:00:00 y la frecuencia configurada es cada 24 horas a las 02:00 (America/Bogota)
- **Cuando** llega la hora programada y la API devuelve 2 contratos que cumplen el prefiltro con `ultima_actualizacion` posterior a la marca de agua menos el solape
- **Entonces** el sistema guarda los 2 contratos como nuevos, con candidatura "Pendiente de marcación", `fecha_corte`, `fecha_ingesta` e `id_ejecucion`, termina en estado "Exitosa" y mueve la marca de agua a la mayor `ultima_actualizacion` procesada

### Escenario 2: Contrato existente modificado en campos de candidatura

- **Dado** que el contrato CO1.PCCNTR.5000001 ya existe y la fuente cambió su `objeto_del_contrato`
- **Cuando** se ejecuta la carga incremental
- **Entonces** el contrato se actualiza, se cuenta como "Actualizado", queda con `actualizado_en_fuente = sí` y la fecha de detección, y su candidatura vuelve a "Pendiente de marcación"; su clasificación, documentos e ítems extraídos no se modifican

### Escenario 3: Contrato modificado en campos que no afectan la candidatura

- **Dado** que la fuente cambió solo `estado_contrato` o `fecha_de_fin_del_contrato` de un contrato existente
- **Cuando** se ejecuta la carga incremental
- **Entonces** el contrato se actualiza y se cuenta como "Actualizado", queda con `actualizado_en_fuente = sí`, y su candidatura y clasificación se mantienen

### Escenario 4: Contrato con nueva fecha de actualización sin cambios en campos permitidos

- **Dado** que la fuente devuelve un contrato con `ultima_actualizacion` más reciente pero todos sus campos permitidos son iguales a los guardados
- **Cuando** se ejecuta la carga incremental
- **Entonces** se actualizan solo `ultima_actualizacion_fuente`, `fecha_corte` e `id_ejecucion`, y el contrato se cuenta como "Sin cambios"

### Escenario 5: Contrato que deja de cumplir el prefiltro

- **Dado** que un contrato guardado fue modificado en la fuente y ya no contiene el UNSPSC `V1.52161505` ni los términos de texto
- **Cuando** se ejecuta la carga incremental
- **Entonces** el sistema lo obtiene mediante la consulta de seguimiento por identificador, lo actualiza y deja su candidatura en "Pendiente de marcación"; el contrato no se elimina

### Escenario 6: No existe carga inicial exitosa

- **Dado** que no hay ninguna ejecución "Exitosa" de carga inicial de SECOP II
- **Cuando** se dispara la carga incremental (programada o manual)
- **Entonces** la carga no se ejecuta, se registra como "Omitida" y se muestra "No existe una carga inicial exitosa de SECOP II. Ejecute primero la carga inicial."

### Escenario 7: Falla de la API durante la carga incremental

- **Dado** que la API falla de forma persistente después de 3 reintentos con espera exponencial
- **Cuando** se agotan los reintentos
- **Entonces** la ejecución queda "Fallida", la marca de agua **no** avanza, los contratos ya escritos se conservan y la siguiente ejecución vuelve a pedir desde la misma marca de agua sin duplicar contratos

### Escenario 8: Registros del solape ya procesados

- **Dado** que el solape de 24 horas trae contratos que ya se procesaron en la ejecución anterior sin cambios posteriores
- **Cuando** se ejecuta la carga incremental
- **Entonces** esos contratos se cuentan como "Sin cambios" y no se duplican

### Escenario 9: Ejecución programada con otra carga en curso

- **Dado** que hay una carga de SECOP II en estado "En curso"
- **Cuando** llega la hora programada de la carga incremental
- **Entonces** la carga programada no inicia y se registra como "Omitida" con el motivo "Ejecución en curso: {id_ejecucion}"

### Escenario 10: Sin cambios en la fuente

- **Dado** que la API no devuelve contratos modificados desde la marca de agua menos el solape
- **Cuando** se ejecuta la carga incremental
- **Entonces** la ejecución termina "Exitosa" con todos los contadores en 0 y la marca de agua no cambia

### Escenario 11: La actualización no dispara reprocesamiento con IA

- **Dado** que un contrato tiene documentos ya descargados e ítems ya extraídos con IA
- **Cuando** la carga incremental actualiza ese contrato
- **Entonces** no se crea ninguna solicitud de descarga de documentos ni de extracción con IA, y los ítems extraídos permanecen iguales

### Escenario 12: Cambio de frecuencia válido e inválido

- **Dado** que el Administrador cambia la frecuencia de la carga incremental
- **Cuando** el nuevo valor es un número entero de horas entre 1 y 168
- **Entonces** la siguiente ejecución se programa con la nueva frecuencia; y **cuando** el valor está fuera de ese rango, no es entero o está vacío, la configuración se rechaza con "La frecuencia de ingesta debe ser un número entero de horas entre 1 y 168" y se conserva la frecuencia anterior

### Escenario 13: Ejecución manual de la carga incremental

- **Dado** que existe una carga inicial "Exitosa" y no hay ejecuciones en curso
- **Cuando** el Administrador ejecuta por comando la carga incremental de SECOP II
- **Entonces** se ejecuta con las mismas reglas que la programada, con tipo "Incremental manual", y no altera la programación siguiente

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO). La carga programada la ejecuta el sistema.
- **Permisos requeridos:** rol Administrador para ejecutar manualmente o cambiar la frecuencia.
- **Valor de negocio:** cumple que un contrato nuevo esté disponible en ≤ 48 horas (NFR-DAT-002, objetivo inicial de ingeniería) y mantiene vigentes los datos que ve el Analista, a bajo costo, porque no reprocesa el histórico ni la IA.

### Reglas de Negocio

- **RN-01 Fuente:** API SODA `https://www.datos.gov.co/resource/{dataset}.json`, dataset configurable (valor inicial: `jbjy-vk9h`). Sin scraping del portal SECOP.
- **RN-02 Requisito previo:** solo se ejecuta si existe al menos una carga inicial de SECOP II con estado "Exitosa". Si no, la ejecución se registra "Omitida" (Escenario 6).
- **RN-03 Marca de agua:** fecha y hora (America/Bogota) igual a la mayor `ultima_actualizacion` procesada en la última ejecución "Exitosa" de SECOP II (inicial o incremental). Solo avanza cuando la ejecución termina "Exitosa". Si la ejecución no procesa registros, no cambia.
- **RN-04 Solape:** la consulta pide `ultima_actualizacion` > (marca de agua − solape). Solape configurable en horas, entero de 0 a 168 (valor inicial: 24).
- **RN-05 Consulta principal:** registros con `ultima_actualizacion` en el rango de RN-04 **y** `fecha_de_firma` ≥ `fecha_inicio_historico` (valor inicial: 2023-01-01) **y** prefiltro de televisores: `codigo_de_categoria_principal` = `V1.52161505`, o `objeto_del_contrato` o `descripcion_del_proceso` en mayúsculas contienen algún término configurado (valor inicial: "TELEVISOR", "SMART TV", "TV").
- **RN-06 Consulta de seguimiento:** registros con `ultima_actualizacion` en el rango de RN-04 cuyo `id_contrato` ya está guardado, consultados en lotes de identificadores (tamaño de lote configurable, valor inicial: 100). Sirve para actualizar contratos que dejaron de cumplir el prefiltro. Un contrato obtenido por ambas consultas se procesa una sola vez.
- **RN-07 Lista blanca y datos sensibles:** se conservan solo los campos de la lista blanca de la ingesta de SECOP II (`id_contrato`, `proceso_de_compra`, `referencia_del_contrato`, `nombre_entidad`, `nit_entidad`, `codigo_entidad`, `departamento`, `ciudad`, `proveedor_adjudicado`, `documento_proveedor`, `codigo_proveedor`, `objeto_del_contrato`, `descripcion_del_proceso`, `codigo_de_categoria_principal`, `modalidad_de_contratacion`, `tipo_de_contrato`, `estado_contrato`, `valor_del_contrato`, `fecha_de_firma`, `fecha_de_inicio_del_contrato`, `fecha_de_fin_del_contrato`, `urlproceso`, `ultima_actualizacion`). Todo otro campo, incluidos banco, tipo y número de cuenta y documentos de identidad de representantes legales, supervisores y ordenadores del gasto, se descarta en memoria y nunca se persiste ni se registra en logs. La respuesta cruda no se persiste.
- **RN-08 Clasificación del resultado por registro:**
  - `id_contrato` no existe → "Nuevo", candidatura "Pendiente de marcación".
  - Existe y algún campo permitido cambió → "Actualizado"; `actualizado_en_fuente = sí`; `fecha_actualizacion_detectada` = fecha y hora de la ejecución.
  - Existe y cambió `objeto_del_contrato`, `descripcion_del_proceso` o `codigo_de_categoria_principal` → además, candidatura "Pendiente de marcación".
  - Existe y ningún campo permitido cambió → "Sin cambios"; se actualizan solo `ultima_actualizacion_fuente`, `fecha_corte` e `id_ejecucion`.
  - `ultima_actualizacion` de la fuente anterior o igual a la guardada → "Sin cambios", sin escribir.
- **RN-09 Rechazos:** se rechaza (no se escribe) el registro con `id_contrato` nulo o vacío, `fecha_de_firma` nula, con formato no ISO 8601 o fuera de la ventana (anterior a `fecha_inicio_historico` o posterior a la fecha de ejecución), con los motivos "Identificador de origen ausente", "Fecha de firma ausente", "Fecha de firma con formato inválido" y "Fecha de firma fuera de la ventana histórica". Un contrato ya guardado nunca se borra por un rechazo: conserva su versión anterior.
- **RN-10 Fecha de corte:** se toma de `rowsUpdatedAt` de `https://www.datos.gov.co/api/views/{dataset}.json` al iniciar; si no está disponible, la fecha y hora de inicio con `fecha_corte_aproximada = sí`. Se escribe en cada contrato leído en la ejecución (nuevo, actualizado o sin cambios con fecha de actualización más reciente).
- **RN-11 URL e identificadores:** se conserva `id_contrato`, `proceso_de_compra` y `url_publica` (texto u objeto con propiedad `url`); URL nula → `sin_url_publica = sí`.
- **RN-12 Reintentos:** tiempo de espera agotado (valor inicial: 60 s), HTTP 429 o 5xx → hasta 3 reintentos (configurable) con espera exponencial (valores iniciales: 2, 4, 8 s). HTTP 400, 401, 403, 404 → sin reintento, ejecución "Fallida".
- **RN-13 Programación:** frecuencia configurable en horas enteras de 1 a 168 (valor inicial: 24, es decir, diaria) y hora de referencia configurable (valor inicial: 02:00 America/Bogota). Valor inválido → se rechaza y se conserva el anterior (Escenario 12).
- **RN-14 Exclusión mutua:** si hay una ejecución de SECOP II "En curso", la programada se registra "Omitida" y la manual se rechaza con "Ya existe una carga en curso para SECOP II (ejecución {id_ejecucion}). Espere a que termine."
- **RN-15 Separación de la extracción:** la carga no crea solicitudes de descarga de documentos ni de extracción con IA, no modifica ítems extraídos ni clasificaciones existentes.
- **RN-16 No eliminación:** la carga incremental nunca elimina contratos guardados, aunque dejen de cumplir el prefiltro.
- **RN-17 App token:** desde secreto o variable de entorno, encabezado `X-App-Token`; si falta, se ejecuta con advertencia "Ejecución sin app token: la API puede aplicar límites más estrictos".
- **RN-18 Tipos de ejecución y estados:** tipo "Incremental programada" o "Incremental manual"; estados "En curso", "Exitosa", "Fallida", "Omitida".

### Interfaz

No requiere interfaz gráfica. Programación por configuración; ejecución manual por comando. Al terminar se escribe en el log el resumen: "Carga incremental SECOP II {estado}. Leídos: {n}. Nuevos: {n}. Actualizados: {n}. Sin cambios: {n}. Rechazados: {n}. Marca de agua: {fecha}."

### Sistemas Externos (Si aplica)

- **API Socrata de datos.gov.co**, dataset `jbjy-vk9h` (JSON, SoQL) y metadatos `/api/views/jbjy-vk9h.json`. Proveedor: Colombia Compra Eficiente vía datos abiertos. App token opcional.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-001 (carga inicial SECOP II), HU-005 (validaciones de calidad), HU-006 (bitácora de ejecuciones), HU-008 (marcación de candidatos SECOP II).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Los registros pueden publicarse con retraso respecto a su `ultima_actualizacion` → resuelto con solape configurable (RN-04).
- Un contrato puede dejar de cumplir el prefiltro tras una modificación → resuelto con consulta de seguimiento por identificador (RN-06) y sin eliminación (RN-16).
- La hora de ejecución diaria → valor inicial configurable 02:00 America/Bogota (RN-13).
- Qué cambios de un contrato obligan a reevaluar la candidatura → solo objeto, descripción y UNSPSC principal (RN-08).

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
