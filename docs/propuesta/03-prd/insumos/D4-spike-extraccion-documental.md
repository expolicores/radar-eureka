---
spike: 'D4'
titulo: 'Extracción de datos de televisores desde documentos SECOP II'
proyecto: 'Seguimiento Compras Públicas'
fecha: '2026-10-02'
autor: 'Juan Camilo (con Consultor Técnico)'
estado: 'Completado — decisiones D4-1 a D4-3 tomadas (2026-10-02); D4-4 (precisión y umbral) en validación manual'
insumo_de: 'PRD (cierre del alcance de extracción, ÉPICA-002)'
---

# Spike D4 — Extracción Documental

**Objetivo (PRD, sección 7):** medir con documentos SECOP II reales la disponibilidad de documentos útiles; la extracción de marca, modelo, tamaño, cantidad, precio unitario e IVA; la ubicación de la evidencia; la precisión por campo; la cobertura; los casos que requieren OCR o lectura multimodal; el costo y el tiempo; la disponibilidad de precios de varios oferentes (FR-026), y la calibración del umbral de aceptación (FR-028).

> **Etiquetas:** **[Medido]** resultado directo sobre la muestra · **[Estimado]** cálculo con supuestos explícitos · **[Pendiente PO]** requiere la validación manual del PO.

---

## 1. Método

1. **Muestra:** 50 contratos del universo de D1 (355 contratos SECOP II de televisores, 2023–2026), estratificados por año (13/13/13/11), con semilla fija. Incluye candidatos por UNSPSC `52161505` y por texto. Script `d4-scripts/d4a_muestra_documentos.py`.
2. **Documentos:** para cada proceso se listaron todos los documentos desde los datasets oficiales de archivos y se **priorizaron hasta 4** por nombre (evaluación económica > oferta o propuesta económica > oferta > aceptación > cotización > contrato > estudio previo > invitación), excluyendo CDP, pólizas, RUT y documentos similares. Se descargaron por la URL oficial.
3. **Perfil:** capa de texto por página; páginas sin texto renderizadas a imagen (110 dpi); ZIP expandidos; XLSX y DOCX convertidos a texto con marcas de hoja y fila. Script `d4b`.
4. **Extracción:** 5 agentes de IA, 10 contratos cada uno, siguiendo [`d4/INSTRUCCIONES_EXTRACCION.md`](d4/INSTRUCCIONES_EXTRACCION.md). Leen texto e **imágenes** (lectura multimodal real), sin inventar datos y con evidencia por campo. Salida: 50 JSON en `d4/extraccion/`. El modelo usado es un **sustituto** del componente de producción; los resultados son indicativos del enfoque de IA multimodal, no de un proveedor específico.
5. **Consolidación y costo:** scripts `d4c`, `d4d` y `d4e`.
6. **Validación manual:** la precisión **no puede medirla el mismo sistema que extrae**. Se generó [`d4/D4_plantilla_validacion_PO.xlsx`](d4/D4_plantilla_validacion_PO.xlsx) con 228 filas campo a campo y 50 filas por contrato, para que el PO registre el valor correcto.

---

## 2. Resumen ejecutivo

