> **Hist?rico (V0.1/V0.2/spike).** Las estrategias RSS/site y comandos experimentales
> descritos abajo fueron retirados. El flujo vigente est? en
> [Market Price Scout](eureka-market-price-scout.md). Se preserva este documento
> como evidencia de decisiones y resultados anteriores, no como instrucciones operativas.

# Web Discovery V0.2 — ofertas concretas

Incremento local de `investigation/market_benchmark`, sin nuevos proveedores,
scraping HTML, browser automation, LLM, refresh de tokens ni escrituras de negocio.

## Estrategia

1. Si se habilita Mercado Libre, consultar opcionalmente su catálogo con los
   límites existentes. Solo un detalle seleccionado y verificado puede aportar
   su atributo `MODEL` como referencia canónica de búsqueda.
2. Si esa etapa falla, continuar con la referencia original o la canónica ya
   proporcionada por el caller. Web Search nunca requiere éxito de Mercado Libre.
3. Ejecutar hasta **9 queries web distintas**, máximo 10 resultados por query:
   cuatro variantes amplias/comerciales y cinco `site:`. Las amplias permiten
   encontrar tiendas distintas de los dominios dirigidos.
4. Clasificar y rankear resultados usando únicamente título, URL y snippet del
   buscador. **No abrir las URLs** para obtener HTML.
5. Intentar `/items/{id}` solo para IDs de publicaciones concretas descubiertos
   (o suministrados explícitamente), máximo diez. No repetir el discovery de
   catálogo después de Web Search ni inventar IDs a partir de catálogo.
6. Normalizar, deduplicar y usar la agregación y política de señales existentes.

## Queries y límites

Se usan marca, referencia original, canónica cuando existe, tipo de producto,
tamaño/capacidad/dimensiones, familia y contexto comercial Colombia/COP.
No hay constantes Samsung, televisores ni MCO80188666 en el generador.

Para Samsung / 58U8000H / UN58U8000H / televisor / 58 pulgadas se generan:

1. `"UN58U8000H" precio Colombia COP`
2. `"Samsung UN58U8000H" televisor 58 pulgadas precio Colombia`
3. `"Samsung 58U8000H" comprar Colombia COP`
4. `"Samsung U8000H" televisor 58 pulgadas comprar Colombia`
5. `site:mercadolibre.com.co "UN58U8000H" comprar Colombia COP`
6. `site:falabella.com.co "UN58U8000H" comprar Colombia COP`
7. `site:alkosto.com "UN58U8000H" comprar Colombia COP`
8. `site:ktronix.com "UN58U8000H" comprar Colombia COP`
9. `site:exito.com "UN58U8000H" comprar Colombia COP`

El máximo se configura con `--max-web-queries 1..9`, default 9. Las queries se
deduplican. Sin canónica se usa la original; sin atributos opcionales se omiten
esos términos, sin inventarlos. Un error de proveedor detiene las variantes web
restantes, sin reintentos. Resultados vacíos permiten continuar con las siguientes.
Se mantiene el límite por respuesta y timeout del adaptador de búsqueda existente.

El máximo de Mercado Libre se conserva: hasta 4 queries de catálogo, 3 detalles
y 10 ítems (17 requests). `--no-catalog` permite omitir la etapa de catálogo si
ya se conoce una referencia canónica. No se usa `/sites/MCO/search`.

## Clasificación y evidencia mínima

| Tipo de página | Ejemplos de señales | Candidato fuerte |
| --- | --- | --- |
| `product_page` | Referencia en slug, `/product/{id}`, `/p/{id}`, `/{producto}/p` | Sí, si identidad compatible |
| `marketplace_listing` | URL colombiana con ID MCO de publicación explícito | Sí, si identidad compatible |
| `home_page` | Raíz o home regional | No |
| `brand_page` | `/brand/`, `/marca/`, landing de marca | No |
| `category_page` | Categoría, búsqueda interna, promociones generales | No |
| `editorial` | Wikipedia, blog, noticia, manual, PDF de soporte | No |
| `unknown` | Estructura sin indicios suficientes de producto | No |

Los indicios de dominio reconocido, modelo en título/slug, precio y disponibilidad
incrementan prioridad. Un modelo/tamaño incompatible, accesorio, repuesto o
condición no comparable reduce prioridad y se rechaza por matching.

Una página fuerte **no equivale** a una observación económica válida. Además
debe tener identidad exact/high, precio total observable inequívoco, COP,
contexto comercial y disponibilidad no conocida como agotada. Sin precio se
conserva como candidato/evidencia, sin entrar a min/mediana/max.
Los precios pueden observarse en título o snippet. No se calculan cuotas,
descuentos ni conversiones implícitas.

La referencia canónica compatible y su combinación explícita de familia+tamaño
permiten `high`; no ocultan referencias o tamaños materialmente distintos.
Se conserva la referencia original del producto público. Los datos de catálogo
no crean una observación con precio ni acreditan una compra pública.

## Dedupe y provenance

- Misma URL normalizada, incluso entre queries.
- Misma tienda + producto solicitado + mismo precio: una oferta representativa.
  Se conserva cada evidencia excluida en `benchmark.duplicates`.
- Misma publicación MCO entre Web Search y API: preferir API recuperada y válida.
- Distintos sellers de Mercado Libre no se presentan como distintos retailers.
- Se conservan query y fecha del resultado, `discovered_queries`, snippet,
  `page_type`, `discovery_score`, match level/reason y motivo de exclusión.
- La selección prefiere API, validez y prioridad de discovery antes de fecha/ID;
  no se elige la oferta por producir una diferencia de precio más favorable.

