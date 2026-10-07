# Historia #005: Validaciones de calidad en la ingesta y registro de rechazos

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Controlar Calidad y Trazabilidad de la Ingesta  
**Prioridad:** Crítica  
**FRs relacionados:** FR-010

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que cada registro de SECOP II y de la TVEC pase por un catálogo explícito de validaciones de calidad (campos obligatorios, formatos de fecha y valor, duplicados) y que los registros que no las cumplan queden registrados con su motivo,  
**Para** que el universo de análisis no contenga datos rotos y pueda saber qué se descartó, por qué y de qué fuente.

## Descripción

Las cargas de SECOP II (contratos) y de la TVEC (ítems y órdenes) reciben datos de la API de datos.gov.co que pueden venir incompletos, con formatos inválidos o repetidos. Esta historia define un **catálogo único de reglas de calidad** con dos severidades:

- **Rechazo:** el registro no se escribe (si ya existía, se conserva su versión anterior) y queda en el **registro de rechazos**.
- **Advertencia:** el registro se escribe, con el dato problemático en nulo cuando corresponde, y queda marcado con el código de la advertencia.

Las reglas se aplican en memoria, después de descartar los campos no permitidos, y antes de escribir. El Administrador puede consultar los rechazos y advertencias por ejecución, fuente y regla mediante consulta o script (no requiere interfaz gráfica).

---

## Criterios de Aceptación

### Escenario 1: Registro válido

- **Dado** que un contrato SECOP II o un ítem TVEC cumple todas las reglas del catálogo
- **Cuando** la carga lo procesa
- **Entonces** el registro se escribe sin códigos de advertencia y no aparece en el registro de rechazos

### Escenario 2: Campo obligatorio ausente con severidad Rechazo

- **Dado** que un registro llega sin un campo obligatorio de severidad Rechazo (ej. contrato sin `nombre_entidad`, ítem TVEC sin `precio`)
- **Cuando** la carga lo valida
- **Entonces** el registro no se escribe, se agrega al registro de rechazos con la fuente, la ejecución, el identificador de origen (si existe), el código de regla, el campo, el valor recibido y el motivo, y la carga continúa

### Escenario 3: Valor numérico inválido en un campo crítico de la TVEC

- **Dado** que un ítem TVEC trae `precio` o `cantidad` no numérico, igual a 0 o negativo
- **Cuando** la carga lo valida
- **Entonces** el ítem se rechaza con el motivo "Precio unitario no válido" o "Cantidad no válida"

### Escenario 4: Dato con problema de severidad Advertencia

- **Dado** que un contrato trae `valor_del_contrato` no numérico o negativo, o `fecha_de_fin_del_contrato` con formato inválido
- **Cuando** la carga lo valida
- **Entonces** el contrato se escribe con ese campo en nulo, con el código de la advertencia en `advertencias_calidad`, y la ejecución cuenta la advertencia

### Escenario 5: Total del ítem TVEC no coincide con precio × cantidad

- **Dado** que un ítem TVEC tiene `precio = 2.150.000`, `cantidad = 4` y `total = 8.800.000`
- **Cuando** la carga lo valida
- **Entonces** el ítem se escribe con todos sus valores tal como llegaron y con la advertencia CAL-TVI-08 "Total del ítem no coincide con precio × cantidad", porque la diferencia (200.000) supera la tolerancia

### Escenario 6: Duplicado dentro de una misma ejecución

- **Dado** que la misma ejecución recibe dos veces el mismo identificador de origen
- **Cuando** la carga lo valida
- **Entonces** se conserva la versión con la fecha de actualización de la fuente más reciente (si son iguales, la última recibida) y la otra se registra como rechazo con el motivo "Duplicado en la ejecución"

### Escenario 7: Nueva versión rechazada de un registro existente

- **Dado** que un contrato ya guardado llega en una carga incremental sin `fecha_de_firma`
- **Cuando** la carga lo valida
- **Entonces** la nueva versión se rechaza, el contrato conserva su versión anterior sin modificaciones y queda con `ultima_version_rechazada = sí` y la fecha del rechazo

### Escenario 8: Corrección posterior en la fuente

- **Dado** que un contrato tenía `ultima_version_rechazada = sí`
- **Cuando** una carga posterior recibe una versión que cumple todas las reglas de Rechazo
- **Entonces** el contrato se actualiza con la nueva versión y `ultima_version_rechazada` pasa a "no"; el rechazo anterior se conserva en el registro de rechazos