1. **La extracción multimodal funciona donde el dato existe.** El 100 % de los campos extraídos tiene evidencia (documento y página). Las 99 imágenes leídas (26 de 50 contratos requirieron imagen) fueron legibles. 15 de 19 precios unitarios tienen confianza alta **[Medido]**. La precisión formal queda **[Pendiente PO]**.
2. **El cuello de botella no es la IA: es la disponibilidad del dato en la fuente.** De 36 contratos en categoría, solo **16 (44 %) tienen precio unitario adjudicado** en los documentos, y 18 (50 %) tienen algún precio unitario. En los demás el precio no está publicado: valor global que mezcla el TV con otros bienes o servicios, oferta ganadora no publicada, o formatos de oferta en blanco **[Medido]**.
3. **La meta del Brief de cobertura ≥ 60 % no se alcanza con la definición actual.** No es por falla técnica, sino porque el dato no existe en ~45–50 % de los contratos en categoría. **Esto contradice una meta aprobada y requiere una decisión del PO** (sección 9).
4. **El 28 % de los candidatos no son compras de televisores** (14 de 50), incluidos **7 con UNSPSC `52161505`**: mantenimiento, CCTV, señalización digital, pantallas inflables, lotes equivocados y comodatos. La clasificación (FR-013) es indispensable, no opcional **[Medido]**.
5. **Marca y modelo son escasos en SECOP II:** marca en 9 de 32 ítems y modelo en 7 de 32 (~22–28 %). La comparación de *mismo modelo* vendrá casi siempre de la TVEC; en SECOP II predomina la *equivalencia*. Esto confirma el diseño del PRD **[Medido]**.
6. **IVA:** en 10 de 19 ítems con precio (53 %) el IVA es **indeterminado** **[Medido]**. Con la regla del PRD, más de la mitad de las comparaciones con SECOP II quedarán marcadas como incompletas en IVA.
7. **FR-026 (precios de varios oferentes): baja disponibilidad.** 20 de 50 contratos tienen 2 o más oferentes, pero solo **5 (10 %)** publican precio unitario por oferente; los demás solo publican el total de la oferta **[Medido]**. Aplica el criterio acordado: **se recomienda posponerlo**.
8. **El costo no es un riesgo:** ≈ USD 0,05 por contrato con Sonnet 5.5 (mediana), ≈ USD 19 para el universo de 355 contratos sin margen **[Estimado]** (sección 7).

---

## 3. Disponibilidad documental [Medido]

| Métrica | Valor |
|---|---|
| Contratos con documentos publicados | **50/50** |
| Documentos por proceso (mediana; rango) | 21,5 (5 – 419) |
| Documentos priorizables por proceso (mediana) | 9 |
| Contratos con menos de 2 documentos priorizables | 3 |
| Documentos seleccionados y descargados | 190 (PDF 169, XLSX 12, DOCX 9); **0 fallas de descarga** |
| Páginas analizadas | 1.234 |
| **Páginas sin capa de texto** | **431 (34,9 %)** |
| Documentos 100 % escaneados | 45 de 162 documentos paginados |
| **Contratos que requirieron lectura de imagen** | **26 de 50 (52 %)** |
| Imágenes leídas por el extractor | 99, todas legibles |
| Tokens de entrada por contrato (mediana / p90 / máx.) | ≈ 14.800 / 30.200 / 71.300 |

**Problemas documentales observados:**
- **Imágenes incrustadas en páginas con texto:** tablas de ítems que son imágenes dentro de una página que sí tiene texto (ej. 4838434, 7922631, 9691113). El perfil por "página sin texto" **no las detecta**; hay que detectar imágenes por página o páginas con baja densidad de texto.
- **Formatos de la entidad en blanco:** anexos de "propuesta económica" sin diligenciar (6249401, 8234869, 9640674, 5372563) que parecen ofertas pero no tienen valores.
- **Duplicados:** el mismo documento cargado varias veces (9691113, 9829420, 8729908, 6432982). Se resuelve con deduplicación por hash.
- **Archivos vacíos:** PDF de 130 bytes (9640674).
- **Lote equivocado:** en procesos por lotes, los documentos descargados correspondían a otro lote (5390141).

---

## 4. Resultado de la extracción por contrato [Medido]

| Resultado | Contratos | % de 50 | % de los 36 en categoría |
|---|---|---|---|
| Fuera de categoría o sin TV (servicios, CCTV, señalización, comodato, lote equivocado) | 14 | 28 % | — |
| TV en categoría **sin precio unitario** en los documentos | 18 | 36 % | 50,0 % |
| TV con precio unitario solo de **presupuesto o cotización** | 2 | 4 % | 5,6 % |
| TV con **precio unitario adjudicado** | **16** | **32 %** | **44,4 %** |

**Por qué faltó el precio unitario (20 contratos en categoría):**

