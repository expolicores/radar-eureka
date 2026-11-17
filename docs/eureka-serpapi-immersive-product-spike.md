> **Informe hist?rico preservado.** Los scripts y tests de spike descritos aqu?
> fueron retirados al consolidar una sola implementaci?n productiva. Los JSON
> originales de `.local` se mantienen. Flujo y comandos vigentes:
> [Integraci?n limitada de SerpApi](eureka-serpapi-integration.md).

# Último spike aislado — profundidad de tiendas con Immersive Product

## Resultado

**No llegamos a tres ofertas compatibles del Samsung UN58U8000H.**

Una request real, el **04/11/2026 a las 20:11 Bogotá**, usando el `page_token`
del Google Product compatible `5647722602654877558`.

| Métrica | Resultado |
|---|---:|
| Requests ejecutadas / páginas consultadas | 1 / 1 |
| HTTP | 200 |
| Retries | 0 |
| Stores recibidos en Immersive | 3 |
| Stores únicos recibidos | 3 |
| Ofertas previas conservadas | 3 |
| Repetidas contra la evidencia previa | 3 |
| Ofertas únicas consolidadas | 3 |
| exact | 0 |
| high | 2 |
| ambiguous | 1 |
| incompatible | 0 |
| Compatibles con precio, URL distinta y tienda identificada | **2** |
| Nuevas URLs compatibles | **0** |
| `stores_next_page_token` | Ausente |
| Página adicional | No |

Los conteos de identidad también son 0 exact, 2 high y 1 ambiguous tomando solo
la respuesta nueva. No se suman dos veces los resultados previos y los recién recibidos.

## Tiendas y ofertas

Precios devueltos por Google, no verificación de checkout:

| Tienda | Referencia en título | Precio | Shipping | Diagnóstico |
|---|---|---:|---|---|
| exito.com | UN58U8000HKXZL | $ 1.799.900 | Gratis | high |
| Tienda Online Puntos Colombia | UN58U8000HKXZL | $ 3.339.900 | + $ 7.500 | high |
| Addi | No aparece la referencia completa; Samsung 58 pulgadas | $ 2.270.000 | + $ 10.000 | ambiguous |

Enlaces directos, sin parámetros de tracking en esta presentación:

- Éxito: `https://www.exito.com/televisor-samsung-58-pulgadas-led-uhd-4k-smart-tv-un58u8000hkxzl-3254967/p?idsku=3856068`
- Puntos Colombia: `https://tiendaonline.puntoscolombia.com/televisor-samsung-58-pulgadas-led-uhd4k-smart-tv-un58u8000hkxzl-925434/p?idsku=2245927`
- Addi: `https://marketplace.addi.com/producto/4958940`

Los títulos y los precios coinciden con las tres ofertas del spike anterior.
`more_stores=true` **no aportó tiendas ni referencias nuevas en este producto**.
El límite documentado es de hasta 13 o el máximo disponible; no implica recibir
13 tiendas en todos los productos. [Documentación oficial](https://serpapi.com/google-immersive-product-stores).

## Request y paginación

Se envió una request con:

```text
engine=google_immersive_product
page_token=<leído del raw anterior, sin hardcodearlo>
more_stores=true
gl=co
hl=es
location=Bogota, Bogota, Colombia
```

El provider confirmó `engine=google_immersive_product` y `more_stores=true`.
No repitió `gl`, `hl` ni `location` en `search_parameters`; no se afirma que los
aplicara nuevamente. El token procede de la consulta anterior localizada en Colombia.

No apareció `stores_next_page_token` ni en `product_results` ni en la raíz.
Se detuvo con `stop_reason=no_next_page`, sin gastar otra request.

El script permite exclusivamente una segunda página si falta suficiencia y existe
token de continuación. Conserva el mismo `page_token` y agrega
`next_page_token=stores_next_page_token`. Nunca hay una tercera página, refresh
de token, búsqueda adicional ni retries automáticos.

## Matching y dedupe diagnósticos

Se reutiliza únicamente la función de diagnóstico del spike anterior, fuera del
pipeline productivo: exact/high/ambiguous/incompatible. No se modifica matching.

La referencia regional `UN58U8000HKXZL` es high frente a `UN58U8000H`.
U8500H, otro tamaño o un accesorio no se acepta. Un título genérico no hereda la
identidad por compartir el token o ID del producto. La marca puede proceder del
contexto del mismo producto cuando la página adicional no la repite.

Dedupe por tienda normalizada + URL + referencia + precio numérico. Se ignoran
fragmentos y parámetros de tracking (`utm_*`, `srsltid`, `gclid`, `fbclid`), pero se
conservan SKU y otros parámetros comerciales. Enteros y floats equivalentes comparten
precio de dedupe. La URL también debe ser distinta para contar hacia la parada:
dos precios del mismo enlace no fabrican una tercera oferta.

Se conservan resultados previos, respuesta nueva y duplicados como provenance.
Que la fila consolidada tenga origen previo no significa que se haya omitido la
respuesta nueva: los duplicados guardan la observación Immersive y el raw contiene
las tres tiendas recién devueltas.

## Evidencia y ejecución reproducible

Ruta:
`backend/.local/serpapi-immersive-product-spike/20261105T011148Z-rsdlf7k5/`

- `page-1.raw.json`: respuesta completa sanitizada.
- `diagnostic.json`: resumen, filas consolidadas, páginas y duplicados.

Se verificó ausencia de la API key en ambos artefactos. Se usa la configuración
`SERPAPI_API_KEY` existente de entorno/`backend/.env`. No se cambia `.env` ni se
imprimen credenciales. Los tokens públicos de navegación quedan en raw; la consola
muestra solo metadatos y hash del token, no el request con credenciales.

Desde `backend`:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_serpapi_immersive_product_spike.py `
  --product-response .local/serpapi-google-product-spike/20261105T005209Z-l89swcn0/5647722602654877558.raw.json
```

Cada ejecución crea directorio único. No sobrescribe evidencia previa. Tokens
antiguos pueden dejar de funcionar; el script registra el fallo sin refrescarlos
ni generar requests extra.

## Archivos y validación

Solo se agregan:

- `backend/scripts/eureka_serpapi_immersive_product_spike.py`
- `backend/tests/unit/test_serpapi_immersive_product_spike.py`
- Este documento.

No hay cambios a archivos existentes, pipeline, Market Price Scout, benchmark,
señales, matching productivo, navegador ni scraping directo. Se reutilizan helpers
de los scripts aislados anteriores, sin nueva dependencia productiva.

**18 tests nuevos pasan**; los tres spikes suman **65 tests pasando**. Ruff,
formato y Mypy del nuevo script pasan. Se prueban parada anticipada, una sola página
adicional, igualdad del token base, dedupe, precisión de identidad, fallos y ausencia
de credenciales en raw sanitizados.

## Recomendación final

**Integrar SerpApi con limitación**, si se autoriza después: como fuente auxiliar
estructurada de discovery/ofertas, no como garantía de tres precios comparables.
Shopping → Product sí produjo dos ofertas explícitas útiles; Immersive no agregó
profundidad para este token. La insuficiencia debe conservarse cuando no se obtengan
tres ofertas compatibles; Addi sigue ambigua y no debe promoverse automáticamente.

Esta es una recomendación, no una integración ejecutada. No se hicieron solicitudes
adicionales para forzar una tercera oferta ni se relajaron referencias.
