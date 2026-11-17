# SerpApi — integración limitada en Market Benchmark

## Flujo vigente

Producto → ShoppingSearchPort → Google Shopping → hasta 3 Google Product → stores
→ matching existente → MarketObservation → dedupe/benchmark existentes.

Si falta suficiencia y un producto compatible aporta token: opcionalmente una
consulta Immersive `more_stores=true` y una única continuación. Después:

1. Mercado Libre `/items/{MCO...}` para URLs concretas encontradas.
2. PageVerifier cuando pueda completar evidencia de un candidato insuficiente.
3. Market Price Scout para las observaciones faltantes.
4. `insufficient_market_evidence` si sigue faltando evidencia.

Ninguna fuente externa es obligatoria. Una fuente fallida no borra las observaciones
útiles de otra. La API nativa tiene prioridad sobre el proveedor; un rechazo explícito
de un listing por esa API tampoco se oculta con un precio inferior en la jerarquía.

No se cambian `matching.py`, comparación/señales definitivas, Estado vs Estado,
documentos públicos, scoring, DB, scheduler o el agente general Eureka.
No hay migraciones ni nuevas dependencias.

## Arquitectura

- `ports.ShoppingSearchPort.discover(...)`: frontera independiente del proveedor.
- `ShoppingDiscoveryResult`: observaciones del contrato existente y diagnóstico;
  no introduce otro contrato monetario.
- `serpapi_adapter.SerpApiShoppingAdapter`: Shopping/Product/Immersive, selección
  acotada y normalización con `match_identity` existente.
- `serpapi_http.SerpApiHttp`: único transporte, configuración y sanitización.
- `service.run_benchmark(..., shopping=...)`: coordinación sin importar SerpApi.
- `scripts/eureka_market_benchmark.py`: composición explícita; `auto` usa SerpApi
  primero, `serpapi` permite diagnóstico estructurado aislado y `mercadolibre`
  mantiene la ruta estructurada previa sin SerpApi/Scout.

La lectura de la UI sigue siendo una proyección local. Abrir una página no llama
a proveedores ni dispara corridas. `--publish` conserva su significado existente.

## Configuración y seguridad

Se reutiliza `SERPAPI_API_KEY` de `backend/.env` o del entorno.
`SERPAPI_TIMEOUT_SECONDS` es opcional: default 45 s, entre 5 y 60.
La key es SecretStr y se excluye del repr/configuración visible.

Origen fijo `https://serpapi.com/search.json`, engines/parámetros permitidos,
sin redirecciones, proxies de entorno ni retries. Cuerpo máximo 8 MB.
La key no aparece en URL persistida, excepciones ni recibos. El transporte redacta
credenciales también si el provider las repite en mensajes o URLs. Los errores
guardan códigos/HTTP status, nunca el texto HTTP de excepción.

Los recibos conservan endpoint sin query sensible, ID de búsqueda, producto,
atributos, store, product_id y contexto de mercado. Los tokens de navegación se
usan internamente; en el diagnóstico de requests se guardan hashes, no sus valores.
No se copia el payload entero del proveedor al agente conversacional.

## Discovery y límites

Query a partir de marca, referencia canónica preferida —o referencia original—,
tipo, tamaño y capacidad. La referencia original permanece en ProductIdentity.
Localización de Shopping: `gl=co`, `hl=es`, Bogotá. Product/Immersive usan `gl=co`, `hl=es`.

- Una búsqueda Shopping, hasta 40 candidatos inspeccionados localmente.
- Hasta 3 product_id distintos plausibles, en secuencia.
- Los resultados ambiguos pueden motivar una consulta de detalle; no un precio válido.
- Máximo **2 consultas Immersive en toda la ejecución**, para un único producto
  compatible, con el mismo token base. La segunda exige continuación y falta de suficiencia.
- Presupuesto total SerpApi: **6 intentos** (1 + 3 + 2), sin retries.
- Se corta al alcanzar target válido y diversidad, o el máximo de observaciones.
  Defaults: target 3, máximo 5, idealmente 2 fuentes independientes.