| Causa | Contratos | Tipo |
|---|---|---|
| Valor **global** que mezcla el TV con otros bienes, servicios o instalación, sin desglose publicado | 9 | **Estructural** (el dato no existe) |
| **Oferta del adjudicatario no publicada**: solo hay evaluaciones con totales por oferente | 5 | **Estructural** |
| **Formato de oferta en blanco** o archivo vacío | 3 | **Estructural** |
| Tabla de precios como **imagen incrustada** no procesada | 2 | **Técnica** (corregible) |
| Anexo con precios **existente pero no seleccionado** (límite de 4 documentos) | 1–2 adjudicados; ~4 más con precio de presupuesto o techo | **Técnica** (corregible) |

**Cobertura recuperable [Estimado]:** corrigiendo las causas técnicas (detectar imágenes incrustadas y seleccionar más de 4 documentos, incluidos "anexo técnico/económico", "precios techo" y cotizaciones en ZIP), la cobertura de **precio adjudicado** subiría a ~47–53 % de los contratos en categoría, y la de **cualquier precio unitario** (incluido presupuesto) a ~60–65 %. **El tope lo fija la publicación de la fuente, no la extracción.**

---

## 5. Campos extraídos [Medido]

Sobre 32 ítems de televisor con datos (los ítems marcador sin datos no cuentan):

| Campo | Presente | Confianza alta / media / baja | Observación |
|---|---|---|---|
| **Cantidad** | 31 (97 %) | 25 / 3 / 3 | Casi siempre disponible |
| **Tamaño (pulgadas)** | 29 (91 %) | 24 / 3 / 2 | Casi siempre disponible |
| **Precio unitario** | 19 (59 %) | 15 / 4 / 0 | Disponibilidad limitada por la fuente (sección 4) |
| **Marca** | 9 (28 %) | 6 / 1 / 2 | Las entidades especifican por características; la marca aparece en ofertas y cotizaciones |
| **Modelo / referencia** | 7 (22 %) | 3 / 3 / 1 | Ídem; a veces es la referencia "o equivalente" del pliego (confianza baja) |
| **IVA** (en ítems con precio) | con IVA 6 · sin IVA 3 · **indeterminado 10** | — | Casos especiales: precio unitario sin IVA con total con IVA; exención de IVA en San Andrés |
| **Evidencia por campo** | **100 %** | — | Documento y página (u hoja y fila) en cada campo no nulo |
| Tipo de precio | adjudicado 16 · contratado 1 · presupuesto 2 | — | |
| Inconsistencias registradas | 33 | — | Aritméticas y de valor; ver sección 6 |

**La precisión por campo (NFR-CAL-002) no se puede calcular sin la validación manual** **[Pendiente PO]**. La plantilla trae 228 filas campo a campo con la evidencia de cada una. Indicadores indirectos: confianza alta en el 79 % de los precios unitarios, aritmética consistente (cantidad × precio unitario = total) en todos los casos donde ambos datos existen, salvo los registrados como inconsistencia.

---

## 6. Calidad de datos de la fuente [Medido]

- **El valor del contrato en datos abiertos no coincide con la oferta aceptada** en varios casos (ej. 89,8 M frente a 61,0 M; 19,99 M frente a 11,99 M; 34,47 M frente a 23,14 M). **No se debe usar el valor de datos abiertos como sustituto del precio** sin verificarlo en documentos.
- Errores aritméticos en tablas de los oferentes (ej. 4 × 1.020.000 registrado como 4.800.000).
- Hay contratos que no son compras: un comodato y un televisor como premio de lotería (este último sí es una compra válida).
- El UNSPSC `52161505` también se usa para servicios de mantenimiento y CCTV.

---

## 7. Costo y tiempo [Estimado]

**Supuestos:** una llamada por contrato con el paquete priorizado completo; 1 token ≈ 3,5 caracteres en español; ≈ 1.500 tokens por imagen de página (≈ ancho × alto / 750 a 110 dpi); 2.000 tokens de salida. **No incluye** razonamiento del modelo, reintentos ni caché: aplicar un margen de ×1,5–3. Precios de la API de Anthropic vigentes al 2026-09-25.

