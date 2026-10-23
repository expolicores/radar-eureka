# Spike CDP: navegador iniciado manualmente

## Vigencia local desde get-info

El candidate adapter preserva `data[].FechaVencimiento` y `data[].EstadoProceso`
de POST `/cliente/contratos/get-info/MP?perfiles=1086005`. No añade requests,
endpoints ni filtros remotos. El formato observado `YYYY-MM-DD HH:mm:ss` se
interpreta en America/Bogota (UTC−5), contrastado con seis fechas manuales.
Los timestamps con offset explícito se normalizan a Bogotá.

Todos los procesos del ámbito quedan en `processes`, con published_at, recent,
age_days, deadline_at, deadline_timezone, provider_status, validity_status y
validity_warning. `raw_source_reference` conserva FechaPublicacion,
FechaVencimiento y EstadoProceso originales. `deadline_at` es ISO con offset,
o null si no existe/no se puede parsear. Las fechas inválidas generan
`validity_warning="invalid_deadline_at"`; las ausentes se cuentan como unknown.

La hora de evaluación es única para toda la corrida y se registra como
`validity_evaluated_at`, igual que la referencia de frescura. Se decide únicamente
por deadline: posterior a now → open; anterior o igual → closed; ausente/inválido
→ unknown. Un estado Published, Publicado, Open o Abierto con deadline vencido
produce `provider_status_deadline_conflict`. Ese conflicto es un warning, no un
error, y el proceso queda closed. Un provider_status de cierre tampoco puede
anular un deadline futuro: se conserva el estado como evidencia y rige la fecha.

Orden local: scope → deduplicación → frescura → SECOP II → vigencia → selección
de candidatos → documentos. `eligible_total` conserva todos los SECOP II;
`eligible_recent` conserva los recientes con cualquiera de las tres vigencias;
`eligible` contiene solo recientes open. Unknown nunca se elimina del output,
pero no abre documentos automáticamente. La corrida completa aplica los límites
documentales después de filtrar a open; mantiene el caso individual Boyacá +
refrigerio, no ejecuta un plan documental de seis búsquedas.

Por consulta y en el resumen consolidado se guardan secop_ii_recent,
secop_ii_open, secop_ii_closed, secop_ii_unknown y
provider_status_deadline_conflicts. Estos contadores cubren **SECOP II recientes**,
antes del límite de selección documental. Open+closed+unknown = secop_ii_recent.
El consolidado deduplica entre búsquedas; cada consulta cuenta sus coincidencias.
Los warnings de vigencia globales se emiten una vez por proceso reciente SECOP II;
los históricos/otras fuentes conservan su validity_warning en el propio proceso.

Comandos desde `backend/`, para ejecutar solo tras autorización:

```powershell
# Discovery del plan, sin documentos
.\.venv\Scripts\python.exe scripts/eureka_licitaciones_cdp.py `
  --discovery-plan-only `
  --search-plan scripts/licitaciones_search_plan.v1.json `
  --recent-days 7

# Corrida completa individual: documentos solo de recientes SECOP II open
.\.venv\Scripts\python.exe scripts/eureka_licitaciones_cdp.py `
  --region boyaca --object refrigerio --profile-id 1086005 `
  --recent-days 7 --max-processes 30 --max-document-processes 3 --max-documents 2
```

Esta integración experimental solo se prueba offline en esta iteración. No
modifica Radar, DB, scheduler, scoring ni frontend. La metadata del proveedor
puede quedar desactualizada: open representa su deadline informado al evaluar,
sin verificación adicional de adendas o sincronización con SECOP.

## Frescura local antes de documentos

`--recent-days 7` aplica una ventana local a los procesos consolidados. El valor
predeterminado se configura con `default_recent_days` en
`scripts/licitaciones_search_plan.v1.json`; la CLI tiene prioridad. El modo completo
y `--discovery-only` leen ese mismo valor sin cargar ni ejecutar el plan de seis
búsquedas. `--check-session` conserva su sondeo y no aplica frescura comercial.

Desde `backend/`, para una futura corrida autorizada de discovery:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_licitaciones_cdp.py `
  --discovery-plan-only `
  --search-plan scripts/licitaciones_search_plan.v1.json `
  --recent-days 7
