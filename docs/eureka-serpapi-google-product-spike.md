> **Informe hist?rico preservado.** Los scripts y tests de spike descritos aqu?
> fueron retirados al consolidar una sola implementaci?n productiva. Los JSON
> originales de `.local` se mantienen. Flujo y comandos vigentes:
> [Integraci?n limitada de SerpApi](eureka-serpapi-integration.md).

# Segundo spike aislado — SerpApi Google Product

## Alcance y ejecución

Ejecutado **04/11/2026, aproximadamente 19:52 Bogotá** (05/11 UTC).
Tres requests secuenciales, sin retries, sin consultas a tiendas, browser ni integración.
Se reutilizan exclusivamente configuración, transporte y sanitización del primer
script aislado. No se importa ni modifica el matching productivo o Market Price Scout.

Archivos agregados:

- `backend/scripts/eureka_serpapi_google_product_spike.py`
- `backend/tests/unit/test_serpapi_google_product_spike.py`
- Este documento.

No se modifican archivos existentes en este incremento, `.env`, dependencias,
pipeline, benchmark, señales o datos de negocio.

Desde `backend`, reproduciendo la selección del Shopping anterior:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_serpapi_google_product_spike.py `
  --shopping-diagnostic .local/serpapi-shopping-spike/20261104T221344Z-zefd3jz1/diagnostic.json `
  --max-products 3
```

Para un ID concreto:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_serpapi_google_product_spike.py `
  --product-id 5647722602654877558
```

Cada ejecución crea directorio único en `.local/serpapi-google-product-spike/`.
El ID debe ser numérico; máximo tres IDs únicos. Se priorizan candidatos ambiguos
con familia U8000H y luego tamaño 58, conservando el orden de Shopping como desempate.
Se corta si aparece un producto con tres ofertas utilizables o un 401/403/429.
La key procede del entorno o `backend/.env`, nunca de argumentos ni del código.

## Request real

```json
{
  "engine": "google_product",
  "product_id": "<seleccionado del Shopping previo>",
  "gl": "co",
  "hl": "es",
  "offer_view": "true",
  "location": "Bogota, Bogota, Colombia"
}
```

Los tres respondieron HTTP 200. El provider confirmó `gl=co`, `hl=es` y
`offer_view=true`. **No repitió `location` en search_parameters**: no se puede
afirmar que Google Product aplicara Bogotá, aunque sí confirmó país e idioma.
La [documentación actual](https://serpapi.com/google-product-api) describe el
modo por ID/oferta y `product_results.stores`; la forma concreta se inspeccionó
en los raw reales, sin asumir que todos los campos opcionales existían.

## Resultados consolidados

| Métrica | Resultado |
|---|---:|
| IDs probados | 3 |
| Con `product_results` | 2 |
| Con `stores` | 2 |
| Filas de tiendas/ofertas | 6 |
| Con `extracted_price` numérico | 6 |
| Con enlace directo a tienda | 6 |
| Ofertas con referencia explícita compatible con UN58U8000H | **2** |
| Grupo con tres ofertas utilizables para el objetivo | **No** |

Los precios son referencias devueltas por Google, no verificación de página/stock
o checkout. No se calcula mediana ni se genera benchmark/señal.

## ID 5647722602654877558 — candidato Éxito / U8000H

`product_results`:

- `title`: Samsung Televisor Smart Crystal Uhd 4K U8000h
- `brand`: Samsung
- `price_range`: $ 1.749.900–$ 1.849.900
- `product_attributes`: marca Samsung, Series 8, tamaño 58”
- `page_token`: presente, 1.367 caracteres; completo en JSON, abreviado en consola.

**Encabezado: ambiguous**, porque no trae la referencia completa. Eso no invalida
la evidencia explícita de las tiendas, pero tampoco confirma automáticamente todas
las ofertas del ID. El rango agregado no cubre todos los precios individuales:
no se usa como sustituto de `stores[].price`.

| Tienda | Título/referencia de tienda | Precio | Envío | Identidad de oferta |
|---|---|---:|---|---|
| exito.com | Samsung 58 pulgadas … UN58U8000HKXZL | $ 1.799.900 | Gratis | high |
| Tienda Online Puntos Colombia | Samsung 58 pulgadas … UN58U8000HKXZL | $ 3.339.900 | $ 7.500 | high |
| Addi | Televisor SAMSUNG 58 pulgadas LED Uhd4K Smart TV | $ 2.270.000 | $ 10.000 | ambiguous |

Links devueltos, disponibles íntegros con parámetros en los raw:

- Éxito: `https://www.exito.com/televisor-samsung-58-pulgadas-led-uhd-4k-smart-tv-un58u8000hkxzl-3254967/p`
- Puntos Colombia: `https://tiendaonline.puntoscolombia.com/televisor-samsung-58-pulgadas-led-uhd4k-smart-tv-un58u8000hkxzl-925434/p`
- Addi: `https://marketplace.addi.com/producto/4958940`