| Modelo | USD por contrato (mediana) | USD por contrato (p90) | Universo 355 contratos (sin margen) | Con margen ×1,5–3 |
|---|---|---|---|---|
| Haiku 4.5 ($1 / $5 por M tokens) | 0,025 | 0,040 | ≈ 9,5 | ≈ 14 – 29 |
| Sonnet 5.5 ($2 / $10) | 0,050 | 0,080 | ≈ 19 | ≈ 29 – 57 |
| Opus 5.5 ($4 / $20) | 0,099 | 0,161 | ≈ 38 | ≈ 57 – 114 |

- **La carga incremental** es de ~100 contratos SECOP II por año: unos pocos dólares al año.
- **El costo no es un driver relevante** del MVP. La elección del modelo debería decidirse por precisión (validación del PO) y no por costo.
- **Tiempo:** los agentes tardaron ~30–40 s por contrato incluyendo lectura de imágenes. No es representativo de una llamada de API en producción. El objetivo inicial NFR-PER-004 (≤ 5 min por documento) parece holgado, pero no se midió en producción.

---

## 8. Respuesta a cada pregunta de D4

| Pregunta de D4 (PRD) | Resultado |
|---|---|
| Disponibilidad de documentos útiles | 50/50 con documentos; mediana 9 priorizables. **Precio adjudicado publicado en 44 % de los contratos en categoría.** |
| Marca / modelo | 28 % / 22 % de los ítems. Escasos en SECOP II. |
| Tamaño / cantidad | 91 % / 97 %. |
| Precio unitario | 59 % de los ítems; adjudicado en 44 % de los contratos en categoría. |
| IVA | Indeterminado en 53 % de los ítems con precio. |
| Ubicación de la evidencia | **100 %** de los campos con documento y página. |
| Precisión por campo | **[Pendiente PO]**: plantilla generada. |
| Cobertura | 44 % (precio adjudicado) / 50 % (cualquier precio) de los contratos en categoría. Recuperable con mejoras técnicas a ~47–53 % / ~60–65 % **[Estimado]**. |
| OCR / multimodal | **52 %** de los contratos requirieron imagen; 34,9 % de las páginas escaneadas; imágenes legibles. **Multimodal indispensable.** |
| Costo y tiempo | ≈ USD 0,05 por contrato (Sonnet 5.5, sin margen); no es un driver. |
| Varios oferentes (FR-026) | **10 %** con precio unitario por oferente. **Baja disponibilidad.** |
| Umbral de aceptación (FR-028) | **[Pendiente PO]**: se calibra con la plantilla, comparando la confianza con el resultado validado. |

---

## 9. Implicaciones y decisiones para el PO

**D4 encontró evidencia que contradice una decisión existente** (la meta de cobertura del Brief), por lo que se presenta para decisión. El resto son ajustes dentro del alcance del PRD.

| # | Tema | Evidencia | Recomendación |
|---|---|---|---|
| **D4-1** | **Meta de cobertura ≥ 60 %** (Brief, NFR-CAL-003) | El precio unitario adjudicado **no está publicado** en ~45–50 % de los contratos en categoría. | Separar dos indicadores: **(a) Disponibilidad en la fuente** (% de contratos en categoría con precio unitario publicado), que se **reporta sin meta** porque no depende del producto; **(b) Cobertura de extracción** (% de contratos con precio publicado que el sistema extrae automáticamente), con la **meta ≥ 60 %** o mayor (≥ 80 % es razonable según la muestra). Así el KPI mide el producto y no a la fuente. |
| **D4-2** | **FR-026** (varios oferentes) | Solo 10 % de los contratos publican precio unitario por oferente. | **Posponer** según el criterio ya acordado en el PRD. No bloquea el flujo principal. |
| **D4-3** | **Precio unitario derivado** | En contratos de un solo tipo de TV con valor global y cantidad conocida, el precio unitario se puede calcular como total ÷ cantidad. | Permitirlo **solo** cuando el contrato contenga únicamente televisores del mismo tipo y la cantidad esté documentada, marcado como **"derivado"** y con confianza menor. Nunca en contratos mixtos. *(Regla de extracción dentro de FR-025; no amplía el alcance.)* |
| **D4-4** | **Precisión y umbral** | No medibles sin una verificación independiente. | Que el PO diligencie la plantilla, priorizando precio unitario, cantidad y tamaño; con eso se calculan NFR-CAL-002 y el umbral de FR-028. |