```

La secuencia local es ámbito región/objeto, deduplicación, frescura, SECOP II y
selección de candidatos. Se mantienen las seis búsquedas, payloads remotos,
page=1, límite 30, pausas y política de retry. No se envía fecha al portal ni se
añaden requests. UNSPSC continúa pendiente y desactivado.

Se toma una sola hora de referencia al iniciar la corrida, registrada como
`freshness_evaluated_at`, usando Bogotá (UTC−5). Los timestamps sin zona del
proveedor se interpretan en Bogotá; los que incluyen offset se comparan como
instantes. La ventana es inclusiva: edad entre cero y recent_days × 24 horas.
`age_days` muestra días fraccionarios (seis decimales); la decisión usa la edad
sin redondear. Hoy y seis días cumplen una ventana de siete; ocho días no.
El reloj puede inyectarse como `now` en las funciones para pruebas deterministas.

`discovery.json` conserva todos los procesos del ámbito, incluidos los históricos,
con published_at, age_days, recent y freshness_warnings. Las fechas inválidas o
ausentes se conservan, con age_days=null, recent=false y warning
`invalid_published_at`. Las fechas futuras tienen edad negativa, recent=false y
warning `future_published_at`. Ninguno de esos casos aborta el discovery: su
validación de fecha se difiere a esta capa; el preflight mantiene sus controles
de fecha/enriquecimiento independientes.

`eligible_total` conserva todos los SECOP II del ámbito; `eligible_recent` contiene
los recientes; `eligible` contiene los recientes open tras la validación de vigencia.
En la corrida completa, los límites de selección se aplican a esa última lista,
por lo que históricos, closed y unknown nunca abren inventario, descarga ni
extracción. La provenance de búsquedas coincidentes se conserva en el plan.

`search_plan_summary.json` y `run_summary.json` incluyen unique_processes_total,
unique_processes_recent, secop_ii_total, secop_ii_recent, stale_processes e
invalid_published_at, además de recent_days y la hora de evaluación. stale_processes
cuenta **todos los no recientes**, incluyendo fechas inválidas y futuras;
invalid_published_at es un subconjunto de ese contador. Los contadores anteriores
unique_processes/unique_secop_ii del plan siguen representando todos los procesos,
sin restringirse a recientes. Los warnings de frescura se cuentan una sola vez por
proceso consolidado. No se reescriben corridas históricas ya guardadas.

## Plan experimental de discovery suave

Esta extensión solo se ha probado offline. No se ejecutaron consultas reales como
parte de su implementación. La corrida completa anterior y los comandos
`--check-session`, `--diagnose-preflight` y `--discovery-only` se conservan.

Después de abrir Edge CDP, hacer login manual si hace falta y comprobar
`--check-session`, el comando del plan, desde `backend/`, es:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_licitaciones_cdp.py `
  --discovery-plan-only `
  --search-plan scripts/licitaciones_search_plan.v1.json
```

Ejecutarlo requiere autorización para la corrida real; no forma parte de las
pruebas offline. Omitir `--search-plan` usa ese mismo archivo por defecto.
Usar `--search-plan` sin `--discovery-plan-only` es un error para evitar activar
accidentalmente documentos. El modo no carga Settings, verifica Tesseract,
consulta inventarios, descarga archivos ni ejecuta OCR.

El JSON versionado separa regiones, términos explícitos, límites, pausas y
búsquedas. Las seis entradas son Boyacá/refrigerio, Boyacá/papeleria, Boyacá/aseo,
Casanare/refrigerio, Casanare/papeleria y Casanare/aseo, en ese orden. No se genera
una matriz cartesiana. Hay nueve términos disponibles, sin expansión de sinónimos.
Boyacá reutiliza el archivo local ignorado de 123 IDs existente, conservando su
orden; Casanare contiene exactamente los 19 IDs validados, 4009001–4009019.
Las rutas del archivo de IDs y del catálogo son relativas al JSON del plan.

