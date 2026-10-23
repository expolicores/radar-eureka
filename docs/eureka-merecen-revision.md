# Merecen Revisión

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

## Inclusión y orden

Entran observaciones SECOP identificables con objeto disponible, incluidos diferidos
por límite, evaluados no elegibles, procesos sin alerta, con score, con canonicals o
con revisión documental. Las alertas existentes también pueden consultarse y filtrarse.
Las filas inválidas y las fuentes externas no SECOP no se proyectan.

Por defecto se ocultan deadlines vencidos, publicaciones anteriores a siete días y
resultados marcados fuera de alcance/ventana o sin publicación válida. La vigencia
se calcula al consultar contra el deadline, interpretando fechas sin zona en Bogotá.
Los deadlines desconocidos se conservan: no se equiparan a cerrados.
Los filtros permiten consultar cerrados y, con `include_excluded`, históricos/fuera
de alcance; no recuperan filas inválidas ni fuentes externas.

Orden: abiertos primero, deadline más cercano, score descendente, publicación
descendente e identidad para desempatar. Hay búsqueda por código, entidad y objeto;
filtros de fuente, vigencia, ubicación, score, monto, deadline, funnel, alerta existente
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
`origin=legacy_unknown`. Al consultar procesos históricos activos que no tienen registro,
se crea una sola entrada con la hora actual de registro y `origin=historical_backfill`.
La UI indica expresamente «Registro histórico: fecha original de entrada desconocida».
Esa fecha significa **registrado desde**, no una supuesta fecha histórica exacta.
No se inventan timestamps ni se reescriben eventos antiguos de fuentes.

Lista, detalle y respuesta de evaluación incluyen ambos campos. La columna
«Entró a revisión» y el detalle usan DD/MM/YYYY HH:mm en America/Bogota;
publicación, deadline y «Última revisión» humana permanecen separados.
La primera consulta puede escribir exclusivamente estos registros de entrada,
sin lanzar adquisición ni modificar los resultados del funnel.

Los criterios y el orden de la bandeja permanecen iguales. Este registro no promueve
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