- El diagnóstico distingue intentos del proveedor de requests; key ausente no
  cuenta como request de red.

Los stores se contrastan de forma individual: no se toma el modelo del padre para
completar el título genérico de una tienda. Un contexto explícitamente contradictorio
tampoco se ignora. Ambigüedad queda como `partial`/`reject` del matching existente,
con `provider_metadata.identity_diagnostic=ambiguous` cuando corresponde, y siempre
fuera del cálculo monetario.

Los candidatos Shopping usan el mismo MarketObservation, pero se guardan en
`shopping_discovery.shopping_candidates`; los stores quedan en el benchmark.
Esto evita confundir un enlace agregador Google con una oferta directa de tienda.

## Contrato y jerarquía de evidencia

Se amplía MarketObservation de forma aditiva con `product_id`, `shipping`,
`currency_inferred`, `provider_metadata` y `source_type=shopping_provider`.
Se reutiliza ApiEvidence con `source=serpapi`, conservando la forma antigua de ML.

| Prioridad | price_evidence_level | Significado |
|---|---|---|
| 1 | api_verified_price | API nativa de marketplace |
| 2 | page_verified_price | Página concreta visitada y verificada |
| 3 | shopping_provider_price | Oferta estructurada SerpApi; tienda/checkout no visitados |
| 4 | snippet_price | Candidato débil; no entra monetariamente por sí solo |

Source identifica el engine (`serpapi_google_product`, `serpapi_google_immersive_product`);
discovery_method conserva `serpapi_google_shopping`. Se guardan título, marca/modelo,
tienda, precio, shipping, captura, URL, atributos, rank/rating/reviews, razones y provenance.
La UI distingue precio del proveedor y COP inferido. No lo etiqueta como página verificada.

La inferencia de COP exige contexto colombiano confirmado por el provider o heredado
del detalle validado, un precio expresado con `$` y ninguna contradicción de moneda.
Moneda explícita distinta, `alt_currency` ambiguo o contexto sin confirmación no se
convierten en COP. El contexto se conserva durante la paginación; Immersive no
restablece Colombia si Product había indicado otro mercado.

Dedupe mantiene URL/listing/seller/retailer y agrega la eliminación de `srsltid`
como tracking. Prioriza evidencia válida y luego la jerarquía anterior. No cambia
independencia de fuentes: varios sellers ML siguen siendo un marketplace concentrado.

El benchmark puede mostrar estadísticas parciales de referencias válidas, como antes;
dos observaciones siguen siendo insuficientes y no habilitan una comparación/señal
definitiva. Addi u otros ambiguos nunca entran en min/mediana/max.

## Graceful degradation

Key ausente, 401/403, 429, timeout, 5xx y payload inválido se registran sin abortar.
401/403/429/key ausente detienen más intentos de ese provider en la ejecución.
Shopping vacío, detalle sin stores, Fully empty, respuesta parcial y token ausente
producen warnings/limitaciones. Los detalles parciales aprovechables se conservan.

Con SerpApi activo no se repiten consultas de catálogo ML: solo se enriquecen MCOs
concretos. Si no existe tal ID no se llama a `/items`. Una respuesta 401/403/etc.
de ML permite conservar el precio estructurado válido; una respuesta nativa que
rechaza identidad/condición del listing evita validarlo con la fuente inferior.

No se visita innecesariamente una tienda cuya oferta estructurada ya es suficiente.
PageVerifier puede mejorar un candidato ambiguo; un fallo aislado no tumba el resto.
Scout recibe únicamente el faltante y excluye URLs de observaciones válidas existentes.

## Ejecución Samsung

Desde `backend`, flujo completo manual (puede realizar requests reales):

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --brand Samsung --model 58U8000H --canonical-model UN58U8000H `
  --size "58 pulgadas" --product-type televisor --domain-id MCO-TELEVISIONS `
  --output-directory .local/market-benchmark/nueva-ejecucion