Los límites se validan antes de conectar CDP: perfil 1086005, máximo seis búsquedas,
30 resultados solicitados, página 1, un retry como máximo y pausas entre 3 y 60
segundos. Por defecto se esperan cuatro segundos entre búsquedas y cuatro antes
del único retry. Se reutilizan las columnas, byColumn=1, FechaPublicacion DESC y
el POST get-info del adapter. `query` solo lleva Objeto y ubicacion_filter.
El plan no cambia filtros de la UI. Un preflight separado añade GET get-config-user
y un sondeo get-info sin filtros; no cuenta como búsqueda comercial. El máximo
de solicitudes es 14: dos de preflight y seis búsquedas con hasta dos intentos.

Las llamadas son estrictamente secuenciales. Solo 5xx o timeout identificado por
Axios permiten retry. Una segunda falla transitoria en la misma búsqueda detiene
el plan (`repeated_provider_failure`); con retries=0, se detiene en la primera.
401/419, perfil no disponible, dataset genérico y 429 detienen inmediatamente.
Dos búsquedas consecutivas con respuestas inválidas o enriquecimiento insuficiente
detienen con `repeated_invalid_response`, sin retry. Una búsqueda exitosa reinicia
ese contador. El preflight conserva su validación de salud y sus códigos de salida;
no hay login automático. Una respuesta filtrada vacía válida se admite después
de un preflight saludable. El plan exige al menos 80 % de filas enriquecidas,
omite filas incompletas con warning y rechaza páginas con más de 30 filas.

El filtrado local exige departamento coincidente y el término explícito dentro
del Objeto, normalizando mayúsculas y acentos. Los procesos que cumplen ambos
se consolidan; la lista `eligible` aplica localmente id_fuente_contract==3 **o**
key_config==secop2. Las filas fuera del ámbito se cuentan en rows_received y
generan warning, pero no se incorporan a oportunidades consolidadas.
La deduplicación usa fuente/perfil/id_contrato, con fallback a fuente/perfil/
CodigoProceso cuando falta id_contrato. Conserva matched_searches, matched_objects
y matched_regions sin duplicados. duplicates_across_queries cuenta apariciones
adicionales entre búsquedas, excluyendo repeticiones dentro de una misma respuesta.

UNSPSC permanece `pending_remote_mapping`. Se lee el catálogo JSON ya existente
`config/eureka_radar.v1.json`, sin activar servicios Radar ni modificarlo. Ese
archivo contiene **ocho familias y 44 códigos únicos**, no ocho códigos: no se
inventó ni seleccionó arbitrariamente un subconjunto de ocho. Cada búsqueda puede
declarar `"unspsc": ["50192703"]` usando solo códigos de ese catálogo; se registra
la intención y un warning, pero **no se envía ningún filtro UNSPSC**. Se rechazan
keys remotas o un estado distinto de pending_remote_mapping hasta validar el
contrato real en otra iteración. `matched_unspsc` queda vacío, pues declarar un
código pendiente no demuestra que el proceso lo haya cumplido.

Se crea un directorio nuevo bajo `.local/spike_licitaciones_info/experimental-cdp-*`
con `discovery.json`, `search_plan_summary.json` y `run_summary.json`. Se guardan
resultados parciales tras cada búsqueda y al finalizar, incluso al abortar. El
resumen contiene conteos planeados/ejecutados/exitosos/fallidos, filas recibidas,
únicos, SECOP II, duplicados, duración y stop_reason. Cada búsqueda conserva
región, término, UNSPSC solicitado, payload enviado, count del proveedor, filas,
elegibles, intentos, estado, duración y warnings. No se guardan cookies, tokens,
passwords, headers ni cuerpos completos de configuración del usuario.

Pendientes explícitos: filtro remoto Portal, Entidad, Cuantía, Modalidad, Número,
Estado, Fecha de publicación, Contratistas, Participantes, Actividad económica,
paginación más allá de 30, fecha relativa últimos N días, combinaciones masivas,
concurrencia, scheduler, integración Radar/DB, login automático y UNSPSC remoto.
La estabilidad del plan de seis consultas y el volumen por región/término deben
comprobarse en una corrida real pequeña autorizada posteriormente.

## Candidate adapter experimental: flujo recomendado