Las tres incluyen `details_and_offers` con disponibilidad/envío declarados por Google.
Éxito tiene rating/reviews; condición/descuento/cupón no estaban presentes.
Solo **dos ofertas** confirman explícitamente una referencia regional compatible.
No se adopta la identidad de Addi por pertenecer al mismo grupo.

## ID 15641674424257352919 — candidato JAD / Samsung 58"

HTTP 200 con error de contenido del provider:
`Google Product hasn't returned any results for this query.`

`search_information.product_results_state=Fully empty`.
Sin `product_results` ni tiendas. No se repitió la consulta. La respuesta completa
queda preservada; el estado se recoge en la revisión offline y en el script final.

## ID 7330734637672633877 — candidato Grupo Mansión

`product_results`:

- `title`: Televisor Samsung Crystal 4K UHD Smart TV
- `brand`: Samsung
- `price_range`: $ 1.745.891–$ 2.053.900
- Atributos: marca Samsung, 3840 × 2160, 4K, Series 8, Titanium Gray, tamaño 58”
- `page_token`: presente, 1.362 caracteres.

El encabezado es **ambiguous**; las tres ofertas son **incompatible** con el objetivo UN58U8000H:

| Tienda | Modelo en título/enlace | Precio | Envío |
|---|---|---:|---|
| Samsung Electronics Colombia | U8500H / UN58U8500HKXZL | $ 1.849.900 | Gratis |
| Éxito | UN58U8500HKXZL | $ 2.230.809 | Gratis |
| Falabella Colombia | U8500H | $ 4.799.800 | No informado |

Este resultado demuestra que una ficha/título genérico puede agrupar ofertas de
otro modelo. No se trasladan estos precios al Samsung UN58U8000H.

## Diagnóstico y evidencia

La identidad se evalúa con título, marca y atributos del producto, por separado
del título de cada tienda: exact, high, ambiguous o incompatible. `high` admite
referencia original explícita o sufijo regional KXZL, sin equiparar F con H/U8500H.
La coincidencia de tienda nunca se deduce del texto de la query ni del ID por sí solo.

Una oferta candidata útil requiere referencia propia exact/high, padre sin
contradicción explícita, precio numérico positivo, link directo y ausencia de condición
usada/reacondicionada declarada. El padre puede seguir siendo ambiguo aunque dos
tiendas sí identifiquen el modelo: se conserva esa diferencia y no se promociona
la ficha del producto silenciosamente. No son reglas del matching productivo.

Ruta de evidencia:
`.local/serpapi-google-product-spike/20261105T005209Z-l89swcn0/`

- `<id>.raw.json`: payload sanitizado de cada request.
- `<id>.diagnostic.json` y `summary.json`: evaluación original capturada.
- `offline_review.json`: revisión final de los mismos raw, **sin nuevas requests**.

La evaluación original exigía referencia tanto en encabezado como en tienda, por
lo que marcaba cero ofertas útiles. La revisión final distingue correctamente los
dos títulos explícitos H de las tiendas de un encabezado genérico. Se conservan
ambas evaluaciones sin alterar los raw. La conclusión de aceptación no cambia:
no hay tres ofertas confirmadas para el objetivo.

Se comprobó ausencia de la API key en todos los JSON. Tokens de selección de oferta
son datos públicos de navegación del provider, no credenciales; se conservan íntegros
en JSON y solo se muestra una vista abreviada en consola.

## Recomendación

**Investigar más.** La relación producto → varias tiendas → precios/enlaces directos
sí funciona. Para este Samsung hay dos referencias compatibles concretas y una
tercera oferta ambigua, todavía insuficientes para aceptar tres precios del mismo modelo.

El siguiente paso acotado sería confirmar la referencia de la oferta Addi mediante
evidencia adicional autorizada. No se ejecutó esa consulta ni scraping/browser.
No integrar automáticamente IDs ni rangos agregados sin validar sus ofertas.

Validación: 23 tests de este spike y 24 del anterior (**47 pasan**), Ruff/formato
y Mypy del script. Sin modificaciones al pipeline actual.
