# Merecen Revisión

## Carga de la bandeja: últimos siete días

La lista consulta observaciones de corridas iniciadas en los últimos siete días
(`radar_run.started_at >= now - 7 días`), antes de proyectar y paginar. En PostgreSQL
se restringe además a referencias exactas de miembros persistidos de revisión,
incluyendo la identidad oficial explícita en la URL de origen. No se infieren
equivalencias NTC–REQ. Se omiten del listado los diagnósticos extensos de cobertura;
las banderas persistidas de cobertura parcial se conservan.

La ventana se refiere a cuándo se observó el proceso, no cambia su fecha inmutable
`review_first_seen_at` ni el orden por primera entrada. No se borran históricos,
evaluaciones ni evidencia: el detalle sigue disponible por identidad. La metadata
de procesos ya presente en resultados recientes se reutiliza; solo los resultados
incompletos necesitan una consulta puntual al proceso almacenado.

La tabla incluye «URL del proceso»: enlace HTTP/HTTPS de la fuente persistida,
abierto en otra pestaña; si falta, muestra «Sin URL disponible». No fabrica URLs.

Ruta local: `/eureka/revision`. Lista y detalle para analizar procesos ya descubiertos,
sin ejecutar discovery, descarga, OCR, consolidación, scoring ni creación de alertas.

## Datos y arquitectura

`ReviewRepository` lee `eureka.radar_run`, sus resultados por proceso, oportunidades
y alertas existentes. `HumanReviewService` proyecta esos resultados, completa metadata
con los procesos persistidos y reúne las observaciones por identidad exacta del origen
o ID estable del proveedor. La fuente no es un gate de admisión; ver el
[criterio de evidencia y advertencias del agregador CDP](licitaciones-cdp-agregador.md).
El detalle reutiliza los servicios de consulta de facts, extracciones y detalle Eureka.
No existe una segunda lógica de extracción documental.

Se conservan todas las fuentes (`socrata`, `licitaciones_info_cdp`), corridas y resultados
en el historial. No se infieren equivalencias NTC–REQ. Una alerta existente se enlaza
por identidad canónica exacta; esta vista nunca crea ni promueve alertas.

La proyección consolida referencias históricas `licitaciones_info:<perfil>:<id>`
con identidades oficiales SECOP I/II cuando una observación CDP persistida vincula
esa referencia exacta con una única identidad oficial. Una referencia ambigua no
se fusiona; tampoco se compara por texto, entidad o número de proceso aproximado.
`equivalent_identities` y el historial conservan las identidades originales y la
referencia del proveedor. La consolidación ocurre antes de filtros, orden y paginación.

Se toma el menor `review_first_seen_at` válido de las identidades equivalentes,
sin modificar las filas originales. Se reúnen sus alertas y evaluaciones humanas;
la evaluación visible es la más reciente por `reviewed_at`, y `manual_assessments`
conserva todas las notas/evaluaciones para consulta en el detalle. No se borran datos.
`source_metadata_review` se omite de los motivos visibles, incluso si aparece en
evidencia histórica. La fuente se conserva como provenance, no como motivo negativo.

## Contadores de corrida CDP

`review_candidates` mantiene su significado y `review_candidates_total` lo hace
explícito: procesos que cumplen el criterio de revisión. No significa nuevas entradas.
`review_new_entries` cuenta inserciones confirmadas con `INSERT … ON CONFLICT DO NOTHING
RETURNING`; `review_existing_entries` cuenta conflictos con entradas ya existentes.
El resultado se guarda en el outcome del proceso como `review_entry` y se conserva
durante las posteriores actualizaciones de esa misma corrida. Así, una entrada
insertada al persistir metadata no se reclasifica como existente al guardar el resultado.
Para candidatos persistidos: `new + existing = total`. Estos contadores históricos
no representan el número visible en la bandeja. Si existe una alerta nueva o previa
para la identidad exacta (o un alias comprobado), el proceso se muestra únicamente
en Alertas. Se excluye de Merecen Revisión antes de filtros y paginación, incluso
con `include_excluded=true`. Se conservan notas, primera entrada y evidencia histórica;
no se borran alertas ni se alteran scoring o dedupe. Esta vista nunca promueve alertas.

Las corridas históricas sin ese desglose muestran «No registrado (histórico)»;
no se rellenan contadores retrospectivos a partir de la UI.

## Inclusión y orden

Desde la corrección de admisión de 24/10/2026, la pertenencia persistida en
`manual_process_review` es obligatoria: los resultados de corrida por sí solos no
crean una fila visible. Socrata no tiene un bypass de evidencia. Ambos orígenes
necesitan señal comercial real: coincidencia del catálogo/UNSPSC/candidate_terms,
búsqueda comercial validada, score preliminar positivo o facts comerciales relevantes.
Título, ubicación, monto, publicación y deadline desconocido no bastan.

Una exclusión fuerte requiere evidencia independiente adicional, como score positivo
o facts comerciales confirmados; su propio trigger textual no es una excepción.
Un deadline desconocido con señal comercial puede entrar como «Deadline por verificar».
Los descartes sin señal no se insertan y permanecen íntegros en el detalle de corrida.
`record_review_entry` se llama únicamente si `review_candidate=true`.

La admisión de revisión usa los matchers existentes, sin modificar sus reglas ni la
decisión comercial. La metadata completa se conserva ahora en los outcomes Socrata,
incluido el deadline, para evitar que una fila descartada pierda su información al
proyectarse. Los contadores añaden rechazos de revisión por falta de señal,
deadline-only y exclusión fuerte; no reemplazan los del funnel comercial.

La lista se revalida al volver a la pestaña y cada 15 segundos; el endpoint usa
`Cache-Control: no-store`. Una limpieza en DB elimina su pertenencia efectiva y la
UI sustituye el resultado almacenado en caché por la respuesta real del backend.

