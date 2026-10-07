# Épicas Funcionales - Seguimiento Compras Públicas

**Fecha:** 2026-10-02  
**Autor:** Juan Camilo  
**Documento relacionado:** [PRD](./PRD.md)  
**Estado:** PRD aprobado conceptualmente — D4 completado; sujeto a validación de precisión D4-4 y validación de usuarios D5

---

## Resumen de Épicas

Este documento detalla las **9 épicas funcionales** identificadas para Seguimiento Compras Públicas, priorizadas según valor de negocio y complejidad técnica.

> 📖 Ver [PRD](./PRD.md) para contexto completo de FRs, NFRs, exclusiones y riesgos.

---

### ÉPICA-001: Universo de Compras Públicas de Televisores

**Prioridad**: Crítica  
**FRs cubiertos**: FR-001 a FR-017

**Descripción**:
Construye el universo de datos sobre el que trabaja todo el producto: los contratos de SECOP II y los ítems de la Tienda Virtual del Estado Colombiano (TVEC) relacionados con televisores, con 3 años de histórico y actualización continua. Las dos fuentes se obtienen por la API oficial de datos.gov.co, sin scraping.

El valor está en convertir dos fuentes dispersas en un universo único y confiable de **ítems de televisor**: un contrato puede tener varios bienes, y solo los televisores dentro del límite de categoría aprobado entran al análisis. La clasificación confirma cada candidato, porque la búsqueda por código o texto trae falsos positivos.

Esta épica también aplica la minimización de datos: los campos personales sensibles del dataset de contratos nunca entran al sistema.

**Capacidades Incluidas**:
- Carga inicial de 3 años de contratos SECOP II e ítems TVEC.
- Actualización incremental (configuración inicial: diaria), separada de la extracción documental.
- Identificación de candidatos por UNSPSC `52161505` y/o texto.
- Clasificación **estricta** de cada ítem contra el límite de categoría, con motivo: descarta servicios de mantenimiento o instalación, CCTV, señalización, comodatos y lotes que no son de TV, aunque tengan UNSPSC `52161505`.
- Corrección manual de la clasificación por el Administrador.
- Registro de cada ingesta y de los registros rechazados por calidad.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-SEG-005: 0 campos personales sensibles almacenados.
- NFR-DAT-001 / NFR-DAT-002: ingesta diaria; contrato disponible en ≤ 48 h.
- NFR-DAT-004: histórico completo en ≤ 7 días.
- NFR-DAT-005: tolerancia a fallas de la API sin perder ni duplicar registros.

**Factores Críticos**:
- Integraciones: API Socrata de datos.gov.co (datasets `jbjy-vk9h`, `usqp-5nsn`/`3hdv-smhz`, `rgxm-mmea`). Las consultas agregadas grandes pueden superar el tiempo de espera; se requiere app token y carga incremental.
- Relación ítem TVEC ↔ orden ↔ entidad no verificada en D1.
- La clasificación de candidatos (reglas y/o IA) define el denominador de los indicadores de cobertura. En D4, el **28 %** de los candidatos no eran compras de TV, y la mitad tenía UNSPSC `52161505`.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base; se usa solo como complemento si el PRD lo requiere.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] El histórico 2023–hoy de SECOP II y TVEC está cargado y se actualiza a diario.
- [ ] Cada candidato tiene clasificación (incluido / excluido / requiere revisión) con criterio y método registrados.
- [ ] Una revisión manual de 50 candidatos al azar confirma la clasificación en ≥ 95 % de los casos.
- [ ] Una prueba automática confirma que ningún campo personal excluido existe en la base de datos.


---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** 13 historias
**Última actualización:** 2026-10-02

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
| Ingestar Contratos SECOP II | [HU-001](./epicas/epica-001/HU-001-carga-inicial-historico-secop-ii/historia.md) | Carga inicial del histórico de contratos SECOP II | Crítica |
| Ingestar Contratos SECOP II | [HU-002](./epicas/epica-001/HU-002-carga-incremental-secop-ii/historia.md) | Carga incremental periódica de contratos SECOP II | Crítica |
| Ingestar Órdenes de la TVEC | [HU-003](./epicas/epica-001/HU-003-ingesta-items-tvec/historia.md) | Ingesta inicial e incremental de ítems de la TVEC | Crítica |
| Ingestar Órdenes de la TVEC | [HU-004](./epicas/epica-001/HU-004-relacion-item-orden-entidad-tvec/historia.md) | Relacionar cada ítem TVEC con su orden de compra, entidad y fecha | Crítica |
| Controlar Calidad y Trazabilidad de la Ingesta | [HU-005](./epicas/epica-001/HU-005-validaciones-calidad-ingesta/historia.md) | Validaciones de calidad en la ingesta y registro de rechazos | Crítica |
| Controlar Calidad y Trazabilidad de la Ingesta | [HU-006](./epicas/epica-001/HU-006-bitacora-ejecuciones-ingesta/historia.md) | Bitácora de ejecuciones de ingesta | Crítica |
| Controlar Calidad y Trazabilidad de la Ingesta | [HU-007](./epicas/epica-001/HU-007-verificacion-ausencia-datos-sensibles/historia.md) | Verificación automática de ausencia de datos personales sensibles | Crítica |
| Identificar Candidatos a Televisor | [HU-008](./epicas/epica-001/HU-008-marcar-candidatos-secop-ii/historia.md) | Marcar candidatos a televisor en contratos SECOP II | Crítica |
| Identificar Candidatos a Televisor | [HU-009](./epicas/epica-001/HU-009-marcar-candidatos-tvec/historia.md) | Marcar candidatos a televisor en ítems de la TVEC | Crítica |
| Clasificar Ítems de Televisor | [HU-010](./epicas/epica-001/HU-010-clasificar-items-por-reglas/historia.md) | Clasificar ítems candidatos contra el límite de categoría por reglas | Crítica |
| Clasificar Ítems de Televisor | [HU-011](./epicas/epica-001/HU-011-clasificar-contratos-secop-mixtos/historia.md) | Clasificar contratos SECOP II y soportar contratos mixtos a nivel de ítem | Crítica |
| Clasificar Ítems de Televisor | [HU-012](./epicas/epica-001/HU-012-clasificacion-asistida-ia/historia.md) | Clasificación asistida por IA de candidatos que requieren revisión | Alta |
| Clasificar Ítems de Televisor | [HU-013](./epicas/epica-001/HU-013-revision-correccion-manual-clasificacion/historia.md) | Revisión y corrección manual de la clasificación de candidatos | Crítica |

📁 [Ver todas las HU de esta épica](./epicas/epica-001/)

