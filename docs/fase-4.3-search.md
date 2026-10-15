# Fase 4.3 · Búsqueda transversal sin IA

Implementación local de solo lectura. **0014_transversal_search se aplicó a desarrollo
con autorización el 14 de octubre de 2026**, conservando las 28 tablas históricas y sus
41.582 filas con hashes SHA-256 idénticos. Search está operativo y validado por HTTP y
navegador. La API conserva el 503 controlado para bases que todavía no tengan sus
funciones SQL. [Validación operativa en desarrollo](validacion-4.3-desarrollo.md).

## Arquitectura y fuentes

`entrypoints → search → servicios públicos de eureka/extraction/documents/ingestion`.
Los repositorios SQL de cada módulo conservan la propiedad de sus tablas. Search compone
metadata, oportunidad opcional y evidencia persistida, sin invocar ingestion, descargas,
OCR, consolidación, Radar ni scoring. Las consultas HTTP usan transacciones READ ONLY;
la búsqueda usa REPEATABLE READ para mantener consistente la selección de versiones.

Fuentes: `ingestion.secop_process`; `documents.document_process`, `document_version` y
últimos intentos disponibles; `extraction.extraction_run`, `content_fragment`,
`structured_fact`, `canonical_fact`, `canonical_fact_evidence`; `eureka.opportunity` y
`alert`. Las compras simuladas quedan en `/explorar`.

Vigencia: última adquisición disponible por documento, última extracción utilizable con
fragments de esa versión y todas las referencias de los structured facts dentro del
conjunto vigente. Se recalcula **en memoria y sin persistir** el digest con la función
existente de consolidación; solo se aceptan canonical facts cuyo input_digest coincide.
No basta con escoger el hecho más reciente. Los candidatos SQL pueden incluir historia;
la validación en lotes de 250 excluye esa historia del resultado y de la evidencia.

## Normalización, ranking y evidencia

Minúsculas, NFKD, eliminación de acentos y puntuación y espacios normalizados. PostgreSQL
FTS con configuración `spanish`, expresiones equivalentes entre consulta e índice y
tokens parametrizados. Los operadores del usuario no se interpolan en SQL. Los alias
son los explícitos del catálogo Radar existente: no se modifica ese catálogo ni se
infieren marcas, equivalencias comerciales o jerarquías UNSPSC.

| Nivel | Regla |
|---:|---|
| 5 | PRODUCT/PURCHASE_ITEM canónico exacto normalizado |
| 4 | Alias explícito o coincidencia canónica/estructurada sin ser prefijo |
| 3 | Metadata exacta normalizada |
| 2 | Frase o FTS documental |
| 1 | Token/prefijo |

Desempates: origen canonical → structured → metadata → texto, modalidad, prioridad
Eureka, publicación descendente e ID estable. El **score nunca ordena ni se recalcula**.
Los structured facts solo son fallback cuando falta el tipo canónico vigente equivalente,
incluso si ese tipo canónico está en conflicto. Marca exige texto explícito en BRAND,
PRODUCT/PURCHASE_ITEM, metadata o documento; nunca se deduce del fabricante o del contexto.
OCR y nativo tienen las mismas reglas de ranking y conservan su locator.

Cada resultado contiene tipo/modalidad, campo, valor o snippet (máximo 320 caracteres),
referencia canónica o fragment y hasta cinco razones. Presupuesto prioriza BUDGET_COP
confirmado, structured vigente como fallback y metadata; desconocido no satisface un
rango explícito. El endpoint de evidencia verifica pertenencia al proceso y vigencia.
El frontend reutiliza `groupEvidence` y `EvidenceDocuments` con Eureka.

## API y UI

`GET /api/search`: q, product, brand, entity, department, municipality, category, unspsc,
budget_min/budget_max, published_from/published_to, priority, page/page_size. Fecha final
**inclusive**. UNSPSC exacto de ocho dígitos; rangos invertidos se rechazan. La categoría
y prioridad usan la oportunidad persistida cuando existe. No se infieren categorías
para procesos sin oportunidad. Page size 1–100, page 1–10.000; fuera de rango retorna
items vacíos manteniendo total. Las restricciones q/product/brand combinadas son AND;
los alias de cada término son OR.