### Escenario 9: Consulta de rechazos y advertencias

- **Dado** que existen rechazos y advertencias de varias ejecuciones
- **Cuando** el Administrador consulta filtrando por fuente, ejecución, código de regla o rango de fechas
- **Entonces** obtiene la lista con fuente, ejecución, identificador de origen, código, campo, valor recibido, motivo y fecha, y el total por código de regla; si no hay resultados obtiene "No hay registros de calidad para los filtros indicados."

### Escenario 10: Los rechazos no guardan datos sensibles

- **Dado** que un registro rechazado traía campos no permitidos (ej. número de cuenta)
- **Cuando** se escribe en el registro de rechazos
- **Entonces** solo se guardan el campo validado y su valor si el campo pertenece a la lista de campos permitidos; ningún campo no permitido se registra

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO).
- **Permisos requeridos:** rol Administrador para consultar el registro de rechazos. El Analista no accede.
- **Valor de negocio:** evita comparaciones con datos rotos y permite explicar qué parte del universo se pierde por calidad de la fuente.

### Reglas de Negocio

- **RN-01 Orden de aplicación:** (1) descarte de campos no permitidos; (2) reglas de Rechazo; (3) reglas de Advertencia; (4) deduplicación de la ejecución; (5) escritura. Si un registro incumple varias reglas de Rechazo, se registra un rechazo por cada regla incumplida, pero el registro cuenta una sola vez en el contador de rechazados.
- **RN-02 Catálogo — Contratos SECOP II:**

  | Código | Regla | Severidad | Motivo |
  |---|---|---|---|
  | CAL-SEC-01 | `id_contrato` nulo o vacío | Rechazo | Identificador de origen ausente |
  | CAL-SEC-02 | `fecha_de_firma` nula | Rechazo | Fecha de firma ausente |
  | CAL-SEC-03 | `fecha_de_firma` no interpretable como fecha ISO 8601 | Rechazo | Fecha de firma con formato inválido |
  | CAL-SEC-04 | `fecha_de_firma` fuera de la ventana histórica (anterior a `fecha_inicio_historico` o posterior a la fecha de ejecución) | Rechazo | Fecha de firma fuera de la ventana histórica |
  | CAL-SEC-05 | `nombre_entidad` nulo o vacío | Rechazo | Entidad ausente |
  | CAL-SEC-06 | `objeto_del_contrato` y `descripcion_del_proceso` ambos nulos o vacíos | Rechazo | Objeto y descripción ausentes |
  | CAL-SEC-07 | `ultima_actualizacion` nula o no interpretable | Rechazo | Fecha de actualización ausente o inválida |
  | CAL-SEC-08 | `proceso_de_compra` nulo o vacío | Advertencia | Sin proceso de compra (no se podrán obtener documentos) |
  | CAL-SEC-09 | `valor_del_contrato` nulo, no numérico o negativo (se guarda nulo) | Advertencia | Valor del contrato ausente o inválido |
  | CAL-SEC-10 | `valor_del_contrato` = 0 | Advertencia | Valor del contrato en cero |
  | CAL-SEC-11 | `fecha_de_inicio_del_contrato` o `fecha_de_fin_del_contrato` con formato inválido (se guarda nula) | Advertencia | Fecha de ejecución con formato inválido |
  | CAL-SEC-12 | `fecha_de_fin_del_contrato` anterior a `fecha_de_inicio_del_contrato` | Advertencia | Fecha de fin anterior a la de inicio |
  | CAL-SEC-13 | `codigo_de_categoria_principal` no cumple el formato `V1.` seguido de 8 dígitos (se guarda tal como llegó) | Advertencia | Código UNSPSC con formato no reconocido |
  | CAL-SEC-14 | `urlproceso` nula o vacía | Advertencia | Sin URL pública |

