# Historia #001: Carga inicial del histórico de contratos SECOP II

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Ingestar Contratos SECOP II  
**Prioridad:** Crítica  
**FRs relacionados:** FR-001, FR-002, FR-006, FR-008, FR-009

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** cargar desde la API oficial de datos.gov.co el histórico de contratos de SECOP II relacionados con televisores firmados desde la fecha inicial configurada,  
**Para** que el producto cuente con un universo inicial de contratos trazable a la fuente oficial, sin datos personales sensibles, sobre el cual identificar y clasificar televisores.

## Descripción

Esta historia construye la primera carga del universo SECOP II. El sistema consulta el dataset oficial **SECOP II – Contratos Electrónicos** (`jbjy-vk9h`) por la API Socrata (SODA) de datos.gov.co, trae los contratos firmados dentro de la ventana histórica configurada que cumplen el **prefiltro de televisores** (código UNSPSC principal o términos de texto) y los guarda con su identificador de origen, la URL pública del proceso y la fecha de corte de la fuente.

La carga aplica **minimización de datos desde el origen**: solo se conservan los campos de una lista explícita de campos permitidos. Los campos personales sensibles (banco, tipo y número de cuenta, documentos de identidad de representantes legales, supervisores y ordenadores del gasto) se descartan en memoria y nunca se escriben en ninguna capa.

La carga no descarga documentos ni ejecuta extracción con IA: solo deja los contratos disponibles para los procesos posteriores (marcación de candidatos, clasificación y gestión documental). La marcación precisa de candidatos la hace la HU-008; esta historia deja cada contrato en estado de candidatura "Pendiente de marcación".

La carga se inicia por comando o script del Administrador (no requiere interfaz gráfica, según la nota de implementación del Dominio 12 del PRD).

---

## Criterios de Aceptación

### Escenario 1: Carga inicial exitosa del histórico

- **Dado** que la configuración tiene `fecha_inicio_historico = 2023-01-01`, el dataset `jbjy-vk9h`, los términos de prefiltro "TELEVISOR", "SMART TV" y "TV", y la API responde correctamente
- **Cuando** el Administrador ejecuta el comando de carga inicial de SECOP II
- **Entonces** el sistema consulta la API de forma paginada, guarda cada contrato devuelto que tenga `fecha_de_firma` entre 2023-01-01 y la fecha de ejecución, conserva solo los campos permitidos, registra en cada contrato `id_contrato`, `proceso_de_compra`, `url_publica`, `fecha_corte`, `fecha_ingesta` e `id_ejecucion`, deja la candidatura en "Pendiente de marcación" y muestra al final el resumen: "Carga inicial SECOP II finalizada. Leídos: {n}. Nuevos: {n}. Actualizados: {n}. Sin cambios: {n}. Rechazados: {n}."

### Escenario 2: Descarte de campos personales sensibles

- **Dado** que la respuesta de la API incluye, además de los campos permitidos, campos de banco, tipo y número de cuenta, y documentos de identidad de representante legal, supervisor y ordenador del gasto
- **Cuando** el sistema procesa la página de resultados
- **Entonces** esos campos se descartan antes de persistir, y no aparecen en la base de datos, en los logs, en los registros de rechazo ni en archivos temporales

### Escenario 3: Lista de campos permitidos con un campo prohibido

- **Dado** que la lista de campos permitidos configurada contiene un campo cuyo nombre coincide con la lista de patrones prohibidos (ej. `nombre_del_banco`)
- **Cuando** el Administrador ejecuta el comando de carga
- **Entonces** la carga no inicia, no se consulta la API y se muestra el error "La lista de campos permitidos contiene un campo prohibido: nombre_del_banco. Corrija la configuración antes de ejecutar la carga."

### Escenario 4: Contrato sin fecha de firma o fuera de la ventana

- **Dado** que la API devuelve un contrato con `fecha_de_firma` nula, o con `fecha_de_firma` anterior a `fecha_inicio_historico`, o posterior a la fecha de ejecución
- **Cuando** el sistema procesa el registro
- **Entonces** el contrato no se guarda como contrato del universo, se cuenta como rechazado con el motivo "Fecha de firma ausente" o "Fecha de firma fuera de la ventana histórica" según corresponda, y la carga continúa con el siguiente registro

### Escenario 5: Contrato sin identificador de origen

- **Dado** que la API devuelve un registro con `id_contrato` nulo o vacío
- **Cuando** el sistema procesa el registro
- **Entonces** el registro no se guarda, se cuenta como rechazado con el motivo "Identificador de origen ausente" y la carga continúa

