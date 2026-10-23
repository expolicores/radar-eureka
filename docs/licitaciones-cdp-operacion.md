# Licitaciones.info (CDP): operación manual en Eureka

Implementación operativa local. La migración y la primera corrida integrada deben validarse antes de usarla en producción. Esta entrega no ejecuta requests reales ni aplica migraciones a la base operativa.

## Arquitectura y plan aplicado

Se reutilizan `eureka.radar_run` y sus resultados por proceso; la operación se separa mediante `source=licitaciones_info_cdp`. `metrics` guarda funnel, búsquedas, warnings y duración. Los resultados conservan la metadata, matched_searches, evidencia original, etapa, motivo, decisión y revisión documental. Radar conserva su historial filtrado por `source=socrata`.

El módulo `public_procurement.licitaciones_cdp` coordina sesión, discovery y progreso. Su adapter carga los scripts validados del repositorio y se conecta únicamente al Edge CDP existente. No crea páginas, contextos ni sesiones. El worker manual arranca solo al pulsar el botón; no hay tarea programada CDP ni ejecución al arrancar la aplicación.

La operación inyecta un inventario documental en `ExistingRadarPipeline`, el mismo pipeline de Radar: persistencia del proceso → evaluación Eureka → documentos → extracción nativa/OCR → facts → consolidación → detalles/scoring → decisión de alerta. No se copian reglas comerciales. Las alertas se guardan en la tabla y bandeja existentes. Se preserva el score existente cuando corresponde reutilizar canonicals completos.

Se implementaron incrementalmente persistencia/source, caso de uso, conexión al pipeline, dedupe, endpoints, UI y pruebas. La corrida real es el paso pendiente, sujeto a autorización.

## Políticas y gates

El preflight separa fuentes externas de la población SECOP antes de medir calidad
(ver [heurística y diagnósticos](spike-licitaciones-cdp.md)). Mantiene el umbral
del 80 % sobre las candidatas SECOP identificadas por URL oficial o identificador
SECOP, independientemente de source ID/key_config. Las SECOP incompletas penalizan
el ratio. Una página totalmente externa es inconclusa, no una sesión expirada.
El motivo `insufficient_secop_sample` y las métricas quedan en el resumen y en
`metrics.preflight`; la UI diferencia esa causa de `unhealthy_response` y de la
sesión expirada, sin sugerir login en los dos primeros casos. Se reutiliza el
estado de corrida `failed` para el bloqueo, sin nueva migración. Los controles
de endpoint/perfil/JSON/universo genérico y los gates comerciales no cambian.

- Seis búsquedas: Boyacá y Casanare, cada una refrigerio, papeleria y aseo, en ese orden.
- Secuencial, pausa de 4 segundos, página 1, límite 30, un retry transitorio por consulta. Preflight previo validado.
- Sin fechas remotas, UNSPSC, login automático, CAPTCHA ni cambios automáticos de filtros.
- Se conservan todos los procesos descubiertos; recent=true y open pueden avanzar con identidad y metadata útiles, independientemente de la fuente. Los documentos dependen de capacidad validada; las demás fuentes siguen metadata-only. Ver [semántica de agregador y revisión](licitaciones-cdp-agregador.md).
- Frescura local: 7 días. `FechaVencimiento` se interpreta en America/Bogota. Deadline futuro=open; vencido=closed; ausente/inválido=unknown. EstadoProceso es evidencia, nunca decide vigencia.
- Hasta 3 procesos documentales y 2 documentos seleccionados por proceso. Inventario secuencial; no hay búsqueda masiva. Los documentos históricos permanecen guardados, pero no amplían la selección de descarga/extracción de esta corrida.
- Priorización validada: invitación, estudios previos, especificaciones, anexo/ficha técnica. Descargas HTTPS SECOP limitadas a 20 MiB/60 segundos; un retry para network_error/timeout, pausa 4 segundos.
- OCR compartido con máximo 20 páginas; conserva cobertura y evidence. Suspicious, partial y missing activan «Requiere revisión documental manual», sin introducir un nuevo filtro comercial o de scoring.
- Se vuelve a comprobar frescura/vigencia antes de consultar el inventario por si el deadline venció durante la corrida.

## Revisión documental al reutilizar evidencia

La revisión operacional combina por OR señales de la corrida actual y anotaciones
documentales persistidas en corridas CDP terminadas del mismo `process_reference`
exacto. Excluye la corrida en curso y otras fuentes/procesos. La lectura es local;
no consulta el portal ni modifica facts, canonicals, documentos o alertas previas.

