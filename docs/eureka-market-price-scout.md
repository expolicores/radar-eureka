> **V1 hist?rico.** La pol?tica vigente exige verificaci?n API/p?gina: ver
> [Market Price Scout V1.1](eureka-market-price-scout-v11.md). Los resultados de
> aceptaci?n y decisiones V1 de abajo se conservan como historial.

# Market Price Scout — flujo vigente

## Alcance

Producto identificado → discovery determinístico opcional → conteo válido deduplicado
→ Scout solo si faltan precios → matching existente → enriquecimiento MCO opcional
→ dedupe y benchmark existentes.

El agente conversacional Eureka no se consulta ni modifica. Sin DB, migraciones,
scheduler, documentos públicos, OCR, CDP o cambios a Estado vs Estado/señales definitivas.

## Puerto e implementación

`ports.py` define `MarketPriceScout.scout(ScoutRequest) -> Iterable[MarketObservation]`.
El request incluye identidad, especificaciones, Colombia/COP, objetivo faltante,
máximo faltante y URLs ya cubiertas. No hay un contrato paralelo para ofertas.
La iteración es interrumpible para una futura implementación con browser.

`FoundryMarketPriceScout` es un adaptador dedicado: una llamada Responses con
Web Search, usando el endpoint de proyecto ya configurado. No crea versiones,
conversaciones ni tools del agente general. No envía precios/documentos públicos.
No necesita otra librería; usa el extra `foundry` existente.

Configuración en `backend/.env` (no en ejemplos ni en git):

```dotenv
AZURE_FOUNDRY_PROJECT_ENDPOINT=https://RESOURCE.ai.azure.com/api/projects/PROJECT
MARKET_PRICE_SCOUT_MODEL=gpt-4.1-mini-eureka
MARKET_PRICE_SCOUT_TIMEOUT=120
```

Solo las dos últimas variables son nuevas y opcionales. No se reutilizan instrucciones
ni configuración mutable del agente general. Mercado Libre conserva su configuración actual.

## Activación, presupuesto y parada

- Por defecto objetivo 3, máximo deseado 5. Configurables entre 1 y 5.
- Se cuentan observaciones válidas **después** de deduplicar, incluyendo API y evidencia
  reutilizada. Con 3 válidas no se llama al Scout.
- Con 1 o 2 se preservan y se pide solo lo que falta; máximo faltante = máximo − existentes.
- Una invocación del Scout, máximo 3 tool calls hosted, timeout 120 s (configurable hasta 180),
  sin reintentos SDK. El proveedor puede limitar búsqueda/navegación según el modelo.
- El adaptador devuelve como máximo el número solicitado; el núcleo admite hasta 10
  candidatos de una implementación iterable y corta al alcanzar el objetivo válido.
  El presupuesto de candidatos no significa 10 precios aceptados.
- El servicio detiene/cierra el iterador en cuanto alcanza el objetivo. Una respuesta
  hosted es una llamada indivisible: no se cancela a mitad de generación por cada precio.
- El discovery barato normal es catálogo ML/IDs explícitos/evidencia ya guardada. El puerto
  `WebSearch` opcional permite una única consulta barata si se inyecta un proveedor útil;
  **no existe un proveedor RSS predeterminado** ni 9 queries `site:`.

## Evidencia y controles

Se reutilizan `SearchResult`, `MarketObservation`, matching, `web_pages`, `urls` y
agregación. El modelo no decide validez: el servicio recalcula identidad, precio,
moneda y página concreta desde el texto de evidencia. `partial`/`reject` no entran
al benchmark monetario. No hay allowlist de retailers.

El adaptador admite únicamente URLs que aparezcan en fuentes/citas de la respuesta
hosted. Guarda título, cita de precio, URL, fecha de captura, consulta, proveedor e ID
de respuesta. No guarda razonamiento interno. Procedencia:
`discovery_method=market_price_scout`, `extraction_method=grounded_web_quote`;
si ML enriquece, `extraction_method=mercadolibre_api` con vínculo al candidato web.

**Límite de evidencia:** la cita es extraída por el modelo de resultados grounded;
no se descarga ni verifica independientemente el HTML. El proveedor puede usar contenido
cacheado. Se conservan `scout_quote_not_independently_page_verified`,
`hosted_search_may_use_cached_content` y las limitaciones existentes de stock,
impuestos/envío y checkout. Captura actual no certifica antigüedad del precio.
Fuentes oficiales: [Web Search de Azure](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/web-search).

URLs con ID concreto MCO pasan una vez por `/items/{id}`, sin `/sites/MCO/search`
ni refresh automático. API válida tiene preferencia sobre web. 401/403/429/timeout/5xx
o payload inválido se registran sin borrar evidencia web válida. URLs de catálogo
`/p/MCO...` sin listing no se confunden con `/items`.

Tres vendedores ML siguen siendo `marketplace_concentrated_evidence`; no se altera
independencia ni política de señales. La oferta MC-070-2026 continúa preliminar,
antes de IVA y con conflicto de encabezado; el Scout no puede promoverla a compra.

## Ejecución Samsung

Desde `backend`, con credencial Azure manual vigente y Mercado Libre opcional:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --brand Samsung --model 58U8000H --canonical-model UN58U8000H `
  --size "58 pulgadas" --product-type televisor --domain-id MCO-TELEVISIONS `
  --output-directory .local/market-price-scout/nueva-ejecucion