### Escenario 6: Contrato sin URL pública del proceso

- **Dado** que un contrato llega con `urlproceso` nulo o vacío
- **Cuando** el sistema lo guarda
- **Entonces** el contrato se carga con `url_publica` nula y con el indicador `sin_url_publica = sí`, y se cuenta en el resumen como "Advertencias: {n}"

### Escenario 7: Fecha de corte no disponible en los metadatos

- **Dado** que la consulta de metadatos del dataset falla o no trae el dato de última actualización
- **Cuando** inicia la carga
- **Entonces** el sistema usa como `fecha_corte` la fecha y hora de inicio de la ejecución, marca `fecha_corte_aproximada = sí` en cada contrato cargado en esa ejecución y continúa la carga

### Escenario 8: Falla transitoria de la API con reintento exitoso

- **Dado** que una solicitud de página devuelve tiempo de espera agotado, HTTP 429 o HTTP 5xx
- **Cuando** el sistema reintenta con espera exponencial y la API responde correctamente antes de agotar los reintentos
- **Entonces** la página se procesa normalmente, sin registros perdidos ni duplicados, y el reintento queda anotado en los errores de la ejecución como recuperado

### Escenario 9: Falla persistente de la API

- **Dado** que una solicitud falla en el intento original y en los 3 reintentos configurados
- **Cuando** se agotan los reintentos
- **Entonces** la ejecución termina con estado "Fallida", los contratos de las páginas ya procesadas permanecen guardados, se muestra "La carga inicial SECOP II falló en la página {n}: {detalle del error}. Puede volver a ejecutarla; los registros ya cargados no se duplicarán." y la siguiente ejecución completa la carga sin duplicar contratos

### Escenario 10: Error no recuperable de la API

- **Dado** que la API responde HTTP 400, 401, 403 o 404
- **Cuando** el sistema recibe esa respuesta
- **Entonces** no reintenta, la ejecución termina con estado "Fallida" y se muestra "La API de datos.gov.co rechazó la consulta (HTTP {código}). Verifique el identificador del dataset, la consulta y el app token."

### Escenario 11: Re-ejecución sobre datos ya cargados

- **Dado** que la carga inicial ya se ejecutó con éxito y la fuente no ha cambiado
- **Cuando** el Administrador vuelve a ejecutar la carga inicial
- **Entonces** ningún contrato se duplica, los contratos cuyo `ultima_actualizacion` no cambió se cuentan como "Sin cambios" y los que tienen `ultima_actualizacion` más reciente se actualizan y se cuentan como "Actualizados"

### Escenario 12: Ejecución concurrente

- **Dado** que existe una carga de SECOP II en estado "En curso"
- **Cuando** el Administrador intenta iniciar otra carga de SECOP II
- **Entonces** la nueva carga no inicia y se muestra "Ya existe una carga en curso para SECOP II (ejecución {id_ejecucion}). Espere a que termine."

### Escenario 13: Ejecución sin app token

- **Dado** que la variable de entorno o secreto del app token de datos.gov.co no está configurado
- **Cuando** el Administrador ejecuta la carga
- **Entonces** la carga se ejecuta sin el encabezado de token y la ejecución registra la advertencia "Ejecución sin app token: la API puede aplicar límites más estrictos"

### Escenario 14: La fuente no devuelve registros

- **Dado** que la consulta con la ventana y el prefiltro configurados no devuelve ningún registro
- **Cuando** termina la consulta
- **Entonces** la ejecución termina con estado "Exitosa", con todos los contadores en 0, y se muestra "La fuente no devolvió contratos para la ventana y el prefiltro configurados."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (en el MVP es el PO).
- **Permisos requeridos:** acceso de operación al entorno donde corre el proceso de ingesta (rol Administrador). El Analista no puede ejecutar cargas.
- **Valor de negocio:** sin este universo no existe ningún análisis posterior; es la base del Benchmark 1 y del denominador de los indicadores de cobertura.

### Reglas de Negocio

