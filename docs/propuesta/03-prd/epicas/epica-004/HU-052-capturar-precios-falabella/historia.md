# Historia #052: Capturar observaciones de Falabella con vendedor = Falabella desde sitemaps y datos estructurados

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Capturar Precios Automáticamente con Salvaguardas  
**Prioridad:** Alta  
**FRs relacionados:** FR-043, FR-044, FR-045, FR-046

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** un conector de Falabella que lea sus sitemaps de producto y los datos estructurados de las páginas de televisores, aceptando solo ofertas vendidas por Falabella,  
**Para** sumar la fuente secundaria al Benchmark 2 con evidencia auditable, sin mezclar vendedores terceros del marketplace ni precios condicionados.

## Descripción

**Prioridad Alta (no Crítica):** la automatización de las fuentes retail no es condición de éxito del MVP; sin este conector, el Benchmark 2 sigue con carga manual o por archivo.

D6 verificó que Falabella publica **sitemaps de páginas de producto** (un índice con varios archivos de hasta 25.000 URLs cada uno) y **datos estructurados schema.org** con marca, precios (oferta y normal), SKU interno y **vendedor** (Falabella o un tercero), en rutas permitidas por su `robots.txt`. Es un marketplace mixto: la Adenda 2 exige aceptar solo ofertas con **vendedor = Falabella**. Además, Falabella publica precios asociados a su tarjeta (CMR), que son precios condicionados.

El conector se ejecuta dentro del marco común de captura (HU-050), que aplica `robots.txt`, ritmo, volumen, User-Agent, prohibición de evasión, filtros de televisor individual, reglas comunes, almacenamiento y registro de la ejecución. Esta HU define **solo lo específico de Falabella**.

---

## Criterios de Aceptación

### Escenario 1: Página de televisor vendida por Falabella

- **Dado** que una página permitida publica datos estructurados Product con nombre "Televisor LG 65 pulgadas UHD 4K Smart TV 65UT8050PSA", marca "LG", sku "123456789", una oferta de vendedor "Falabella" con precio 2099900, moneda COP, disponibilidad InStock, y un precio normal de 2499900
- **Cuando** el conector la procesa
- **Entonces** se guarda una observación con `marca = "LG"`, `modelo_referencia = "65UT8050PSA"`, `sku = "123456789"`, `ean_gtin` nulo, `vendedor = "Falabella"`, `precio_efectivo = 2099900`, `precio_anterior = 2499900` (solo evidencia), `condicion_especial = ninguna` y `metodo_adquisicion = sitemap_datos_estructurados`

### Escenario 2: Oferta de un vendedor tercero

- **Dado** que la única oferta de la página es de "ElectroMundo Store"
- **Cuando** el conector la procesa
- **Entonces** no se crea observación y se registra el descarte `vendedor_tercero` con el vendedor y la URL

### Escenario 3: Varias ofertas en la página

- **Dado** que la página publica una oferta de "Falabella" a 2.099.900 COP y otra de "ElectroMundo Store" a 1.950.000 COP
- **Cuando** el conector la procesa
- **Entonces** la observación usa solo la oferta de Falabella y la del tercero se registra como descarte `vendedor_tercero`

### Escenario 4: Página sin vendedor publicado

- **Dado** que la oferta no publica vendedor
- **Cuando** el conector la procesa
- **Entonces** no se crea observación y se registra el descarte `vendedor_no_identificable` (Falabella no tiene vendedor implícito)

### Escenario 5: Precio CMR junto al precio general

- **Dado** que la oferta de Falabella publica precio general 2.099.900 COP y precio CMR 1.899.900 COP
- **Cuando** el conector la procesa
- **Entonces** `precio_efectivo = 2099900`, `condicion_especial = ninguna` y `precios_condicionados_evidencia` contiene {1899900, `tarjeta_especifica`, rótulo leído}

### Escenario 6: Solo precio CMR

- **Dado** que la oferta de Falabella solo publica un precio CMR de 1.899.900 COP
- **Cuando** el conector la procesa
- **Entonces** se guarda la observación con `precio_efectivo = 1899900`, `condicion_especial = tarjeta_especifica` y `apta_para_referencia = no`

