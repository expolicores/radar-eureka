---
spike: 'D1'
titulo: 'Exploración de SECOP II / datos.gov.co para el MVP de televisores'
proyecto: 'Seguimiento Compras Públicas'
fecha: '2026-10-01'
autor: 'Juan Camilo (con Consultor Técnico)'
estado: 'Completado — decisiones del PO tomadas (2026-10-02)'
insumo_de: 'PRD'
---

# Spike D1 — SECOP II / datos.gov.co

**Objetivo:** responder las preguntas del spike D1 del Brief aprobado con datos reales y actuales, antes de iniciar el PRD.

**Método:** consultas a la API pública de datos.gov.co (Socrata/SODA, sin autenticación) y descarga de una muestra de documentos de procesos reales de televisores. Scripts reproducibles en [`d1-scripts/`](d1-scripts/). Corte de datos: **2026-10-01**. Ventana analizada: **2023-01-01 a 2026-09-30** (3 años de histórico + 2026).

> **Etiquetas:** **[Verificado]** observado directamente en este spike · **[Muestra]** observado en una muestra, extrapolar con cuidado · **[No verificado]** inferido, requiere confirmación.

---

## 1. Resumen ejecutivo

1. **Los datos estructurados de SECOP II existen, están actualizados a diario y se consultan por API sin scraping** **[Verificado]**. Pero **no traen ítems, cantidades, precios unitarios ni marca/modelo**: esa información está en los documentos.
2. **Los documentos de cada proceso tienen una URL oficial de descarga, publicada en datasets abiertos**, y se descargaron **sin CAPTCHA ni login** **[Verificado, muestra de 39 documentos]**. La ruta "API → documentos" es viable sin scraping del portal.
3. **El universo de televisores en SECOP II es pequeño**: **~355 contratos** en 2023–2026 (≈100 por año), en 272 entidades, con mediana de **COP 22,9 millones** por contrato **[Verificado]**.
4. **Hallazgo principal: la Tienda Virtual del Estado Colombiano (TVEC) publica cada ítem comprado con descripción, precio unitario y cantidad, ya estructurado.** En 2023–2026 hay **1.146 líneas de televisores, 930 órdenes y ~6.000 unidades**, y el **36 %** de las líneas trae un código de modelo identificable **[Verificado]**. Es la fuente más comparable para el Benchmark 1 (compras públicas vs. compras públicas) y **no requiere extracción con IA**.
5. **~28 % de los PDF de la muestra no tiene capa de texto** (escaneados) y algunos escaneados con OCR traen ruido. La extracción multimodal sigue siendo necesaria para SECOP II, lo que confirma la necesidad del spike D4 **[Muestra]**.
6. **En los documentos de la entidad los televisores suelen especificarse por características ("65 pulgadas, 4K, Smart"), no por modelo**. La marca y el modelo aparecen en ofertas, cotizaciones y fichas técnicas. En SECOP II predominará la comparación **por equivalencia**; la de **mismo modelo** vendrá sobre todo de TVEC **[Muestra]**.

**Conclusión:** el MVP es viable con fuentes oficiales. El universo es pequeño pero suficiente, y **cambia de forma importante si se incorpora TVEC**. Hay tres decisiones del PO antes del PRD (sección 10).

---

## 2. Datasets relevantes

