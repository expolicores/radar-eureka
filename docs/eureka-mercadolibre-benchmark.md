> **Hist?rico (V0.1/V0.2/spike).** Las estrategias RSS/site y comandos experimentales
> descritos abajo fueron retirados. El flujo vigente est? en
> [Market Price Scout](eureka-market-price-scout.md). Se preserva este documento
> como evidencia de decisiones y resultados anteriores, no como instrucciones operativas.

# Mercado Libre Colombia — adaptador de benchmark V0.1

[Web Discovery V0.2](eureka-web-discovery-v02.md) añade búsquedas comerciales
orientadas a páginas concretas y aprovecha el modelo de catálogo verificado
antes de Web Search. Mercado Libre conserva su carácter opcional y no bloqueante.

Implementación opt-in y **no bloqueante** en `investigation/market_benchmark/mercadolibre_adapter.py`.
Web Search es el discovery amplio y funciona sin Mercado Libre. El adaptador
complementa Web Search y reutiliza sus contratos, matching, agregación y política
de señales. No usa el agente conversacional, scraping, CDP, LLM ni LECTOR.
No requiere tablas/migraciones, scheduler ni escrituras de negocio.

## Auditoría y fuentes oficiales

Se reutilizaron `MarketObservation`, `ProductIdentity`, `PublicOffer`,
`PublicProduct`, `PrivateMarketBenchmark`, `compare` y `MarketReportStore`.
El matching de identidad se extrajo a `match_identity` para que el adaptador
estructurado no fabrique resultados Web Search ni mantenga otra lógica de modelos.
`ApiEvidence` conserva origen, país, endpoint, captura y campos públicos observados.

Se verificó la documentación oficial:

