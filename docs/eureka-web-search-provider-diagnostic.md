> **Hist?rico (V0.1/V0.2/spike).** Las estrategias RSS/site y comandos experimentales
> descritos abajo fueron retirados. El flujo vigente est? en
> [Market Price Scout](eureka-market-price-scout.md). Se preserva este documento
> como evidencia de decisiones y resultados anteriores, no como instrucciones operativas.

# Spike mínimo — provider de Web Search

Fecha de ejecución: **04/11/2026, aproximadamente 14:27 Bogotá**.
Solo dos consultas al backend existente, sin retailers, matching ni ranking.

## Componente identificado

- Clase: `BingRssSearch`.
- Archivo: `backend/src/public_procurement/investigation/market_benchmark/web_search_adapter.py`.
- Backend real: **Bing RSS**, GET `https://www.bing.com/search`.
- No es el agente Eureka, Foundry, Azure AI Search ni una API autenticada de Bing.
- Configuración fija: `format=rss`, `mkt=es-CO`, timeout 30 segundos,
  respuesta máxima 512.000 bytes, primeros 10 ítems. Sin retries.
- Recibe un string en `.search(query)`. `urlencode` lo pone íntegro en `q`;
  solo codifica caracteres para transporte, sin quitar `site:` ni comillas.
- User-Agent fijo `EurekaResearch/0.1`; no se usan API keys, tokens o cookies
  de la aplicación. No se carga `.env` para este spike.
- La respuesta se parsea como XML RSS con `defusedxml`, recorriendo
  `channel/item`. `title`, `link` y `description` pasan a título, URL y snippet.
  El adaptador normal admite HTTPS sin credenciales en URL; conserva orden de
  los primeros 10 ítems, añade captura UTC y `search_provider=bing_rss`.
  No aplica matching comercial ni reordena resultados.

## Ejecución

Desde `backend`, una query (default del spike):

```powershell
.\.venv\Scripts\python.exe scripts/eureka_web_search_diagnostic.py
```