---

### ÉPICA-002: De Documentos a Datos Comparables

**Prioridad**: Crítica  
**FRs cubiertos**: FR-018 a FR-025, FR-027 a FR-034, FR-099, FR-100

**Descripción**:
Resuelve el cuello de botella identificado en la tesis: en SECOP II, el precio unitario, la cantidad, la marca y el modelo **solo existen dentro de los documentos** del proceso. Esta épica obtiene los documentos por la URL oficial, prioriza los que sirven (ofertas, evaluaciones económicas, cotizaciones, contratos, estudios previos) y extrae los datos de cada ítem de televisor con IA, guardando el documento y la página de origen de cada dato.

Es el **primer incremento de IA** del producto y la principal fuente de riesgo técnico (~28 % de PDF escaneados en la muestra de D1, especificaciones genéricas sin modelo). Por eso incluye control de calidad: nivel de confianza, detección de inconsistencias aritméticas, marca de "información insuficiente" y revisión humana con historial de correcciones.

La extracción se puede desactivar sin afectar el resto del producto: la base determinística y la TVEC siguen operando.

**Capacidades Incluidas**:
- Listado y descarga de documentos por URL oficial, incluidos .zip y .rar.
- Priorización de documentos (estrategia inicial de ~8 relevantes por proceso, ajustable), incluidos anexos económicos y técnicos, precios techo y cotizaciones en ZIP; exclusión de formularios en blanco; deduplicación por hash; lote correcto.
- Detección de páginas sin capa de texto **y de imágenes incrustadas** en páginas con texto; OCR o lectura multimodal cuando haga falta.
- Extracción por ítem: descripción, marca, modelo, tamaño, resolución, tecnología, Smart, cantidad, precio unitario (`explicito` o `derivado`), total, IVA.
- Precio unitario **derivado** (total del ítem ÷ cantidad) solo bajo las 6 condiciones de FR-099; nunca en contratos mixtos ni con el valor de datos abiertos (FR-100).
- Umbral configurable de aceptación automática, calibrado en D4; datos críticos de confianza baja o incierta a revisión humana.
- Inconsistencias aritméticas tratadas como señales de revisión de calidad, no como irregularidades.
- Validación humana de los datos extraídos por el Administrador/Revisor (validar, corregir, rechazar).
- Registro de costo y tiempo por documento.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-CAL-001 / NFR-CAL-002: precisión ≥ 90 % con metodología definida.
- NFR-CAL-003: disponibilidad en la fuente (reporte), cobertura de extracción ≥ 80 % (provisional) y cobertura end-to-end (reporte).
- NFR-PER-004: ≤ 5 minutos por documento (p95).
- NFR-OBS-001: costo por documento visible.
- NFR-EVO-003: IA desactivable por configuración.

**Factores Críticos**:
- Dependencia del spike **D4** (precisión por campo, cobertura, costo, OCR/multimodal, disponibilidad de múltiples oferentes y calibración del umbral). El alcance de extracción para desarrollo se cierra definitivamente después de D4.
- **Resultado D4:** el límite principal es la **disponibilidad en la fuente** (~44–50 % de los contratos en categoría publica precio unitario), no la extracción. Multimodal necesario en ~52 % de los contratos; costo ≈ USD 0,05 por contrato (Sonnet 5.5, sin margen).
- Heterogeneidad documental: PDF nativos, escaneados con OCR ruidoso, XLSX, DOCX, imágenes y archivos comprimidos.
- La selección del modelo de IA y del servicio de OCR o multimodal se decide en arquitectura (Foundry u otra opción justificada técnicamente).
- Costo variable por documento: es uno de los principales drivers de costo.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye el agente de investigación (siguiente incremento agéntico, post-MVP).
- NO incluye la extracción y comparación de precios de **múltiples oferentes** (FR-026, pospuesta por D4 → ÉPICA-009).
- NO incluye la extracción de cláusulas contractuales, garantías ni condiciones de entrega.
- NO incluye procesar todos los documentos de cada proceso, solo los priorizados.
- NO incluye la extracción de categorías distintas a televisores.
- NO incluye la base de conocimiento RAG sobre los documentos.

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] Precisión ≥ 90 % sobre una muestra diversa de ≥ 50 documentos validados a mano, reportada global y por campo, sin que la global esconda un campo crítico débil.
- [ ] **Cobertura de extracción ≥ 80 %** (provisional, se calibra con D4-4) sobre los contratos SECOP II con información disponible en la fuente; **disponibilidad en la fuente** y **cobertura end-to-end** reportadas (TVEC aparte).
- [ ] El 100 % de los precios derivados conserva valor total, cantidad, fórmula, fuente, ubicación e indicador de derivado.
- [ ] El 100 % de los datos extraídos referencia documento y página (u hoja y celda).
- [ ] El 100 % de las correcciones humanas conserva el valor original, el usuario y la fecha.