| Dataset | ID | Registros (2026-10-01) | Uso en el MVP |
|---|---|---|---|
| SECOP II – Contratos Electrónicos | `jbjy-vk9h` | 6.092.927 | **Principal.** Contrato, entidad, proveedor, valor, fechas, modalidad, UNSPSC principal, objeto. |
| SECOP II – Procesos de Contratación | `p6dx-8zbt` | 9.249.545 | Proceso: precio base, modalidad, estado, respuestas/ofertas, categorías adicionales. |
| SECOP II – Archivos Descarga Desde 2025 | `dmgg-8hin` | 74.939.975 | **Documentos 2025+** con URL de descarga. |
| SECOP II – Archivos Descarga Histórico 2024 / 2023 / 2022 / Hasta 2021 | `nbae-kzan` / `3skv-9na7` / `kgcd-kt7i` / `f8va-cf4m` | 42.700.867 (2024) | Documentos del histórico. |
| **TVEC – Compras por ítem** | `3hdv-smhz` | 1.451.133 | **Ítem, precio unitario, cantidad, total, fecha, orden.** |
| TVEC – Items | `usqp-5nsn` | 1.451.133 | Mismo contenido con `id_entidad` (en `3hdv-smhz` la entidad aparece como "No definido"). |
| TVEC – Consolidado | `rgxm-mmea` | 167.929 | Encabezado de órdenes: entidad, proveedor, total, ítems en texto, agregación. |
| SECOP I – Procesos de Compra Pública | `f789-7hwg` | — | 240 contratos de televisores desde 2023 (ver sección 10). |
| SECOP I – Archivos Descarga | `ps88-5e3v` | — | Documentos SECOP I (no explorado a fondo). |
| Otros SECOP II útiles a futuro | Adiciones `cb9c-h8sn`, Modificaciones `u8cx-r425`, Ofertas por proceso `wi7w-2nvm`, Proveedores `qmzu-gj57` | — | Ciclo de vida del contrato y ofertas: fuera del MVP. |

No se encontró en datos abiertos un dataset de **ítems o precios unitarios de SECOP II** **[Verificado: búsqueda en catálogo]**.

---

## 3. Campos clave y cómo se relacionan

**Contratos (`jbjy-vk9h`)**: `id_contrato` (CO1.PCCNTR.…), `proceso_de_compra` (CO1.BDOS.…), `nombre_entidad`, `nit_entidad`, `codigo_entidad`, `proveedor_adjudicado`, `documento_proveedor`, `objeto_del_contrato`, `descripcion_del_proceso`, `codigo_de_categoria_principal` (formato `V1.52161505`), `modalidad_de_contratacion`, `valor_del_contrato`, `fecha_de_firma`, `estado_contrato`, `urlproceso`, `ultima_actualizacion`.

**Archivos (`dmgg-8hin` e históricos)**: `proceso`, `n_mero_de_contrato`, `id_documento`, `nombre_archivo`, `descripci_n`, `extensi_n`, `tamanno_archivo`, `fecha_carga`, `url_descarga_documento`.

**TVEC ítems (`3hdv-smhz` / `usqp-5nsn`)**: `orden_de_compra`/`orden`, `fecha`, `item`, `price`/`precio`, `qty`/`cantidad`, `unidad_de_medida`, `line_total`/`total`, `id_entidad`.

| Relación | Llave | Estado |
|---|---|---|
| Contrato → documentos | `contratos.proceso_de_compra` = `archivos.proceso` | **[Verificado]** en 98 de 100 contratos muestreados (los 2 restantes, de 2026, aún sin documentos cargados) |
| Contrato → proceso | `proceso_de_compra` ↔ `procesos.id_del_proceso` | **[No verificado]** |
| Contrato → proveedor | `documento_proveedor` / `codigo_proveedor` | **[No verificado]** contra `qmzu-gj57` |
| TVEC ítem → orden y entidad | `usqp-5nsn.orden` ↔ `rgxm-mmea.identificador_de_la_orden` | **[No verificado]** |

---

## 4. Cómo identificar contratación de televisores

Contratos SECOP II firmados desde 2023-01-01 **[Verificado]**:

| Criterio | 2023 | 2024 | 2025 | 2026 (a sep) | Total |
|---|---|---|---|---|---|
| UNSPSC principal `52161505` (Televisores) | 56 | 65 | 67 | 37 | **225** |
| Texto "TELEVISOR" en objeto o descripción | 49 | 57 | 56 | 32 | 194 |
| **Unión** (UNSPSC o texto, incl. "SMART TV") | 89 | 107 | 106 | 53 | **355** |
| Familia `521615` (audio y video de consumo) | 306 | 299 | 330 | 144 | 1.079 |