### Escenario 7: Sitemaps sin cambios desde la ejecución anterior

- **Dado** que el índice de sitemaps indica para un archivo la misma fecha `lastmod` que en la ejecución anterior
- **Cuando** inicia la ejecución
- **Entonces** el conector no vuelve a descargar ese archivo y usa la lista de URLs guardada de la ejecución anterior; los archivos con `lastmod` nuevo o sin `lastmod` sí se descargan

### Escenario 8: Patrón de URL de televisores no configurado

- **Dado** que el patrón de URL de televisores de Falabella está vacío
- **Cuando** el Administrador intenta habilitar la captura
- **Entonces** se rechaza con `"Configure el patrón de URL de televisores de Falabella antes de habilitar la captura."`

### Escenario 9: Producto agotado, moneda distinta o modelo no identificable

- **Dado** que la oferta de Falabella tiene disponibilidad OutOfStock, moneda distinta de COP, o el producto no tiene modelo identificable
- **Cuando** el conector la procesa
- **Entonces** no se crea observación y se registra el descarte `no_disponible`, `moneda_no_cop` o `modelo_no_identificable`, respectivamente

### Escenario 10: Posible cambio de estructura

- **Dado** que más del 50 % de las páginas de televisor leídas en la ejecución no tiene datos estructurados Product
- **Cuando** termina de procesarlas
- **Entonces** la ejecución termina `fallida` con motivo `"posible cambio de estructura en Falabella"` y se emite `captura_fallida`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (configura el conector); el sistema lo ejecuta como `conector:Falabella`.
- **Permisos requeridos:** rol Administrador para configurar el patrón de URL y el índice de sitemaps.
- **Valor de negocio:** segunda fuente retail, necesaria para alcanzar la referencia agregada del Benchmark 2 (configuración inicial: ≥ 3 observaciones de al menos 2 fuentes).

### Reglas de Negocio

**RN-01 — Rutas requeridas.** Sitemaps de páginas de producto y patrón de URL de televisores. Si `robots.txt` prohíbe alguna, el marco común suspende la fuente (HU-053). El conector no solicita carrito, cuenta, búsqueda ni ninguna ruta distinta de sitemaps y páginas de producto.

**RN-02 — Sitemaps.** Origen: directivas `Sitemap:` del `robots.txt` vigente; si no hay, la URL de índice configurada; si tampoco, ejecución `fallida` con motivo `"Sin sitemap de productos para Falabella"`. Para no consumir el volumen semanal, un archivo de sitemap cuyo `lastmod` en el índice no cambió desde la última descarga exitosa no se vuelve a descargar: se usa la lista de URLs guardada. Archivos sin `lastmod` se descargan en cada ejecución.

**RN-03 — URLs candidatas.** URLs que cumplen el patrón de URL de televisores de Falabella (expresión configurable de 3 a 200 caracteres, obligatoria para habilitar: `"Configure el patrón de URL de televisores de Falabella antes de habilitar la captura."`; inválida: `"El patrón de URL no es válido."`). Cada URL se procesa una sola vez por ejecución.

**RN-04 — Mapeo de datos estructurados (schema.org Product).**

