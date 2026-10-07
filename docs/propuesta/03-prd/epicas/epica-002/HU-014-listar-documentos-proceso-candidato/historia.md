# Historia #014: Listar y registrar los documentos publicados de cada proceso candidato

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Obtener y Priorizar Documentos del Proceso  
**Prioridad:** Crítica  
**FRs relacionados:** FR-018, FR-024 (registro del documento con identificador estable, nombre, tipo, fecha de carga y URL de origen)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema obtenga desde los datasets oficiales de Archivos Descarga de SECOP II la lista completa de documentos publicados de cada proceso candidato y registre cada documento con un identificador estable,  
**Para** contar con el inventario documental de cada proceso, trazable a su URL oficial, sobre el cual se priorizan, descargan y leen los documentos que contienen precios y cantidades de televisores.

## Descripción

En SECOP II el precio unitario, la cantidad, la marca y el modelo de un televisor solo existen dentro de los documentos del proceso. Esta HU construye el inventario de esos documentos: por cada proceso de un contrato candidato a televisor (identificado en la épica de universo de compras), consulta los datasets oficiales de Archivos Descarga de datos.gov.co (el de documentos desde 2025 y los históricos por año), y registra cada documento con su `id_documento`, nombre, descripción, extensión (tipo), tamaño, fecha de carga y URL oficial de descarga.

La HU no descarga archivos (eso lo hace HU-016) ni decide cuáles se procesan (HU-015). Es un proceso automático, separado de la ingesta de contratos: la ingesta no dispara reprocesamiento con IA, y esta HU tampoco lo hace. No requiere interfaz gráfica: sus resultados se consultan mediante el registro de ejecución y consultas sobre el inventario.

---

## Criterios de Aceptación

### Escenario 1: Listado exitoso de los documentos de un proceso candidato

- **Dado** que existe el contrato SECOP II candidato `CO1.PCCNTR.7654321`, con clasificación "incluido" y `proceso_de_compra` = `CO1.BDOS.1234567`, y el dataset `dmgg-8hin` publica 23 documentos con `proceso` = `CO1.BDOS.1234567`
- **Cuando** se ejecuta el listado documental
- **Entonces** el sistema registra los 23 documentos, cada uno con `id_documento`, nombre de archivo, descripción, extensión, tamaño, fecha de carga, URL de descarga, número de contrato, dataset de origen y fecha del listado; y el estado documental del proceso pasa a "documentos listados" con el conteo 23

### Escenario 2: Documentos de un mismo proceso repartidos en varios datasets anuales

- **Dado** que el proceso `CO1.BDOS.1234567` tiene 10 documentos en el dataset histórico 2024 (`nbae-kzan`) y 6 en el dataset desde 2025 (`dmgg-8hin`), y uno de ellos (`id_documento` 500100) aparece en ambos datasets
- **Cuando** se ejecuta el listado documental
- **Entonces** el sistema registra 15 documentos distintos; el documento 500100 queda una sola vez, con los datos del primer dataset en el orden configurado y con ambos datasets anotados como origen

### Escenario 3: Proceso sin documentos publicados

- **Dado** que el proceso `CO1.BDOS.2222222` (contrato firmado hace 3 días) no tiene registros en ninguno de los datasets configurados y todas las consultas respondieron correctamente
- **Cuando** se ejecuta el listado documental
- **Entonces** el proceso queda en estado "sin documentos publicados" con la fecha de la verificación, y vuelve a consultarse en la siguiente ejecución

### Escenario 4: Contrato excluido por la clasificación

- **Dado** que el contrato `CO1.PCCNTR.3333333` tiene clasificación "excluido" (ej. servicio de mantenimiento de televisores)
- **Cuando** se ejecuta el listado documental
- **Entonces** el sistema no consulta ni registra documentos de su proceso

### Escenario 5: Contrato reclasificado de "excluido" a "incluido"

- **Dado** que el contrato `CO1.PCCNTR.3333333` fue corregido manualmente de "excluido" a "incluido" después de la última ejecución
- **Cuando** se ejecuta el siguiente listado documental
- **Entonces** el sistema lista y registra los documentos de su proceso como en el Escenario 1

### Escenario 6: Reejecución sin duplicados y con cambio de metadatos

- **Dado** que el proceso `CO1.BDOS.1234567` ya tiene 23 documentos registrados, la fuente publica ahora 25 (2 nuevos) y el documento 500101 cambió su nombre de "oferta.pdf" a "oferta_economica.pdf"
- **Cuando** se ejecuta nuevamente el listado documental
- **Entonces** el inventario queda con 25 documentos (sin duplicar los 23 existentes), los 2 nuevos se marcan como "nuevo", y el documento 500101 conserva el mismo `id_documento`, con el nombre actualizado y el nombre anterior en su historial

### Escenario 7: Registro de la fuente sin URL de descarga o sin identificador