- **RN-01 Fuente oficial:** la única fuente es la API SODA `https://www.datos.gov.co/resource/{dataset}.json`, con `dataset` configurable (valor inicial: `jbjy-vk9h`). No se consulta ni se hace scraping del portal transaccional de SECOP.
- **RN-02 Ventana histórica:** se cargan contratos con `fecha_de_firma` ≥ `fecha_inicio_historico` y ≤ fecha de ejecución. `fecha_inicio_historico` es configurable (valor inicial: `2023-01-01`, equivalente a los últimos 3 años de histórico). Cambiar el parámetro no elimina contratos ya cargados.
- **RN-03 Prefiltro de televisores en la consulta:** la consulta solicita contratos que cumplan al menos una condición: (a) `codigo_de_categoria_principal` = `V1.52161505`; (b) `objeto_del_contrato` en mayúsculas contiene alguno de los términos configurados; (c) `descripcion_del_proceso` en mayúsculas contiene alguno de los términos configurados. Términos: lista configurable (valor inicial: "TELEVISOR", "SMART TV", "TV"). El prefiltro es amplio a propósito; la marcación precisa de candidatos no forma parte de esta historia y cada contrato queda con candidatura "Pendiente de marcación".
- **RN-04 Campos permitidos (lista blanca):** solo se conservan estos campos de origen, con su nombre interno:

  | Campo origen | Campo interno | Tipo |
  |---|---|---|
  | `id_contrato` | `id_contrato` | Texto (obligatorio, clave única) |
  | `proceso_de_compra` | `proceso_de_compra` | Texto |
  | `referencia_del_contrato` | `referencia_contrato` | Texto |
  | `nombre_entidad` | `entidad_nombre` | Texto |
  | `nit_entidad` | `entidad_nit` | Texto |
  | `codigo_entidad` | `entidad_codigo` | Texto |
  | `departamento` | `departamento` | Texto |
  | `ciudad` | `municipio` | Texto |
  | `proveedor_adjudicado` | `proveedor_nombre` | Texto |
  | `documento_proveedor` | `proveedor_documento` | Texto |
  | `codigo_proveedor` | `proveedor_codigo` | Texto |
  | `objeto_del_contrato` | `objeto` | Texto |
  | `descripcion_del_proceso` | `descripcion_proceso` | Texto |
  | `codigo_de_categoria_principal` | `unspsc_principal` | Texto (formato origen `V1.########`) |
  | `modalidad_de_contratacion` | `modalidad` | Texto |
  | `tipo_de_contrato` | `tipo_contrato` | Texto |
  | `estado_contrato` | `estado_contrato` | Texto |
  | `valor_del_contrato` | `valor_contrato_referencia` | Decimal COP, 2 decimales |
  | `fecha_de_firma` | `fecha_firma` | Fecha |
  | `fecha_de_inicio_del_contrato` | `fecha_inicio` | Fecha |
  | `fecha_de_fin_del_contrato` | `fecha_fin` | Fecha |
  | `urlproceso` | `url_publica` | URL |
  | `ultima_actualizacion` | `ultima_actualizacion_fuente` | Fecha y hora |

  La lista blanca es configurable. Cualquier campo de la respuesta que no esté en ella se descarta en memoria antes de persistir y nunca se escribe en base de datos, logs, registros de rechazo ni archivos. La respuesta cruda de la API no se persiste. Si un campo permitido no existe en la respuesta, se guarda nulo sin error.