---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** 17 historias
**Última actualización:** 2026-10-02

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
| Obtener y Priorizar Documentos del Proceso | [HU-014](./epicas/epica-002/HU-014-listar-documentos-proceso-candidato/historia.md) | Listar y registrar los documentos publicados de cada proceso candidato | Crítica |
| Obtener y Priorizar Documentos del Proceso | [HU-015](./epicas/epica-002/HU-015-priorizar-documentos-relevantes-proceso/historia.md) | Priorizar los documentos relevantes de cada proceso para la extracción | Crítica |
| Obtener y Priorizar Documentos del Proceso | [HU-016](./epicas/epica-002/HU-016-descargar-documentos-url-oficial/historia.md) | Descargar los documentos priorizados desde la URL oficial sin evadir restricciones | Crítica |
| Obtener y Priorizar Documentos del Proceso | [HU-017](./epicas/epica-002/HU-017-excluir-vacios-en-blanco-duplicados/historia.md) | Excluir documentos vacíos, formularios en blanco y duplicados | Crítica |
| Obtener y Priorizar Documentos del Proceso | [HU-018](./epicas/epica-002/HU-018-descomprimir-archivos-zip-rar/historia.md) | Descomprimir archivos ZIP y RAR y tratar su contenido como documentos del proceso | Crítica |
| Preparar Documentos para la Lectura | [HU-019](./epicas/epica-002/HU-019-leer-formatos-documentales-soportados/historia.md) | Leer los formatos documentales soportados y generar su representación con ubicaciones | Crítica |
| Preparar Documentos para la Lectura | [HU-020](./epicas/epica-002/HU-020-detectar-paginas-lectura-visual/historia.md) | Detectar las páginas que requieren OCR o lectura multimodal | Crítica |
| Preparar Documentos para la Lectura | [HU-021](./epicas/epica-002/HU-021-conservar-copia-evidencia-documental/historia.md) | Conservar la copia y la evidencia de los documentos de los que se extraen datos | Crítica |
| Extraer Datos de Ítems de Televisor | [HU-022](./epicas/epica-002/HU-022-extraer-items-televisor-con-evidencia/historia.md) | Extraer con IA los datos de cada ítem de televisor con su evidencia de origen | Crítica |
| Extraer Datos de Ítems de Televisor | [HU-023](./epicas/epica-002/HU-023-determinar-base-tributaria-precio/historia.md) | Determinar si cada precio extraído es con IVA, sin IVA o de base indeterminada | Crítica |
| Extraer Datos de Ítems de Televisor | [HU-024](./epicas/epica-002/HU-024-calcular-precio-unitario-derivado/historia.md) | Calcular el precio unitario derivado solo cuando se cumplen las seis condiciones | Crítica |
| Extraer Datos de Ítems de Televisor | [HU-025](./epicas/epica-002/HU-025-marcar-items-informacion-insuficiente/historia.md) | Marcar los ítems con información insuficiente indicando el motivo | Crítica |
| Controlar la Calidad de la Extracción | [HU-026](./epicas/epica-002/HU-026-aplicar-umbral-aceptacion-automatica/historia.md) | Aplicar el umbral configurable de aceptación automática y dirigir a revisión los datos dudosos | Crítica |
| Controlar la Calidad de la Extracción | [HU-027](./epicas/epica-002/HU-027-detectar-inconsistencias-aritmeticas/historia.md) | Detectar inconsistencias aritméticas en los datos extraídos y dirigirlas a revisión de calidad | Crítica |
| Controlar la Calidad de la Extracción | [HU-028](./epicas/epica-002/HU-028-revisar-datos-extraidos-item/historia.md) | Validar, corregir o rechazar los datos extraídos de un ítem conservando el historial | Crítica |
| Operar y Medir la Extracción con IA | [HU-029](./epicas/epica-002/HU-029-desactivar-extraccion-ia-configuracion/historia.md) | Activar o desactivar la extracción con IA por configuración sin afectar las funciones determinísticas | Crítica |
| Operar y Medir la Extracción con IA | [HU-030](./epicas/epica-002/HU-030-registrar-costo-tiempo-extraccion/historia.md) | Registrar el costo estimado y el tiempo de procesamiento de la extracción por documento | Alta |

📁 [Ver todas las HU de esta épica](./epicas/epica-002/)

---

### ÉPICA-003: Normalización y Emparejamiento de Televisores

**Prioridad**: Crítica  
**FRs cubiertos**: FR-035 a FR-040

**Descripción**:
Hace comparables televisores descritos de formas muy distintas: un estudio previo pide "65 pulgadas, 4K, Smart"; la TVEC registra "GSF01-TELEVISOR SAMSUNG FLAT LED CRYSTAL SMART TV 55"; Alkosto publica un nombre comercial con su EAN. Esta épica lleva todo a un esquema común y empareja productos como **mismo modelo** o **equivalentes**, con criterios visibles.

Es la base de la credibilidad del producto: una mala equivalencia produce falsos positivos (riesgo R2). La regla de la Adenda 2 aplica sin excepción: **nunca se relajan los criterios para forzar una referencia**.

**Capacidades Incluidas**:
- Esquema común: marca, modelo normalizado, tamaño, resolución, tecnología, Smart, generación.
- Normalización **sintáctica** de modelos (espacios, guiones, mayúsculas, formatos equivalentes), sin eliminar componentes del código que puedan ser variantes técnicas (ej. sufijos regionales).
- Emparejamiento por modelo exacto o EAN.
- Emparejamiento por equivalencia de características; referencias distintas solo se tratan como equivalentes si las características técnicas lo sustentan.
- Clasificación visible del emparejamiento con sus criterios.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-CAL-005: 100 % de las comparaciones clasificadas.
- NFR-EVO-002: nuevas categorías por configuración de reglas de equivalencia.

**Factores Críticos**:
- Solo el 36 % de las líneas TVEC traen código de modelo; los documentos de SECOP II rara vez traen modelo.
- Las variantes por sufijo regional reducen las coincidencias de "mismo modelo" y aumentan la dependencia de la equivalencia.
- Definir las reglas de equivalencia (qué características deben coincidir) requiere conocimiento del dominio y validación con el PO.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] El 100 % de los ítems comparados tiene clasificación de emparejamiento y criterios visibles.
- [ ] En una muestra de 50 emparejamientos revisados a mano, ≥ 95 % de los "mismo modelo" y ≥ 90 % de los "equivalentes" son correctos.
- [ ] Ningún emparejamiento usa criterios por debajo de los configurados.


---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** 11 historias
**Última actualización:** 2026-10-02

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
| Normalizar Atributos al Esquema Común | [HU-031](./epicas/epica-003/HU-031-normalizar-marca-tamano-resolucion/historia.md) | Normalizar marca, tamaño y resolución al esquema común | Crítica |
| Normalizar Atributos al Esquema Común | [HU-032](./epicas/epica-003/HU-032-normalizar-tecnologia-smart-generacion/historia.md) | Normalizar tecnología de pantalla, Smart y generación del televisor | Crítica |
| Normalizar Códigos de Modelo | [HU-033](./epicas/epica-003/HU-033-identificar-codigo-modelo-origen/historia.md) | Identificar el código de modelo en el registro de origen | Crítica |
| Normalizar Códigos de Modelo | [HU-034](./epicas/epica-003/HU-034-normalizar-sintaxis-codigo-modelo/historia.md) | Normalizar sintácticamente el código de modelo | Crítica |
| Emparejar por Mismo Modelo | [HU-035](./epicas/epica-003/HU-035-emparejar-mismo-modelo-marca-modelo/historia.md) | Emparejar como mismo modelo por marca y modelo normalizado | Crítica |
| Emparejar por Mismo Modelo | [HU-036](./epicas/epica-003/HU-036-emparejar-mismo-modelo-ean-gtin/historia.md) | Emparejar como mismo modelo por EAN/GTIN | Crítica |
| Emparejar por Equivalencia Técnica | [HU-037](./epicas/epica-003/HU-037-configurar-reglas-equivalencia/historia.md) | Configurar las reglas de equivalencia por categoría | Crítica |
| Emparejar por Equivalencia Técnica | [HU-038](./epicas/epica-003/HU-038-emparejar-productos-equivalentes/historia.md) | Emparejar productos equivalentes por características técnicas | Crítica |
| Clasificar y Explicar el Emparejamiento | [HU-039](./epicas/epica-003/HU-039-clasificar-resultado-emparejamiento/historia.md) | Clasificar el resultado de emparejamiento de cada ítem | Crítica |
| Clasificar y Explicar el Emparejamiento | [HU-040](./epicas/epica-003/HU-040-consultar-criterios-emparejamiento/historia.md) | Consultar los criterios de emparejamiento de un ítem | Crítica |
| Clasificar y Explicar el Emparejamiento | [HU-041](./epicas/epica-003/HU-041-verificar-criterios-no-relajados/historia.md) | Verificar que ningún emparejamiento use criterios relajados | Crítica |