- **Dado** que un registro del dataset para el proceso `CO1.BDOS.1234567` llega sin `url_descarga_documento`, y otro llega sin `id_documento`
- **Cuando** se ejecuta el listado documental
- **Entonces** ambos quedan registrados como "rechazado en listado" con el motivo "falta URL de descarga" y "falta identificador del documento" respectivamente, no se consideran para priorización y se contabilizan como rechazados en el registro de la ejecución

### Escenario 8: URL fuera de los dominios permitidos

- **Dado** que un registro trae `url_descarga_documento` = `http://otro-sitio.example/archivo.pdf`
- **Cuando** se ejecuta el listado documental
- **Entonces** el documento queda como "rechazado en listado" con el motivo "URL fuera de los dominios oficiales permitidos" y nunca se intenta descargar

### Escenario 9: Falla de la API de datos abiertos

- **Dado** que la consulta al dataset `nbae-kzan` responde con tiempo de espera agotado en el intento inicial y en los 3 reintentos configurados
- **Cuando** se ejecuta el listado documental
- **Entonces** la ejecución queda en estado "parcial" con el dataset y el error registrados; los procesos afectados conservan su estado documental anterior y **no** se marcan como "sin documentos publicados"; los documentos obtenidos de los demás datasets sí se registran

### Escenario 10: Proceso con muchos documentos

- **Dado** que el proceso `CO1.BDOS.4444444` publica 419 documentos y la página de consulta configurada es de 100 registros
- **Cuando** se ejecuta el listado documental
- **Entonces** el sistema recorre todas las páginas y registra los 419 documentos, sin truncar el resultado

### Escenario 11: Registro de la ejecución

- **Dado** que terminó una ejecución del listado documental
- **Cuando** el Administrador consulta el registro de ejecuciones
- **Entonces** encuentra la fecha y hora de inicio y fin, el estado (completa / parcial / fallida), los procesos consultados, los documentos nuevos, actualizados y rechazados, y los errores con el dataset que los produjo

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO). El proceso es automático; el Administrador solo consulta resultados y registros.
- **Permisos requeridos:** Rol Administrador para consultar el inventario y el registro de ejecuciones. El Analista no accede a esta operación.
- **Valor de negocio:** Sin inventario documental no hay extracción de precios en SECOP II; es el primer paso del flujo documentos → datos comparables y la base de la trazabilidad a la fuente oficial.

### Reglas de Negocio

- **RN-01 — Procesos objetivo:** se listan los documentos de cada `proceso_de_compra` asociado a un contrato SECOP II marcado como candidato a televisor cuya clasificación sea "incluido", "requiere revisión" o aún no tenga clasificación. Los contratos con clasificación "excluido" no se listan. Si un contrato cambia de "excluido" a otra clasificación, su proceso entra en la siguiente ejecución. Si cambia a "excluido", su inventario se conserva pero deja de actualizarse.
- **RN-02 — Datasets consultados (configurable):** lista ordenada de datasets de Archivos Descarga de SECOP II. Configuración inicial, en este orden: `dmgg-8hin` (desde 2025), `nbae-kzan` (2024), `3skv-9na7` (2023), `kgcd-kt7i` (2022), `f8va-cf4m` (hasta 2021). Para cada proceso se consultan **todos** los datasets de la lista, porque un proceso puede tener documentos cargados en años distintos.
- **RN-03 — Relación proceso ↔ documento:** un documento pertenece al proceso cuando `archivos.proceso` = `contratos.proceso_de_compra`, comparados sin espacios al inicio o al final y sin distinguir mayúsculas de minúsculas.
- **RN-04 — Datos registrados por documento:** `id_documento` (identificador estable), `nombre_archivo`, `descripcion`, `extension` (tipo), `tamanno_archivo` (bytes), `fecha_carga`, `url_descarga_documento`, `n_mero_de_contrato`, proceso, dataset(s) de origen, fecha y hora del primer listado y de la última verificación.
- **RN-05 — Identificador estable y no duplicación:** el identificador del documento es el `id_documento` de la fuente. Un mismo `id_documento` se registra una sola vez por proceso, aunque aparezca en varios datasets o en varias ejecuciones; se conservan los datos del primer dataset según el orden de RN-02 y se anotan todos los datasets de origen. Si en una ejecución posterior cambian nombre, descripción, tamaño, extensión o URL, se actualiza el registro y el valor anterior se conserva en el historial del documento con la fecha del cambio. Nunca se borra un documento registrado; si deja de aparecer en la fuente se marca "no publicado en la última verificación".
- **RN-06 — Campos obligatorios y nulos:** sin `id_documento` o sin `url_descarga_documento` el registro queda "rechazado en listado" con el motivo correspondiente y no pasa a priorización. Sin nombre → se registra "(sin nombre)". Sin extensión → se toma el sufijo del nombre de archivo (texto después del último punto, en minúsculas); si no hay sufijo → "desconocida". `fecha_carga` ausente o con formato inválido → se guarda nula con la advertencia "fecha de carga no válida", sin rechazar el documento. Tamaño ausente o no numérico → nulo.
- **RN-07 — URL válida:** la URL debe ser absoluta, con esquema `https` o `http`, y su dominio debe estar en la lista configurable de dominios oficiales permitidos (configuración inicial: `community.secop.gov.co`). En otro caso: "rechazado en listado", motivo "URL fuera de los dominios oficiales permitidos" o "URL no válida".
- **RN-08 — Proceso sin documentos:** si todas las consultas del proceso respondieron correctamente y no hay registros, el estado documental del proceso es "sin documentos publicados", con fecha de verificación. Se vuelve a consultar en cada ejecución.
- **RN-09 — Reejecución:** cada ejecución vuelve a listar todos los procesos objetivo. Los documentos nuevos se marcan "nuevo" con su fecha. Un documento nuevo **no** dispara por sí mismo una nueva extracción con IA de documentos ya procesados.
- **RN-10 — Frecuencia (configurable):** el listado documental es un proceso separado de la ingesta de contratos. Configuración inicial: una ejecución diaria, posterior a la ingesta incremental.
- **RN-11 — Tolerancia a fallas:** ante tiempo de espera o error 5xx de la API se reintenta con espera exponencial (configuración inicial: 3 reintentos). Si un dataset sigue fallando, la ejecución queda "parcial", se registra el dataset y el error, y los procesos afectados conservan su estado anterior: una consulta fallida **nunca** produce el estado "sin documentos publicados". Si fallan todos los datasets, la ejecución queda "fallida".
- **RN-12 — Paginación:** se recorren todas las páginas de resultados de cada consulta (tamaño de página configurable; configuración inicial: 1.000 registros). El resultado nunca se trunca.
- **RN-13 — Estado documental del proceso:** tras una consulta completa, el proceso queda en "documentos listados" (con el número de documentos válidos) o "sin documentos publicados".
- **RN-14 — Registro de la ejecución:** por cada ejecución se guarda: inicio, fin, estado (completa / parcial / fallida), procesos consultados, documentos nuevos, actualizados y rechazados, y errores (dataset, mensaje, hora).
- **RN-15 — Credenciales:** el app token de datos.gov.co se toma del gestor de secretos o de variables de entorno cifradas; nunca se escribe en el código, en la configuración versionada ni en los registros.
- **RN-16 — Sin descarga:** esta HU no descarga contenido de los documentos; solo registra sus metadatos.

