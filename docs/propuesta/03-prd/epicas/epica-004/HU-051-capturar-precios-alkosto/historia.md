# Historia #051: Capturar observaciones de Alkosto desde su sitemap y datos estructurados

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Capturar Precios Automáticamente con Salvaguardas  
**Prioridad:** Alta  
**FRs relacionados:** FR-043, FR-044, FR-045

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** un conector de Alkosto que lea su sitemap de productos y los datos estructurados schema.org de las páginas de televisores permitidas por su `robots.txt`,  
**Para** obtener automáticamente observaciones de la fuente principal del Benchmark 2 con evidencia auditable y sin evadir ninguna restricción.

## Descripción

**Prioridad Alta (no Crítica):** la automatización de las fuentes retail no es condición de éxito del MVP; si este conector no está disponible o la fuente se suspende, el Benchmark 2 sigue con carga manual o por archivo.

D6 verificó que Alkosto no tiene API pública, pero publica un **sitemap de productos** (≈ 31.000 URLs, ≈ 330 de televisores) y **datos estructurados schema.org** en las páginas de producto (precio, moneda COP, SKU = EAN, nombre con marca, modelo y tamaño), en rutas permitidas por `robots.txt` (que prohíbe la búsqueda: `?q=`, `/search/`). El vendedor es la propia tienda. La Adenda 2 acepta este mecanismo como lectura permitida de datos estructurados, sujeta a la revisión de términos de uso antes de producción.

Este conector se ejecuta dentro del marco común de captura (HU-050), que ya aplica `robots.txt`, ritmo, volumen, User-Agent, prohibición de evasión, filtros de televisor individual, reglas de vendedor, precio efectivo y condiciones especiales, almacenamiento y registro de la ejecución. Esta HU define **solo lo específico de Alkosto**: cómo obtener las URLs de televisores y cómo convertir los datos estructurados de una página en los campos de una observación.

---

## Criterios de Aceptación

### Escenario 1: Captura de una página de televisor de Alkosto

- **Dado** que la página permitida de un televisor publica datos estructurados Product con nombre "Televisor SAMSUNG 55 Pulgadas LED Uhd4K Smart TV UN55DU7000KXZL", marca "SAMSUNG", sku "8806095520005", oferta con precio 1899900, moneda "COP" y disponibilidad "InStock"
- **Cuando** el conector la procesa
- **Entonces** entrega una oferta con `producto_descripcion` = el nombre, `marca = "SAMSUNG"`, `modelo_referencia = "UN55DU7000KXZL"`, `sku = "8806095520005"`, `ean_gtin = "8806095520005"`, `tamano_pulgadas = 55`, `resolucion = 4K UHD`, `tecnologia_pantalla = LED`, `smart = sí`, vendedor ausente (se asigna "Alkosto" por vendedor implícito), precio vigente 1899900 y la evidencia del bloque de datos estructurados; la observación se guarda con `metodo_adquisicion = sitemap_datos_estructurados`

### Escenario 2: Obtención de URLs de televisores desde el sitemap

- **Dado** que `robots.txt` de Alkosto declara el índice de sitemaps y el patrón de URL de televisores está configurado
- **Cuando** inicia la ejecución
- **Entonces** el conector lee el índice, lee los sitemaps de producto y toma como candidatas solo las URLs que cumplen el patrón de televisores, sin solicitar ninguna ruta de búsqueda

### Escenario 3: Patrón de URL de televisores no configurado

- **Dado** que el patrón de URL de televisores de Alkosto está vacío
- **Cuando** el Administrador intenta habilitar la captura de Alkosto
- **Entonces** se rechaza con `"Configure el patrón de URL de televisores de Alkosto antes de habilitar la captura."`

### Escenario 4: Modelo en el campo `model`

- **Dado** que los datos estructurados incluyen la propiedad `model = "55UT8050PSA"`
- **Cuando** el conector procesa la página
- **Entonces** `modelo_referencia = "55UT8050PSA"` sin intentar extraerlo del nombre

### Escenario 5: Modelo no identificable

- **Dado** que la página no tiene `model` y el nombre "Televisor KALLEY 32 Pulgadas HD Smart" no contiene ningún código de modelo según la regla RN-04
- **Cuando** el conector la procesa
- **Entonces** no se crea observación y se registra el descarte `modelo_no_identificable`

### Escenario 6: Producto agotado

- **Dado** que la oferta tiene disponibilidad "OutOfStock" o "SoldOut"
- **Cuando** el conector la procesa
- **Entonces** no se crea observación y se registra el descarte `no_disponible`

### Escenario 7: Moneda distinta de COP o sin precio