📁 [Ver todas las HU de esta épica](./epicas/epica-003/)

---

### ÉPICA-004: Referencias de Mercado Trazables

**Prioridad**: Crítica  
**FRs cubiertos**: FR-041 a FR-053

**Descripción**:
Implementa la **base propia de observaciones de mercado** de la Adenda 2, separando cómo se consigue un precio de cómo se usa. Cada observación guarda su trazabilidad mínima y su **método de adquisición**. Las observaciones de Alkosto (principal) y Falabella (secundaria) pueden llegar por captura automática, **cuando exista un mecanismo permitido y viable** (sitemaps, datos estructurados u otros aprobados), o por carga manual o semiautomática. **La automatización completa no es condición de éxito del MVP** y su indisponibilidad no bloquea el Benchmark 2.

El valor es que el Benchmark 2 deja de depender de que exista una API comercial: el MVP puede validar la comparación con mercado aunque la automatización sea parcial, y la base acumula desde el primer día el **histórico propio** de precios que el mercado no publica.

Incluye las salvaguardas de cumplimiento: solo vendedor = la tienda, precio efectivo (no tachado), marca de precios condicionados, suspensión automática ante bloqueos o cambios de `robots.txt`, y un protocolo contra el sesgo en la carga manual.

**Capacidades Incluidas**:
- Captura automática de Alkosto y Falabella cuando sea permitida y viable (configuración inicial: semanal; ritmo y volumen como parámetros configurables).
- Filtro de vendedor = la tienda.
- Precio efectivo, con el precio anterior como evidencia; marca de precios condicionados.
- Suspensión automática y alerta ante CAPTCHA, bloqueo o cambio de `robots.txt`.
- Carga manual individual con evidencia adjunta y registro del usuario.
- Carga semiautomática por archivo CSV.
- Registro de todas las ofertas encontradas y los términos de búsqueda (protocolo contra sesgo).
- Histórico inmutable de observaciones.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-CUM-002 a NFR-CUM-006: `robots.txt`, ritmo de solicitudes, User-Agent, cero evasión, términos de uso antes de producción.
- NFR-DAT-003: captura semanal.
- NFR-DIS-003: la base de observaciones entra en el respaldo.
- NFR-EVO-001: nuevas fuentes solo con un nuevo conector.

**Factores Críticos**:
- Términos de uso de Alkosto y Falabella sin verificar (D6): bloqueo para producción, no para el MVP de validación.
- Cambios en la estructura de los datos publicados pueden romper la captura sin aviso.
- La carga manual depende de tiempo humano del Administrador.
- Los límites de ritmo y volumen son parámetros iniciales sujetos a términos de uso, `robots.txt`, comportamiento de la fuente y validación técnica.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] El 100 % de las observaciones tiene el registro mínimo completo, incluido el método de adquisición.
- [ ] El 100 % de las observaciones manuales se muestran como manuales.
- [ ] Si hay captura automática, se suspende sola en una prueba que simula bloqueo o cambio de `robots.txt`.
- [ ] El Benchmark 2 funciona con observaciones cargadas a mano aunque ninguna fuente esté automatizada.
- [ ] Una carga CSV de prueba con 100 observaciones se procesa con validación campo a campo.


---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** 12 historias
**Última actualización:** 2026-10-02

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
| Gestionar Base de Observaciones de Mercado | [HU-042](./epicas/epica-004/HU-042-almacenar-observaciones-mercado/historia.md) | Almacenar observaciones de precio de mercado con registro mínimo trazable | Crítica |
| Gestionar Base de Observaciones de Mercado | [HU-043](./epicas/epica-004/HU-043-conservar-historico-observaciones/historia.md) | Conservar el histórico inmutable de observaciones de mercado | Crítica |
| Aplicar Reglas de Precio de Referencia | [HU-044](./epicas/epica-004/HU-044-filtrar-vendedor-tienda/historia.md) | Aceptar solo observaciones cuyo vendedor sea directamente la tienda | Crítica |
| Aplicar Reglas de Precio de Referencia | [HU-045](./epicas/epica-004/HU-045-registrar-precio-efectivo/historia.md) | Usar el precio efectivo de venta y conservar el precio anterior solo como evidencia | Crítica |
| Aplicar Reglas de Precio de Referencia | [HU-046](./epicas/epica-004/HU-046-marcar-precios-condicionados/historia.md) | Identificar y marcar precios sujetos a condiciones especiales | Crítica |
| Cargar Observaciones Manual y Semiautomáticamente | [HU-047](./epicas/epica-004/HU-047-registrar-observacion-manual/historia.md) | Registrar manualmente una observación de precio con evidencia adjunta | Crítica |
| Cargar Observaciones Manual y Semiautomáticamente | [HU-048](./epicas/epica-004/HU-048-registrar-busqueda-manual-completa/historia.md) | Registrar una búsqueda manual con todas las ofertas comparables y sus términos | Crítica |
| Cargar Observaciones Manual y Semiautomáticamente | [HU-049](./epicas/epica-004/HU-049-cargar-observaciones-csv/historia.md) | Cargar observaciones de precio de forma semiautomática con un archivo CSV | Crítica |
| Capturar Precios Automáticamente con Salvaguardas | [HU-050](./epicas/epica-004/HU-050-ejecutar-captura-automatica-controlada/historia.md) | Ejecutar la captura automática controlada de una fuente retail | Alta |
| Capturar Precios Automáticamente con Salvaguardas | [HU-051](./epicas/epica-004/HU-051-capturar-precios-alkosto/historia.md) | Capturar observaciones de Alkosto desde su sitemap y datos estructurados | Alta |
| Capturar Precios Automáticamente con Salvaguardas | [HU-052](./epicas/epica-004/HU-052-capturar-precios-falabella/historia.md) | Capturar observaciones de Falabella con vendedor = Falabella desde sitemaps y datos estructurados | Alta |
| Capturar Precios Automáticamente con Salvaguardas | [HU-053](./epicas/epica-004/HU-053-suspender-captura-ante-bloqueo/historia.md) | Suspender la captura automática y notificar ante CAPTCHA, bloqueo, autenticación o cambio de robots.txt | Alta |