```

No se hardcodean ofertas/precios/URLs. Elegir directorio nuevo: no se sobrescriben
recibos existentes. Sin `--publish` no cambia la proyección que consume la UI.
`--public-product ruta.json` permite el caso público preliminar preservando su evidencia.
`--web-receipt ruta/market_benchmark.json` reutiliza candidatos con fecha original;
no cambia el recibo fuente. `--no-scout` desactiva fallback. `--source mercadolibre`
ejecuta solamente discovery/enriquecimiento estructurado.

`market_benchmark.json` incluye diagnóstico `market_price_scout`, evidencia normalizada,
duplicados, errores sanitizados, benchmark y limitaciones. Fallo externo →
`completed_with_warnings`/`insufficient_market_evidence` cuando corresponda, sin abortar.
Un número insuficiente de ofertas se informa como insuficiencia, nunca se inventa.

## Limpieza de experimentos

| Pieza | Decisión |
|---|---|
| `BingRssSearch`, transporte/redirecciones RSS | Retirados del código productivo |
| Script `eureka_web_search_diagnostic.py` y tests RSS | Retirados; resultado histórico preservado |
| Generador de 9 queries `site:`/allowlist de 5 tiendas | Retirado |
| `--max-web-queries`, `--source web-search/combined` | Retirados; CLI `auto/mercadolibre` |
| Discovery web V0.2 | Simplificado a una consulta opcional inyectada, sin proveedor predeterminado |
| Canonicalización de catálogo y expansión ML | Mantenidas |
| Matching, clasificación de páginas, URL/MCO, dedupe/diversidad | Mantenidos sin relajar criterios |
| Diagnóstico offline de rechazados | Mantenido para operación, no consulta proveedores |
| `run_mercadolibre_benchmark` | Fachada compatible sobre la misma orquestación, sin segundo pipeline |
| Docs V0.1/V0.2/spike y `.local` | Históricos preservados e identificados como tales |

Inventario de este incremento (respecto al estado local previo, que ya contenía
trabajo sin commit):

- Agregados: `market_benchmark/ports.py`, `market_benchmark/foundry_scout.py`,
  `tests/unit/investigation/test_market_price_scout.py` y este documento.
- Modificados dentro de `market_benchmark/`: `service.py`, `schemas.py`,
  `query_expansion.py`, `web_discovery.py`, `mercadolibre_adapter.py` (procedencia API).
- Modificados: `backend/scripts/eureka_market_benchmark.py`, tests
  `test_market_benchmark.py`, `test_market_source_degradation.py`,
  `test_market_rejection_diagnostics.py`; frontend `MarketBenchmark.tsx` y
  `MarketBenchmark.test.tsx` (estado y procedencia del Scout).
- Renombrado y ajustado: `test_web_discovery_v02.py` → `test_market_web_evidence.py`;
  conserva matching/clasificación/enriquecimiento y elimina expectativas de 9 queries.
- Retirados: `market_benchmark/web_search_adapter.py`,
  `backend/scripts/eureka_web_search_diagnostic.py`,
  `tests/unit/investigation/test_web_provider_diagnostic.py`.
- Marcados históricos: `docs/eureka-investigacion-mercado-privado.md`,
  `docs/eureka-mercadolibre-benchmark.md`, `docs/eureka-web-discovery-v02.md`,
  `docs/eureka-web-search-provider-diagnostic.md`.

No se modificaron `matching.py`, `aggregation.py`, reglas de señales ni el agente general.

Deuda deliberada: browser/verificación directa de página, control por cada acción
interna del proveedor, actualización automática de credenciales y verificación de
checkout. No se implementan en este incremento.

## Aceptación real — 04/11/2026

Un intento acotado, sin `--publish`, sin precios/URLs predefinidos:
`backend/.local/market-price-scout-samsung-20261104-v1/market_benchmark.json`.

- Mercado Libre: 5 requests, catálogo `MCO80188666` verificado, sin errores.
- Scout: una invocación Responses; devolvió 3 candidatos citados.
- Éxito: `UN58U8000FKXZL`, modelo diferente; además múltiples precios/cuotas.
- Mercado Libre: listado general de TVs de 58 pulgadas, texto de U8500;
  no listing MCO concreto, precio ambiguo.
- Falabella: página general de TVs de 58 pulgadas con U8500H; referencia diferente
  y múltiples precios.
- **0 observaciones válidas**, `insufficient_market_evidence`. Sin mediana,
  comparación o señal. Ninguna llamada `/items` porque no se encontró un ID de listing.
- Se conservan los tres rechazos, citas, URLs y referencia de respuesta en el recibo.
  No se hizo otra búsqueda para forzar el resultado ni se flexibilizó matching.

La infraestructura y la degradación funcionan; este intento **no valida todavía**
un benchmark comercial de tres precios para el modelo solicitado.

## Validación offline

- 31 casos del Scout, 312 tests de investigación en total: pasan.
- 8 tests del componente de benchmark del frontend: pasan.
- Ruff/format, Mypy del módulo y CLI, lint/typecheck/build frontend y 13 contratos
  de importación: pasan.
- Suite unitaria backend ampliada: 1.574 pasan, 1 omitido, 4 fallos ajenos a este
  módulo. Los fixtures CDP usan publicación 19/20 de octubre y vencimiento 30 de
  octubre de 2026, pero ejecutan con reloj real de noviembre: quedan stale/closed.
  Los cuatro pasan reproduciendo offline el reloj 23/10/2026, sin editar código
  ni fixtures CDP. Queda pendiente estabilizar esos tests fuera de este incremento.