- **Dado** que la oferta tiene `priceCurrency = "USD"`, o no tiene precio
- **Cuando** el conector la procesa
- **Entonces** no se crea observación y se registra el descarte `moneda_no_cop` o `sin_precio_vigente`

### Escenario 8: SKU que no es un GTIN válido

- **Dado** que el sku publicado es "ALK-998877"
- **Cuando** el conector lo procesa
- **Entonces** se guarda `sku = "ALK-998877"` y `ean_gtin` nulo

### Escenario 9: Página sin datos estructurados o posible cambio de estructura

- **Dado** que una página no contiene datos estructurados Product
- **Cuando** el conector la procesa
- **Entonces** se registra el descarte `datos_estructurados_ausentes`; y si en la ejecución más del 50 % de las páginas de televisor leídas no tiene datos estructurados, la ejecución termina como `fallida` con motivo `"posible cambio de estructura en Alkosto"` y se emite `captura_fallida`

### Escenario 10: Vendedor publicado distinto de la tienda

- **Dado** que los datos estructurados publican `seller.name = "Proveedor Externo SAS"`
- **Cuando** se aplica la regla de vendedor
- **Entonces** no se crea observación y se registra el descarte `vendedor_tercero`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (configura el conector); el sistema lo ejecuta como `conector:Alkosto`.
- **Permisos requeridos:** rol Administrador para configurar el patrón de URL y el índice de sitemaps.
- **Valor de negocio:** observaciones semanales de la fuente principal del Benchmark 2 sin tiempo humano.

### Reglas de Negocio

**RN-01 — Rutas requeridas.** El conector declara como rutas requeridas: las URLs de sitemap de producto y el patrón de URL de televisores. Si `robots.txt` prohíbe alguna, el marco común suspende la fuente (HU-053). El conector nunca construye ni solicita URLs de búsqueda (`?q=`, `/search/`) ni ninguna ruta distinta de sitemaps y páginas de producto.

**RN-02 — Origen de los sitemaps.** Se usan las URLs declaradas con la directiva `Sitemap:` en el `robots.txt` vigente. Si no declara ninguna, se usa la URL de índice de sitemaps configurada por el Administrador; si tampoco existe, la ejecución termina como `fallida` con motivo `"Sin sitemap de productos para Alkosto"`.

**RN-03 — URLs candidatas.** Son candidatas las URLs de los sitemaps de producto que cumplen el **patrón de URL de televisores** (expresión configurable por el Administrador, de 3 a 200 caracteres, que se registra al habilitar el conector verificándola contra el sitemap vigente). Sin patrón no se puede habilitar la captura: `"Configure el patrón de URL de televisores de Alkosto antes de habilitar la captura."` Patrón inválido: `"El patrón de URL no es válido."` Las URLs repetidas entre sitemaps se procesan una sola vez por ejecución.

**RN-04 — Mapeo de datos estructurados (schema.org Product, en JSON-LD o microdatos).**

| Campo de la observación | Origen | Regla |
|---|---|---|
| `producto_descripcion` | `name` | Recortado a 300 caracteres |
| `marca` | `brand.name` o `brand` | Si falta, descarte `datos_estructurados_ausentes` |
| `modelo_referencia` | `model` o `mpn` | Si no existen: del `name`, el token más largo de 6 a 20 caracteres formado solo por letras, dígitos y guiones, con al menos 2 letras y 2 dígitos, que no sea una medida ni una resolución (ej. "55PULGADAS", "UHD4K", "3840X2160" se excluyen); en empate, el primero. Sin resultado: descarte `modelo_no_identificable` |
| `sku` | `sku` | Tal como se publica (1 a 64 caracteres) |
| `ean_gtin` | `gtin13`, `gtin12`, `gtin14`, `gtin8` o `gtin`; si no hay, `sku` | Solo si es un GTIN válido (8, 12, 13 o 14 dígitos con dígito de control); si no, nulo |
| precio vigente | `offers.price` (o `offers.lowPrice` si es AggregateOffer) | Interpretado como entero COP |
| precio anterior | `offers.priceSpecification` con tipo de precio de lista, si existe | Solo evidencia; si no existe, nulo |
| moneda | `offers.priceCurrency` | Distinta de COP: descarte `moneda_no_cop` |
| disponibilidad | `offers.availability` | `OutOfStock`, `SoldOut` o `Discontinued`: descarte `no_disponible`; ausente o cualquier otro valor: se procesa |
| vendedor | `offers.seller.name` | Ausente: vendedor implícito "Alkosto" |
| `tamano_pulgadas` | `name` | Primer número de 2 o 3 dígitos seguido de "pulgadas", "pulg", `"` o `''`, entre 10 y 120; si no, nulo |
| `resolucion` | `name` | "8K" → 8K; "4K" o "UHD" → 4K UHD; "Full HD" o "FHD" → Full HD; "HD" → HD; si no, `desconocida` |
| `tecnologia_pantalla` | `name` | "Mini LED" → Mini LED; "OLED" (no precedido de "Q") → OLED; "QLED" → QLED; "LED" → LED; si no, `desconocida` |
| `smart` | `name` | Contiene "Smart" → sí; si no, `desconocido` |

