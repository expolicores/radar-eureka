# Corridas independientes por fechas

En `/explorar` hay dos acciones: **Nueva corrida Estado vs Estado** y **Nueva corrida Estado vs mercado privado**. Ambas reciben exclusivamente fecha inicial y final, inclusivas en Bogotá y con máximo 60 días. No se selecciona un producto ni una corrida previa.

## Arquitectura

```text
fechas → Socrata → selección → inventarios → documentos/extracción
       → informe público → reconstrucción económica por producto
           ├─ state_vs_state: comparación pública existente
           └─ state_vs_private_market: private_market_candidates
                → solo elegibles → pipeline privado existente
                → benchmark → comparación/señal cuando la evidencia alcance
```

`ExistingResearchPipeline(public_evidence_only=True)` reutiliza scripts y límites públicos. El ciclo económico conserva sus reglas de vinculación y confirmación y omite la comparación Estado vs Estado en la rama privada. No consume informes publicados ni usa `--reuse-directory`. El informe previo de extracción puede contener comparaciones preliminares intermedias; no se muestran como resultado privado.

La muestra sigue siendo la de televisores existente, no todos los procesos nacionales. No se amplían taxonomías ni filtros.

## Candidatos

`PrivateMarketCandidate` contiene candidate_id estable por proceso/producto, process_identity/process_code, product_id/description/brand/model, status (eligible/ineligible/pending_review), reasons, public_evidence_status, public_product validado, evidence, warnings, market_status, market_report_id y reused_market_from.

- Sin marca/modelo: ineligible.
- Identidad conflictiva/incierta, precio unitario ausente, provenance incompleta o fecha de compra no acreditada: pending_review, sin requests privados.
- PublicProduct confirmado solo parte del purchase_price verificado por el ciclo y su fecha de compra verificada. No usa publicación como fecha de compra.
- Una oferta documental consistente permite PublicOffer/documented_unconfirmed_offer, exclusivamente como investigación preliminar. Nunca se promueve a compra por su nombre ni por encontrar precios privados.
- Documento, página, hash/versión, texto, método, conflictos y limitaciones quedan preservados.

La proyección actual exige precio unitario y página trazable para consultar mercado. Los productos sin ellos permanecen pendientes, sin inventar datos. Presupuestos y valores globales no sustituyen precios de oferta o compra.

## Reutilización y costos

La etapa pública se ejecuta una vez. Se deduplican candidatos repetidos del mismo producto del ciclo. La búsqueda privada es secuencial. Si otro candidato tiene exactamente la misma ProductIdentity completa (marca/modelo/atributos), se reutilizan observaciones capturadas en ESTA corrida y se aplica `build_report` existente a la evidencia pública propia del candidato. No se heredan precios públicos, comparaciones ni señales de otro proceso. Se registra reused_market_from.

Composición auto intacta: SerpApi → MCO cuando aplica → PageVerifier → Scout fallback. Conserva presupuestos y objetivos 3/5; detiene búsqueda al alcanzar suficiencia. No relaja matching ni fuerza una tercera oferta. Los errores privados aislados se registran por candidato, conservando evidencia pública y continuando con warnings. Una falla de la fase pública impide pasar a mercado.

## API y persistencia

Prefijo: `/api/v1/investigation`.

- POST `/runs`: Estado vs Estado.
- POST `/market-runs`: Estado vs mercado privado.
- Ambos body: `{"start_date":"2026-10-01","end_date":"2026-10-31"}`.
- GET `/market-runs/active` y `/market-runs/{id}`: seguimiento privado.
- GET `/market-runs/{id}/research`: procesos, productos y decisiones de elegibilidad del run; sin recibos crudos de proveedores.
- GET `/private-market?run_id={id}`: presentación segura de sus benchmarks, sin fallback al último informe.

Se elimina `/market-products` como entrada al flujo. ResearchRun persiste run_type, fechas y límites UTC, status, stage, counts, warnings/errors, created_at/started_at/finished_at y result_url. Históricos públicos sin run_type conservan state_vs_state.

```text
market-date-runs/<UUID>/run.json
market-date-runs/<UUID>/<artefactos públicos existentes>
market-date-runs/<UUID>/private-market-candidates.json
market-date-runs/<UUID>/products/<candidate_id>/input.json
market-date-runs/<UUID>/products/<candidate_id>/market_benchmark.json
market-date-runs/<UUID>/result.json
```

Se abre `/explorar?private_run=<UUID>&market_run=<UUID>`: procesos y benchmarks del mismo run. No escribe sobre latest.json ni el último benchmark histórico. Los recibos antiguos por producto permanecen disponibles por UUID para lectura; no son inputs de nuevas corridas.

Etapas: discovery, documents_extraction, research_report, economic_cycle, product_identification, private_market_discovery (incluye verificación/fallback), benchmark, comparison, finished. No se simulan callbacks que el proveedor no expone.

Conteos: processes_discovered, processes_selected, products_identified, private_market_candidates, private_market_products_processed/failed, private_market_observations_valid, benchmarks_sufficient/insufficient, comparisons_generated, signals_generated. Observaciones y benchmarks se cuentan por candidato público; una reutilización no implica requests nuevos.

Sin migraciones ni dependencias nuevas. Mantiene worker local, JSON atómico, lease OS y recuperación por reinicio sin auto-reanudar. Pendientes: cola durable, cancelación, historial general y más categorías. No se ejecutó corrida real durante esta corrección; pruebas con fixtures/proveedores simulados.
