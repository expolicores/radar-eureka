> **Informe hist?rico preservado.** Los scripts y tests de spike descritos aqu?
> fueron retirados al consolidar una sola implementaci?n productiva. Los JSON
> originales de `.local` se mantienen. Flujo y comandos vigentes:
> [Integraci?n limitada de SerpApi](eureka-serpapi-integration.md).

# Spike aislado — SerpApi Google Shopping

Ejecución: **04/11/2026 17:13:44 Bogotá**. Una sola request, sin retries,
sin páginas de retailers ni consultas adicionales de producto.

## Archivos y alcance

Solo se agregan:

- `backend/scripts/eureka_serpapi_shopping_spike.py`
- `backend/tests/unit/test_serpapi_shopping_spike.py`
- Este documento.

El script no importa servicios de Eureka ni el matching productivo. No modifica
Market Price Scout, matching, señales, UI, DB, documentos, configuración o dependencias.
No usa browser. Las etiquetas son exclusivamente un diagnóstico del título devuelto,
no una validación comercial, contractual o de precio de página.

## Ejecución

Desde `backend`:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_serpapi_shopping_spike.py
```

Lee `SERPAPI_API_KEY` desde el entorno o `backend/.env`, sin modificar ese archivo.
El entorno tiene prioridad. Crea un subdirectorio único dentro de
`backend/.local/serpapi-shopping-spike/`; nunca sobrescribe ejecuciones previas.
`--output-directory` cambia únicamente la carpeta raíz de los artefactos.

Request a `https://serpapi.com/search.json`:

```json
{
  "engine": "google_shopping",
  "q": "Samsung UN58U8000H",
  "gl": "co",
  "hl": "es",
  "location": "Bogota, Bogota, Colombia"
}
```

La credencial va al provider como parámetro requerido, pero se omite de logs,
consola y artefactos. La respuesta se guarda como JSON raw estructural sanitizado:
se redactan credenciales en campos, mensajes y URLs. No se persisten los bytes HTTP
originales que pudieran contener la key. Se verificó que los JSON reales no contienen
la API key. No se siguen redirecciones del endpoint. Timeout I/O 45 s, cuerpo hasta 8 MB.

Errores distinguidos: key ausente, 401/403, 429, otros HTTP, timeout/network,
payload inválido y ausencia de `shopping_results`. Sin retries automáticos.

## Resultado observado

HTTP **200**, `search_metadata.status=Success`.
El provider confirmó `location_used=Bogota,Bogota,Colombia`, `gl=co`, `hl=es`,
`google_domain=google.com`, `device=desktop`.

Artefactos:

- `.local/serpapi-shopping-spike/20261104T221344Z-zefd3jz1/response.raw.json`
- `.local/serpapi-shopping-spike/20261104T221344Z-zefd3jz1/diagnostic.json`

| Métrica | Cantidad |
|---|---:|
| `shopping_results` | 9 |
| `extracted_price` numérico positivo | 9 |
| `source` / tienda | 9 |
| `product_link` | 9 |
| `product_id` | 9 |
| `position`, `title`, `price` | 9 cada uno |
| `rating`, `reviews` | 6 cada uno |
| `delivery` | 0 |
| Campo explícito `currency` | 0 |
| Enlace directo `link` de tienda | 0 |
| Plausibles con referencia canónica explícita | **0** |
| Ambiguos | 6 |
| Modelos distintos | 3 |

Los nueve `product_link` apuntan a **Google**, no al checkout/página de la tienda.
Los nueve resultados incluyen enlaces `serpapi_product_api`,
`serpapi_immersive_product_api` y token público de navegación de producto.
También aparecen `multiple_sources` (4), `extensions` (2) y, en un caso,
`alternative_price`, `old_price`, `extracted_old_price`, `tag`. Se preserva el
inventario real de campos por resultado y sus frecuencias en `diagnostic.json`.

## Ejemplos reales

Los precios son los devueltos por Google Shopping; no se certifican como precio
de checkout ni se infiere moneda únicamente por `$` o por `gl=co`.

