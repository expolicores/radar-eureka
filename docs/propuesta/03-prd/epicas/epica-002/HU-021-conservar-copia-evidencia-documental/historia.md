# Historia #021: Conservar la copia y la evidencia de los documentos de los que se extraen datos

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Preparar Documentos para la Lectura  
**Prioridad:** Crítica  
**FRs relacionados:** FR-024 (copia del archivo, hash, URL original, fuente, fecha de descarga y ubicación de la evidencia)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema conserve una copia inalterable de cada documento del que se extrajo un dato, con su hash, URL original, fuente, fecha de descarga y la ubicación exacta del dato,  
**Para** poder volver a la evidencia de origen de un precio o una cantidad aunque el documento original cambie o deje de estar publicado en SECOP II.

## Descripción

El principio del producto es "evidencia antes que acusación": cada señal debe poder reconstruirse hasta el documento y la página de origen (NFR-CAL-004). Los documentos de SECOP II pueden reemplazarse o dejar de estar disponibles, y sin una copia la señal dejaría de ser reproducible.

Esta HU conserva, para todo documento del que se haya extraído al menos un dato de un ítem de televisor, una copia del archivo con su huella SHA-256 y sus metadatos de origen, y la vincula con cada dato extraído y su ubicación (página, hoja o celda). Como las señales se generan después de la extracción (épica de señales), la copia se conserva desde el momento de la extracción, de modo que cualquier señal futura que use ese dato sea reproducible. La estrategia de almacenamiento se define en arquitectura; esta HU define qué se conserva, cuánto tiempo y cómo se verifica.

---

## Criterios de Aceptación

### Escenario 1: Conservación al extraer un dato

- **Dado** que de la página 2 del documento 600002 "Propuesta_economica_ganador.pdf" (hash `9f2c…a41b`, descargado el 2026-09-28 desde `https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=600002`, dataset `dmgg-8hin`) se extrajo el precio unitario 2.150.000 de un ítem
- **Cuando** se registra el dato extraído
- **Entonces** el sistema conserva la copia del archivo como "versión 1" del documento 600002 con hash, URL original, fuente "SECOP II — Archivos Descarga (dmgg-8hin)", fecha de descarga, `id_documento` y proceso, y vincula el dato con esa versión y con la ubicación "página 2"

### Escenario 2: Dato extraído de una hoja de cálculo o de un archivo interno

- **Dado** que la cantidad 8 se extrajo de la celda `Oferta!C5` del archivo interno `600010::Anexo/precios.xlsx`
- **Cuando** se registra el dato extraído
- **Entonces** se conserva la copia del archivo interno con su hash, la referencia al comprimido 600010 y la URL de este, y el dato queda vinculado a la ubicación "hoja Oferta, celda C5"

### Escenario 3: Dato leído de una página por lectura visual o de un documento de texto

- **Dado** que el dato se extrajo de la imagen generada de la página 3 de un PDF escaneado, o de la página 2 de la representación paginada de un DOCX
- **Cuando** se registra el dato extraído
- **Entonces** además del archivo original se conservan la imagen de la página o la representación paginada usadas, vinculadas a la misma versión

### Escenario 4: El documento original cambia en la fuente

- **Dado** que el Administrador solicitó la redescarga del documento 600002 y el nuevo contenido tiene un hash diferente
- **Cuando** se completa la redescarga
- **Entonces** se crea la "versión 2" del documento; los datos ya extraídos siguen vinculados a la versión 1, que se conserva sin cambios, y el historial del documento muestra ambas versiones con su hash y fecha

### Escenario 5: El documento original deja de estar disponible

- **Dado** que la URL original del documento 600002 responde 404 en una verificación posterior
- **Cuando** se consulta la evidencia de un dato vinculado a ese documento
- **Entonces** la copia conservada sigue disponible y se muestra la anotación "el documento original ya no está disponible en la fuente (verificado el {fecha})"

### Escenario 6: Consulta de la evidencia de un dato

- **Dado** que un usuario autenticado (Analista o Administrador) consulta la evidencia del precio unitario de un ítem
- **Cuando** solicita la evidencia
- **Entonces** obtiene la copia del documento (versión vinculada), el nombre, la ubicación (página, u hoja y celda), el hash, la URL original, la fuente y la fecha de descarga

### Escenario 7: Integridad comprometida

- **Dado** que al servir la copia de la versión 1 de 600002 el hash recalculado no coincide con el registrado
- **Cuando** se solicita la evidencia
- **Entonces** el sistema no entrega la copia como evidencia válida, muestra el mensaje "La copia de este documento no supera la verificación de integridad; se notificó al Administrador" y genera un aviso al Administrador con documento, versión y hashes

### Escenario 8: Intento de eliminar una copia referenciada

- **Dado** que la versión 1 de 600002 está vinculada a datos extraídos
- **Cuando** cualquier proceso o usuario intenta eliminarla o sobrescribirla
- **Entonces** la operación se rechaza con el mensaje "La copia está vinculada a datos extraídos y no puede eliminarse ni modificarse"

### Escenario 9: Documento sin datos extraídos

