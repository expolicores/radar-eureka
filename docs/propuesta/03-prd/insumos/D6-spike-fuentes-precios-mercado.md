---
spike: 'D6'
titulo: 'Fuentes de precios de mercado para televisores (Benchmark 2)'
proyecto: 'Seguimiento Compras Públicas'
fecha: '2026-10-02'
autor: 'Juan Camilo (con Consultor Técnico)'
estado: 'Completado con decisiones de adquisición progresiva (2026-10-02) — ver Adenda 2 del Brief'
insumo_de: 'PRD'
---

# Spike D6 — Fuentes de Precios de Mercado

**Objetivo:** para cada fuente candidata del Benchmark 2 del Brief, identificar qué mecanismo de obtención existe según el orden aprobado (**1) API/datos oficiales → 2) mecanismos públicos de integración → 3) scraping como último recurso**, sin evasión de CAPTCHA), qué campos entrega, sus restricciones y si sirve para el MVP.

**Método:** pruebas de bajo volumen (decenas de solicitudes, identificadas con un User-Agent de investigación), revisión de `robots.txt`, sitemaps y datos estructurados publicados, y búsqueda de documentación oficial. Scripts en [`d6-scripts/`](d6-scripts/). Corte: **2026-10-02**.

> **Etiquetas:** **[Verificado]** observado directamente · **[Muestra]** observado en una muestra pequeña · **[No verificado]** requiere confirmación.

---

## 1. Resumen ejecutivo

1. **Ninguna de las tiendas candidatas ofrece hoy una API pública y autorizada (nivel 1) para consultar precios de televisores** **[Verificado]**.
2. **Mercado Libre:** la API existe, pero **la búsqueda de publicaciones está bloqueada**. Responde 403 sin token, y hay reportes de 403 incluso con token, asociados a cambios en sus políticas de API. Esto **corrige un hecho del Brief** ("Mercado Libre dispone de APIs para consulta de publicaciones"): la API existe, pero **no** permite buscar publicaciones abiertamente.
3. **Éxito:** su plataforma (VTEX) responde una API de catálogo con marca, modelo, EAN, precio y vendedor, pero **su `robots.txt` prohíbe `/api/`**. No se recomienda usarla sin autorización. Además, la mayoría de los televisores los venden **terceros del marketplace** (9 de 10 en la muestra).
4. **Alkosto y Falabella:** no tienen API pública, pero **publican sitemaps de producto y datos estructurados schema.org** (precio en COP, marca, SKU/EAN y vendedor) en páginas de producto **permitidas por su `robots.txt`**. Se leyeron sin bloqueos ni CAPTCHA **[Verificado]**. Es el mecanismo más viable, pero **técnicamente es lectura de páginas** (nivel 3, en su forma menos invasiva). Requiere **aceptación explícita del PO** y **revisión de los términos de uso**, que no se pudieron leer de forma automática.
5. **Emparejamiento por mismo modelo:** **9 de los 25 modelos** más comprados en la TVEC en 2025–2026 aparecen hoy en el catálogo de Alkosto **[Muestra, indicativo]**. La comparación de mismo modelo contra mercado es posible pero parcial; la equivalencia seguirá siendo necesaria.
6. **IVA:** los precios al consumidor se publican con impuestos incluidos (la API de VTEX trae `Tax = 0` sobre el precio final). **[No verificado jurídicamente]** El Estatuto del Consumidor (Ley 1480 de 2011) exige informar el precio total con impuestos incluidos. Si se confirma, el Benchmark 2 cumple la regla de "precio final con IVA" del Brief.

**Recomendación:** Benchmark 2 del MVP con **Alkosto (principal) y Falabella (secundaria, filtrando por vendedor)**, leyendo sitemaps y datos schema.org en páginas permitidas, con baja frecuencia y evidencia guardada. **Excluir Mercado Libre y Éxito** del MVP salvo acceso autorizado. Hay tres decisiones del PO (sección 6).

---

## 2. Evaluación por fuente