**RN-05 — Evidencia.** Por cada observación: copia textual del bloque de datos estructurados leído, URL, fecha y hora de la respuesta, código de respuesta y hash SHA-256 del bloque.

**RN-06 — Detección de cambio de estructura.** Si más del 50 % (configurable) de las páginas de televisor leídas en una ejecución no tiene datos estructurados Product, la ejecución termina `fallida` con motivo `"posible cambio de estructura en Alkosto"` y se emite `captura_fallida`. Las observaciones ya creadas en esa ejecución se conservan.

**RN-07 — Reglas del marco común.** Vendedor = la tienda (vendedor implícito de Alkosto: sí), precio efectivo, condiciones especiales, filtros de producto, validación del registro mínimo, ritmo, volumen, User-Agent y registro de la ejecución se aplican según el marco común de captura (HU-050). Valores: `metodo_adquisicion = sitemap_datos_estructurados`, `registrado_por = conector:Alkosto`, `iva_condicion` = valor por defecto de captura de la fuente (inicial: `indeterminado`), porque los datos estructurados de Alkosto no declaran IVA.

### Interfaz

Sin interfaz propia. El Administrador configura el patrón de URL de televisores y, si hace falta, la URL de índice de sitemaps mediante la operación administrativa del catálogo de fuentes.

### Sistemas Externos (Si aplica)

**Alkosto (sitio web público):** `robots.txt`, sitemaps de producto (XML) y páginas de producto con datos estructurados schema.org. Respuesta correcta: 200 con datos estructurados; no disponible: timeout o 5xx (reintentos del marco común); respuesta inesperada: página sin datos estructurados o con estructura distinta (RN-04, RN-06); restricción: 401, 403, 429 o CAPTCHA (suspensión, HU-053). Términos de uso sin verificar (D6): bloqueo para producción, no para el MVP de validación.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-050 (marco común de captura), HU-053 (suspensión), HU-044 (vendedor implícito), HU-045 (precio efectivo), HU-046 (condiciones especiales), HU-042 (registro mínimo).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Patrón de URL de televisores:** D6 identificó las URLs de televisores en el sitemap sin documentar el patrón; se vuelve un parámetro obligatorio que el Administrador registra al habilitar el conector. Resuelta (RN-03).
2. **Extracción del modelo desde el nombre** con una regla determinística cuando no existe `model`/`mpn`. Resuelta (RN-04).
3. **Producto agotado** no es precio disponible al consumidor: se descarta. Resuelta (RN-04).
4. **IVA de Alkosto** queda `indeterminado` por defecto hasta que el PO documente la verificación. Resuelta (RN-07).
5. **Cambio de estructura** detectado por proporción de páginas sin datos estructurados (> 50 %, configurable). Resuelta (RN-06).

---

## Validación INVEST

- [x] **Independiente:** Esta HU puede implementarse sin dependencias bloqueantes de otras HU
- [x] **Negociable:** Describe QUÉ se necesita, no CÓMO implementarlo (detalles técnicos son negociables)
- [x] **Valiosa:** Aporta valor tangible al negocio o usuario final (beneficio claro)
- [x] **Estimable:** El equipo puede estimar esfuerzo (scope claro, no ambiguo)
- [x] **Pequeña:** Completable en pocos días/persona (no excede 1 sprint)
- [x] **Testeable:** Criterios de aceptación permiten verificar cuándo está terminada

## Validación Anti-Ambigüedad

- [x] **Auto-contenida:** Un desarrollador puede implementar esta HU leyendo SOLO este archivo
- [x] **Reglas completas:** Todas las reglas de negocio incluyen formatos, rangos, límites y comportamiento ante nulos
- [x] **Errores explícitos:** El comportamiento ante cada tipo de error está documentado (mensaje, acción, redirección)
- [x] **Edge cases cubiertos:** Criterios de aceptación incluyen casos borde y estados vacíos
- [x] **Supuestos resueltos:** No quedan supuestos pendientes de validación
- [x] **Datos claros:** Origen, formato y proveedor de cada dato están especificados

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes de usuario implementados
- [ ] Pruebas funcionales pasando

---

## Registro de Cambios

| Fecha | Versión | Descripción | Autor |
|-------|---------|-------------|-------|
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-004 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