- **RN-05 Patrones prohibidos (lista negra de control):** lista configurable de patrones de nombre de campo, evaluados sin distinguir mayúsculas ni tildes. Valor inicial: contiene "banco"; contiene "cuenta"; contiene "cedula"; contiene ("identificacion" o "documento") junto con ("representante", "supervisor" u "ordenador"). Si algún campo de la lista blanca coincide con un patrón prohibido, la carga no inicia (Escenario 3). `documento_proveedor` está permitido porque identifica al proveedor adjudicado y no pertenece a los campos excluidos por FR-006.
- **RN-06 Valor del contrato:** `valor_contrato_referencia` se guarda solo como dato de referencia del contrato; su nombre interno deja explícito que no es precio unitario ni valor adjudicado del ítem.
- **RN-07 Identificador y trazabilidad:** `id_contrato` es la clave única del contrato. Se conservan `proceso_de_compra` y `url_publica`. `urlproceso` puede llegar como texto o como objeto con la propiedad `url`; en ambos casos se guarda el texto de la URL. Si es nulo o vacío se guarda nulo y `sin_url_publica = sí` (advertencia, no rechazo).
- **RN-08 Fecha de corte:** al iniciar la ejecución se consultan los metadatos `https://www.datos.gov.co/api/views/{dataset}.json` y se toma `rowsUpdatedAt` (segundos epoch) convertido a fecha y hora de America/Bogota. Si la consulta falla o el dato no existe, `fecha_corte` = fecha y hora de inicio de la ejecución y `fecha_corte_aproximada = sí`. Cada contrato guarda `fecha_corte`, `fecha_corte_aproximada`, `fecha_ingesta` (fecha y hora de escritura) e `id_ejecucion`.
- **RN-09 Paginación:** orden estable `id_contrato` ascendente; tamaño de página configurable (valor inicial: 1.000 registros); se avanza con desplazamiento hasta recibir una página vacía o con menos registros que el tamaño de página.
- **RN-10 Escritura idempotente:** si `id_contrato` no existe → se crea ("Nuevo"). Si existe y `ultima_actualizacion` de la fuente es posterior a la guardada → se actualiza ("Actualizado"). Si es igual o anterior → no se modifica ("Sin cambios"). Un mismo `id_contrato` nunca existe dos veces.
- **RN-11 Rechazos propios de esta carga:** se rechaza el registro (no se guarda como contrato) cuando: `id_contrato` es nulo o vacío ("Identificador de origen ausente"); `fecha_de_firma` es nula ("Fecha de firma ausente"); `fecha_de_firma` no se puede interpretar como fecha ISO 8601 ("Fecha de firma con formato inválido"); `fecha_de_firma` está fuera de la ventana de RN-02 ("Fecha de firma fuera de la ventana histórica"). Cada rechazo se cuenta y se registra con id de ejecución, `id_contrato` si existe, campo, valor recibido y motivo, sin incluir campos fuera de la lista blanca.
- **RN-12 Reintentos:** ante tiempo de espera agotado (valor inicial: 60 segundos por solicitud), HTTP 429 o HTTP 5xx, se reintenta hasta 3 veces (configurable) con espera exponencial (valores iniciales: 2, 4 y 8 segundos). HTTP 400, 401, 403 y 404 no se reintentan. Agotados los reintentos, la ejecución queda "Fallida"; las páginas ya escritas se conservan.
- **RN-13 App token:** si existe, se envía en el encabezado `X-App-Token`. Se lee de un gestor de secretos o variable de entorno; nunca se escribe en el repositorio ni en logs. Si no existe, la ejecución continúa con advertencia.
- **RN-14 Exclusión mutua:** solo puede existir una ejecución de SECOP II en estado "En curso". Una ejecución "En curso" sin actividad por más de 6 horas (configurable) se considera abandonada y pasa a "Fallida" al iniciar una nueva.
- **RN-15 Estados de la ejecución:** "En curso", "Exitosa" (sin errores técnicos, con o sin rechazos de datos), "Fallida".
- **RN-16 Separación de procesos:** la carga no descarga documentos, no ejecuta extracción con IA ni clasificación; solo persiste contratos.
- **RN-17 Tiempo:** la carga inicial debe completarse dentro del objetivo de NFR-DAT-004 (histórico completo ≤ 7 días incluida la extracción; objetivo inicial de ingeniería, recalibrable).

### Interfaz

No requiere interfaz gráfica. Se ejecuta por comando o script del Administrador. Salida esperada en consola o log: avance por página ("Página {n}: {registros} registros") y el resumen final del Escenario 1, con el estado de la ejecución y, si hubo, advertencias y errores.

### Sistemas Externos (Si aplica)

- **API Socrata de datos.gov.co:** `https://www.datos.gov.co/resource/jbjy-vk9h.json` (datos, consultas SoQL con `$select`, `$where`, `$order`, `$limit`, `$offset`) y `https://www.datos.gov.co/api/views/jbjy-vk9h.json` (metadatos). Formato JSON. Proveedor: Colombia Compra Eficiente vía portal de datos abiertos del Estado. Autenticación opcional por app token.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-002 (carga incremental SECOP II), HU-005 (validaciones de calidad), HU-006 (bitácora de ejecuciones), HU-007 (verificación de ausencia de datos sensibles), HU-008 (marcación de candidatos SECOP II).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La carga trae solo contratos que cumplen el prefiltro de televisores, no los 6 millones de contratos del dataset → resuelto en RN-03.
- Los nombres exactos de los campos sensibles del dataset no están documentados en D1 → resuelto con lista blanca (RN-04) más patrones prohibidos de control (RN-05).
- Los campos `departamento`, `ciudad`, `tipo_de_contrato` y fechas de inicio/fin no fueron verificados en D1 → resuelto: si no existen, se guardan nulos sin error (RN-04).
- La fecha de corte se toma de los metadatos del dataset → resuelto en RN-08, con alternativa aproximada.
- Tamaño de página, tiempo de espera y tiempos de reintento → valores iniciales configurables (RN-09, RN-12).

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