- **355 contratos, 347 procesos y 272 entidades.** Valor del contrato: mediana COP 22,9 M y p90 COP 123,9 M **[Verificado]**.
- **Modalidades:** mínima cuantía 177; régimen especial 107; subasta inversa 37; contratación directa 25; menor cuantía 8; licitación 1 **[Verificado]**.
- **Falsos positivos por texto [Muestra]:** la búsqueda textual atrapa contratos de ecoturismo, mesa de ayuda, pólizas o derechos humanos que mencionan un televisor de pasada. **Se necesita un paso de clasificación** (reglas + revisión, o IA) que confirme que el contrato incluye al menos un televisor dentro del alcance del Brief.
- **Contratos mixtos:** hay casos como "52 equipos de cómputo + 1 televisor" o "aires acondicionados y televisores". El análisis es por **ítem**, no por contrato.
- El UNSPSC por sí solo no basta: 130 de los 355 contratos no tienen `52161505` como categoría principal.

---

## 5. Qué está estructurado y qué requiere documentos

| Dato del flujo | SECOP II | TVEC |
|---|---|---|
| Entidad, proveedor, fecha, modalidad, valor total | Estructurado | Estructurado (entidad vía `usqp-5nsn`/consolidado) |
| Objeto / descripción | Estructurado (texto libre) | Estructurado (texto del ítem) |
| **Ítem, cantidad, precio unitario** | **Solo en documentos** | **Estructurado** |
| **Marca / modelo** | En ofertas, cotizaciones y fichas técnicas; casi nunca en estudios previos | En el texto del ítem: 36 % con código de modelo, 83 % con tamaño |
| IVA | En documentos (ej. "Subtotal / IVA 19 % / Total", "precio unitario + IVA") | **No determinado** |
| Presupuesto oficial y precios de los oferentes | En documentos (informes de evaluación económica) | No aplica |

**Documentos útiles para extraer precio unitario [Muestra]:** propuesta u oferta económica (a veces .xlsx), informe de evaluación económica (trae los precios unitarios de **todos** los oferentes), contrato o aceptación de oferta, cotizaciones del análisis del sector y estudios previos (especificaciones y presupuesto).

**Ejemplos reales:**
- *IE Antonia Santos (2026)*: anexo económico en .xlsx con ítems separados: televisor 65" ×8, soporte ×8 e instalación ×8. El televisor se puede **discriminar** de la instalación.
- *SENA Cazucá (2026)*: el informe de evaluación económica lista el precio unitario de 6 oferentes (COP 2,49 M a 3,59 M) e incluso una alerta de "precio artificialmente bajo".
- *Distrito de Turbo (2026)*: contrato escaneado con OCR que trae televisores de 65" y 75" con especificaciones genéricas y "Subtotal / IVA (19 %)". El texto tiene ruido de OCR ("resoluci6n", "debefa").

---

## 6. Acceso a documentos

- **Mecanismo [Verificado]:** el dataset de archivos publica `url_descarga_documento` (`community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=…`). Es un mecanismo público de descarga referenciado desde datos abiertos oficiales, no un scraping del portal.
- **Descarga [Verificado, muestra]:** 39 de 39 documentos se descargaron por HTTP directo, sin CAPTCHA ni autenticación.
- **Disponibilidad por año [Muestra]:** 25 de 25 contratos con documentos en 2023, 2024 y 2025, y 23 de 25 en 2026. Hay datasets de archivos por año, así que **el histórico de 3 años es viable**.
- **Volumen [Muestra]:** mediana de **23 documentos por proceso**. Formatos: PDF 93 %, y además docx, zip, xlsx, rar y jpg. **Los .zip y .rar contienen más documentos** y hay que descomprimirlos.
- **Capa de texto [Muestra de 32 PDF]:** 23 con texto extraíble; **9 sin texto (~28 %)**, que requieren OCR o lectura multimodal. Algunos con texto vienen de OCR previo con errores.
- **Selección de documentos:** no conviene procesar los 23 documentos de cada proceso. Se necesita una **priorización por nombre y descripción** (oferta, económica, evaluación, cotización, contrato, aceptación, estudio previo), y eso reduce costo y ruido.