El flujo empaquetado ya reprodujo el spike en una corrida real controlada. Esta
iteración añade hardening y contratos `licitaciones-candidate-v1`; sus cambios solo
se prueban offline hasta una nueva autorización. Sigue fuera del producto.

Desde `backend/`, el orden recomendado es:

A. Abrir Edge: `.\.venv\Scripts\python.exe scripts/licitaciones_cdp_open.py`.

B. Hacer login manual si hace falta y abrir Contratos desktop desde Vila Frontier.

C. Comprobar salud:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_licitaciones_cdp.py --check-session
```

Este modo valida CDP, una pestaña desktop válida, sesión y acceso al endpoint del
perfil `1086005`. Envía GET get-config-user y un POST mínimo a get-info/MP con
`limit=30`, `page=1`, `query={}`, FechaPublicacion DESC y las columnas validadas.
La respuesta debe tener filas y exponer CodigoProceso, FechaPublicacion,
id_fuente_contract y key_config. Al menos el 80 % de las filas debe tener referencia,
fecha parseable e id_fuente_contract/key_config no vacíos. 27/30 (90 %) es saludable;
no se exige 100 %. No hace discovery comercial, no
filtra candidatos, no escribe discovery.json ni crea inventarios, binarios o OCR.
Para verificar get-info es inevitable enviar ese sondeo: no se usa una respuesta
cacheada como prueba de sesión vigente. Informa la última publicación observada;
no impone una fecha de corte ni garantiza la frescura de sincronización del proveedor.

Para diagnosticar un rechazo sin modificar el criterio de aceptación:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_licitaciones_cdp.py --check-session --diagnose-preflight
```

Este modo adicional imprime y guarda `preflight-diagnostic-*.json` bajo `.local`:
host, payload exacto, status/JSON/endpoint, count, filas, limit/page, primeras tres
referencias, presencia de campos enriquecidos y `invalid_criterion`. No guarda el
cuerpo completo, headers o estado del navegador. También guarda enriched_rows,
enriched_ratio, min_enriched_ratio y warnings. El sondeo envía `query={}` y
`limit=30`. Si el proveedor devuelve más filas que las solicitadas, se registra
`provider_ignores_limit` como warning: nunca invalida la sesión por sí solo.
Se conserva el diagnóstico histórico del falso negativo con limit=1, pero esa
condición ya no se usa como rechazo de sesión.

La validación de salud está separada de `validate_discovery`: discovery mantiene
sus controles estrictos de límite/identidad y no se amplía su volumen. Se mantiene
el rechazo explícito de count=1337370 como universo genérico conocido; además se
verifican JSON, filas, campos esperados, fechas y proporción de enriquecimiento,
por lo que un count diferente no basta para declarar sesión saludable. El umbral
técnico está en `SESSION_ENRICHED_RATIO_MIN=0.8`, dentro del código experimental.

El preflight clasifica primero cada fila, sin usar `id_fuente_contract`, `key_config`
ni el flag no validado `EsSecop`. Identifica `secop_candidate` por hostname exacto
`community.secop.gov.co`, `contratos.gov.co` o `www.contratos.gov.co` en `Link`, o
por un identificador completo `CO1.NTC.<dígitos>` / `CO1.REQ.<dígitos>` en
`idUltimaFase`, `noticeUID` o `CodigoProceso`. No acepta coincidencias parciales
de dominio ni URLs con userinfo como evidencia oficial. Sin evidencia SECOP,
un enlace HTTP(S) externo válido es `external_candidate`; el resto, `unknown_source`.

Solo la población SECOP identificada entra en el denominador del 80 %. Una fila
SECOP sin código, fuente, key o fecha parseable permanece en ese denominador como
`secop_unenriched`, incluso si la clave falta completamente. Una muestra no vacía
es el mínimo; no se añade otro umbral de tamaño de muestra. Sin ninguna fila
SECOP identificable, el resultado es `preflight_status=inconclusive`,
`reason=insufficient_secop_sample`, ratio `null` y salida 19: se detiene antes de
discovery sin pedir login. Con calidad insuficiente se informa
`unhealthy_response`; con calidad suficiente, `healthy`. Un 401/419 conserva
`session_expired` y su instrucción manual.