📁 [Ver todas las HU de esta épica](./epicas/epica-004/)

---

### ÉPICA-005: Señales que Merecen Revisión, con Evidencia

**Prioridad**: Crítica  
**FRs cubiertos**: FR-054 a FR-070

**Descripción**:
Es el corazón de la propuesta de valor: compara el precio unitario de cada televisor contra el **Benchmark 1 (compras públicas: SECOP II + TVEC)** y el **Benchmark 2 (mercado)**, con reglas de temporalidad, base tributaria y emparejamiento, y produce una **"señal que merece revisión"** cuando la desviación lo justifica.

Cada señal lleva su evidencia completa (benchmark, observaciones, fórmula, desviación, emparejamiento, IVA, métodos de adquisición, fecha de corte, confianza) y permite navegar hasta el documento y la página de origen. Nunca usa lenguaje acusatorio. El Benchmark 2 se degrada a "no disponible" sin bloquear el Benchmark 1.

La épica también recoge la calificación del analista sobre cada señal, que es el insumo del KPI de validación humana, y un mecanismo para reportar errores.

**Capacidades Incluidas**:
- Benchmark 1 con distribución de precios públicos comparables en una ventana temporal.
- Benchmark 2 con observaciones retail cercanas a la fecha, o "referencia de mercado disponible", o "no disponible".
- Comparación solo en la misma base tributaria.
- Referencia estadística agregada (ej. mediana).
- Generación de señales con estrategia híbrida configurable (atípicos Q3 + 1,5 × IQR con muestra suficiente; si no, +30 % mismo modelo / +50 % equivalente), solo para **priorizar** revisión.
- Solo desviaciones por encima generan señal; los precios anormalmente bajos van a revisión de calidad.
- Evidencia navegable hasta el documento y la página.
- Calificación de la señal por el analista y reporte de errores.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-CAL-004: trazabilidad 100 %.
- FR-068: un precio `derivado` reduce la confianza de la señal frente a uno `explicito`.
- NFR-CAL-006: 0 comparaciones mezclando IVA sin marca.
- NFR-CAL-007: ≥ 70 % de señales calificadas como sustentadas.
- NFR-CUM-007: 0 términos acusatorios.
- NFR-PER-002: detalle de señal en ≤ 3 s.

**Factores Críticos**:
- Parámetros analíticos con configuración inicial aprobada (P-01 a P-04: ventanas ±6/±12 meses y ±30 días; mínimos ≥ 5 y ≥ 3 de 2 fuentes; estrategia híbrida de señal; solo desviación al alza). Son configurables y se recalibran con evidencia real.
- Revisión de la Ecuación 2 de la tesis: no se usa un promedio simple por entidad.
- IVA de la TVEC no determinado: tarea de verificación **INV-01** antes de cerrar la arquitectura analítica. Hasta verificarlo, esas comparaciones se marcan como incompletas/no confiables.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje de sobreprecio o corrupción.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] El 100 % de las señales muestra benchmark, observaciones, fórmula, emparejamiento, IVA, métodos de adquisición y confianza.
- [ ] Desde cualquier señal se llega a la evidencia de origen en ≤ 3 clics.
- [ ] Sin referencia retail confiable, el Benchmark 2 aparece como "no disponible" y el Benchmark 1 se calcula igual.
- [ ] ≥ 3 usuarios del perfil de diseño califican señales; ≥ 70 % se califican como sustentadas.


---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** 15 historias
**Última actualización:** 2026-10-02

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
| Selección de Comparables | [HU-054](./epicas/epica-005/HU-054-seleccionar-comparables-benchmark-1/historia.md) | Seleccionar comparables públicos del Benchmark 1 con ventana temporal configurable | Crítica |
| Selección de Comparables | [HU-055](./epicas/epica-005/HU-055-seleccionar-observaciones-benchmark-2/historia.md) | Seleccionar observaciones retail del Benchmark 2 cercanas a la fecha de la compra | Crítica |
| Selección de Comparables | [HU-056](./epicas/epica-005/HU-056-homologar-base-tributaria-iva/historia.md) | Homologar la base tributaria (IVA) y marcar comparaciones incompletas | Crítica |
| Cálculo de Benchmarks | [HU-057](./epicas/epica-005/HU-057-calcular-benchmark-1-compras-publicas/historia.md) | Calcular el Benchmark 1 – Contratación pública y la desviación del precio contratado | Crítica |
| Cálculo de Benchmarks | [HU-058](./epicas/epica-005/HU-058-calcular-benchmark-2-mercado/historia.md) | Calcular el Benchmark 2 – Mercado con degradación a "no disponible" | Crítica |
| Generación y Confianza de Señales | [HU-059](./epicas/epica-005/HU-059-generar-senal-desviacion-al-alza/historia.md) | Generar la «señal que merece revisión» por desviación al alza con regla híbrida configurable | Crítica |
| Generación y Confianza de Señales | [HU-060](./epicas/epica-005/HU-060-enviar-precios-bajos-revision-calidad/historia.md) | Dirigir los precios anormalmente bajos a la cola de revisión de calidad | Crítica |
| Generación y Confianza de Señales | [HU-061](./epicas/epica-005/HU-061-calcular-confianza-de-la-senal/historia.md) | Calcular el nivel de confianza de la comparación y de la señal | Crítica |
| Presentación de Evidencia Trazable | [HU-062](./epicas/epica-005/HU-062-registrar-evidencia-de-la-senal/historia.md) | Registrar la evidencia completa y reproducible de cada señal | Crítica |
| Presentación de Evidencia Trazable | [HU-063](./epicas/epica-005/HU-063-ver-detalle-de-la-senal/historia.md) | Ver el detalle de una señal con su comparación, su evidencia y la advertencia de no conclusión | Crítica |
| Presentación de Evidencia Trazable | [HU-064](./epicas/epica-005/HU-064-navegar-a-evidencia-de-origen/historia.md) | Navegar desde la señal hasta el contrato, el documento y la página de origen, y cada observación de referencia | Crítica |
| Presentación de Evidencia Trazable | [HU-065](./epicas/epica-005/HU-065-garantizar-lenguaje-no-acusatorio/historia.md) | Garantizar lenguaje no acusatorio en todos los textos generados por el sistema | Crítica |
| Validación Humana de Señales | [HU-066](./epicas/epica-005/HU-066-calificar-senal-sustentada/historia.md) | Calificar una señal como suficientemente sustentada para merecer revisión | Crítica |
| Validación Humana de Señales | [HU-067](./epicas/epica-005/HU-067-reportar-error-dato-o-senal/historia.md) | Reportar un error en un dato o en una señal | Crítica |
| Validación Humana de Señales | [HU-068](./epicas/epica-005/HU-068-gestionar-reportes-de-error/historia.md) | Gestionar los reportes de error y registrar su resolución | Crítica |