---

## 7. Mecanismos de consulta (API)

- **API:** Socrata SODA en `https://www.datos.gov.co/resource/{id}.json`, con consultas SoQL (`$select`, `$where`, `$group`, `$order`, `$limit`). Metadatos y columnas en `/api/views/{id}.json`. Catálogo en `api.us.socrata.com/api/catalog/v1` **[Verificado]**.
- **Actualización:** los datasets principales muestran datos actualizados al **2026-10-01**, es decir, a diario **[Verificado]**.
- **Sin autenticación** funcionó para todas las consultas del spike. Un conteo sobre un dataset grande (`rpmr-utcd`, SECOP Integrado) **superó el tiempo de espera** **[Verificado]**. Para producción conviene usar un **app token** de Socrata y **cargas incrementales** por `ultima_actualizacion` o fecha **[No verificado: límites exactos]**.
- **Orden de preferencia del Brief:** se cumple en el nivel 1 (API y datos oficiales) para todos los datos estructurados y para la ubicación de los documentos. **No hace falta scraping** para el MVP.

---

## 8. Volumen y calidad de datos

**Universo del MVP (2023–2026-09):**

| Fuente | Volumen de televisores | Unidad de análisis |
|---|---|---|
| SECOP II (contratos) | ~355 contratos, 272 entidades | Contrato → ítems extraídos de documentos |
| SECOP I | 240 contratos | Por explorar |
| **TVEC** | **1.146 líneas, 930 órdenes, ~6.000 unidades** | **Ítem con precio unitario** |

Marcas en TVEC: Samsung 545 líneas, LG 354, TCL 18, Kalley 16, Challenger 8, Hisense 5.

**Implicaciones para los KPIs del Brief:**
- La muestra de **≥ 50 documentos** validados a mano es factible.
- La **cobertura ≥ 60 %** se mide sobre un universo de ~355 contratos de SECOP II, o más si se suman TVEC y SECOP I.
- Con ~100 contratos por año en SECOP II, el Benchmark 1 **solo con SECOP II** tendría pocas observaciones por tamaño y período. **Con TVEC la densidad se multiplica.**

**Problemas de calidad detectados:**
1. **Falsos positivos en la identificación por texto** (sección 4).
2. **Especificaciones genéricas** en los documentos de la entidad; el modelo solo aparece en ofertas y fichas técnicas.
3. **PDF escaneados (~28 %) y ruido de OCR.**
4. **Documentos empaquetados** en .zip y .rar.
5. **Procesos (`p6dx-8zbt`)**: la búsqueda "TELEVISOR" arroja miles de procesos, la mayoría en estado "Presentación de oferta". Puede ser una peculiaridad del dataset (procesos sin cerrar, duplicados por fase). **Usar contratos como unidad base**, y procesos solo como complemento **[No verificado]**.
6. **TVEC**: el texto del ítem no está normalizado (mayúsculas, prefijos "GSF01-", códigos internos), el 64 % no trae código de modelo, en `3hdv-smhz` la entidad aparece como "No definido" (usar `usqp-5nsn`), y **no se sabe si el precio incluye IVA**.
7. **Datos personales sensibles en contratos**: el dataset trae banco, tipo y **número de cuenta**, y documentos de identidad de representantes legales, supervisores y ordenadores del gasto. El MVP **no debe ingerir ni mostrar** esos campos (minimización, Ley 1581/2012).

---

## 9. Validación de los supuestos del Brief

