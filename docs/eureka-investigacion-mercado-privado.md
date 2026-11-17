> **Hist?rico (V0.1/V0.2/spike).** Las estrategias RSS/site y comandos experimentales
> descritos abajo fueron retirados. El flujo vigente est? en
> [Market Price Scout](eureka-market-price-scout.md). Se preserva este documento
> como evidencia de decisiones y resultados anteriores, no como instrucciones operativas.

# Estado vs mercado privado — V0.1

El discovery web vigente se describe en [Web Discovery V0.2](eureka-web-discovery-v02.md):
hasta nueve queries controladas y gating de páginas concretas. El caso real y
las cifras de la prueba inicial de este documento se conservan como histórico.

Módulo determinístico independiente en
`backend/src/public_procurement/investigation/market_benchmark/`.
No usa el agente Eureka, extracción con LLM, CDP, LECTOR ni scraping de retailers.
No modifica el cálculo Estado vs Estado, Radar ni datos de negocio.
No requiere migraciones.

## Flujo y ejecución explícita

Producto público con marca, referencia y precio documental → una búsqueda backend
→ observaciones con snippet original → matching → deduplicación → mediana
→ comparación con signo → señal investigativa si hay evidencia suficiente.

Desde `backend`, con un JSON de entrada pública verificada:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --public-product ruta/producto-publico.json `
  --output-directory .local/market-benchmark/nueva-ejecucion `
  --publish
```

Para una señal final, el JSON debe satisfacer `PublicProduct`: identidad/código/entidad del proceso,
descripción, marca/modelo, precio unitario positivo, etapa `contract`, `awarded`
o `accepted_offer`, fecha con zona horaria, referencia de evidencia, documento,
página/referencia y origen `explicit` o `calculated`. Presupuesto no es admisible.
El servicio exige provenance; quien produce la entrada debe verificarla contra
la evidencia original. La validación del contrato no certifica un documento por sí sola.

También se admite `PublicOffer` (`public_price_stage="offer"`) como evidencia
preliminar. Su fecha puede ser desconocida y queda `null`: no se sustituye por
fecha de publicación/carga/captura. Una oferta nunca se convierte implícitamente
en compra ni genera señal final. Se muestran precio y benchmark, pero no se
calcula una diferencia numérica sin homologar impuestos. Las discrepancias de
código en el documento se conservan y bloquean comparación/señal definitivas,
incluso si alguien etiquetara la entrada como contractual.

También existe un modo de investigación de producto sin evidencia pública:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_market_benchmark.py `
  --brand Samsung --model 58U8000H `
  --output-directory .local/market-benchmark/nueva-ejecucion `
  --publish
