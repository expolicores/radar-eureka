> **Flujo ampliado:** la entrada estructurada vigente es
> [SerpApi](eureka-serpapi-integration.md). PageVerifier y Scout siguen como fallbacks.
> Los comandos y resultados de aceptaci?n V1.1 de abajo son hist?ricos.

# Market Price Scout V1.1 — verificación de páginas

## Cambio acotado

La búsqueda existente sigue encontrando candidatos. Antes de aceptar dinero:

1. Reutilizar candidatos guardados y comprobar páginas concretas antes de buscar más.
2. Si hay listing MCO, intentar `/items/{id}` primero; API válida evita la descarga HTML.
3. Si falta API válida, verificar la URL concreta mediante `MarketPageVerifier`.
4. Solo precios API/página verificados y coincidencia exact/high entran al benchmark.
5. Snippets/cache, páginas generales y fallos quedan en JSON como evidencia débil/rechazada.

No cambian matching global, reglas de señales definitivas, Estado vs Estado,
documentos públicos, scoring ni el agente conversacional. Sin nuevas fuentes/API,
browser, JS, crawler, login, checkout, historial o migraciones.

## Puerto y adaptador

`ports.MarketPageVerifier.verify(product, candidate) -> MarketObservation` reutiliza
el contrato existente. La entrada ya contiene URL, dominio/retailer, título/snippet
y producto con referencia original/canónica y especificaciones.

`HttpMarketPageVerifier` descarga solo esa URL. Lee JSON-LD `Product`/`Offer` y
metadatos comerciales de precio/moneda; no ejecuta scripts ni interpreta precios
desde el texto de búsqueda. Si el HTML necesita JS para exponer el dato, no se inventa.
Varias ofertas/precios, rangos o bloques de recomendaciones sin vínculo claro a la
URL se rechazan por ambigüedad. Se contrastan marca, modelo explícito, tamaño/capacidad
y contradicciones de tipo de producto. La comparación cm/pulgadas usa conversión exacta.

Límites: 10 URLs únicas por ejecución, lectura secuencial, hasta 3 redirecciones,
2 MB descomprimidos por página y presupuesto de lectura de 20 s (timeout I/O máximo
10 s). DNS usa el resolver del sistema. HTTPS público, sin credenciales en URL,
puertos alternativos, destinos privados, proxies de entorno o cookies de sesión.
No hay retries de páginas. Cada redirección se valida nuevamente.

`httpx` ya existía como dependencia de desarrollo; se declara ahora como dependencia
runtime y se actualizó `uv.lock` sin cambiar versiones.

## Calidad y provenance

| Nivel | Procedencia | Uso monetario |
|---|---|---|
| `api_verified_price` | `/items`, evidencia estructurada API | Si identidad/condiciones son válidas |
| `page_verified_price` | HTTP 200 + producto/oferta en HTML | Si identidad/precio/moneda son válidos |
| `snippet_price` | Snippet/cache o verificación incompleta | Nunca por sí solo |

La agregación conserva evidencia débil, pero excluye snippets de min/mediana/max
incluso si un caller anterior marcó su matching como válido. En dedupe se prefiere
API válida, luego página verificada y finalmente snippet. No se cambia independencia:
tres vendedores ML siguen siendo marketplace concentrado.

`PageEvidence` conserva candidato original, URL final, HTTP status, captura actual,
SHA-256 del cuerpo, campos extraídos y localizador de extracción JSON-LD/meta.
No imprime ni guarda HTML completo en el recibo. Un precio observado hoy no garantiza
stock, impuestos, envío o checkout; estas limitaciones existentes permanecen.

Por candidato: `verification_status`, `extraction_method`, `price_evidence_level`,
`match_level`, `price`, `currency`, `rejection_reason`, `source`, `captured_at` y URLs.
La consola muestra un resumen compacto; el recibo guarda observaciones y duplicados.
`page_verification` resume intentos únicos, aceptados/rechazados y motivos por candidato.
Los motivos incluyen también candidatos repetidos; no equivalen al número de GETs.

Motivos centralizados en `RejectionReason`:
`wrong_model`, `wrong_size`, `wrong_product_type`, `wrong_brand`,
`accessory_or_replacement`, `generic_page`, `no_price`, `ambiguous_price`,
`currency_unknown`, `unavailable`, `blocked`, `stale_or_cache_only`,
`verification_failed`.

Vencimiento explícito de `priceValidUntil`, HTTP 304 sin cuerpo o respuesta marcada
stale no confirman precio actual. Un bloqueo/fallo de página no aborta otras ofertas;
los fallos quedan como degradaciones. API fallida permite intentar la página sin borrar
evidencia previa ni ampliar retries.