| Supuesto del Brief | Resultado |
|---|---|
| 1. Los datos abiertos de SECOP II cubren los campos estructurados necesarios | ✅ **Validado parcialmente.** Entidad, proveedor, modalidad, fechas, valores y UNSPSC sí; ítems y precios unitarios no. |
| 2. Los documentos son accesibles de forma automatizada | ✅ **Validado** por URL oficial y sin CAPTCHA (en muestra). |
| 3. Se puede identificar el "mismo bien" en televisores | ⚠️ **Parcial.** Viable en TVEC (36 % con modelo) y en ofertas. En estudios previos predomina la equivalencia. |
| 7. El volumen de televisores es suficiente | ⚠️ **Justo en SECOP II** (~100 contratos por año); **suficiente con TVEC**. |
| 9. Se puede determinar si el valor incluye IVA | ⚠️ **En documentos de SECOP II, frecuentemente sí; en TVEC, no determinado.** |
| Revisión crítica: volumen de la tesis (50–150 procesos por día) | Superado: el dataset de procesos SECOP II tiene 9,25 M de registros. El volumen relevante para el MVP es el de televisores, no el total. |
| Revisión crítica: scraping con Selenium | Confirmado como innecesario para el MVP. |

---

## 10. Decisiones requeridas al PO antes del PRD

| # | Decisión | Recomendación del consultor | Impacto |
|---|---|---|---|
| **P1** | ¿Se incorpora **TVEC** (Tienda Virtual del Estado: órdenes e ítems) como fuente del MVP? | **Sí.** Son compras públicas con precio unitario y modelo estructurados. Alimentan directamente el Benchmark 1 y la comparación de **mismo modelo**, y no requieren extracción con IA. | Cambia el alcance de ingesta. El Brief nombra SECOP II como fuente principal, así que requiere una **adenda al Brief**. |
| **P2** | ¿Se incluye **SECOP I** (240 contratos de televisores desde 2023)? | **Diferir a post-MVP**, salvo que el PRD muestre que hace falta densidad. Tiene otra estructura y otros datasets de documentos. | +68 % del universo de contratos, con costo de integración adicional. |
| **P3** | Regla de identificación de televisores | UNSPSC `52161505` + búsqueda textual como candidatos → **clasificación a nivel de ítem** (incluido o excluido según el límite de la categoría del Brief), con revisión en una muestra. | Define la precisión del universo y el denominador del KPI de cobertura. |

**Decisiones del PO (2026-10-02):**
- **P1:** ✅ Se incorpora la TVEC como fuente del MVP.
- **P2:** ❌ SECOP I no se incluye en el MVP.
- **P3:** Candidatos por código UNSPSC `52161505` y/o búsqueda de texto. Se confirman a nivel de ítem contra el límite de categoría del Brief.

Registradas en la **Adenda 1** del Brief.

**Otros insumos para el PRD:**
- **Unidad de análisis = ítem de televisor**, no contrato.
- **Requisito de priorización de documentos** por tipo, y manejo de .zip y .rar.
- **Requisito de OCR o lectura multimodal** para ~28 % de los PDF (dimensionar en D4).
- **Exclusión de datos personales sensibles** del dataset de contratos.
- **Carga incremental** con app token.
- **Precios de todos los oferentes** en los informes de evaluación económica: una fuente adicional de referencia pública, a evaluar en el PRD.

---

## 11. Limitaciones del spike

- Muestras pequeñas: 100 contratos para verificar documentos, 39 descargas y 32 PDF para medir la capa de texto. Los porcentajes son indicativos.
- No se verificaron: la relación procesos↔contratos, la relación de órdenes TVEC con su encabezado, los límites exactos de la API, el tratamiento de IVA en TVEC ni los documentos de SECOP I.
- No se midió la precisión de extracción: eso es el spike D4.
- No se revisaron términos de uso específicos del endpoint de descarga de documentos, más allá de que está publicado en datasets abiertos oficiales.