| Fuente | Mecanismo disponible | Nivel (orden del Brief) | Campos obtenidos | Restricciones observadas | Recomendación MVP |
|---|---|---|---|---|---|
| **Mercado Libre** | API oficial. `/sites/MCO/search` → **403**; `/products/search` → **403** (PolicyAgent); solo `domain_discovery` responde (categoría `MCO14903` Televisores) | 1, pero **bloqueado** para búsqueda | — | Búsqueda de publicaciones restringida. El acceso al catálogo requiere app OAuth **[No verificado si se concede]**. Marketplace con vendedores heterogéneos, incluidos productos usados o reacondicionados. | **Excluir.** Reevaluar si se registra una app y se confirma el acceso al catálogo. |
| **Éxito** | API VTEX `catalog_system/pub` responde JSON | 1 técnico, pero **prohibido por robots** (`Disallow: /api/`) | Marca, `Modelo`/`Referencia`, **EAN**, `Price`, `ListPrice`, `Tax`, vendedor, especificaciones (tamaño, resolución, tipo de panel) | `robots.txt` prohíbe `/api/`. **Marketplace dominante** (9 de 10 resultados de terceros). Mezcla accesorios y combos ("TV + crispetera"). | **Excluir la API.** Opción futura: solicitar autorización o un feed a Éxito. |
| **Alkosto** | **Sitemap de productos** (30.993 URLs, `lastmod` diario; 332 URLs de televisores) + **schema.org** en la página (`price`, `priceCurrency=COP`, `sku`=EAN) | **2–3**: datos publicados para buscadores, obtenidos leyendo páginas | Precio de venta, moneda, SKU/EAN, nombre con marca, modelo y tamaño (en URL y título) | `robots.txt` permite productos y prohíbe búsqueda (`?q=`, `/search/`). Sin CAPTCHA en la prueba. **Términos de uso no verificados.** Vendedor: la propia tienda. | **Incluir (principal)**, sujeto a P2 y a la revisión de términos. |
| **Falabella** | **Sitemaps PDP** (índice con varios archivos de 25.000 URLs) + **schema.org** (`brand`, `price` oferta/normal, `sku`, `seller`) | **2–3** (igual que Alkosto) | Marca, precio(s), SKU interno, vendedor (Falabella o tercero) | `robots.txt` permite todo salvo carrito y cuenta. **Términos de uso no verificados.** Marketplace mixto, filtrable por `seller`. | **Incluir (secundaria)**, solo con vendedor = Falabella, sujeto a P2. |
| **TVEC / Acuerdos Marco** | API oficial datos.gov.co (ver D1) | 1 | Ítem, precio unitario, cantidad, fecha | — | **Ya incorporada como Benchmark 1** (compra pública). No se usa como precio de mercado: es el precio que pagó el Estado. |
| **Google Shopping** | Sin API pública de consulta de precios (la API de contenido es para comerciantes) | — | — | — | **Descartada.** |

---

## 3. Calidad y comparabilidad de los datos de mercado

- **Precio a usar:** el **precio de venta vigente** (`Price` / precio de oferta), guardando también el precio "antes" (`ListPrice` / precio normal). El precio tachado suele estar inflado (ej. COP 1.739.900 frente a 4.200.000 en la muestra de Éxito) y **no debe usarse como referencia** **[Muestra]**.
- **Vendedor:** en Éxito y Falabella hay terceros del marketplace. **Propuesta:** priorizar el vendedor = la propia tienda y tratar a los terceros como observaciones separadas, con menor confianza, o excluirlos (P3).
- **Ruido de catálogo:** en la búsqueda aparecen soportes, muebles para TV, adaptadores y combos. Hace falta filtrar por categoría y especificaciones, con la misma lógica de límite de categoría del Brief **[Verificado]**.
- **Identificadores para el mismo modelo:** Éxito y Alkosto exponen **EAN/GTIN**; la TVEC y los documentos de SECOP II **no**. El emparejamiento será por **código de modelo**, tolerando sufijos regionales (ej. `55UA7300PSB` / `PSA`, `UN85DU8000KXZL`).
- **Cobertura de mismo modelo [Muestra, indicativo]:** de los 25 modelos más frecuentes en la TVEC 2025–2026, **9 aparecen en Alkosto** y 2 en el único sitemap de Falabella revisado (de varios). Varios "modelos" de la TVEC son códigos internos (ej. `AMEPIE0377`), no modelos del fabricante.
- **Temporalidad:** las tiendas publican el **precio actual** y retiran los modelos descontinuados. Esto confirma la decisión del Brief: el Benchmark 2 aplica a contratos recientes y al **histórico propio** de precios que el sistema empiece a guardar.
- **IVA:** precio al consumidor con impuestos incluidos (ver resumen, punto 6) **[No verificado jurídicamente]**.

---

## 4. Volumen y frecuencia estimados

- **Universo por tienda:** del orden de **cientos de televisores** (Alkosto: 332 URLs de TV en el sitemap) **[Verificado para Alkosto]**.
- **Frecuencia propuesta:** captura **semanal** (o diaria solo para los modelos presentes en contratos recientes), con descarga de sitemaps y luego solo de las páginas de televisores. Se estiman **< 1.000 solicitudes por tienda y semana** **[No verificado: estimación]**.
- **Evidencia por observación** (según el Brief): producto/modelo, características, precio de venta y precio "antes", vendedor, fuente, URL, fecha y hora de consulta, indicador de IVA incluido y **copia del bloque de datos estructurados** leído, para auditar la observación.