📁 [Ver todas las HU de esta épica](./epicas/epica-005/)

---

### ÉPICA-006: Exploración y Ficha del Contrato

**Prioridad**: Crítica  
**FRs cubiertos**: FR-071 a FR-076

**Descripción**:
Da al analista la puerta de entrada: buscar, filtrar y ordenar contratos e ítems de televisor, ver la **lista priorizada de señales** y abrir la **ficha del contrato** con sus datos, ítems extraídos, benchmarks, señales, documentos, estado de procesamiento y enlace a la fuente oficial.

Es la base determinística del producto: funciona sin IA sobre los datos estructurados y los ya extraídos.

**Capacidades Incluidas**:
- Búsqueda y filtros por entidad, proveedor, modalidad, fechas, UNSPSC, territorio, valor, fuente y señal.
- Ordenamiento por desviación, valor, fecha o confianza.
- Lista priorizada de señales.
- Ficha de contrato con estado de procesamiento y motivos de información insuficiente.
- Fecha de actualización visible.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-PER-001 / NFR-PER-002 / NFR-PER-003: ≤ 3 s p95 con 20 usuarios concurrentes.
- NFR-USA-001 a NFR-USA-004: desktop-first, responsive, navegadores, WCAG AA.

**Factores Críticos**:
- Visualizaciones de distribución de precios, que son claves para entender el Benchmark 1.
- Experiencia desktop-first con versión funcional en tablet y móvil.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] Todos los filtros de FR-071 funcionan y combinan.
- [ ] Búsqueda y ficha responden en ≤ 3 s p95 con 20 usuarios concurrentes.
- [ ] La ficha muestra el estado de procesamiento y los motivos de información insuficiente del 100 % de los contratos.


---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** 15 historias
**Última actualización:** 2026-10-02

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
| Búsqueda y Filtrado de Compras | [HU-069](./epicas/epica-006/HU-069-explorar-compras-de-televisores/historia.md) | Explorar el listado de compras públicas de televisores | Crítica |
| Búsqueda y Filtrado de Compras | [HU-070](./epicas/epica-006/HU-070-filtrar-por-entidad-proveedor-modalidad/historia.md) | Filtrar la exploración por entidad, proveedor y modalidad | Crítica |
| Búsqueda y Filtrado de Compras | [HU-071](./epicas/epica-006/HU-071-filtrar-por-fechas-valor-y-unspsc/historia.md) | Filtrar la exploración por fechas, rango de valor y UNSPSC | Crítica |
| Búsqueda y Filtrado de Compras | [HU-072](./epicas/epica-006/HU-072-filtrar-por-territorio-fuente-y-senal/historia.md) | Filtrar la exploración por territorio, fuente y existencia de señal | Crítica |
| Búsqueda y Filtrado de Compras | [HU-073](./epicas/epica-006/HU-073-ordenar-resultados-de-exploracion/historia.md) | Ordenar los resultados de la exploración por desviación, valor, fecha o confianza | Crítica |
| Priorización de Señales | [HU-074](./epicas/epica-006/HU-074-ver-lista-priorizada-de-senales/historia.md) | Ver la lista priorizada de señales que merecen revisión | Crítica |
| Priorización de Señales | [HU-075](./epicas/epica-006/HU-075-filtrar-y-ordenar-lista-de-senales/historia.md) | Filtrar y ordenar la lista de señales que merecen revisión | Crítica |
| Consulta de la Ficha del Contrato | [HU-076](./epicas/epica-006/HU-076-ver-datos-clave-de-la-ficha/historia.md) | Ver los datos clave del contrato y el enlace a la fuente oficial en la ficha | Crítica |
| Consulta de la Ficha del Contrato | [HU-077](./epicas/epica-006/HU-077-ver-items-de-televisor-en-la-ficha/historia.md) | Ver los ítems de televisor extraídos en la ficha del contrato | Crítica |
| Consulta de la Ficha del Contrato | [HU-078](./epicas/epica-006/HU-078-ver-benchmarks-del-item-en-la-ficha/historia.md) | Ver los benchmarks de cada ítem con la distribución de precios comparables en la ficha | Crítica |
| Consulta de la Ficha del Contrato | [HU-079](./epicas/epica-006/HU-079-ver-senales-del-contrato-en-la-ficha/historia.md) | Ver las señales que merecen revisión del contrato en la ficha | Crítica |
| Consulta de la Ficha del Contrato | [HU-080](./epicas/epica-006/HU-080-ver-documentos-del-proceso-en-la-ficha/historia.md) | Ver los documentos del proceso en la ficha del contrato | Crítica |
| Seguimiento del Procesamiento y Frescura de Datos | [HU-081](./epicas/epica-006/HU-081-ver-estado-de-procesamiento/historia.md) | Ver el estado de procesamiento del contrato en la ficha | Crítica |
| Seguimiento del Procesamiento y Frescura de Datos | [HU-082](./epicas/epica-006/HU-082-ver-motivos-informacion-insuficiente/historia.md) | Ver los motivos de información insuficiente del contrato en la ficha | Crítica |
| Seguimiento del Procesamiento y Frescura de Datos | [HU-083](./epicas/epica-006/HU-083-mostrar-fecha-de-actualizacion-datos/historia.md) | Mostrar la fecha de actualización de los datos en la exploración y en la ficha | Crítica |

📁 [Ver todas las HU de esta épica](./epicas/epica-006/)

---

### ÉPICA-007: Espacio de Investigación del Analista

**Prioridad**: Crítica  
**FRs cubiertos**: FR-077 a FR-087

**Descripción**:
Permite al analista convertir señales en investigaciones: crear casos, guardar señales, contratos y evidencias, escribir notas y retomar el trabajo después. Los casos son privados y guardan una instantánea de la evidencia, de modo que no cambian si se recalculan los benchmarks.

Incluye el registro, inicio de sesión, recuperación de contraseña, roles Analista/Administrador y la aceptación de términos y de la política de datos, que son requisitos de la decisión de acceso con login.