Diagnóstico y logs incluyen `rows_total`, `secop_candidates`, `external_candidates`,
`unknown_source_rows`, `secop_enriched`, `secop_unenriched`,
`secop_enriched_ratio`, `min_enriched_ratio`, `preflight_status` y `reason`.
Los alias históricos `enriched_rows` / `enriched_ratio` ahora describen la muestra
SECOP en el preflight. Discovery conserva su contrato anterior sobre las filas
del resultado comercial; no cambian búsquedas, filtros, límites ni gates.

D. Opcionalmente ejecutar solo discovery:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_licitaciones_cdp.py --discovery-only `
  --region boyaca --object refrigerio --profile-id 1086005 --max-processes 30
```

Genera únicamente `discovery.json` y `run_summary.json` en un directorio nuevo.
No consulta documentos, no crea storage, no descarga archivos ni ejecuta OCR.
Ambos modos ligeros omiten la configuración y comprobación de Tesseract: funcionan
sin OCR instalado. `--check-session` y `--discovery-only` son excluyentes.

E. Ejecutar la corrida completa con el comando 30 / 3 / 2 descrito abajo.

Cada corrida de discovery/completa realiza el mismo preflight mínimo antes del
discovery comercial. La consulta de salud no cambia los filtros de la UI.
No hay login automático, cambio de perfil, navegación forzada ni nuevos contextos.

### Errores operativos

| Código de salida | Identificador | Acción |
|---|---|---|
| 0 | healthy/completed/completed_with_warnings | Revisar warnings y cobertura |
| 1 | fallo inesperado/configuración local | Revisar el resumen y configuración |
| 2 | errores parciales de documentos | Se conserva el resto de la corrida |
| 10 | cdp_unavailable | Abrir Edge con el helper CDP |
| 11 | invalid_tab | Dejar una única pestaña Contratos desktop en col.licitaciones.info |
| 12 | session_expired | Iniciar sesión manualmente y volver a ejecutar |
| 13 | profile_unavailable | Seleccionar Vila Frontier desde la UI y comprobar permisos |
| 14 | invalid_get_info | Revisar formato/universo del proveedor; no se intenta fallback |
| 15 | preflight_failed | Revisar carga de la aplicación/sesión y volver a ejecutar |
| 16 | generic_dataset | El proveedor devolvió el universo genérico conocido; revisar contexto |
| 17 | invalid_response | JSON, filas, campos o endpoint no válidos; revisar diagnóstico |
| 18 | insufficient_enriched_rows | Menos del 80 % de las candidatas SECOP enriquecidas en preflight; revisar respuesta |
| 19 | insufficient_secop_sample | Preflight inconcluso, sin muestra SECOP identificable; no pedir otro login |

HTTP 401/419 se clasifican como sesión no aceptada/expirada y detienen la corrida,
también si ocurren durante inventarios. HTTP 403/404 en el endpoint del perfil se
clasifican como `profile_unavailable`: esto informa indisponibilidad del endpoint,
sin afirmar si la causa es permiso, perfil o cambio del proveedor. Una respuesta
200 con count genérico es `generic_dataset`. JSON inválido, filas vacías,
redirección inesperada o campos ausentes es `invalid_response`. Calidad inferior
al umbral es `insufficient_enriched_rows`. `invalid_get_info` queda reservado para
el contrato estricto de discovery; no clasifica el exceso de filas del sondeo.
El error no desencadena login, reintentos agresivos ni filtros alternativos.

Los logs usan etapas `preflight`, `discovery`, `documents`, `extraction`, `summary`.
No incluyen cookies, tokens, credenciales, valores de headers ni detalles internos
de las excepciones CDP. El modo de salud imprime el estado y no crea artefactos.

### Contratos y deduplicación

Definiciones: `backend/scripts/licitaciones_candidate_contracts.py`. Los contratos
son internos al experimento y versionados en la salida; no hay tablas ni adapter
productivo nuevo. Los identificadores son cadenas y los importes decimales también
se representan como cadenas para evitar pérdida de precisión. Importes no parseables
quedan null, con el valor original en la referencia fuente.