```

Solo la fuente SerpApi, sin páginas de tiendas, ML o Scout:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --source serpapi --no-page-verification `
  --brand Samsung --model 58U8000H --canonical-model UN58U8000H `
  --size "58 pulgadas" --product-type televisor `
  --output-directory .local/serpapi/nueva-ejecucion
```

Se exige directorio nuevo. Sin `--publish` no cambia la proyección UI.
`--no-scout` desactiva el fallback Foundry en `auto`. El diagnóstico offline
`--diagnose-receipt ruta/market_benchmark.json` no hace requests y también explica
rechazos de ofertas SerpApi.

## Aceptación offline con evidencia real como fixture

Fixture: `backend/tests/fixtures/serpapi_samsung.json`, derivado de los tres spikes;
token sustituido por un selector ficticio, sin secretos. Precios/URLs de este caso
solo existen en fixtures/tests e informes históricos, no en lógica productiva.

- Éxito y Puntos Colombia: high y precio estructurado válido; COP inferido señalado.
- Addi: título incompleto, partial/ambiguous conservado, no monetario.
- Resultado: **2 válidas**, **1 ambigua**, `insufficient_market_evidence`, sin señal.
- Immersive simulado repite tres ofertas: se conservan como duplicados, no seis precios.

Recibo de validación local, marcado `offline_fixture_no_external_requests`:
`backend/.local/serpapi-integration-fixture-q7f07dud/market_benchmark.json`.
No se hicieron nuevas consultas reales ni se publicaron resultados durante este incremento.

## Limpieza e inventario

Agregados:

- `market_benchmark/serpapi_http.py`, `market_benchmark/serpapi_adapter.py`
- `tests/fixtures/serpapi_samsung.json`
- `tests/unit/investigation/test_serpapi_adapter.py`
- Este documento.

Modificados:

- Módulo: `ports.py`, `schemas.py`, `service.py`, `aggregation.py`, `urls.py`,
  `page_verifier.py`, `diagnostics.py`.
- `backend/scripts/eureka_market_benchmark.py`.
- `test_market_source_degradation.py` (doble del provider y trigger MCO explícitos).
- Frontend `MarketBenchmark.tsx`, `MarketBenchmark.test.tsx` (calidad y contexto monetario).
- Informes de los tres spikes y documentación V1.1 identificados como históricos.

Retirados:

- Scripts `eureka_serpapi_shopping_spike.py`, `eureka_serpapi_google_product_spike.py`,
  `eureka_serpapi_immersive_product_spike.py`.
- Sus tres archivos `test_serpapi_*_spike.py`.

Migrados: transporte/sanitización/configuración, límites de requests/paginación y
provenance. Se reemplaza la heurística específica del Samsung por matching existente.
Se retiran tests exclusivos de los runners experimentales; la cobertura productiva
verifica normalización, fuente caída, calidad, moneda, dedupe y fallback.
Se mantienen todos los `.local` y los informes históricos: no son comandos vigentes.

## Validación y deuda

396 tests de investigación, incluidos 41 de SerpApi, y 9 tests del componente visual
pasan. Ruff/formato, Mypy, contratos de importación y lint/typecheck/build frontend pasan.
Suite backend unitaria completa: 1658 passed, 4 failed, 1 skipped. Los cuatro fallos
son de CDP, ajenos a este incremento: sus fixtures de octubre usan reloj real de
noviembre y quedan stale/closed. Log local: `backend/.local/serpapi-backend-unit-validation.txt`.

Deuda deliberada: sin garantía de tres ofertas, tokens que pueden caducar, selection
acotada a 3 productos, sin retries automáticos, stock/envío/condiciones de pago o
descuentos sin verificar en checkout. La diversidad sigue siendo la agrupación existente
por plataforma/dominio; no es un análisis de propiedad corporativa de retailers.
El matching conserva sus limitaciones actuales; no se agregan equivalencias para
compensar resultados genéricos del provider.