- [Búsqueda de productos y detalle de catálogo](https://developers.mercadolibre.com.co/en_us/real-estate-subscribe-to-our-feeds/products-search):
  `/products/search` con `site_id`, `q`, `status`, y `/products/{id}`.
- [Detalle de publicaciones](https://developers.mercadolibre.com.co/en_us/list-products):
  usar `/items/{id}` exclusivamente para IDs concretos descubiertos por web o
  entregados explícitamente. No se usa multiget en este flujo.
- [Ítems públicos y disponibilidad](https://developers.mercadolibre.com.co/en_us/items-and-searches):
  búsquedas públicas devuelven publicaciones activas y `available_quantity` es
  referencial; no significa inventario exacto.
- [OAuth server-side](https://developers.mercadolibre.com.co/es_co/autenticacion-y-autorizacion):
  Authorization Code, credenciales y tokens exclusivamente en backend.

El usuario validó OAuth, catálogo e ítems individuales, y confirmó 403 para
`/sites/MCO/search`. Ese endpoint se eliminó del flujo y de la allowlist HTTP.
No se hace una búsqueda de publicaciones del usuario ni se toma su inventario
particular como sustituto del mercado amplio.

## Configuración

Copiar las entradas de `backend/config/mercadolibre.env.example` en `backend/.env`
o definirlas como variables del proceso backend.

- `MERCADOLIBRE_ACCESS_TOKEN`: obligatorio para el spike.
- `MERCADOLIBRE_CLIENT_ID`, `MERCADOLIBRE_CLIENT_SECRET`,
  `MERCADOLIBRE_REFRESH_TOKEN`: reservados para OAuth manual/server-side;
  no se usan aquí para intercambiar ni refrescar tokens.

No poner valores en frontend, `VITE_*`, argumentos CLI, archivos example ni logs.
Los settings usan `SecretStr` y ocultan entradas de errores. El transporte usa
Bearer exclusivamente en el header, rechaza parámetros no permitidos y bloquea
todas las redirecciones para no reenviar credenciales. No hay acceso anónimo,
login automático ni refresh automático. No se necesita configurar una conexión
de Foundry para este adaptador.

## Endpoints y carga máxima de una ejecución

Solo origen `https://api.mercadolibre.com`; país fijo `MCO`.

1. Hasta cuatro `GET /products/search?site_id=MCO&status=active&q=...&limit=5`.
2. Hasta tres `GET /products/MCO...`, solo para candidatos exact/high.
3. Hasta diez `GET /items/MCO...`, únicamente con IDs concretos de URLs web o CLI.

Máximo 17 requests, secuenciales, timeout 20 s por request y límite 2 MB por
respuesta. Sin retries, paginación adicional ni consultas de usuarios/vendedores.
No se toma el primer catálogo como correcto: se contrastan identidad y atributos,
se verifica detalle activo y se selecciona solo una coincidencia inequívoca en
la muestra validada. Catálogo ambiguo o no encontrado queda explícito.
El descubrimiento de catálogo se puede omitir (`--no-catalog`). Un producto de
catálogo no es una publicación: nunca se transforma su resultado en un precio
válido ni se inventa un item ID a partir de un catalog product ID.
Las URLs `/p/MCO...` identifican catálogo y no se envían a `/items/{id}`.

`query_expansion.py` genera variantes genéricas a partir de marca/referencia,
tipo de producto, tamaño/capacidad/dimensiones y familia. Se deduplican y limitan
a cuatro consultas, sin reglas de marca o categoría en el generador.
Para Samsung con tamaño explícito, por ejemplo: `Samsung 58U8000H`,
`Samsung televisor 58U8000H`, `Samsung 58 pulgadas 58U8000H`,
`Samsung 58 pulgadas U8000H`.

`ProductIdentity` admite contexto opcional `product_type`, `size`, `capacity`,
`dimensions`, `product_family`, `expected_domain_id`, `expected_catalog_product_id`
y `relevant_attributes`. Es contexto local del benchmark; no cambia la taxonomía
global. El dominio esperado es explícito, no se deduce una categoría universal.
Dominios incompatibles se rechazan aunque mencionen la referencia. Medidas
explícitas contradictorias también se rechazan; no se inventan conversiones.
Se puede reconstruir una referencia partida con marca+tamaño+familia+dominio
concordantes como `high`, sin ocultar una referencia o tamaño materialmente distinto.

El resultado conserva candidatos de catálogo, detalles, selección/motivo,
candidatos de publicaciones, observaciones, errores, warnings y requests sanitizados.
Un catálogo coincidente no disculpa atributos contradictorios de una publicación.

## Normalización y exclusiones

Solo publicaciones `active`, nuevas, COP, identificadas en MCO y con permalink
colombiano HTTPS, vendedor identificable y precio total positivo/finito.
Se preservan título, atributos, seller/store/catalog IDs, condición, estado,
garantía, dominio, tags, `date_created` y `last_updated` cuando vienen en la respuesta. Datos ausentes quedan nulos;
no se inventan seller names ni permalinks.

`price` es el precio listado: no se multiplican cuotas, no se suman fletes y no
se reconstruyen descuentos. Promoción se marca si `original_price > price`.
Se rechazan usados, reacondicionados/open box, accesorios/bundles, variantes de
precio ambiguas, subastas y referencias/tamaños incompatibles.
El matching de atributos puede fortalecer un título incompleto, pero no ocultar
un conflicto de modelo o tamaño.

`available_quantity_reference` solo informa disponibilidad. No se usa en
aritmética económica ni se muestra como unidades exactas de stock.
Ausente → disponibilidad desconocida; cero → no disponible y excluida.

## Dedupe y suficiencia

- Una publicación se cuenta una vez por URL/listing ID, incluso entre Web Search
  y API. Se prefiere la observación estructurada de API sobre el snippet.
- Una observación válida representativa por seller y producto, aunque tenga
  otras publicaciones/precios. Orden determinístico: API, validez, exactitud,
  captura más reciente y luego ID/URL; no se elige por precio más favorable.
- Duplicados quedan en `benchmark.duplicates`, con `duplicate_of`, evidencia y
  exclusión del cálculo. No se borran sus recibos.
- Mercado Libre cuenta como **una plataforma** en `retailers_count` e
  `independent_sources_count`. `distinct_sellers_count` informa vendedores aparte.
- `observations_count` cuenta observaciones no duplicadas, incluidas rechazadas;
  `valid_observations_count` es la muestra económica efectiva.

Suficiencia:

| Clasificación | Regla |
| --- | --- |
| `sufficient_diverse_market_evidence` | ≥3 observaciones válidas, ≥2 fuentes/plataformas |
| `marketplace_concentrated_evidence` | ≥3 válidas, todas en Mercado Libre |
| `insufficient_market_evidence` | <3 válidas |
| `limited_source_diversity` | ≥3 válidas, un único retailer distinto de Mercado Libre |

Concentrado puede tener min/mediana/max provisionales, pero **no genera comparación
ni señal fuerte**. Se mantiene mediana como referencia y confianza conservadora.
Los contadores no presentan cada vendedor como retailer independiente.

## Ejecutar desde backend

Web Search amplio más Mercado Libre opcional, con la oferta pública localizada:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --source combined `
  --public-product .local/market-benchmark-samsung-58u8000h-20261104/mc070-public-offer.json `
  --product-type televisor --size "58 pulgadas" --domain-id MCO-TELEVISIONS `
  --output-directory .local/market-benchmark-combined-nueva-ejecucion
```

Para una prueba de catálogo solamente, usar `--source mercadolibre` con los
mismos campos de producto/contexto. No producirá precios si no hay IDs de publicaciones.
Para combinar con un recibo web anterior **sin volver a consultar Web Search**,
usar `--source mercadolibre` y añadir:

```powershell
--web-receipt .local/market-benchmark-samsung-58u8000h-20261104/market_benchmark.original.json
```

Web Search sigue disponible como fuente original (default `--source web-search`).
Para enriquecer una publicación concreta sin catálogo, usar
`--source mercadolibre --no-catalog --item-id MCO_ID_REAL` (reemplazar el ID por
uno de publicación comprobado; no usar el ID de catálogo MCO80188666).
`--item-id` es repetible, máximo diez IDs. No se ejecutó una prueba real en esta
iteración; estos comandos son instrucciones para una ejecución posterior.
`--publish` es opcional: únicamente actualiza la proyección JSON local del benchmark.
No dispara peticiones desde React ni desde el endpoint GET de lectura.
Cada candidato conserva su fecha original al reutilizar un recibo web; se advierte
que el benchmark combina capturas distintas.

## Caso público y bloqueos que se mantienen

MC-070-2026, documento 878001221, PDF página 339, TEAM IT, 1 Samsung 58U8000H,
$3.767.123 **antes de IVA**. Sigue siendo oferta no confirmada, sin fecha de
oferta acreditada y con encabezado MC-028-2026 distinto del expediente.
No se inventa aceptación por coincidir el proveedor o monto global.
El benchmark privado puede mostrarse, pero no hay señal definitiva ni diferencia
numérica sin homologación tributaria y compra sustentada.

## Errores y resultados

- Configuración ausente: `missing_auth_configuration`, cero HTTP de Mercado Libre.
- 401: `token_expired_or_invalid`; renovación manual requerida.
- 403: `access_forbidden`; no se intenta otra sesión ni país. Web Search continúa.
- 429: `rate_limited`; se detiene la fuente API sin retries, el benchmark continúa.
- Timeout/red/JSON inválido: códigos explícitos sin cuerpo remoto ni secretos.
- Catálogo/publicación 404: diagnóstico específico; no se fabrica el recurso.
- Resultados vacíos: `catalog_empty_results`; catálogo ausente queda explícito.
- Payload malformado y 5xx: degradación sanitizada, sin abortar el benchmark.
- La respuesta conserva `source_degradations`, errores por etapa y
  `mercadolibre.source_status=degraded`; `status=completed_with_warnings`.
  El comando combined/mercadolibre termina normalmente ante degradación opcional.
  Solo se mantiene el error CLI original si la fuente elegida es exclusivamente
  Web Search y esa fuente falla.

Un error HTTP/de formato de enriquecimiento **no borra una observación web** que
ya tenga evidencia suficiente. Un detalle API recuperado correctamente que pruebe
condición/estado incompatible sí se conserva como rechazo y prevalece sobre el
snippet para esa misma publicación. Continúan la deduplicación y la política de
señales existente; no se convierte una fuente degradada en prueba de ausencia.

Web Search conserva `source_type=web_search` y clasifica `web_source_kind` como
`retailer_web`, `marketplace_web`, `manufacturer_web` u `other_web`. Estas etiquetas
son clasificación de provenance; no se convierten en nuevos retailers por vendedor.

## Resultado histórico del primer adaptador — 04/11/2026

- 41 tests específicos Mercado Libre; 73 junto al benchmark previo.
- Suites backend afectadas: **395 pasan, 1 omitido**.
- Frontend completo: **160 pasan** con `--maxWorkers=2`; los cinco tests de la
  tarjeta cubren también vendedores, concentración y error de configuración.
  La ejecución inicial de alta concurrencia tuvo el timeout preexistente de
  `HumanReviewPage`; no se modificó esa funcionalidad.
- Ruff/formato, Mypy, ESLint, TypeScript/build y 13 contratos de imports correctos.
- Comprobación del comando Samsung 58U8000H: **`configuration_error`** /
  **`missing_auth_configuration`**, porque no existe token en el entorno backend.
- Requests reales a Mercado Libre: **0**. Retries: **0**.
- Catálogo, publicaciones, vendedores y precios: **no recuperados**, no se puede
  concluir que no existan. Min/mediana/max no calculables; sin señal ni comparación final.
- Recibo local:
  `backend/.local/mercadolibre-samsung-58u8000h-20261104/market_benchmark.json`.
- No se usó `--publish`: se conserva la proyección previa de investigación.

Ese recibo histórico no describe la autenticación actual: el usuario confirmó
posteriormente OAuth y acceso a los endpoints indicados. En esta iteración no se
inspeccionaron ni imprimieron sus secretos y no se hicieron peticiones reales.

## Verificación de la integración no bloqueante

- Suites backend afectadas: **432 pasan, 1 omitido**; incluyen 110 pruebas del
  benchmark, adaptador y degradación entre fuentes.
- Frontend completo: **161 pasan** con `--maxWorkers=2`.
- Ruff/formato, Mypy, ESLint, build/TypeScript y 13 contratos de imports correctos.
- `--help` comprobado sin cargar credenciales ni ejecutar consultas.
- Sin llamadas reales en esta iteración. No se modificó `.env`, automatización
  de tokens, comparación Estado vs Estado, políticas de señales definitivas,
  taxonomía global, límites documentales ni Radar.
- El fixture MCO80188666 aparece solo en tests/documentación, nunca en producción.

Archivos de esta iteración:

- `backend/src/public_procurement/investigation/market_benchmark/schemas.py`
- `backend/src/public_procurement/investigation/market_benchmark/query_expansion.py` (nuevo)
- `backend/src/public_procurement/investigation/market_benchmark/matching.py`
- `backend/src/public_procurement/investigation/market_benchmark/aggregation.py`
- `backend/src/public_procurement/investigation/market_benchmark/mercadolibre_adapter.py`
- `backend/src/public_procurement/investigation/market_benchmark/service.py`
- `backend/scripts/eureka_market_benchmark.py`
- `backend/tests/unit/investigation/test_mercadolibre_benchmark.py`
- `backend/tests/unit/investigation/test_market_source_degradation.py` (nuevo)
- `frontend/src/features/research/MarketBenchmark.tsx`
- `frontend/src/features/research/MarketBenchmark.test.tsx`
- `docs/eureka-mercadolibre-benchmark.md`