- Proceso: external_source, profile_id, codigo_proceso, entity_name, object,
  department, municipality, published_at, amount, id_contrato, id_fuente_contract,
  id_ultima_fase, key_config y raw_source_reference. La referencia estable es
  `licitaciones_info:<profile_id>:<id_contrato>`; raw_source_reference conserva
  identificadores y metadata pública original, no estado del navegador.
- Documento: process_reference, document_reference, document_name, document_type,
  extension, secop_document_id, source_url, extraction_mode, extraction_status,
  total_pages, processed_pages, coverage_ratio, text_length y warnings. Se usa
  `<process_reference>:document:<secop_document_id>`. Los inventarios conservan
  documentos no seleccionados con `not_selected`; fallos de descarga/extracción
  quedan explícitos. Fragments, diagnósticos, hashes y rutas locales se conservan.
- Hecho: process_reference, document_reference, fact_type, value, unit,
  normalized_value, confidence, suspicious, evidence_text, page_reference,
  extraction_mode y coverage_ratio. `provenance` conserva el hecho original con
  source_locator, spans, IDs de fragments/runs y confianza original. El modo de
  extracción del contrato es el del documento; la provenance conserva el método
  concreto de cada página nativa/OCR.

Deduplicación básica: igualdad exacta de proceso, documento, tipo, valor, unidad y
normalized_value. No corrige texto, espacios, marcas, aliases ni unidades; tampoco
fusiona documentos/procesos diferentes. En un grupo se conserva el primer hecho,
`occurrences` y todos los hechos/evidencias originales en `provenance_records`,
incluidas sus páginas. Se conserva la menor confianza y cualquier marca suspicious.
Los flags de cobertura incompleta nunca se convierten en cobertura completa al
deduplicar. No se calculan canonical facts.

Resumen explícito: full_coverage_documents, partial_coverage_documents,
native_documents, ocr_documents, mixed_documents, suspicious_facts,
raw_facts_found, facts_found y facts_deduplicated. Los modos son categorías
excluyentes; mixed tiene su propio contador. Partial cuenta documentos extraídos
sin cobertura completa. Los fallos sin resultado de extracción se contabilizan
como errores, no como documentos completos. Se mantiene el límite OCR de 20 páginas.

## Corrida completa y configuración

Desde `backend/`, con las dependencias locales del proyecto, OCR y
`scripts/requirements-licitaciones-spike.txt` instaladas:

```powershell
.\.venv\Scripts\python.exe scripts/licitaciones_cdp_open.py
```

El helper abre Edge visible con `--remote-debugging-address=127.0.0.1`,
`--remote-debugging-port=9222` y el perfil dedicado
`backend/.local/spike_licitaciones_info/edge-cdp-profile`. Si el puerto ya ofrece
CDP válido, lo reutiliza sin abrir otra instancia. Si está ocupado sin CDP válido,
se detiene; nunca mata navegadores. Si Edge no está instalado, informa el error.
Un perfil que ya estaba abierto sin debugging debe cerrarse manualmente antes de
reintentar. El perfil conserva cookies gestionadas por Edge, sin exportarlas.
No guardes contraseñas en el administrador del perfil dedicado.

Haz login manual si hace falta y entra a Contratos desde la UI. Deja una única
pestaña desktop funcional en `col.licitaciones.info`, con Vila Frontier activo.
El comando no navega para cambiar de host si solo encuentra `mcol` ni rehace login.

Después, únicamente cuando se autorice la corrida real:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_licitaciones_cdp.py `
  --region boyaca `
  --object refrigerio `
  --profile-id 1086005 `
  --max-processes 30 `
  --max-document-processes 3 `
  --max-documents 2