**Ajustes técnicos que entran al PRD (sin cambiar el alcance):**
1. **Clasificación obligatoria y estricta** (FR-013): el 28 % de los candidatos no son compras de TV, incluso con UNSPSC `52161505`. Excluir servicios de mantenimiento, CCTV, señalización, comodatos y lotes que no son de TV.
2. **Selección documental** (FR-019): subir de 4 a ~8 documentos por proceso; incluir anexos técnicos y económicos, "precios techo", cotizaciones dentro de ZIP y formatos XLSX; **detectar formatos en blanco**; **deduplicar por hash**; respetar el lote correcto en procesos por lotes.
3. **Detección de imágenes incrustadas** (FR-023): procesar como imagen las páginas que contienen tablas o imágenes aunque tengan algo de texto.
4. **No usar el valor del contrato en datos abiertos** como precio sin verificarlo en documentos.
5. **IVA:** mantener la regla "indeterminado = incompleto". Esperar ~50 % de comparaciones SECOP II incompletas en IVA y comunicarlo en la evidencia.
6. **Mismo modelo vs. equivalente:** confirmado; la TVEC aporta casi todo el *mismo modelo*, y SECOP II se compara principalmente por equivalencia.

---

## 9.1 Decisiones del PO (2026-10-02)

- **D4-1 ✅** Tres indicadores de cobertura: disponibilidad en la fuente (se reporta), cobertura de extracción (meta ≥ 80 %, provisional) y cobertura end-to-end (se reporta); TVEC aparte. → Brief Adenda 3, NFR-CAL-003, FR-091.
- **D4-2 ✅** FR-026 pospuesto fuera del core del MVP (ÉPICA-009).
- **D4-3 ✅** Precio unitario derivado con 6 condiciones estrictas; nunca en contratos mixtos ni con el valor de datos abiertos; `precio_unitario_tipo = derivado` con menor confianza propagada. → FR-099, FR-100, FR-068.
- **D4-4 🔄** Validación manual en curso, con prioridad precio unitario → cantidad → tamaño → modelo → marca → demás. El umbral de aceptación sale de la relación confianza ↔ corrección observada.
- **Ajustes técnicos incorporados al PRD:** clasificación estricta (FR-013); ~8 documentos como estrategia inicial ajustable, anexos y ZIP, formularios en blanco, deduplicación, lote correcto (FR-019); imágenes incrustadas (FR-023).

## 10. Limitaciones

- **La precisión no está medida:** requiere la validación manual del PO (sección 9, D4-4).
- El extractor usado es un **sustituto** del componente de producción; otro modelo o proveedor puede dar resultados distintos.
- Muestra de 50 contratos: los porcentajes tienen margen amplio (±10–14 puntos con 95 % de confianza para proporciones cercanas al 50 %).
- La selección se limitó a 4 documentos por proceso; parte de la falta de precio puede deberse a esa decisión (cuantificada en la sección 4).
- No se midió latencia ni costo real de una API en producción.
- Las causas por contrato se basan en las observaciones del extractor y en una verificación parcial de los documentos no seleccionados.

**Archivos:** `d4/d4_muestra_inventario.json` · `d4/d4_perfil_documentos.json` · `d4/d4_metricas_documentales.json` · `d4/extraccion/*.json` (50) · `d4/d4_resultados_extraccion.json` · `d4/d4_costo_estimado.json` · `d4/D4_plantilla_validacion_PO.xlsx` · `d4/documentos/` (documentos e imágenes de evidencia) · `d4-scripts/`.