### Interfaz

Proceso automático sin interfaz gráfica obligatoria. El Administrador consulta el inventario de documentos por proceso y el registro de ejecuciones mediante consultas, registros (logs) o una vista administrativa mínima, según lo defina la arquitectura.

### Sistemas Externos (Si aplica)

- **API de datos abiertos de datos.gov.co (Socrata/SODA):** datasets de Archivos Descarga de SECOP II `dmgg-8hin`, `nbae-kzan`, `3skv-9na7`, `kgcd-kt7i`, `f8va-cf4m`. Campos usados: `proceso`, `n_mero_de_contrato`, `id_documento`, `nombre_archivo`, `descripci_n`, `extensi_n`, `tamanno_archivo`, `fecha_carga`, `url_descarga_documento`. Autenticación con app token.
- **Contratos SECOP II ya ingeridos** (dataset `jbjy-vk9h`, épica de universo de compras): aportan `proceso_de_compra`, `id_contrato` y la clasificación del candidato.

---

## Contexto y Referencias

**Épica origen:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)

**Exclusiones de la Épica:**
- NO incluye el agente de investigación (siguiente incremento agéntico, post-MVP).
- NO incluye la extracción y comparación de precios de múltiples oferentes (FR-026, pospuesta por D4).
- NO incluye la extracción de cláusulas contractuales, garantías ni condiciones de entrega.
- NO incluye procesar todos los documentos de cada proceso, solo los priorizados.
- NO incluye la extracción de categorías distintas a televisores.
- NO incluye la base de conocimiento RAG sobre los documentos.

**Historias relacionadas:** HU-015 (priorización de documentos), HU-016 (descarga), HU-021 (conservación de copia y evidencia).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Los contratos "requiere revisión" o sin clasificación también se listan, porque la clasificación a nivel de ítem puede necesitar los documentos → RN-01.
- Se consultan todos los datasets anuales para cada proceso, porque un proceso puede tener documentos cargados en años distintos → RN-02.
- La URL de descarga se restringe a una lista configurable de dominios oficiales (inicial `community.secop.gov.co`) para no descargar de sitios no oficiales → RN-07.
- Una consulta fallida nunca se interpreta como "proceso sin documentos" → RN-11.
- El listado se reejecuta sobre todos los procesos objetivo (volumen del MVP ≈ 355 procesos) y el tamaño de página inicial es 1.000 registros → RN-09, RN-12.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-002 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