---

## 5. Relación con el orden de preferencia del Brief

| Nivel | Resultado |
|---|---|
| **1. API / datos oficiales** | Disponible solo para fuentes públicas (SECOP II, TVEC). **No disponible o no autorizada** para precios de mercado: Mercado Libre bloqueada, API de Éxito prohibida por robots. |
| **2. Mecanismos públicos de integración** | **Sitemaps y datos estructurados schema.org** publicados por Alkosto y Falabella para buscadores. No hay feeds ni catálogos descargables oficiales. |
| **3. Scraping (último recurso)** | Leer los datos estructurados exige **descargar las páginas de producto**. Es scraping en su forma menos invasiva: páginas permitidas por robots, sin evasión, baja frecuencia y sin CAPTCHA encontrado. |

**Conclusión:** para el Benchmark 2 **no existe un nivel 1**. El MVP puede tener precios de mercado **solo si el PO acepta una captura de nivel 2–3** con reglas estrictas, o si se consigue acceso autorizado (API de Mercado Libre con app aprobada, o un acuerdo o feed con alguna tienda).

---

## 6. Decisión del PO: estrategia de degradación y carga manual (2026-10-02)

**Criterio de éxito de D6 [Decisión]:** D6 no necesita demostrar que el 100 % del Benchmark 2 se puede automatizar. Debe determinar qué fuentes se automatizan hoy, cuáles requieren más exploración, cuáles se usan manualmente durante el MVP, cuáles se excluyen y qué información mínima conserva cada observación. **La disponibilidad limitada de APIs comerciales deja de ser un bloqueante para el PRD.**

**Principios [Decisión]:**
- Lo prioritario es demostrar el flujo *contrato → identificar televisor → normalizar → referencias comparables → comparar → señal → evidencia trazable*.
- **Base de precios como componente independiente:** se separa **A. conseguir el dato de mercado** de **B. usarlo para normalizar, comparar y generar señales**. A puede empezar parcialmente manual y automatizarse después sin bloquear la validación de B.
- **No automatizar por automatizar.** Se acepta cargar a mano 50, 100 o N referencias como mecanismo temporal de discovery/MVP.
- **Un dato manual nunca se presenta como si fuera automático.**

**Niveles progresivos de adquisición por fuente [Decisión]:**
1. Integración automática autorizada (API, dataset, feed, sitemap o datos estructurados disponibles).
2. Extracción web controlada, cuando sea técnica y jurídicamente viable, con las reglas de D6.
3. Exploración de nuevas fuentes (otras tiendas, catálogos, fuentes públicas, acuerdos marco, proveedores de información).
4. Carga manual o semiautomática.

### 6.1 Clasificación final de fuentes

| Fuente | Clasificación MVP | Condición / siguiente paso |
|---|---|---|
| **Alkosto** | **Automatizable hoy** (sitemap + datos schema.org en páginas permitidas por robots) | Revisión manual de términos de uso antes de producción. Mientras tanto, carga manual o semiautomática. |
| **Falabella** | **Automatizable hoy** (igual que Alkosto) | Igual que Alkosto. Filtrar por vendedor (ver P3). |
| **Mercado Libre** | **Manual en el MVP** + **exploración** | Explorar registro de app OAuth y acceso al catálogo. **Excluida:** la búsqueda por API bloqueada y cualquier scraping de su búsqueda. |
| **Éxito** | **Manual en el MVP** + **exploración** | Explorar autorización o feed con Éxito. **Excluida:** su API `/api/`, prohibida por `robots.txt`. |
| **Otras tiendas** (ej. Ktronix, Homecenter, Panamericana; catálogos de fabricantes) | **Exploración** | Aplicar el mismo análisis de D6 antes de automatizar. Uso manual permitido. |
| **TVEC / Acuerdos Marco** | **No es fuente de mercado** | Ya es Benchmark 1 (compra pública). |
| **Google Shopping** | **Excluida** | Sin API pública de consulta de precios. |

### 6.2 Registro mínimo de cada observación de precio [Decisión]

Aplica a cualquier método de adquisición: producto · marca/modelo · SKU/EAN cuando exista · vendedor · precio observado · fuente · URL o referencia · fecha de observación · condición de IVA cuando pueda determinarse · evidencia · **método de adquisición** (API / fuente estructurada / extracción web / manual).