```

Este modo **nunca genera comparación ni señal**, aunque encuentre precios privados.
No se ejecuta automáticamente al entrar a la UI.

## Fuente web y controles

Adaptador experimental `BingRssSearch`: una consulta exacta orientada a Colombia,
máximo 10 resultados, timeout 30 segundos, respuesta máxima 512 KB, sin retries.
Solo solicita al buscador; bloquea redirecciones fuera de su origen. No visita
los enlaces de los resultados. RSS es una interfaz experimental cuya calidad,
disponibilidad y precisión no están garantizadas; está detrás del puerto `WebSearch`.
No se usan las credenciales ni el agente remoto de Foundry.

Se preservan consulta, proveedor, URL, título, snippet y captura por candidato.
La etiqueta retailer es el hostname observado, no una certificación del vendedor.
Se infiere COP solo con mención explícita o dominio colombiano reconocido;
otros dominios siguen siendo admisibles si la moneda es explícita.

Identidad exacta: marca y referencia completas. Equivalencia `high` acotada a
prefijo Samsung `UN` y sufijos regionales explícitos `K`/`KXZL`, sin cambiar la
referencia base ni tamaño. No hay equivalencias por similitud libre.
`partial` requiere al menos familia/tamaño concordante; resultados genéricos o
irrelevantes se rechazan. Solo exact/high con precio válido entran al benchmark.

Se excluyen accesorios, bundles detectados, usados/reacondicionados, precio
ambiguo, múltiples precios distintos, cuotas y moneda no confirmada. Se conserva
promoción con total inequívoco. Disponibilidad desconocida se conserva con nota;
agotados no se agregan. Las reglas son conservadoras: un snippet de precio
anterior/actual o financiación junto a un total se conserva como evidencia pero
no se usa para calcular el benchmark.

Deduplicación: hostname sin `www`, URL sin fragmento/tracking, referencia y precio.
Rutas/ofertas distintas se conservan. No se resuelven aliases de vendedor,
marketplaces ni equivalencias desconocidas de URLs en esta versión.

## Benchmark y límites

Con mínimo 3 observaciones válidas: min/mediana/max; Decimal en todos los cálculos.
La diferencia es público menos mediana privada, con porcentaje firmado sobre
la mediana. No se aplica umbral de diferencia.
Con menos de 3: `insufficient_market_evidence`, sin comparación ni señal.
Poca diversidad de retailers y disponibilidad desconocida quedan visibles.
La confianza es una heurística conservadora acotada a 0,65, no una probabilidad.

Toda comparación conserva fecha pública, captura privada, separación temporal,
provenance y la advertencia:

> Benchmark privado capturado en fecha actual; no representa necesariamente el
> precio de mercado vigente en la fecha de la compra pública.

Los snippets no verifican checkout, stock final, envío, impuestos ni condiciones
comerciales. La señal `PUBLIC_VS_PRIVATE_PRICE_DIFFERENCE` solo representa una
diferencia cuantificada, no una conclusión sobre su causa.

## Persistencia y UI

`market_benchmark.json` conserva cada ejecución en la carpeta indicada.
`--publish` actualiza únicamente `investigation/private-market-latest.json`.
No sobrescribe `investigation/latest.json` ni facts, canonicals o señales de negocio.
GET `/api/v1/investigation/private-market` es una proyección de lectura sin búsqueda.
Explorar y Señales muestran la tarjeta separada, límites y observaciones desplegables.
La publicación local expone la última ejecución; historial multi-benchmark queda pendiente.

## Única prueba real — 04/11/2026, 08:36:33 Bogotá

Consulta: `"Samsung 58U8000H" precio Colombia COP`.
Una petición al buscador, sin peticiones a retailers ni reintentos.
9 candidatos: páginas generales Samsung (6), Falabella (2) y Wikipedia (1).
Ninguno confirmó el modelo ni un precio de producto completo.

- Observaciones válidas: **0**; retailers válidos: **0**.
- Min/mediana/max: ausentes.
- En la prueba inicial, el precio comunicado de **$3.767.123 COP** aún no tenía
  vínculo documental localizado. Posteriormente se verificó offline como oferta,
  según el apartado siguiente; no se repitió la búsqueda.
- Comparación y señal: **no generadas**.
- Estado inicial: `insufficient_market_evidence` y `missing_public_evidence`.
  Tras localizar el documento: `insufficient_market_evidence` y
  `documented_unconfirmed_offer`.

Evidencia local:
`backend/.local/market-benchmark-samsung-58u8000h-20261104/market_benchmark.json`.
El buscador devolvió resultados genéricos pese a la referencia exacta. Esto
limita la fuente elegida; **no demuestra que el producto no exista en el mercado**.
Falta validar otra fuente de búsqueda útil y demostrar la aceptación de la oferta
y su vinculación documental antes de afirmar que el caso funciona end-to-end.

La impresión inicial de consola falló por codificación Windows después de guardar
el JSON. Se corrigió la salida a ASCII escapado, sin repetir la consulta.
La clasificación de los mismos candidatos se revisó offline; se preservó el recibo original.

## Localización de la oferta MC-070-2026 — verificación local posterior

- Proceso del inventario: **MC-070-2026**, `CO1.REQ.11253117`, Universidad del Atlántico.
- Contrato asociado en metadata: `CO1.PCCNTR.10103437` (snapshot: en aprobación,
  sin fecha de firma). Proveedor de metadata: TEAM IT SAS. Esto no demuestra por
  sí solo aceptación de la fila económica.
- Archivo: `OFERTA ECONOMICA  MC-070-2026.pdf`, documento oficial **878001221**.
- SHA-256: `d5cb637298be9587ce50ccc6f85bc53acc0aec48c92cca1006822d7233d91899`.
- **Página PDF 339 de 340**: cantidad 1, TV Samsung 58U8000H, valor unitario y
  total del ítem **$3.767.123 COP**. Proponente: TEAM IT.
- **Página 337**: encabezado `VALOR UNI ANTES DE IVA / VALOR TOTAL ANTES DE IVA`.
  El valor del ítem es antes de IVA; no se compara directamente con retail sin
  confirmar una base tributaria equivalente. No se infiere un precio contractual
  ni se suma IVA automáticamente.
- Ese mismo encabezado dice **MC-028-2026**, distinto de MC-070-2026 del inventario.
  Se conserva `document_process_reference_mismatch`; no se decide arbitrariamente
  si es error de plantilla o de asociación documental.
- Fecha de oferta no establecida: `public_price_date=null`.

Se buscó texto nativo únicamente en el PDF ya descargado y se inspeccionó la
página 339 visualmente. Sin peticiones, descargas nuevas, OCR ni escrituras DB.
La inspección puntual no cambió el límite general de extracción de 300 páginas
ni reescribió su resultado histórico `page_limit`.

Recibos locales junto al benchmark: `mc070-native-locator.json`,
`mc070-page-339.png` y `mc070-public-offer.json`.
La proyección actual conserva oferta, documento/página, proponente, evidencia y
advertencias; `comparison=null`, `signal=null`. Solo se reutilizaron los mismos
9 resultados de búsqueda originales.

## Verificación

- 32 tests del módulo: matching, cuotas, promociones, moneda, mediana,
  dedupe, diferencias con signo, provenance, gating, JSON y endpoint sin escrituras,
  errores de búsqueda, bloqueo de redirecciones, oferta sin fecha y conflicto de referencia.
  Tres tests UI del benchmark incluyen oferta preliminar, IVA y conflicto documental.
- Suites backend afectadas: 352 pasan; 1 test opcional omitido.
- Frontend completo: 157 pasan. En una segunda ejecución concurrente apareció
  un timeout de `HumanReviewPage`; su repetición dirigida pasó junto con investigación
  (26 tests). No se modificó esa funcionalidad.
- Ruff/formato, Mypy, ESLint, TypeScript, build y 13 contratos de imports correctos.
- Smoke visual Edge headless con build y recibos reales servidos offline:
  tarjeta visible, cero errores JavaScript. El frontend de desarrollo no estaba
  activo; no se levantó ni reinició el stack para esta comprobación.
- No se hizo una segunda consulta real. Los resultados `.local` no se versionan.