Entran observaciones SECOP identificables con objeto disponible, incluidos diferidos
por límite, evaluados no elegibles, procesos sin alerta, con score, con canonicals o
con revisión documental. Los procesos que ya tienen alerta se consultan en Alertas.
Las filas sin identidad o metadata mínima útil no entran a la vista predeterminada.

Por defecto se ocultan deadlines vencidos, publicaciones anteriores a siete días y
resultados marcados fuera de alcance/ventana o sin publicación válida. La vigencia
se calcula al consultar contra el deadline, interpretando fechas sin zona en Bogotá.
Los deadlines desconocidos se conservan: no se equiparan a cerrados.
Los filtros permiten consultar cerrados y, con `include_excluded`, históricos/fuera
de alcance; no fabrican evidencia ni identidades para filas inválidas.

Orden: `review_first_seen_at DESC NULLS LAST`, antes de paginar. No utiliza
vigencia, deadline, score, publicación ni identidad como criterios de orden. Hay búsqueda por código, entidad y objeto;
filtros de fuente, vigencia, ubicación, score, monto, deadline, funnel
y revisión documental. Score Eureka y evaluación humana se muestran por separado.

## Evaluación humana

La migración `0019_manual_process_review` crea únicamente
`eureka.manual_process_review`: identidad canónica como clave primaria,
`manual_rating` (`high`, `medium`, `low`, `discard` o vacío), `manual_note`,
`reviewed_at` y `reviewed_by`. No modifica tablas del pipeline.
El guardado es un upsert atómico por identidad: sobrevive corridas posteriores.
El analista procede del proveedor de usuario actual de la aplicación; en el entorno
local sigue siendo el usuario demo existente, no un sistema nuevo de autenticación.

Una evaluación Alta/Media/Baja/Descartar no altera score, elegibilidad, dedupe o alertas.
Descartar es una anotación humana, no una exclusión automática del pipeline.
La revisión documental y sus motivos se conservan desde las observaciones persistidas.
Los suspicious facts se muestran a partir de sus IDs/anotaciones guardados, sin
reclasificarlos. El detalle no escribe ni duplica facts/canonicals.

## Trazabilidad temporal

La migración `0020_review_temporal_trace` agrega `review_first_seen_at TIMESTAMPTZ`
y `review_first_seen_origin` a la misma tabla. `reviewed_at` admite NULL para entradas
que todavía no tienen evaluación humana. No hay tablas nuevas.

Para resultados nuevos, al persistir un outcome se observa la pertenencia a la bandeja
con los criterios actuales. La entrada se inserta en la misma transacción, con la hora
real de observación (`origin=observed`). El conflicto por identidad ejecuta DO NOTHING:
ni una segunda corrida ni otra fuente cambian esa fecha. El guardado de evaluación
actualiza únicamente los campos humanos, conservando la entrada original.

Antes de esta versión no había un evento de entrada persistido. No se puede reconstruir
su hora exacta con la fecha de corrida, publicación, deadline o evaluación humana.
La migración conserva los registros humanos anteriores con fecha NULL y
`origin=legacy_unknown`. Consultar procesos históricos sin registro no crea una
fecha con la hora de lectura. Se muestran como «No registrada (histórico)» y
quedan al final. Los backfills que ya estaban persistidos conservan su fecha y
su marca explícita de histórico con fecha original desconocida; no se reescriben.

Lista, detalle y respuesta de evaluación incluyen ambos campos. La columna
«Entró a revisión» y el detalle usan DD/MM/YYYY HH:mm:ss en America/Bogota;
publicación, deadline y «Última revisión» humana permanecen separados.
Las consultas de lista/detalle no escriben registros de entrada histórica.

Los criterios de inclusión de la bandeja permanecen iguales. Este registro no promueve
alertas ni interviene en scoring o dedupe comercial.

## API y frontend

- `GET /api/eureka/revision`: lista paginada y opciones de filtros.
- `GET /api/eureka/revision/{canonical_identity}`: detalle, historial y evidencia existente.
- `PUT /api/eureka/revision/{canonical_identity}`: valoración y nota (máximo 5000 caracteres).

`HumanReviewPage.tsx` implementa lista, filtros, detalle y formulario; usa React Query,
formateadores compartidos y enlaces a alertas/detalle Eureka existentes.
Rutas `/eureka/revision` y `/eureka/revision/:identity`; navegación en `AppShell`.
El contrato OpenAPI y sus tipos generados incluyen los nuevos endpoints.

## Validación local sin corridas nuevas

Pruebas unitarias: ambas fuentes, dedupe exacto, provenance, alerta existente,
caducidad, filtros/orden, persistencia de evaluación y separación del score.
Prueba PostgreSQL: esquema y upsert sin cambios en alertas ni facts.
Frontend: tabla unificada, filtros de solo lectura, formulario y error de lectura.

Se comprobaron con evidencia persistida los casos CM-006-2026, CM-MC-02-2026,
CMI-2026078 y MM-SASI-SGOB-006-2026. MRAM-MC-066-2026 queda oculto por
deadline vencido al consultar. Pruebas locales en
`backend/.local/human-review-validation/` (no versionadas).
No se guardaron valoraciones ficticias en la base operativa.

## Límites actuales

La proyección y los filtros se calculan en memoria desde las corridas persistidas.
Con mayor volumen convendrá trasladar paginación/filtros a SQL. Los datos históricos
ausentes se presentan sin inventarlos; procesos diferidos sin documentos persistidos
tienen detalle documental vacío. No hay promoción manual a alerta ni workflow de
aprobación. La ventana local de esta vista es siete días y no cambia filtros de fuentes.