Se conservan `suspicious_fact`, fallos de extracción/formato, OCR truncado,
cobertura parcial, documentos ausentes y warnings que ya implicaban revisión.
Un resultado actual limpio o `facts=[]` no demuestra que un warning anterior fue
resuelto y no lo borra. No se añade un mecanismo de resolución automática de
warnings en esta corrección. Tampoco se vuelven a clasificar facts históricos:
se leen sus anotaciones persistidas, no se ejecuta la política suspicious otra vez.

`manual_review_reasons` y `manual_review_provenance` acompañan al resultado del
proceso, `document_review` y el snapshot de decisión. La provenance identifica
corridas de origen, motivos, IDs de facts sospechosos y versiones documentales.
Los facts reutilizados se referencian; no se insertan ni se copian como facts nuevos.
Scoring, elegibilidad, `create` y dedupe no cambian; únicamente se propaga la revisión.

La causa del caso CMI-2026078 fue la salida temprana `canonical_reused`, anterior
a `documents.sync`: el servicio `limit_to_synced` conservaba una selección vacía,
y `StructuredExtractionService.list_facts()` filtraba los 33 facts por un conjunto
vacío de fragmentos vigentes. Eso no borraba DB ni canonicals, pero una revisión
basada solo en esa lista perdía los flags anteriores. La corrección recupera el
estado operacional persistido sin ampliar ese scope ni forzar sync/descarga/OCR.

## Identidad y deduplicación

La clave global es la identidad SECOP exacta, preferiblemente `noticeUID=CO1.NTC.…` de la URL pública, o el identificador SECOP disponible. CDP aporta `id_ultima_fase=CO1.NTC.…`. No se utiliza idContrato como identidad global ni se infiere un REQ a partir de un NTC con el mismo número.

Una restricción única de `alert.canonical_key` impide la segunda alerta entre fuentes, incluso con oportunidades distintas. Ambas corridas conservan el hallazgo. CDP registra `duplicate_canonical`, cuenta alert_candidates/duplicate_alerts_skipped y evita repetir documentos cuando ya existe la alerta. Las reglas de alerta existentes siguen aplicándose para nuevas oportunidades. Las actualizaciones de evidencia de una alerta conservan su fuente original y registran la fuente de la nueva evidencia.

Límite conocido: sin noticeUID compartido o alias comprobable, un REQ y un NTC diferentes no se pueden reconciliar con certeza. No se implementa reconciliación avanzada. Los duplicados históricos existentes no se eliminan.

El proceso CDP utiliza el notice SECOP como referencia de persistencia y agrupación documental local. Ese valor **no representa un id de portafolio BDOS**; no se inventa ni se consulta un portafolio por Socrata. Los IDs y URLs de cada documento conservan su procedencia real.

## Migración y arranque

`0018_licitaciones_cdp` depende de `0017_offer_deadline`. Agrega únicamente source/metrics al modelo de corrida y canonical_key único a alertas. El backfill identifica la alerta histórica más antigua por clave; no borra historial. No crea tablas nuevas. Hacer backup y aplicar la migración con el procedimiento habitual del proyecto; no se ha ejecutado en esta entrega.