`GET /api/search/processes/{process_id}/evidence`: exactamente uno de canonical_fact_id
o fragment_id; 404 si no pertenece al proceso o dejó de estar vigente.

`/search`: buscador, filtros desplegables, resultados con explicación, productos,
ubicación, presupuesto, score/prioridad opcionales, paginación y evidencia bajo demanda.
Mantiene filtros en la URL, reinicia página al buscar y permite reintentar errores. El
enlace Eureka aparece solo si ya existe oportunidad; aparecer en búsqueda no la crea.
El menú distingue esta búsqueda SECOP de las compras demo.

## Migración 0014

Dos funciones SQL IMMUTABLE/PARALLEL SAFE:
`public.search_normalize_v1(text)` y `public.search_values_v1(jsonb)`.
Cuatro índices de expresión GIN:

- `ingestion.ix_search_process_fts`: objeto/título, referencia, ID, entidad y ubicación.
- `extraction.ix_search_canonical_fts`: valores de canonical_value, sin nombres de claves.
- `extraction.ix_search_structured_fts`: string_value y valores de normalized_value.
- `extraction.ix_search_fragment_fts`: normalized_text.

No crea tablas, columnas, relaciones, datos duplicados ni backfill. Downgrade elimina
solo estos cuatro índices y las dos funciones; search vuelve a indicar esquema pendiente.
Se comprobó upgrade/downgrade/upgrade exclusivamente en la base aislada, preservando
5.001 procesos, 5.018 canonical facts y 5.039 structured facts. CREATE INDEX es
transaccional y puede bloquear escrituras durante su creación: planificar ventana si
crece el volumen. La autorización separada para desarrollo se recibió y ejecutó después
de estas pruebas; allí se aplicó únicamente upgrade 0013 → 0014, sin downgrade.

## Rendimiento medido

PostgreSQL 16.15 local, copia aislada `public_procurement_search43_test`:
5.001 procesos, 5.003 documentos/versiones/extracciones, 5.099 fragments,
5.039 structured facts, 5.018 canonical facts. Incluye Covarachía más **5.000 procesos
sintéticos**, 50 de ellos con término selectivo `benchmarkneedle`. No extrapolar estos
tiempos a producción. La prueba no accede a Socrata ni ejecuta OCR.

| Índice | Sin índice, ms | Con índice, ms | Tamaño |
|---|---:|---:|---:|
| process_fts | 344,311 | 0,188 | 432 KiB |
| canonical_fts | 68,246 | 0,281 | 24 KiB |
| structured_fts | 94,656 | 0,207 | 24 KiB |
| fragment_fts | 59,909 | 0,133 | 80 KiB |

Los planes pasan de Seq Scan con evaluación FTS por fila a Bitmap Index Scan / Bitmap
Heap Scan. Se conservaron únicamente esos cuatro índices. Dos índices parciales para
últimos intentos y extracciones se descartaron: 0,196 vs 0,193 ms y 0,424 vs 0,279 ms,
respectivamente, con y sin índice; no demostraron beneficio en el caso medido.

| Consulta completa Python + SQL, 10 muestras | p50 ms | p95 ms | Total / página |
|---|---:|---:|---|
| Término selectivo, página 1 | 239,88 | 366,38 | 50 / 20 |
| Término selectivo, página 2 | 253,85 | 330,78 | 50 / 20 |
| Solo filtro municipio Covarachía | 85,91 | 89,71 | 1 / 1 |
| Página 99 del término selectivo | 244,42 | 264,32 | 50 / 0 |

p95 por nearest rank de 10 muestras; no incluye HTTP ni render del navegador. Total
exacto y ranking requieren validar todos los candidatos, también en página 2 o fuera
de rango. No se cargan todos los textos: SQL selecciona fragments coincidentes y se
validan snapshots por lote. Una búsqueda solo con filtros o muy común puede recorrer
muchos procesos y costar más; no se promete costo constante por página.

