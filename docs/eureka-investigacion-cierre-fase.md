# Estado vs Estado — prototipo determinístico funcional, con revisión humana para casos no resolubles

Cierre de la fase actual, sobre el universo de 60 días y los pares existentes. No se amplió discovery, fechas, familias de producto ni comparabilidad. No se ejecutaron Radar, CDP, Web Search, agentes/LLM, LECTOR ni mercado privado.

## Qué funciona

Discovery Socrata/SECOP, inventario, almacenamiento por SHA, extracción nativa/Tesseract acotada, taxonomía/facts/canonicals existentes, reconstrucción económica determinística por producto/etapa, comparación exact/high y provenance. Los presupuestos, valores globales y ofertas no demostradas como aceptadas no se convierten en precios de compra.

Se mantienen los 19 pares técnicos originales, pertenecientes a 7 procesos y 20 observaciones. **Cero pares ready, cero comparaciones monetarias válidas y cero señales nuevas.** No se bajaron requisitos para producir una señal.

## Auditoría de recuperación por contrato

El discovery previo ya recuperaba `id_contrato` en `jbjy-vk9h` mediante igualdad exacta `proceso_de_compra = id_del_portafolio`. El inventario, sin embargo, solo invocaba `fetch(portfolio_id)` sobre `dmgg-8hin.proceso`: no tenía una estrategia contractual adicional.