| Posición | Título | Tienda | Precio / extracted_price | product_id | Diagnóstico |
|---|---|---|---|---|---|
| 1 | Samsung Televisor Smart Crystal Uhd 4K U8000h | exito.com | $ 1.799.900 / 1799900 | 5647722602654877558 | ambiguous |
| 2 | Televisor Samsung Crystal 4K UHD Smart TV | Grupo Mansión | $ 1.699.000 / 1699000 | 7330734637672633877 | ambiguous |
| 3 | Televisor Samsung 58 pulgadas 4K UHD Smart TV UN58U8000FKXZL | Agaval | $ 1.829.900 / 1829900 | 4574648555256200238 | wrong_model |
| 6 | Samsung Televisor 58" 4K UHD 58 Pulgadas Negro | JAD Comercializadora SAS | $ 1.750.000 / 1750000 | 15641674424257352919 | ambiguous |
| 7 | Televisor Samsung 58 147Cm Crystal 4K Ultra : UN58U8500HK | Surticréditos | $ 2.482.000 / 2482000 | 11587798773312050657 | wrong_model |

Los enlaces íntegros están en los JSON, sin truncar. El resultado 9 también muestra
`U8000F + SOPORTE`, incompatible con el modelo H solicitado.

## Diagnóstico mínimo y límites

- `plausible`: marca y `UN58U8000H` explícitos (admite sufijo regional `KXZL`),
  sin modelo/tamaño/tipo contradictorio.
- `wrong_model`, `wrong_size`, `wrong_product_type`: contradicción explícita.
- `ambiguous`: falta marca/referencia completa, aunque el resultado pueda ser útil.

`U8000h` sin referencia completa/tamaño no demuestra `UN58U8000H`. Un TV Samsung
genérico de 58" tampoco. El texto de la query repetido dentro de `product_link`
**no es evidencia** de la identidad del producto.

Se distinguen el conteo de títulos plausibles y el de ofertas plausibles con precio
numérico, source y product_link. Ambos son cero en esta prueba. No se usó esta regla
para modificar matching productivo. Los seis ambiguos quedan como candidatos por
investigar, no como seis incompatibilidades confirmadas.

Otras limitaciones: resultado de una sola query/ubicación/fecha; precios de Google,
no páginas verificadas; stock, moneda explícita, envío e impuestos sin confirmar;
pueden existir variantes, agregaciones o proveedores extranjeros aun con `gl=co`
(por ejemplo, apareció 220-Electronics.com). No se asumen nueve ofertas independientes.

## Google Product API: siguiente investigación posible, no implementada

La [documentación actual de Google Product API](https://serpapi.com/google-product-api)
admite `engine=google_product` con `product_id` o `page_token`. El token proviene de
`immersive_product_page_token` y permite seleccionar una oferta/variante específica.
Con `product_id`, `offer_view=true` solicita también la vista de oferta. El contrato
documenta `product_results.stores`, con nombre, título, link de tienda y datos de precio.
No debe asumirse la vigencia del antiguo parámetro `offers=1` encontrado en blogs antiguos.

Por tanto, **sí hay una vía documentada** para inspeccionar tiendas/ofertas y detalles
de un producto concreto. No se ejecutó: aún falta probar qué devuelve para estos IDs
colombianos, si confirma el modelo H y si expone oferta/moneda/enlace suficientes.

Referencias del contrato de búsqueda:
[Google Shopping API](https://serpapi.com/google-shopping-api),
[campos de shopping_results](https://serpapi.com/shopping-results).

## Conclusión

**Investigar más; no integrar todavía.** SerpApi produjo discovery comercial mucho
más estructurado que el RSS fallido: nueve precios numéricos, tiendas e IDs trazables.
Pero esta consulta **no demuestra tres ofertas del Samsung exacto**. El siguiente
spike razonable sería revisar por ID/token los candidatos ambiguos más prometedores,
empezando por U8000h de Éxito, con un presupuesto acotado y autorización independiente.
No se reemplazó ni conectó con Market Price Scout.

Validación: **24 tests offline pasan**, además de Ruff/formato y Mypy del script.