## Parada

Objetivo default: al menos 3 observaciones válidas y 2 fuentes independientes.
Máximo deseado: 5. Una vez suficiente, no se verifican más URLs ni se consume más
del iterador Scout. Si solo aparecen precios del mismo marketplace, se permite el
benchmark concentrado y se corta al alcanzar 5 o terminar el presupuesto disponible.
La llamada hosted del Scout sigue siendo indivisible y acotada; no se crea otro
agente ni un bucle de búsquedas indefinido.

## Ejecución de referencia

Desde `backend`, reutilizando el recibo anterior para verificar primero sus candidatos:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --brand Samsung --model 58U8000H --canonical-model UN58U8000H `
  --size "58 pulgadas" --product-type televisor --domain-id MCO-TELEVISIONS `
  --no-catalog `
  --web-receipt .local/market-price-scout-samsung-20261104-v1/market_benchmark.json `
  --output-directory .local/market-price-scout-v11/nueva-ejecucion
```

`--no-catalog` evita repetir catálogo ya validado; los listings concretos MCO todavía
pueden enriquecerse por API. `--no-scout` permite verificar únicamente candidatos
existentes sin otra búsqueda. Elegir directorio nuevo; no sobrescribe el recibo fuente.
Omitir `--web-receipt` para discovery habitual. Sin `--publish` no modifica la proyección UI.

## Aceptación real — 04/11/2026

Un solo intento, finalizado aproximadamente **16:26 Bogotá**, recibo:
`backend/.local/market-price-scout-v11-samsung-20261104-v1/market_benchmark.json`.

- Tres candidatos previos + cinco devueltos por una invocación del Scout.
- Seis URLs únicas consolidadas; dos registros duplicados preservados.
- **3 verificaciones HTTP de URL única intentadas**; dos respuestas HTTP 200 leídas.
- Éxito: la página identifica `UN58U8000FKXZL`, diferente del objetivo H.
- Compulago: la página identifica `UN58U8000F`, diferente del objetivo H.
- Samsung: `verification_failed`; no se confirmó contenido de página. El recibo no
  permite atribuir con certeza ese fallo a bloqueo, timeout o formato.
- Listados generales Falabella/ML y otra URL sin clasificación concreta no se descargaron.
- Catálogo/ML API: cero requests; no había listing MCO concreto y la referencia ya estaba dada.
- **0 observaciones monetarias válidas**, 0 páginas aceptadas y 0 fuentes válidas.
- Resultado: `insufficient_market_evidence`, sin mediana, comparación o señal.

Esto valida precisión/rechazos y continuidad, pero **no demuestra todavía** cobertura
comercial de tres precios para este modelo. No se forzó equivalencia F/H/U8500.
El recibo original se conserva; no se repitió la prueba real tras ajustes de diagnóstico.

## Archivos y tests

Agregados:

- `backend/src/public_procurement/investigation/market_benchmark/page_verifier.py`
- `backend/tests/unit/investigation/test_market_page_verification.py`
- `backend/tests/market_pages.py` (páginas sintéticas explícitas para regresiones existentes)
- Este documento.

Modificados:

- Módulo `market_benchmark`: `ports.py`, `schemas.py`, `service.py`, `aggregation.py`,
  `mercadolibre_adapter.py`, `foundry_scout.py`, `diagnostics.py`.
- CLI `backend/scripts/eureka_market_benchmark.py`.
- `backend/pyproject.toml`, `backend/uv.lock`.
- Tests `test_market_benchmark.py`, `test_market_price_scout.py`,
  `test_market_web_evidence.py`, `test_market_source_degradation.py`,
  `test_mercadolibre_benchmark.py`, `test_market_rejection_diagnostics.py`.
- Documento V1 anterior identificado como histórico.

355 tests de investigación pasan, incluidos 43 casos nuevos de verificación.
Ruff/format, Mypy del módulo/CLI y 13 contratos de importación pasan.
Las regresiones comerciales se ejecutan ahora con fixtures de página explícitos,
no promocionando snippets a precios verificados. No se modificó `matching.py`.

## Deuda deliberada

- Páginas que publican precio únicamente mediante JS no se verifican con este adaptador.
- Sin checkout ni validación visual independiente del JSON-LD/meta.
- Sin reconciliación inteligente de varias ofertas, recomendaciones, promociones o rangos.
- Validación de tipos de producto acotada a contradicciones observables; no taxonomía global.
- El resolver DNS del sistema no ofrece presupuesto total cancelable en este adaptador.
- Un fallo de red/formato puede dejar solo evidencia débil; nunca se compensa relajando matching.