| Campo de la observación | Origen | Regla |
|---|---|---|
| `producto_descripcion` | `name` | Recortado a 300 caracteres |
| `marca` | `brand.name` o `brand` | Si falta: descarte `datos_estructurados_ausentes` |
| `modelo_referencia` | `model` o `mpn`; si no, del `name` | Token más largo de 6 a 20 caracteres de letras, dígitos y guiones, con al menos 2 letras y 2 dígitos, que no sea medida ni resolución; en empate, el primero. Sin resultado: descarte `modelo_no_identificable` |
| `sku` | `sku` | SKU interno de Falabella, tal como se publica |
| `ean_gtin` | `gtin13`, `gtin12`, `gtin14`, `gtin8` o `gtin` | Solo si es GTIN válido; el SKU interno no se usa como EAN |
| vendedor | `offers[].seller.name` | Se consideran solo ofertas cuyo vendedor está en los vendedores aceptados de Falabella (inicial: "Falabella"); ausente: descarte `vendedor_no_identificable` |
| precio vigente | `offers[].price` de la oferta de Falabella | Entero COP |
| precio anterior | precio normal o de lista de la oferta de Falabella (`priceSpecification` de tipo lista o precio rotulado "normal") | Solo evidencia; debe ser mayor que el efectivo |
| precio CMR | precio de la oferta de Falabella rotulado o tipificado como CMR / tarjeta | Precio condicionado `tarjeta_especifica` |
| moneda | `priceCurrency` | Distinta de COP: descarte `moneda_no_cop` |
| disponibilidad | `availability` | `OutOfStock`, `SoldOut` o `Discontinued`: descarte `no_disponible` |
| tamaño, resolución, tecnología, smart | `name` | Mismas reglas de lectura desde el nombre que el conector de Alkosto: tamaño = primer número de 2–3 dígitos seguido de "pulgadas", "pulg", `"` o `''` (10–120); "8K" → 8K, "4K"/"UHD" → 4K UHD, "Full HD"/"FHD" → Full HD, "HD" → HD; "Mini LED", "OLED", "QLED", "LED"; "Smart" → sí; si no, nulo/`desconocida`/`desconocido` |

**RN-05 — Precios de la oferta de Falabella.** `precio_efectivo` = menor precio vigente general (sin condición). El precio CMR, si coexiste con uno general, va a `precios_condicionados_evidencia` y no se usa. Si solo existe el precio CMR, la observación se guarda con ese precio, `condicion_especial = tarjeta_especifica`, detalle = rótulo leído (o "Precio con tarjeta CMR" si no hay rótulo) y `apta_para_referencia = no`. Otros rótulos condicionados se detectan con la lista de palabras clave configurable del sistema.

**RN-06 — Evidencia.** Copia textual del bloque de datos estructurados (incluidas todas las ofertas, también las de terceros), URL, fecha y hora de la respuesta, código de respuesta y hash SHA-256.

**RN-07 — Cambio de estructura.** Más del 50 % (configurable) de páginas de televisor leídas sin datos estructurados Product → ejecución `fallida`, motivo `"posible cambio de estructura en Falabella"`, evento `captura_fallida`; las observaciones ya creadas se conservan.

**RN-08 — Valores fijos.** `metodo_adquisicion = sitemap_datos_estructurados`, `registrado_por = conector:Falabella`, `canal_carga = conector`, `id_contexto = id_ejecucion`, `iva_condicion` = valor por defecto de captura de Falabella (inicial: `indeterminado`), salvo que los datos estructurados declaren explícitamente el impuesto incluido.

### Interfaz

Sin interfaz propia. El Administrador configura el patrón de URL de televisores y, si hace falta, la URL de índice de sitemaps mediante la operación administrativa del catálogo de fuentes.

### Sistemas Externos (Si aplica)

**Falabella (sitio web público):** `robots.txt`, índice y archivos de sitemap de producto (XML), páginas de producto con schema.org. Respuesta correcta: 200 con datos estructurados; no disponible: timeout o 5xx (reintentos del marco común); respuesta inesperada: sin datos estructurados, estructura distinta u ofertas sin vendedor (RN-04, RN-07); restricción: 401, 403, 429 o CAPTCHA (suspensión, HU-053). Términos de uso sin verificar (D6): bloqueo para producción, no para el MVP de validación.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-050 (marco común), HU-053 (suspensión), HU-044 (vendedor), HU-045 (precio efectivo), HU-046 (condiciones especiales), HU-051 (conector Alkosto, mismas reglas de lectura del nombre).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Reutilización de sitemaps por `lastmod`** para no consumir el volumen semanal con archivos de 25.000 URLs. Resuelta (RN-02).
2. **Precio CMR** como precio condicionado `tarjeta_especifica`. Resuelta (RN-05).
3. **SKU interno ≠ EAN** en Falabella. Resuelta (RN-04).
4. **Sin vendedor implícito** para Falabella por ser marketplace mixto. Resuelta (RN-04).
5. **Patrón de URL de televisores** como parámetro obligatorio registrado al habilitar el conector. Resuelta (RN-03).

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