**Capacidades Incluidas**:
- Registro **por invitación**, login, logout y recuperación de contraseña.
- Roles Analista y Administrador.
- Aceptación de términos de uso y política de tratamiento de datos.
- Creación de casos desde una señal o un contrato.
- Guardar señales, contratos y evidencias en un caso, con instantánea.
- Notas por caso.
- Lista de casos propios y reanudación.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-SEG-001 a NFR-SEG-004: HTTPS, hash de contraseñas, expiración de sesión, acceso solo del autor.
- NFR-CUM-001: política de tratamiento de datos publicada antes de abrir el registro.

**Factores Críticos**:
- Registro por invitación durante discovery/piloto, sin registro público (P-12). La expiración de sesión (30 min inicial) es configurable.
- Datos personales de los usuarios registrados sujetos a la Ley 1581/2012.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] Un analista crea un caso desde una señal, agrega notas, cierra sesión y lo retoma intacto.
- [ ] Las pruebas de autorización confirman que ningún usuario accede a casos ajenos.
- [ ] La evidencia guardada en un caso no cambia tras recalcular los benchmarks.


---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** 14 historias
**Última actualización:** 2026-10-02

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
| Gestionar Acceso por Invitación | [HU-084](./epicas/epica-007/HU-084-emitir-invitacion-registro-analista/historia.md) | Emitir invitación de registro para un Analista | Crítica |
| Gestionar Acceso por Invitación | [HU-085](./epicas/epica-007/HU-085-registrar-cuenta-analista-por-invitacion/historia.md) | Registrar cuenta de Analista mediante invitación con aceptación de términos y política de datos | Crítica |
| Autenticar y Proteger la Sesión | [HU-086](./epicas/epica-007/HU-086-iniciar-sesion-correo-contrasena/historia.md) | Iniciar sesión con correo y contraseña | Crítica |
| Autenticar y Proteger la Sesión | [HU-087](./epicas/epica-007/HU-087-cerrar-sesion-y-expirar-por-inactividad/historia.md) | Cerrar sesión y expirar la sesión por inactividad | Crítica |
| Autenticar y Proteger la Sesión | [HU-088](./epicas/epica-007/HU-088-recuperar-contrasena-por-correo/historia.md) | Recuperar la contraseña por correo electrónico | Crítica |
| Autenticar y Proteger la Sesión | [HU-089](./epicas/epica-007/HU-089-aplicar-roles-analista-administrador/historia.md) | Aplicar los roles Analista y Administrador con permisos diferenciados | Crítica |
| Crear y Organizar Casos de Investigación | [HU-090](./epicas/epica-007/HU-090-crear-caso-desde-senal/historia.md) | Crear un caso de investigación desde una señal | Crítica |
| Crear y Organizar Casos de Investigación | [HU-091](./epicas/epica-007/HU-091-crear-caso-desde-contrato/historia.md) | Crear un caso de investigación desde un contrato | Crítica |
| Crear y Organizar Casos de Investigación | [HU-092](./epicas/epica-007/HU-092-guardar-elementos-en-caso-existente/historia.md) | Guardar señales, contratos y evidencias en un caso existente | Crítica |
| Documentar Casos con Notas | [HU-093](./epicas/epica-007/HU-093-agregar-nota-a-caso/historia.md) | Agregar notas a un caso | Crítica |
| Documentar Casos con Notas | [HU-094](./epicas/epica-007/HU-094-editar-y-eliminar-notas-de-caso/historia.md) | Editar y eliminar notas de un caso | Crítica |
| Consultar y Retomar Casos Propios | [HU-095](./epicas/epica-007/HU-095-listar-mis-casos/historia.md) | Listar mis casos de investigación | Crítica |
| Consultar y Retomar Casos Propios | [HU-096](./epicas/epica-007/HU-096-abrir-y-retomar-caso-con-instantanea/historia.md) | Abrir y retomar un caso con su evidencia conservada como instantánea | Crítica |
| Consultar y Retomar Casos Propios | [HU-097](./epicas/epica-007/HU-097-restringir-acceso-casos-a-su-autor/historia.md) | Restringir el acceso a casos, elementos y notas únicamente a su autor | Crítica |

📁 [Ver todas las HU de esta épica](./epicas/epica-007/)

---

### ÉPICA-008: Operación, Calidad y Medición del MVP

**Prioridad**: Alta  
**FRs cubiertos**: FR-088 a FR-094

**Descripción**:
Da al Administrador (el PO en el MVP) el control para operar y **medir** el MVP: estado de las fuentes, relanzamiento de ingestas, parámetros analíticos configurables, cola de revisión humana, muestra de validación y tablero de KPIs (precisión, cobertura, trazabilidad, comparabilidad, señales sustentadas y tiempo por caso).

Sin esta épica el MVP funcionaría, pero no podría demostrar que cumple sus criterios de éxito. Por eso es Alta y no Crítica: no bloquea el flujo del analista, pero sí la validación del producto.

**Implementación en el MVP:** el PO es Administrador y Revisor. Estas capacidades **no requieren necesariamente interfaz gráfica**: pueden resolverse con configuración, logs, scripts, consultas, herramientas técnicas o interfaces administrativas mínimas, siempre que el requisito se cumpla y quede trazabilidad. La arquitectura y las HUs definen cuáles necesitan UI.

**Capacidades Incluidas**:
- Visibilidad del estado de las fuentes (última ingesta, errores, suspensiones) y relanzamiento.
- Configuración de términos de búsqueda, ventanas temporales, mínimos de observaciones, reglas y umbrales de señal, umbral de aceptación automática y frecuencias.
- Cola de revisión humana.
- Marcado de la muestra de validación de extracción.
- KPIs del MVP (precisión global y por campo, cobertura sobre SECOP II, trazabilidad, comparabilidad, señales sustentadas).
- Medición del tiempo por caso.
- Log de auditoría.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-OBS-001 a NFR-OBS-003: costos por componente, alertas en ≤ 1 h, logs 30 días.
- NFR-SEG-007: auditoría 12 meses.

**Factores Críticos**:
- La medición del tiempo por caso requiere la línea base manual del discovery (D2).
- Los parámetros analíticos configurables deben versionarse para reproducir señales pasadas.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] Los KPIs se calculan con las fórmulas del PRD a partir de datos reales (por tablero, consulta o script).
- [ ] Cada cambio de configuración queda en el log de auditoría con usuario, fecha y valor anterior.
- [ ] Una ingesta fallida genera alerta en ≤ 1 hora.


---

## 📋 Historias de Usuario Generadas

**Estado:** ✅ Generadas (modo automático, autorizado por el PO)
**Total HU:** 16 historias
**Última actualización:** 2026-10-02

### Descomposición en Features:

| Feature | HU | Título | Prioridad |
|---|---|---|---|
| Operar Fuentes de Datos | [HU-098](./epicas/epica-008/HU-098-consultar-estado-fuentes/historia.md) | Consultar el estado de las fuentes de datos | Alta |
| Operar Fuentes de Datos | [HU-099](./epicas/epica-008/HU-099-relanzar-ingesta-o-captura/historia.md) | Relanzar una ingesta o captura y reactivar una fuente suspendida | Alta |
| Operar Fuentes de Datos | [HU-100](./epicas/epica-008/HU-100-alertar-fallas-ingesta-captura/historia.md) | Alertar al Administrador ante una ingesta o captura fallida o retrasada | Alta |
| Configurar Parámetros del Análisis | [HU-101](./epicas/epica-008/HU-101-configurar-parametros-comparacion-senal/historia.md) | Configurar y versionar los parámetros de comparación y señal | Alta |
| Configurar Parámetros del Análisis | [HU-102](./epicas/epica-008/HU-102-configurar-parametros-operativos/historia.md) | Configurar términos de búsqueda, umbral de aceptación de extracción y frecuencias | Alta |
| Gestionar Revisión y Muestra de Validación | [HU-103](./epicas/epica-008/HU-103-consultar-cola-revision-humana/historia.md) | Consultar la cola de revisión humana | Alta |
| Gestionar Revisión y Muestra de Validación | [HU-104](./epicas/epica-008/HU-104-marcar-muestra-validacion/historia.md) | Marcar contratos y documentos de la muestra de validación manual | Alta |
| Gestionar Revisión y Muestra de Validación | [HU-105](./epicas/epica-008/HU-105-registrar-resultados-validacion/historia.md) | Generar la plantilla de validación y cargar los resultados verificados | Alta |
| Medir KPIs del MVP | [HU-106](./epicas/epica-008/HU-106-calcular-precision-extraccion/historia.md) | Calcular la precisión de la extracción, global y por campo | Alta |
| Medir KPIs del MVP | [HU-107](./epicas/epica-008/HU-107-calcular-indicadores-cobertura/historia.md) | Calcular los tres indicadores de cobertura sobre SECOP II, con TVEC aparte | Alta |
| Medir KPIs del MVP | [HU-108](./epicas/epica-008/HU-108-calcular-kpis-trazabilidad-comparabilidad/historia.md) | Verificar trazabilidad de señales, clasificación de comparaciones y base tributaria | Alta |
| Medir KPIs del MVP | [HU-109](./epicas/epica-008/HU-109-registrar-tiempo-por-caso/historia.md) | Registrar el tiempo que el Analista dedica a cada señal | Alta |
| Medir KPIs del MVP | [HU-110](./epicas/epica-008/HU-110-calcular-kpis-validacion-eficiencia/historia.md) | Calcular los KPIs de señales sustentadas y de eficiencia por caso | Alta |
| Medir KPIs del MVP | [HU-111](./epicas/epica-008/HU-111-consultar-costos-operacion/historia.md) | Consultar el costo por documento procesado con IA y el costo mensual por componente | Alta |
| Auditar Acciones Administrativas | [HU-112](./epicas/epica-008/HU-112-registrar-log-auditoria/historia.md) | Registrar el log de auditoría y aplicar la retención de logs | Alta |
| Auditar Acciones Administrativas | [HU-113](./epicas/epica-008/HU-113-consultar-log-auditoria/historia.md) | Consultar y exportar el log de auditoría | Alta |

📁 [Ver todas las HU de esta épica](./epicas/epica-008/)

---

### ÉPICA-009: Contexto Ampliado y Capacidades Pospuestas

**Prioridad**: Media (Post-MVP)  
**FRs cubiertos**: FR-026, FR-095 a FR-098

**Descripción**:
Agrupa las **candidatas a validar en el PRD** que definió el Brief (fichas de entidad y de proveedor, señales que no son de precio y exportación del expediente de caso) y la **extracción y comparación de precios de múltiples oferentes** (FR-026), pospuesta por D4 porque solo ~10 % de los procesos publica precio unitario por oferente.

**Conclusión del PRD:** ninguna es necesaria para el flujo principal (*contrato → televisor → normalización → referencias → comparación → señal → evidencia trazable*). La evidencia se consulta en la plataforma y se conserva en el caso, sin necesidad de exportarla. Por eso quedan **Post-MVP**. Se recomienda reevaluar la exportación del expediente con el feedback de D5 (mockups), porque es la forma natural de llevar un caso a una veeduría o un medio.

**Capacidades Incluidas**:
- Ficha de entidad con su contratación de televisores e indicadores.
- Ficha de proveedor con sus contratos e indicadores.
- Señales de concentración, contratación directa y presupuesto vs. contratado.
- Exportación del expediente de caso.
- Extracción y comparación de precios de múltiples oferentes de un proceso (FR-026); se reincorpora si aparece una fuente o tipo documental donde sea sistemática.

**NFRs Críticos que Impactan Esta Épica**:
- NFR-CUM-007: lenguaje no acusatorio, especialmente en fichas de proveedor.
- NFR-SEG-005: sin datos personales sensibles en fichas de proveedor persona natural.

**Factores Críticos**:
- Las fichas de proveedor y las señales de concentración aumentan el riesgo legal y reputacional (R3) y se acercan a los "rankings de riesgo" excluidos.

**Exclusiones Explícitas** (prevención scope creep):
- NO incluye rankings de riesgo de entidades ni de proveedores.
- NO incluye publicación abierta de expedientes.
- NO incluye la integración con Proveedores Registrados ni con Multas y Sanciones de SECOP.

**Criterios de Aceptación de Épica** (alto nivel):
- [ ] Se reevalúa su prioridad con los resultados de D5.
- [ ] Antes de construir fichas de proveedor, existe revisión jurídica del lenguaje.
- [ ] Ninguna señal no basada en precio usa lenguaje acusatorio.

---

## Notas sobre Épicas

- **Prioridades**: Crítica (MVP core) | Alta (MVP extendido) | Media (Fase 2) | Baja (Futuro)
- **FRs cubiertos**: Referencia a Requerimientos Funcionales del PRD
- **Factores críticos**: Elementos que incrementan complejidad o riesgo
- **Exclusiones explícitas**: Prevención de scope creep - qué NO incluye cada épica

---

**Próximo Paso**: Validaciones pendientes (D4-4, INV-01) → Arquitectura → Refinamiento de HUs → Mockups / validación con usuarios (D5) → Estimación técnica → Desarrollo del MVP → Pruebas / validación

---

**Estado**: PRD aprobado conceptualmente — D4 completado; sujeto a validación de precisión D4-4 y validación de usuarios D5  
**Última actualización**: 2026-10-02

---

> **Método Ceiba generar prd** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