**Propuestas del consultor para el PRD [a confirmar]:**
- **Usuario que registró** cada observación manual. Así se distingue de la captura automática y se puede auditar.
- **Protocolo de captura manual contra el sesgo:** registrar **todas** las ofertas comparables encontradas en la búsqueda, no solo la más barata o la más cara, junto con los términos de búsqueda usados. Sin esto, una referencia elegida a mano puede fabricar o esconder una señal.
- **El método de adquisición se muestra en la evidencia** de cada señal, y puede pesar en su nivel de confianza.

### 6.3 Estado de las decisiones

| # | Decisión | Estado |
|---|---|---|
| P1 | Fuentes del Benchmark 2 | **Resuelta:** Alkosto (principal) y Falabella (secundaria); Mercado Libre y Éxito fuera inicialmente (Adenda 2, A2.1). |
| P2 | Extracción de sitemaps y schema.org | **Resuelta:** se acepta como nivel 1–2, condicionada a viabilidad jurídica (revisión de términos de uso). |
| P3 | ¿Solo vendedor = la tienda, o también terceros del marketplace? | **Resuelta:** solo vendedor = la tienda (Adenda 2, A2.4). |

---

## 7. Decisiones requeridas al PO antes del PRD (versión inicial, reemplazada por la sección 6)

| # | Decisión | Recomendación del consultor |
|---|---|---|
| **P1** | Fuentes del Benchmark 2 en el MVP | **Alkosto (principal) + Falabella (secundaria).** Excluir Mercado Libre y Éxito del MVP; dejarlos como "reevaluar con acceso autorizado". |
| **P2** | ¿Aceptas leer **sitemaps y datos schema.org** de páginas de producto permitidas por `robots.txt` (nivel 2–3) como mecanismo del Benchmark 2? | **Sí, con reglas:** respetar `robots.txt`; nunca usar endpoints prohibidos (ej. `/api/` de Éxito) ni rutas de búsqueda prohibidas; sin evasión de CAPTCHA ni bloqueos (si aparecen, se suspende la fuente); User-Agent identificado; baja frecuencia; guardar evidencia; **revisar los términos de uso de cada tienda antes de producción**. Si se rechaza, el MVP arranca **solo con el Benchmark 1** y el Benchmark 2 queda pendiente de acceso autorizado. |
| **P3** | ¿Cómo tratar a los vendedores de marketplace? | **Solo vendedor = la tienda** en el MVP. Los terceros tienen precios y condiciones heterogéneos (garantía, estado, envío) y degradan la comparabilidad. |

**Si se aprueba, esto requiere una Adenda 2 al Brief:**
- Corregir el hecho sobre Mercado Libre (API existe, búsqueda de publicaciones restringida).
- Fijar las fuentes del Benchmark 2.
- Registrar la aceptación del mecanismo de nivel 2–3 con sus reglas.
- Agregar al riesgo **R10** que los términos de uso no están verificados y que el acceso puede cambiar sin aviso.

---

## 8. Insumos para el PRD

- **Requisito de captura de mercado:** sitemaps → filtro de televisores → página → lectura de schema.org → normalización (marca, modelo, tamaño, resolución, tecnología) → observación con evidencia.
- **Requisito de suspensión automática** de una fuente ante bloqueo, CAPTCHA o cambio de `robots.txt`.
- **Emparejamiento por modelo** con sufijos regionales tolerados; por EAN cuando exista en ambos lados.
- **Reglas de precio:** usar el precio de venta y no el tachado, con el vendedor registrado.
- **El nivel de confianza** de cada comparación debe reflejar la fuente, el vendedor, el tipo de emparejamiento (mismo modelo o equivalente) y el método de adquisición.
- **Funcionalidad de carga manual o semiautomática** de observaciones de precio, con el registro mínimo de 6.2.
- **Base de precios de referencia** como componente independiente de la comparación.

---

## 9. Limitaciones

- Pruebas de bajo volumen y en un solo día. **No se evaluó el comportamiento de los sitios a mayor frecuencia.**
- **Términos de uso no verificados:** las páginas de términos de Alkosto, Éxito y Falabella se renderizan con JavaScript y no se pudieron leer de forma automática. **Revisión manual pendiente.**
- No se registró una app en Mercado Libre para probar el acceso con token.
- No se verificó jurídicamente la obligación de publicar los precios con IVA incluido.
- La coincidencia de modelos TVEC ↔ tienda se midió por coincidencia en URLs del sitemap (aproximada). Para Falabella se revisó solo 1 de varios archivos de sitemap.