- **Dado** que el documento 600007 "Estudio previo.pdf" se procesó pero no se extrajo de él ningún dato
- **Cuando** termina la extracción del proceso
- **Entonces** no es obligatorio conservar su copia como evidencia; su registro (identificador, nombre, tipo, fecha de carga, URL y hash) se mantiene

### Escenario 10: Usuario no autenticado

- **Dado** que una persona sin sesión iniciada intenta acceder a la URL de una copia de evidencia
- **Cuando** realiza la solicitud
- **Entonces** recibe acceso denegado

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (consume la evidencia) y Administrador (recibe avisos y gestiona redescargas). La conservación es automática.
- **Permisos requeridos:** Usuario autenticado con rol Analista o Administrador para consultar evidencia. Ningún rol puede eliminar ni modificar copias vinculadas.
- **Valor de negocio:** Garantiza la reproducibilidad de las señales (NFR-CAL-004: 100 % de las señales trazables) y protege al producto ante cambios en la fuente.

### Reglas de Negocio

- **RN-01 — Cuándo se conserva:** en el momento en que se registra al menos un dato extraído de un ítem de televisor desde un documento (cualquiera que sea el estado posterior del dato: aceptado, pendiente de revisión, corregido o rechazado), se conserva la copia de la versión del documento usada. Así toda señal que use ese dato es reproducible.
- **RN-02 — Qué se conserva por versión:** archivo original descargado (o archivo interno extraído del comprimido), hash SHA-256, `id_documento`, nombre, tipo, proceso, URL original, fuente (sistema y dataset; ej. "SECOP II — Archivos Descarga (dmgg-8hin)"), fecha y hora de descarga, número de versión y, si aplica, el comprimido de origen con su URL. Además, si el dato se leyó de una imagen de página o de una representación paginada (DOCX/DOC), se conservan esa imagen o esa representación vinculadas a la misma versión.
- **RN-03 — Vínculo dato ↔ evidencia:** cada dato extraído referencia la versión del documento y la ubicación: "página N" (PDF, representación paginada o imagen) o "hoja H, celda C" (hojas de cálculo) o "hoja H, imagen N" (imagen insertada en hoja).
- **RN-04 — Versiones:** si una redescarga produce un hash distinto, se crea una nueva versión (número consecutivo desde 1) con su propia fecha de descarga; las versiones anteriores se conservan sin cambios y los datos ya extraídos siguen vinculados a la versión que usaron. Una redescarga con el mismo hash no crea versión.
- **RN-05 — Inmutabilidad:** una copia vinculada a al menos un dato extraído no puede eliminarse ni sobrescribirse. Intento → mensaje "La copia está vinculada a datos extraídos y no puede eliminarse ni modificarse", sin cambios.
- **RN-06 — Retención:** las copias vinculadas se conservan mientras exista algún dato vinculado y, durante el MVP, sin eliminación automática. Se incluyen en el respaldo de la base de datos, porque no se pueden reconstruir desde la fuente.
- **RN-07 — Integridad:** cada vez que se sirve una copia como evidencia se recalcula su hash y se compara con el registrado. Si no coincide: no se entrega como evidencia válida, se muestra "La copia de este documento no supera la verificación de integridad; se notificó al Administrador" y se avisa al Administrador con documento, versión, hash registrado y hash calculado.
- **RN-08 — Disponibilidad del original:** si una verificación posterior de la URL original devuelve 404 o 410, la versión queda anotada "el documento original ya no está disponible en la fuente (verificado el {fecha AAAA-MM-DD})"; la copia sigue siendo la evidencia.
- **RN-09 — Consulta:** la evidencia de un dato se obtiene a partir del dato e incluye copia de la versión vinculada, nombre, ubicación, hash, URL original, fuente y fecha de descarga.
- **RN-10 — Documentos sin datos:** los documentos de los que no se extrajo ningún dato conservan su registro (identificador, nombre, tipo, fecha de carga, URL, hash); su copia no es obligatoria como evidencia.
- **RN-11 — Acceso:** solo usuarios autenticados con rol Analista o Administrador consultan las copias; los documentos son públicos en la fuente, pero el producto solo los sirve con sesión.

### Interfaz

La consulta de evidencia es una operación disponible para las vistas de señal y ficha de otras épicas (que navegan hasta el documento y la página). En esta HU basta con que la operación devuelva la copia y sus metadatos; los mensajes de RN-05 y RN-07 se devuelven en su respuesta.

### Sistemas Externos (Si aplica)

- **Servidor de descarga de SECOP II** (solo para la verificación de disponibilidad del original).
- **Almacenamiento de evidencia:** definido en arquitectura.

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

**Historias relacionadas:** HU-014 (registro del documento), HU-016 (descarga, hash y redescarga), HU-019 (representación paginada), HU-020 (imágenes de página), HU-022 (datos extraídos con ubicación).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Como las señales se generan después, la copia se conserva para todo documento del que se extrajo al menos un dato (superconjunto de los usados en señales) → RN-01.
- Sin eliminación automática de copias vinculadas durante el MVP → RN-06.
- La integridad se verifica recalculando el hash al servir la copia → RN-07.
- Las copias solo se sirven a usuarios autenticados → RN-11.

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