La columna oficial contractual es **`n_mero_de_contrato`**, confirmada en el [esquema oficial de dmgg-8hin](https://www.datos.gov.co/api/views/dmgg-8hin.json). Poner `CO1.PCCNTR...` en la columna `proceso` no es equivalente: la prueba inicial con esa llave equivocada devolvió cero filas.

Se agregó `SocrataDocumentSource.fetch_by_contract(contract_id)` usando `n_mero_de_contrato = '<PCCNTR exacto>'`. Conserva paginación por cursor y valida el contrato devuelto. No sustituye el inventario por portafolio ni se activa en Radar.

El combinador investigativo `recover_inventory`:

1. Mantiene el inventario actual, incluso cuando se reutiliza desde recibos locales.
2. Acepta contratos únicamente cuando la metadata demuestra su vínculo exacto con el BDOS del proceso.
3. Consulta adicionalmente cada PCCNTR conocido por la columna contractual oficial.
4. Une por `(dataset_id, id_documento)`. Un nombre igual con IDs diferentes no se colapsa; metadata contradictoria no reemplaza silenciosamente la evidencia primaria.
5. Conserva las dos llaves si el mismo documento aparece por ambas. La deduplicación binaria por SHA y el resto del pipeline documental permanecen existentes.

La asociación canónica al proceso y la llave original del proveedor se registran separadamente. Provenance por documento: tipo/valor de llave, campo Socrata, `provider_process_identifier`, portafolio asociado, dataset y si se reutilizó el inventario. No se infieren equivalencias NTC↔REQ ni se inventa una búsqueda por notice cuando no existe una relación oficial disponible.

El resultado puede alimentar los recibos normales del sampler (`inventories.json`, `selected-documents.json` y `selection.json`); `inventory-provenance.json` acompaña el pipeline y el sampler conserva su ruta. En esta validación no hubo documentos nuevos que enviar a descarga/extracción.

## Validación real acotada

Se revisaron las llaves contractuales conocidas de seis de los siete pendientes, más MC-070-2026 como caso de regresión indicado por el usuario. INEM no tiene PCCNTR en la metadata existente de la muestra: se registra esa limitación, sin inventar un contrato ni iniciar discovery nuevo. No se afirma que nunca pueda existir uno en el proveedor.

**MC-070-2026 / CO1.PCCNTR.10103437:** la consulta contractual correcta devolvió los **12 documentos esperados**, entre ellos clausulado, estudios previos y `OFERTA ECONOMICA  MC-070-2026.pdf`.

Hallazgo relevante: esos 12 documentos ya estaban en el inventario previo por BDOS. La oferta ya estaba descargada; su extracción había fallado con `page_limit`. Comprobación local del PDF: **340 páginas**, frente al máximo configurado de **300**. No se aumentó el límite, no se ejecutó otra extracción y no se atribuyó el fallo a ausencia de inventario.

En los siete procesos pendientes, la unión por contrato añadió **0 documentos nuevos** respecto de los inventarios guardados. Se enriqueció la provenance con la llave contractual, sin duplicar documentos. Por tanto, **0 descargas nuevas, 0 OCR nuevos y ninguna adquisición masiva**. El fallback es funcional; en esta muestra no resuelve por sí solo la falta de precio desglosado.

Los contadores `network_requests=0` de `run_summary.json` corresponden a la proyección offline de readiness, no a la fase anterior de consulta contractual. Los recibos de recuperación conservan las consultas por llave y sus resultados.

## Revisión humana recomendada

`human_review_recommended` significa: **hay potencial o evidencia suficiente para conservar el caso, pero el procesamiento determinístico no puede cerrarlo con confianza**. No significa error, señal confirmada ni irregularidad.

La recomendación solo se aplica a casos con potencial demostrado en el alcance revisado, no a todo proceso sin precio. Los realmente descartables o sin interés no pasan automáticamente a revisión humana.

`comparison-readiness-v2` conserva el bloqueo económico original en `economic_readiness_status` por observación y `blocking_status` por par. La clasificación visible puede ser `human_review_recommended`, sin borrar que el bloqueo es, por ejemplo, `missing_both_prices` o un conflicto. Los estados ready y technical_mismatch siguen distinguiéndose y no se alteró el cálculo de comparabilidad.

Motivos estructurados disponibles:

| Motivo | Interpretación |
|---|---|
| `missing_itemized_contract_price` | Falta un precio final desglosado atribuible al producto. |
| `missing_accepted_offer` | No está demostrada la aceptación de la oferta de ese ítem. |
| `ambiguous_product_identity` | La identidad del producto no se puede resolver con confianza. |
| `conflicting_product_reference` | Referencias/especificaciones incompatibles, sin corrección documental inequívoca. |
| `global_contract_value_without_item_breakdown` | El valor global del lote no se puede distribuir entre productos. |
| `missing_quantity` | Falta cantidad verificable. |
| `incomplete_document_cycle` | Evidencia/cobertura del ciclo incompleta. |
| `unresolved_document_relationship` | El enlace entre evidencias no se puede cerrar de forma segura. |
| `extraction_failure` | Documento no extraído correctamente. |
| `oversized_document` | Supera los límites de procesamiento vigentes. |
| `ambiguous_winning_offer` | Identificar al ganador no demuestra qué cotización/precios se aceptaron. |
| `contract_documents_found_but_not_resolved` | Documentos encontrados por contrato, sin resolver el precio de compra. |

## Procesos actualmente marcados

| Alcance | Proceso | Motivo principal |
|---|---|---|
| Par high | RE-00102026, La Gloria | Valor global y cotización sin enlace suficiente de aceptación del ítem. |
| Par exact | MC-071-2026, Universidad del Atlántico | TV U8200H identificado, sin unitario contractual desglosado. |
| Par exact | IEGS-016-2026, General Santander | Aceptación/oferta seleccionada publican el total del lote. |
| Pares high | INEM-SI-01-2026, Leticia | Falta demostrar la oferta final aceptada por ítem; ciclo contractual incompleto en metadata local. |
| Pares high | SAMC-022-2026, Gachancipá | Contrato con valor global, sin precio final atribuible al TV. |
| Pares high | SASI-011-2026, Zipaquirá | Valor global, evidencia pendiente y fallo de extracción documental. |
| Pares high | SAMC-AG-019-2026, Mariquita | Lote heterogéneo sin desglose final del TV. |
| Conflicto solicitado, fuera de los pares | MC-002-2026 | `conflicting_product_reference`: misma referencia 50UA7300PSB asociada a 55″ y 70″. Se conservan ambas alternativas y no se usan monetariamente. |
| Regresión contractual solicitada, fuera de los pares | MC-070-2026 | `oversized_document` y `extraction_failure`: oferta de 340 páginas, límite 300. |

Son **7 procesos de los pares + 2 casos explícitos de auditoría**, todos ya pertenecientes a los 48 procesos originales. Los **19 pares** están como revisión humana recomendada; su bloqueo sigue siendo falta de precio de compra en ambos lados. No se crean filas en la bandeja comercial «Merecen Revisión», casos productivos ni alertas.

## UI y persistencia

En `/senales`, la matriz conserva cada par, sus precios desconocidos y motivos, y muestra **Revisión humana recomendada**. En `/explorar`, se ve la recomendación y su razón tanto en la tabla como en el detalle. MC-002 expone el conflicto y MC-070 el límite documental. Los casos no se presentan como señales confirmadas.

Solo se publica una proyección JSON local derivada. No hubo migración ni modificación de reglas comerciales, filtros, scoring, dedupe, vigencia, comparabilidad o Radar. Los recibos históricos se conservan.

Artefactos: `backend/.local/investigation-contract-closure-20261103/`:

- `inventory-provenance.json`, `recovery-summary.json`: inventario combinado y origen por llave.
- `comparison_readiness.json`, `run_summary.json`: estados, motivos, bloqueo original y contadores.
- `pair_blockers.json`, `blocker_matrix.md`: matriz de los 19 pares.
- `ui-check.json`, `mc002-human-review.png`: verificación visual local.

La evidencia del esquema y la prueba directa de MC-070 se conservan en el directorio anterior `backend/.local/investigation-tv-readiness-20261103/`, en `document-dataset-schema.json` y `mc070-correct-contract-inventory.json`.

## Validación

322 tests backend afectados aprobados, uno OCR opcional omitido. 155 tests frontend aprobados. Ruff/format, Mypy, ESLint, TypeScript/build y los 13 contratos de importación correctos. Cobertura nueva: columna contractual correcta, contrato incorrecto rechazado, dedupe multillave, provenance, metadata contradictoria, descarte sin recomendación automática, conflicto/falta de precio con revisión humana y UI con estado/motivo.

## Pendientes explícitos, sin implementar

- Refinamiento profundo de taxonomía/canónicos y resolución semántica avanzada.
- LECTOR y extracción con agentes/LLM.
- Estado vs mercado privado.
- Histórico longitudinal, TCVE/TVEC y ajustes macroeconómicos.
- Nuevos tipos de señales.
- Resolver manualmente referencias incompatibles y comprobar cuadros económicos finales/relaciones documentales no demostradas.
- Tratamiento dirigido de documentos que superan límites; no se ampliaron límites en esta fase.

Este cierre no implica que todos los documentos de SECOP se expongan homogéneamente, ni que una consulta contractual garantice obtener el precio de cada ítem.