La clasificación de suficiencia conserva los contratos existentes:
`sufficient_diverse_market_evidence`, `marketplace_concentrated_evidence`,
`insufficient_market_evidence` y el caso adicional `limited_source_diversity`.
La concentración en Mercado Libre no equivale al mercado completo.

## Fallos y salida

401/403/429, timeout, 5xx, token ausente, catálogo vacío o malformado y fallos de
enriquecimiento son degradaciones opcionales. La evidencia web suficiente sigue
en el benchmark; no se borra por un fallo de API. Un detalle API recuperado que
demuestre condición/estado incompatible sí prevalece sobre un snippet viejo.
Sin resultados/precios se informa insuficiencia, no una excepción global ni
una conclusión de ausencia de mercado.

`web_discovery` registra versión, queries planeadas/ejecutadas, conteos de tipos
de página y URLs fuertes únicas, estado de fuente y canónica utilizada.
El JSON de ejecución conserva candidatos y evidencia completos. La consola
muestra un resumen compacto y hasta diez candidatos fuertes; `--verbose` imprime
el recibo completo. No se imprimen tokens ni headers.

## Cómo probar desde backend (no ejecutado en esta iteración)

Mercado Libre opcional puede aportar automáticamente la canónica:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --source combined --brand Samsung --model 58U8000H `
  --product-type televisor --size "58 pulgadas" `
  --domain-id MCO-TELEVISIONS `
  --max-web-queries 9 `
  --output-directory .local/market-benchmark-web-v02
```

Para reutilizar la canónica ya verificada y omitir catálogo, añadir
`--no-catalog --canonical-model UN58U8000H`. Esto mantiene enriquecimiento de ítems
concretos si Web Search los descubre. Para Web Search independiente usar
`--source web-search --canonical-model UN58U8000H`, sin dependencia de Mercado Libre.

Para vincular la oferta documentada MC-070-2026, sustituir `--brand/--model` por
`--public-product .local/market-benchmark-samsung-58u8000h-20261104/mc070-public-offer.json`.
Se conserva su etapa de oferta, fecha desconocida, precio antes de IVA y conflicto
de encabezado. Esta iteración **no modifica la política de señales definitivas**.
`--publish` sigue siendo opcional para actualizar solo la proyección JSON local.

El buscador RSS sigue siendo experimental: mejores queries no garantizan que
devuelva ofertas ni precios. La aceptación real debe comprobarse con el recibo
de una ejecución autorizada; los fixtures no son hallazgos reales.

## Archivos de esta iteración

- `market_benchmark/schemas.py`, `query_expansion.py`, `matching.py`, `aggregation.py`,
  `service.py`, `mercadolibre_adapter.py`.
- Nuevos `market_benchmark/urls.py`, `web_pages.py`, `web_discovery.py`.
- `backend/scripts/eureka_market_benchmark.py`.
- Tests: `test_market_benchmark.py`, `test_mercadolibre_benchmark.py`,
  `test_market_source_degradation.py` y nuevo `test_web_discovery_v02.py`.
- UI: `frontend/src/features/research/MarketBenchmark.tsx` y su test.
- Esta documentación y enlaces desde los documentos previos de benchmark.

Sin nuevas dependencias, migraciones ni cambios en Radar, Estado vs Estado,
taxonomía global, límites documentales o automatización de tokens. No se leyó
ni modificó `.env` ni se ejecutaron búsquedas reales para implementar este incremento.

## Verificación

- 146 pruebas específicas del benchmark y fuentes, tras la última guarda de
  atributos canónicos malformados.
- Suites backend ampliadas: 467 pasan, 1 omitido; posteriormente se añadió la
  prueba de esa guarda y se repitieron las 146 focales.
- Frontend completo: 162 pasan (`--maxWorkers=2`).
- Ruff/formato, Mypy, ESLint, TypeScript/build y 13 contratos de imports correctos.
- Generación offline de las nueve queries del ejemplo y `--help` comprobados.
- Todos los proveedores en tests son mocks. No hay observaciones reales nuevas.

## Diagnóstico de rechazados sin cambiar matching

Añadir `--diagnose-rejected` a una corrida imprime los candidatos web rechazados,
además del resumen. Incluye query, domain, url, title, snippet, page_type,
rejection_reason, extracted_mco_id y price_detected. Se priorizan en la salida
Mercado Libre, Falabella, Alkosto, Ktronix y Éxito; los demás dominios también se
conservan. Los duplicados quedan identificados y se mantienen sus queries.
`price_detected` es el precio normalizado ya guardado (o null), no una nueva
extracción de números del snippet ni una reevaluación del matching.

Para diagnosticar la ejecución existente **sin búsquedas, API, configuración ni
escrituras del comando**:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --diagnose-receipt .local/market-benchmark-web-v02/market_benchmark.json
```

En la inspección offline del recibo del usuario se encontraron 62 registros web
rechazados, correspondientes a 50 URLs únicas y 12 duplicados. Cero precios
normalizados y cero IDs de publicaciones MCO. Las queries `site:` devolvieron
dominios ajenos al filtro: Mercado Libre → YouTube/Spotify; Falabella → soporte
Microsoft; Alkosto → Wikipedia; Ktronix → foros/noticias; Éxito → Claro.
Esto evidencia una discrepancia entre consulta y resultados del adaptador/buscador;
no demuestra que no existan ofertas ni justifica relajar matching.

Se exportó la proyección a
`backend/.local/market-benchmark-web-v02/rejected_candidates.diagnostic.json`,
conservando intacto el recibo original. No se hicieron requests ni se cambió
matching/clasificación/scoring. Cuatro tests nuevos comprueban campos, motivos,
prioridad de dominios y ejecución offline sin proveedores ni escrituras;
41 tests afectados pasan, junto con Ruff/formato y Mypy.