Evidencia: [mediciones y planes comparativos](search43/performance.json) y
[SQL y EXPLAIN ANALYZE de las consultas reales del servicio](search43/actual_plans.json).
Los cuatro GIN aparecen también en los planes SQL reales, no solo en ejemplos aislados.
Script reproducible: `backend/scripts/benchmark_transversal_search.py`, requiere
SEARCH_ACCEPTANCE_DATABASE_URL de una copia *_test con golden case y revisión 0014.
Valida que no sea la base local de desarrollo, no resetea tablas, compara retirando
un índice a la vez y lo restaura en finally.

## Validación

- 548 tests unitarios backend pasan; OCR real opt-in se omite en esta ejecución porque
  search no ejecuta OCR. La validación real de 4.2 no cambia.
- 18 comprobaciones PostgreSQL opt-in pasan en la base aislada; cambios de fixtures
  se revierten por rollback. Incluyen vigencia documental/extracción, digest, OCR/nativo,
  deduplicación, proceso sin Eureka y filtros.
- 67 tests frontend pasan; build y typecheck pasan. Cinco tests nuevos de `/search`.
- Mypy y 11 contratos de arquitectura pasan; Ruff/ESLint y formato se verifican.
- Golden responde a jugo hit, chocorramo, refrigerios, 50192703, Covarachía, Boyacá y
  presupuesto 2M–3M, con score 65 y enlace Eureka. Búsqueda y evidencia por HTTP pasan
  sobre la base aislada.
- Validación inicial antes de autorización: alerts/radar-runs/detalle Eureka respondían
  200 y search 503 por migración pendiente; Alembic seguía 0013.
- Validación operativa posterior: upgrade único 0013 → 0014 autorizado; search, evidencia,
  rutas anteriores, /search y enlace Eureka pasan. Hashes/conteos de las 28 tablas de
  negocio idénticos antes/después de migración y smoke tests.

Los casos A–N del pedido se cubren entre unitarios y PostgreSQL: producto/normalización,
texto/OCR, UNSPSC, región, presupuesto inclusivo/excluyente, q+filtros, sin canonical,
ranking, paginación, sin resultados y query vacía con filtros.

Ejecutar los checks PostgreSQL únicamente con SEARCH_ACCEPTANCE_DATABASE_URL apuntando
a una base *_test distinta de desarrollo:
`python -m pytest tests/acceptance/test_search_postgres.py -q`.
No utiliza el fixture destructivo de `tests/integration`.

## Brechas y límites

[SEARCH_GAPS.md](../SEARCH_GAPS.md) clasifica las ocho búsquedas solicitadas y los
controles adicionales. Solo hay un proceso real: las consultas de sillas, pantallas y
papelería no permiten evaluar necesidad semántica. La equivalencia entre refrigerios y
complemento alimentario individual es una hipótesis para revisión futura, sin alias nuevo.
No hay parser monetario libre, inferencia de marcas ni relevancia aprendida. La capacidad
de búsqueda depende de la cobertura que extraction ya haya persistido; no recupera por
sí misma páginas OCR omitidas ni documentos pendientes. La UI ya funciona con datos
reales en desarrollo, además de las pruebas iniciales sobre la copia aislada.

## Archivos de esta fase

Nuevos: `backend/src/public_procurement/search/{__init__,api,ports,adapters,services}.py`,
`search/domain/{__init__,query}.py`, `shared/search_sql.py`,
`{ingestion,documents,extraction}/search_queries.py`, `backend/config/search.v1.json`,
`backend/alembic/versions/0014_transversal_search.py`,
`backend/tests/unit/search/test_search.py`, `backend/tests/acceptance/test_search_postgres.py`,
`backend/scripts/benchmark_transversal_search.py`,
`frontend/src/features/search/{SearchPage.tsx,SearchPage.test.tsx}`,
`frontend/src/features/eureka/EvidenceDocuments.tsx`, `SEARCH_GAPS.md`, este documento y
los dos JSON de planes/mediciones.

Modificados: servicios públicos de ingestion/documents/extraction/eureka,
`backend/src/public_procurement/entrypoints/api/app.py`, `backend/pyproject.toml`,
`frontend/src/{App.tsx,app/AppShell.tsx}`,
`frontend/src/features/eureka/{EvidencePanel.tsx,evidencePresentation.ts}`,
`frontend/src/api/{openapi.json,schema.ts}`, `README.md`.
No se cambiaron .env, catálogo, reglas Radar, scoring ni migraciones anteriores en 4.3.