```

Lee los 123 IDs del archivo local ignorado
`backend/scripts/.local/licitaciones_boyaca_ids.txt`. No los reemplaza por una lista
inventada. La configuración OCR habitual se lee de `backend/.env`: OCR habilitado,
política con idioma `spa`, comando Tesseract y tessdata disponibles. Comprueba
Tesseract real, `spa` y las dependencias OCR antes de conectar. No requiere
variables temporales ni modifica `.env`.

La conexión usa exclusivamente `connect_over_cdp`. Desde la pestaña existente usa
el cliente `window.axios` de la aplicación: el `fetch` independiente del primer
spike no conservaba todo el contexto necesario para documentos. El bootstrap pide
`get-config-user` y exige 200 JSON en el endpoint esperado; sus datos de usuario
no se trasladan al script. Luego ejecuta una sola primera página de
`get-info/MP?perfiles=1086005` con el contrato validado. Exige filas identificables,
fechas parseables y `id_fuente_contract`/`key_config`; rechaza el universo genérico
observado y respuestas que ignoran el límite. Un resultado filtrado vacío se
registra con advertencia: no permite demostrar campos enriquecidos. No se fuerza
count 31 ni referencias concretas, ni se depende de get-conteo. Estas comprobaciones
no garantizan frescura de sincronización del proveedor ni que todo proceso siga abierto.

Filtra localmente Boyacá, coincidencia del término en Objeto, SECOP II y duplicados
por idContrato. Una fila de alcance nacional no bloquea las demás; se registra
excluida. Se consultan documentos de los primeros tres elegibles, sin privilegiar
casos conocidos ni aplicar reglas comerciales productivas.

El parser usa el contrato real `documentos.campos`, con encabezados
Item/Nombre/Tipo/Documento y enlaces HTML recibidos. No construye URLs. Consulta
páginas hasta vacío; una página repetida, formato desconocido o diez páginas sin
fin generan error de inventario incompleto. Prioriza invitación, estudios previos,
especificaciones, anexo técnico y ficha técnica; máximo dos PDF/DOCX/XLSX por proceso.

Reutiliza `SecopDownloader`, `LocalBinaryStorage`, `ExtractionService`, extracción
nativa, fallback OCR y reglas estructuradas existentes del spike. Descargas HTTPS
SECOP con streaming, temporales, validación y movimiento atómico: máximo 20 MiB y
60 segundos por archivo. No envía cookies de Licitaciones a SECOP. Mantiene un
presupuesto conservador de 60 requests (reservando hasta seis por descarga), al
menos 2,1 segundos entre operaciones y timeout API de 20 segundos; sin reintentos
agresivos ni get-conteo. No abre sesiones DB; extracción en dry-run con fábrica DB
prohibida. Desconecta sin cerrar el Edge externo.

Cada ejecución escribe atómicamente, bajo un nuevo directorio
`backend/.local/spike_licitaciones_info/experimental-cdp-*/`:

- `run_summary.json`: límites, OCR real, conteos, modos, hechos, sospechas y errores.
- `discovery.json`: payload, count recibido, metadata pública, elegibles y exclusiones.
- `documents.json`: inventarios, selección y descargas con hash/ruta/tamaño/tipo.
- `extraction.json`: texto/fragments/provenance, diagnósticos y hechos anotados.
- `binaries/`: binarios aislados; no se usa el almacenamiento productivo.

OCR truncado conserva `extraction_status=ocr_truncated`, páginas requeridas,
procesadas/omitidas, total y ratio de páginas cubiertas. La cobertura combina
páginas nativas válidas y OCR exitoso, sin contar intentos fallidos como éxito.
Los hechos de documentos incompletos tienen `document_coverage_complete=false` y
`usable_as_complete_evidence=false`. No se consolidan canonical facts en esta fase.

La política experimental `scripts/licitaciones_fact_policy.v1.json` marca
`suspicious=true` por rangos numéricos técnicos de revisión, falta de evidencia o
producto no respaldado. Conserva valor/evidencia/provenance y `original_confidence`;
solo reduce la confianza del hecho experimental marcado. Por ejemplo, 1509 g en
una presentación individual queda para revisión. Los límites pueden señalar
presentaciones legítimas grandes: no son una decisión comercial ni corrección OCR.
No modifica catálogo, scoring o reglas productivas. Los hechos permanecen en JSON,
incluidos los sospechosos y los procedentes de cobertura parcial.

Códigos de salida y errores de preflight: ver la tabla anterior.
Nunca registra headers de autenticación, cookies, tokens o storage_state.
Todo `.local` sigue ignorado por Git. Sin DB, Radar, scheduler, alertas, migraciones,
Socrata o frontend. Sin autenticación automática ni bypass de CAPTCHA.

Pruebas offline:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_licitaciones_candidate.py tests/unit/test_eureka_licitaciones_cdp.py tests/unit/test_licitaciones_cdp.py tests/unit/test_spike_licitaciones_info.py -q
```