Desde `backend`, con la configuración habitual de DB y almacenamiento:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[cdp]'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn public_procurement.entrypoints.api.app:create_app --factory --reload
```

Desde `frontend`:

```powershell
npm.cmd run dev
```

Abrir `/eureka/licitaciones`. La bandeja compartida está en `/eureka/alerts`.

Antes de la corrida, desde backend, **solo si no hay Edge CDP abierto**:

```powershell
.\.venv\Scripts\python.exe scripts\licitaciones_cdp_open.py
```

Iniciar sesión manualmente, seleccionar Vila Frontier y dejar abierta Contratos desktop. Volver a la aplicación y pulsar «Ejecutar corrida Licitaciones.info». El backend debe correr en el mismo equipo/usuario de Edge, CDP en `127.0.0.1:9222`. Si la sesión falla, la UI muestra la instrucción manual; no intenta recuperarla con credenciales. No ejecutar una corrida hasta autorizar la validación real.

Se requieren los scripts validados del checkout y su configuración local de 123 IDs de Boyacá (`backend/scripts/.local/licitaciones_boyaca_ids.txt`), que no contiene credenciales. Playwright solo conecta por CDP: no hace falta instalar otro navegador. OCR necesita Tesseract y spa con la configuración existente de Eureka.

## API y UI

- `POST /api/eureka/licitaciones-cdp/runs`: inicio manual, 202 después de confirmar persistencia del inicio; 409 si ya hay ejecución o bloqueo de Radar. Sin parámetros para ampliar políticas.
- `GET /api/eureka/licitaciones-cdp/runs`: historial paginado de la fuente.
- `GET /api/eureka/licitaciones-cdp/runs/{id}`: estado, metrics, errores y resultados por proceso.

La vista muestra ayuda CDP, historial, duración, funnel, warnings y procesos con entidad/objeto/ubicación/publicación/deadline/monto/vigencia/etapa/resultado/motivo/revisión/alerta. Consulta progreso mientras hay una corrida activa. La bandeja existente etiqueta la fuente y revisión documental.

No se registran cookies, tokens, passwords ni headers sensibles. Los errores operativos publican código/tipo, no cuerpos del proveedor. La evidencia comercial persistida conserva sus controles habituales de acceso de la aplicación.

## Verificación y deuda

Pruebas locales sin red: gates open/closed/unknown/stale, sesión, errores aislados, retry limitado, facts con revisión, identidad exacta, duplicados en ambos sentidos, selección documental acotada, cableado al pipeline compartido, endpoints e inicio manual/UI. Se conservan las pruebas existentes de scoring, extracción y Radar.

Pendientes de operación: migración PostgreSQL real y corrida integrada controlada; login manual; posibles errores iniciales de red; OCR parcial a 20 páginas; falsos positivos de suspicious; sin scheduler CDP, paginación masiva, UNSPSC remoto ni comparador de fuentes.

El worker vive en el proceso backend, no es una cola durable. Reiniciar el backend interrumpe la ejecución; la próxima corrida marca la anterior de esa fuente como interrumpida. Mantener un solo worker de API local y no reiniciarlo durante la corrida. Las fuentes comparten el bloqueo de Radar para evitar solapamientos. Los servicios de notificación existentes no son invocados por esta operación: solo persiste alertas en la bandeja.

La dependencia actual de scripts del checkout impide distribuir este adapter únicamente como wheel. La extracción/canonicals mantienen sus semánticas existentes; las anotaciones de suspicious se preservan aparte como evidencia de revisión y no reescriben score/confidence de los hechos.

## Archivos de esta integración

### Hardening después de la primera corrida integrada

El lector compartido recibe el Content-Type de la versión documental ya persistida. Solo
acepta los tipos PDF/DOCX/XLSX conocidos; una firma inequívoca `%PDF-` del archivo verificado
selecciona PDF incluso con nombre sin extensión o MIME contradictorio. Si no hay firma PDF,
se usa el MIME reconocido y después una extensión soportada como fallback. La selección
de identidad, worker y fallback OCR usa ese formato, no solamente el nombre. No se renombran
los originales ni se agregan lectores/librerías. Se mantienen verificación de hash, aislamiento
y límites existentes.

Para las nuevas corridas, `metrics.extraction_metrics_version=2`:

- `extraction_attempted`: resultados finales de extracción recibidos por documento,
  incluidos resultados reutilizados; no cuenta nativo y OCR como dos documentos ni cada
  subintento interno. Un fallo excepcional sin resultado se informa como error de proceso.
- `extraction_succeeded`: resultado completed/partial_text, sin error, con texto y fragmentos.
  Una extracción parcial con texto útil puede ser exitosa y requerir revisión simultáneamente.
- `extraction_failed`: resultado recibido que no cumple la condición anterior, incluidos
  unsupported_format, OCR sin texto y resultados vacíos.
- `extracted`: alias de extraction_succeeded; attempted = succeeded + failed.
- `process_errors` y `process_warnings`: cantidad de procesos distintos con al menos un
  error o advertencia respectivamente. Un proceso puede aparecer en ambos contadores.
- `process_error_details` / `process_warning_details`: detalles con código, proceso, etapa
  y versión documental cuando existe. Los errores también aparecen en run.errors y en
  el resultado de cada proceso. No se publican mensajes arbitrarios del proveedor.

Los fallos de extracción/descarga de documentos seleccionados marcan revisión manual,
incluso si impiden llegar a facts o canonicals. Se conservan las banderas cuando otro documento
sí aporta evidencia y se ejecuta la decisión comercial habitual. No se añade un gate de scoring
o alertas. Los fallos aislados y advertencias permiten completed_with_warnings.

Las corridas históricas mantienen su evidencia original. La UI distingue el antiguo extracted
(que incluía fallidos) y muestra el desglose desconocido como no disponible, sin fingir éxitos.
No se requiere migración: Content-Type ya existía en las versiones y metrics/result son JSONB.
La trazabilidad de cada subintento de retry sigue siendo deuda técnica: el retry acotado actual
puede recuperar una descarga dentro de un único acquisition_attempt persistido.

Esta corrección no ejecuta discovery, descargas ni una segunda corrida integrada real.

Archivos del hardening:

- `backend/src/public_procurement/extraction/domain/content.py`.
- `backend/src/public_procurement/extraction/adapters/{format_detection,documents,isolated}.py`.
- `backend/src/public_procurement/extraction/services.py`.
- `backend/src/public_procurement/eureka/adapters/radar_pipeline.py`.
- `backend/src/public_procurement/licitaciones_cdp/services.py`.
- `backend/tests/unit/extraction/{test_format_detection,test_ocr_pipeline}.py`.
- `backend/tests/unit/eureka/test_radar_pipeline.py`.
- `backend/tests/unit/operations/test_observer.py`.
- `backend/tests/unit/test_licitaciones_operations.py`.
- `frontend/src/features/licitaciones/{LicitacionesPage.tsx,LicitacionesPage.test.tsx}`.
- Esta guía.

Nuevos:

- `backend/src/public_procurement/licitaciones_cdp/{__init__,adapters,services,background,api}.py`.
- `backend/src/public_procurement/ingestion/domain/identity.py`.
- `backend/src/public_procurement/documents/adapters/retry.py`.
- `backend/alembic/versions/0018_licitaciones_cdp.py`.
- `backend/tests/unit/test_licitaciones_operations.py`.
- `frontend/src/features/licitaciones/LicitacionesPage.tsx` y `LicitacionesPage.test.tsx`.
- Esta guía.

Modificados:

- `backend/pyproject.toml`: dependencia opcional CDP y capa de arquitectura.
- `backend/src/public_procurement/entrypoints/api/app.py`: router, consultas y worker manual.
- `backend/src/public_procurement/ingestion/services.py`: exporta identidad compartida.
- `backend/src/public_procurement/documents/services.py`: inventario inyectable, retry opt-in y selección acotada; comportamiento por defecto conservado.
- `backend/src/public_procurement/extraction/services.py`: servicio documental inyectable y límite OCR opcional.
- `backend/src/public_procurement/eureka/{services,radar_services,radar_repositories,api}.py`: construcción compartida, source/metrics y dedupe global.
- `backend/tests/unit/documents/test_services.py`: límites ante inventario histórico.
- `frontend/src/{App.tsx,app/AppShell.tsx}`: ruta y navegación.
- `frontend/src/features/eureka/EurekaAlertsPage.tsx`: fuente y revisión documental en la bandeja existente.
- `frontend/src/api/{openapi.json,schema.ts}`: contrato HTTP actualizado.

El checkout ya incluía otros cambios de Radar/operaciones, migración 0017 y scripts experimentales. No se revierten ni se atribuyen a esta integración.
# Trazabilidad temporal de incidencias

Los warnings/errores nuevos conservan `code`, `message`, `run_id`, `generated_at`
UTC y `process_identity` exacta cuando aplica, además de la referencia/código y
documento ya disponibles. Las incidencias de discovery se marcan al generarse;
al regenerar diagnósticos de vigencia/frescura se conserva el primer timestamp
del evento dentro de esa corrida. Cada nueva corrida genera sus propios tiempos.
Los errores y warnings documentales se marcan al recibir el evento o capturar el fallo.
No se registran cuerpos privados de excepciones, cookies o headers sensibles.

Se usan los JSON existentes de corrida/proceso; no hay nueva tabla de eventos ni
migración de errores históricos. Los GET de corridas normalizan los históricos con
`generated_at=null` y `timestamp_status=not_recorded`: nunca usan inicio/fin de corrida
como hora ficticia del warning. Esta normalización de lectura no modifica el historial.

En `/eureka/licitaciones`, «Warnings y errores» muestra Fecha/Hora, código, proceso,
mensaje y corrida. La presentación es DD/MM/YYYY HH:mm:ss en America/Bogota.
Para históricos sin hora aparece «No registrada (histórico)».
Los endpoints GET `/api/eureka/licitaciones-cdp/runs` y `.../runs/{identifier}` conservan
sus rutas; se amplían los objetos de incidencias, no la política de ejecución.