Comparación controlada con la misma frase sin `site:`:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_web_search_diagnostic.py --compare-without-site
```

`--query` permite otro input explícito. `--compare-without-site` solo elimina
el operador para construir la **segunda consulta solicitada**, no transforma
silenciosamente ninguna query enviada. Máximo dos consultas, sin retries.

Cada ejecución crea un directorio nuevo en `.local/web-search-diagnostics/`.
`--output-directory` es opcional; si ese directorio ya existe, el comando aborta
antes de consultar al proveedor, sin sobrescribir nada.

Guarda `query-01.json`, `response-01.xml`, sus equivalentes para la segunda query
y `manifest.json`. Cada JSON incluye input, query efectiva, URL/params reales,
status, metadatos RSS, cantidad de resultados crudos y parseados, ranks originales,
títulos, dominios, URLs, snippets, pubDate/guid/source disponibles y checks
observacionales de dominio/frase visible. El XML se conserva byte por byte con
SHA-256. No se registran headers de request, Set-Cookie ni autenticación.

El diagnóstico muestra también resultados HTTP rechazables por el filtro normal
de URL, sin cambiar ese filtro: distingue `adapter_url_eligible` y
`parsed_results_count`. En esta prueba los 10 resultados fueron HTTPS elegibles;
el parser no descartó ni sustituyó URLs.

## Request principal observado

Input = query efectiva = query declarada por el canal RSS:

```text
site:mercadolibre.com.co "UN58U8000H"
```

Request:

```text
GET https://www.bing.com/search?q=site%3Amercadolibre.com.co+%22UN58U8000H%22&format=rss&mkt=es-CO
```

Parámetros: `q` contiene exactamente el input; `format=rss`; `mkt=es-CO`.
No se envía filtro nativo de dominio separado ni allowlist.

## Comparación real

| Evidencia | Con site: | Sin site: |
| --- | --- | --- |
| Query | `site:mercadolibre.com.co "UN58U8000H"` | `"UN58U8000H"` |
| HTTP | 200 | 200 |
| Content-Type | text/xml; charset=utf-8 | text/xml; charset=utf-8 |
| Ítems RSS / parseados | 10 / 10 | 10 / 10 |
| Dominios | www.caracoltv.com (8), ditu.caracoltv.com (2) | support.google.com (10) |
| Cumplen dominio solicitado | 0/10 | No aplica |
| Referencia visible en título/snippet | 0/10 | 0/10 |
| Tamaño XML | 5.569 bytes | 6.059 bytes |
| Canal RSS repite la query correcta | Sí | Sí |

La segunda URL solo cambia `q` a `%22UN58U8000H%22`; format y mercado permanecen.
Las respuestas difieren, por lo que `site:` cambia el conjunto obtenido, pero
**no actuó como restricción de dominio en esta prueba**.
No se abrieron las páginas destino: ausencia de frase en título/snippet no
demuestra formalmente ausencia en todo el contenido indexado.

SHA-256 de los XML:

- Con site: `95863dd29da56bb9d2bfa5c6dbb0e43fb785108201f10aad96c8ef558ebe5a5b`.
- Sin site: `340aa72b73df6836e675a751c25bcf4ba77656d269b2395c312eb1f11e9ba6f8`.

Evidencia:
`backend/.local/web-search-diagnostics/20261104T192749Z-ag1u6qet/`.

## Soporte documentado vs observado

Microsoft documenta `site:` como restricción para Bing web en
[Advanced search keywords](https://support.microsoft.com/en-us/bing/advanced-search-keywords).
Documenta comillas para frases en
[Advanced search options](https://support.microsoft.com/en-us/bing/advanced-search-options).
Ambas páginas advierten variaciones de disponibilidad regional. No establecen
un contrato específico de capacidades del endpoint RSS usado aquí.

| Capacidad | Conclusión para el backend usado |
| --- | --- |
| Sintaxis `site:` | Documentada para Bing web; no cumplida por RSS en este spike |
| Frases con comillas | Se enviaron y el RSS las repitió; ninguna referencia visible en resultados. Cumplimiento de frase exacta no acreditado |
| Filtro nativo de dominio | No implementado en este adaptador; no se identificó un contrato documentado/verificado para este endpoint RSS |
| Allowlist nativa | No enviada ni verificada para RSS |
| Dominio como parámetro separado | No enviado; request actual solo contiene q/format/mkt; no hay un parámetro RSS validado que recomendar |

`site:` viaja literalmente dentro de `q`. No podemos afirmar con estas dos
consultas si el servidor lo ignora, lo reinterpreta o tiene un fallo específico
de RSS. Por eso no se declara A como hecho global ni C sin evidencia de una
opción nativa soportada. No se inventaron parámetros como compensación.

## Conclusión y siguiente acción

**Clasificación D**: el endpoint/recorrido RSS devuelve resultados irrelevantes
pese a recibir correctamente la query. El canal RSS y URL final confirman el
input; los resultados erróneos ya vienen en el XML crudo. No es el matching,
ranking, un descarte HTTPS ni una modificación local de la query.

Alcance de la conclusión: dos requests del backend y configuración actuales.
No es una certificación de que Bing web carezca del operador ni permite descartar
todos los posibles efectos de intermediarios de red.

Siguiente acción recomendada: tratar este RSS como fuente no validada para
discovery comercial dirigido y revisar su contrato/recorrido de transporte con
esta evidencia antes de decidir una corrección o sustitución. No seguir ajustando
matching para acomodar estos resultados. No se implementó cambio de proveedor,
parámetros productivos, filtros o pipeline.

## Archivos y tests

- Adaptador existente: factoriza la construcción de request, fetch y parseo
  sin modificar parámetros ni conversión normal; añade `.diagnose(query)`.
- Nuevo `backend/scripts/eureka_web_search_diagnostic.py`.
- Nuevo `backend/tests/unit/investigation/test_web_provider_diagnostic.py`.
- Este documento.

Tests del nuevo diagnóstico: codificación de query, metadatos sanitizados,
resultados crudos vs filtro existente, XML malformado conservado, comparación
explícita y protección contra sobrescritura. Los proveedores en tests son mocks.
Ningún recibo de benchmark anterior fue modificado ni se generaron observaciones
comerciales con las consultas del spike.