- **RN-03 Catálogo — Ítems TVEC:**

  | Código | Regla | Severidad | Motivo |
  |---|---|---|---|
  | CAL-TVI-01 | identificador de fila nulo | Rechazo | Identificador de origen ausente |
  | CAL-TVI-02 | `fecha` nula, no interpretable como ISO 8601 o fuera de la ventana histórica | Rechazo | Fecha ausente, con formato inválido o fuera de la ventana |
  | CAL-TVI-03 | descripción del ítem nula o vacía | Rechazo | Descripción del ítem ausente |
  | CAL-TVI-04 | `precio` nulo, no numérico, 0 o negativo | Rechazo | Precio unitario no válido |
  | CAL-TVI-05 | `cantidad` nula, no numérica, 0 o negativa | Rechazo | Cantidad no válida |
  | CAL-TVI-06 | `orden` nula o vacía | Advertencia | Sin número de orden |
  | CAL-TVI-07 | `total` nulo o no numérico (se guarda nulo) | Advertencia | Total del ítem ausente o inválido |
  | CAL-TVI-08 | \|`precio` × `cantidad` − `total`\| > tolerancia | Advertencia | Total del ítem no coincide con precio × cantidad |

  Tolerancia de CAL-TVI-08 configurable: el mayor entre un porcentaje del total (valor inicial: 1 %) y un valor absoluto (valor inicial: COP 1.000). En CAL-TVI-08 los valores se guardan tal como llegaron.
- **RN-04 Catálogo — Órdenes TVEC:** CAL-TVO-01 `identificador_de_la_orden` nulo o vacío → Rechazo "Identificador de origen ausente"; CAL-TVO-02 `fecha` con formato inválido → Advertencia "Fecha de la orden con formato inválido" (se guarda nula); CAL-TVO-03 `total` no numérico o negativo → Advertencia "Total de la orden inválido" (se guarda nulo); CAL-TVO-04 entidad nula o vacía → Advertencia "Orden sin entidad".
- **RN-05 Formatos aceptados:** fechas ISO 8601 (`AAAA-MM-DD` o `AAAA-MM-DDThh:mm:ss[.fff]`); valores numéricos como número JSON o texto con punto decimal y sin separadores de miles (ej. "2150000.50"). Cualquier otro formato es inválido.
- **RN-06 Deduplicación en la ejecución:** clave = identificador de origen (`id_contrato`, identificador de fila TVEC o `identificador_de_la_orden`). Se conserva la versión con fecha de actualización de fuente más reciente; si son iguales, la última recibida. La otra → rechazo con código CAL-DUP-01 "Duplicado en la ejecución".
- **RN-07 Registro de rechazos:** campos: `id_ejecucion`, `fuente` (SECOP II contratos / TVEC ítems / TVEC órdenes), `id_origen` (nulo si falta), `codigo_regla`, `campo`, `valor_recibido` (texto truncado a 500 caracteres; solo si el campo está en la lista de permitidos, si no, nulo), `motivo`, `fecha_hora`. No se eliminan automáticamente durante el MVP.
- **RN-08 Advertencias en el registro:** se guardan como lista de códigos en `advertencias_calidad` del registro escrito y se recalculan en cada nueva versión.
- **RN-09 Registro existente con versión rechazada:** se conserva la versión anterior; `ultima_version_rechazada = sí` y `fecha_ultimo_rechazo`. Una versión válida posterior la limpia (Escenario 8).
- **RN-10 Contadores:** cada ejecución reporta rechazados (registros, no reglas) y advertencias (número de registros con al menos una advertencia), además del total por código de regla.
- **RN-11 Catálogo configurable:** la tolerancia de CAL-TVI-08 es configurable; los códigos, reglas y severidades son parte de esta historia y su cambio es un cambio de requisito.

### Interfaz

No requiere interfaz gráfica. Consulta o script del Administrador con filtros por fuente, ejecución, código de regla y rango de fechas, que devuelve la lista y los totales por código (Escenario 9).

### Sistemas Externos (Si aplica)

No aplica directamente: valida los datos que entregan las cargas de la API de datos.gov.co.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-001, HU-002 (cargas SECOP II), HU-003, HU-004 (cargas TVEC), HU-006 (bitácora de ejecuciones).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El PRD no lista qué campos son obligatorios ni qué severidad tiene cada falla → resuelto con el catálogo de RN-02 a RN-04.
- Un valor del contrato en cero o negativo no impide analizar ítems (es solo referencia) → resuelto como Advertencia (CAL-SEC-09, CAL-SEC-10).
- La diferencia entre precio × cantidad y total en la TVEC se marca, no se corrige → resuelto como Advertencia con tolerancia configurable (CAL-TVI-08).
- Una versión inválida no debe borrar un registro válido anterior → resuelto en RN-09.

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