Las siguientes secciones conservan el procedimiento manual y el observador pasivo
usados para validar CDP originalmente; el comando nuevo realiza el discovery
autorizado directamente mediante el cliente de la aplicación.

Este experimento sustituye la reconstruccion de sesiones por conexion a una
pestana funcional existente. No usa storage_state, cookies exportadas, replay,
DB, Radar, documentos ni OCR. El helper solo observa respuestas nuevas de get-info;
no puede recuperar respuestas anteriores a su conexion.

## 1. Abrir Edge manualmente

Desde PowerShell en la raiz del repositorio, ejecuta tu mismo:

```powershell
$cdpProfile = Join-Path (Get-Location).Path 'backend\.local\spike_licitaciones_info\edge-cdp-profile'
& 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 "--user-data-dir=$cdpProfile" 'https://licitaciones.info/'
```

Es un perfil dedicado, diferente de tu perfil habitual. No cierres otros
navegadores para realizar esta prueba. Si reinicias este perfil, primero cierra
sus ventanas manualmente; no reutilices una ventana iniciada sin debugging.
El perfil contiene la sesion gestionada por Edge y queda dentro de `.local`,
ignorado por Git. El helper no exporta ni copia esa sesion.

Para Chrome, sustituye el ejecutable por el instalado en tu equipo y usa otro
directorio dedicado, por ejemplo `chrome-cdp-profile`, con los mismos flags.
No uses el directorio de perfil normal. Manten el puerto solo en localhost;
no abras reglas de firewall ni lo expongas a la red.

Puedes comprobar sin leer cookies ni tokens:

```powershell
Test-NetConnection 127.0.0.1 -Port 9222 -InformationLevel Quiet
```

## 2. Login y validacion manual, antes de conectar

Haz login manualmente en ese navegador y entra a Contratos mediante la UI.
No navegues directamente a Contratos ni fuerces parametros. Resuelve personalmente
cualquier CAPTCHA. Confirma:

- Contratos carga y muestra el perfil y procesos actuales.
- get-config-user, get-contadores-perfiles-nuevos y get-estados-proceso: HTTP 200.
- get-info: HTTP 200 JSON con procesos actuales y campos enriquecidos.
- get-conteo: HTTP 200.

Si falla esta validacion, detente: conectar CDP no corrige la sesion. Deja una
unica pestana Contratos en este perfil para evitar ambiguedad.

## 3. Conectar el observador, solo despues de confirmar lo anterior

Desde la raiz del proyecto:

```powershell
& '.\backend\.venv\Scripts\python.exe' '.\backend\scripts\observe_licitaciones_cdp.py' --cdp-url http://127.0.0.1:9222 --minutes 60
```

No lanza navegador, no crea context/page, no navega ni vuelve a hacer login.
Observa la unica pestana Contratos existente. Despues de ver `Conectado`, realiza
una accion normal de la UI que genere get-info (por ejemplo, cambiar de pagina).
No apliques aun Boyaca/refrigerio. El helper guarda status, content-type, count,
primeras cinco referencias/departamento/objeto/fecha y campos de fuente, sin
headers de autenticacion, cookies, request bodies ni almacenamiento del navegador.

Salida: `backend/.local/spike_licitaciones_info/cdp-observe-*/observation.json`.
Se actualiza con cada respuesta. Un count distinto del generico no es por si solo
validacion: compara referencias, fechas, campos enriquecidos y tabla visible.
Ctrl+C o timeout desconectan al observador sin cerrar el navegador externo.

## 4. Puertas de validacion

Primero revisar una respuesta correcta observada por CDP contra la UI. Solo tras
esa revision, aplicar manualmente Boyaca + Objeto `refrigerio` en la misma pestana
y comparar nuevamente. No se modifica ningun filtro desde el helper. No hay
implementado un salto automatico a documentos/OCR: esa siguiente etapa requiere
validar esta observacion y mantener la misma sesion funcional.

Pruebas offline del helper:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest backend/tests/unit/test_licitaciones_cdp.py -q
```
