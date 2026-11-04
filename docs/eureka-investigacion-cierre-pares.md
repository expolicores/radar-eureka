# Cierre económico dirigido de los 19 pares técnicos

Actualización posterior: [cierre de fase y revisión humana recomendada](eureka-investigacion-cierre-fase.md).
Los resultados de este documento corresponden a la iteración local previa al fallback contractual.

Continuación offline del ejercicio de 60 días del 3 de noviembre de 2026. **No se amplió el universo y no apareció ningún par monetario válido.**

## Alcance y resultado

Se congelaron los IDs de los 19 pares originales: 1 exacto y 18 high, que reúnen **20 observaciones de 7 procesos**. No son 19 compras independientes. Se revisó además MC-002-2026 exclusivamente por la instrucción de resolver su conflicto; no se agregó a los pares.

Se reutilizaron archivos y fragmentos de las muestras locales de 7/30/60 días, solo para esas identidades. Comprobación adicional de PostgreSQL en transacción READ ONLY: **73 versiones locales**, todas ya representadas en esos recibos; ningún anexo descargado adicional oculto en el registro. Se analizaron económicamente **41 versiones de los siete procesos y 2 del caso suplementario**, sin procesar documentos clasificados como irrelevantes para el cierre económico.

No discovery, inventarios nuevos, descargas, Web Search, CDP, mercado privado, TVEC, agentes/LLM ni LECTOR. No inserciones ni cambios de facts/canonicals, scoring, Radar, alertas o casos productivos. La proyección reutiliza los registros de evidencia existentes, sin duplicarlos en DB. Sin migración.

| Resultado | Cantidad |
|---|---:|
| Pares exact/high iniciales | 1 / 18 |
| Procesos / observaciones únicos de los pares | 7 / 20 |
| Procesos con precio de compra adicional | 0 |
| Unitarios de compra utilizables explícitos / calculados | 0 / 0 |
| Pares ready / comparaciones válidas / señales | 0 / 0 / 0 |
| Pares missing_both_prices | 19 |
| Conflictos resueltos | 0 |
| Conflicto de producto no resuelto | 1 proceso / 2 alternativas (MC-002-2026) |
| Observaciones de pares marcadas para revisión manual | 20 |
| Procesos para revisión manual | 7, más MC-002-2026 como caso separado |
| Proveedor documental adicional identificado | 1 (INEM) |
| Requests a proveedores / descargas nuevas / escrituras DB | 0 / 0 / 0 |

Los unitarios de la tabla cuentan **precios de compra utilizables de las observaciones congeladas**. No significan que no existan cotizaciones con precios ni que MC-002-2026 carezca de dos valores contractuales legibles. SENA/Manizales no se volvieron a revisar: no forman parte de estos pares.

## Hallazgos que bloquean el cierre

| Proceso | Evidencia local revisada | Bloqueo concreto / siguiente soporte necesario |
|---|---|---|
| MC-071-2026, Universidad del Atlántico | `CLAUSULADO DBS-228-2026 + corregido 3vz.pdf`, p. 6, describe 1 TV U8200H; `CO1_PCCNTR_9947091_Firmado.pdf`, p. 3, agrupa el lote en $469.839.184 | El TV está identificado, pero no tiene unitario contractual desglosado. Falta cuadro de precios aceptado/contratado del ítem; no dividir el valor de computadores + TV entre una unidad. |
| IEGS-016-2026, General Santander | `CO1_PCCNTR_10008800_Firmado.pdf`, p. 3, «COMPUTADORES Y TELEVISORES»; comunicado de aceptación y oferta seleccionada, p. 1 | Los tres soportes publican el total de $7.918.910 del lote. «OFERTA SELECCIONADA» es una comunicación de resultado, no una oferta económica desglosada. Falta el precio aceptado del TV U8200H. |
| RE-00102026, La Gloria | `CO1_PCCNTR_10116127_Firmado.pdf`, p. 3; `1 Propuesta Economica (1).pdf`, p. 1; contrato anexo de muestras anteriores | El contrato electrónico agrupa equipos en $29.208.500. Hay cotización de TV por $3.970.000, pero no enlace suficiente de oferta/ítem aceptado. El anexo contiene un objeto de vestuarios regionales contradictorio con los equipos: no se usa para resolver aceptación o precio. |
| SASI-011-2026, Zipaquirá | `CO1_PCCNTR_9992869_Firmado.pdf`, p. 3; adjudicación; evaluación jurídica y cotizaciones | «herramientas comisarías» es un único renglón global de $428.421.658. Las cotizaciones no prueban los precios aceptados de ADM INVESTMENTS. El contrato menciona un anexo de compra que no está entre las copias locales disponibles. |
| SAMC-AG-019-2026, Mariquita | `CO1_PCCNTR_9995104_Firmado.pdf`, p. 3; resolución de adjudicación y evaluación | Contrato por $465.000.000 con un único valor global VG para equipos, mobiliario y otros elementos. Falta desglose final aceptado/contratado del TV; conocer a JDI SAS como proveedor no permite imputar un unitario. |
| INEM-SI-01-2026, Leticia | Resolución de adjudicación INEM-SI-001-2026, p. 3, artículo primero; cotizaciones ALISHA y SHEDA | Se identifica documentalmente a SHEDA y adjudicación global de $716.043.600. La resolución incorpora unitarios de su oferta económica, pero no los enumera. No se demuestra que la cotización de septiembre sea la oferta final ganadora; tampoco se promueven los unitarios de ALISHA. Falta identificar la oferta final aceptada y sus renglones de TV. Se conserva la variante textual SI-01/SI-001; no se inventa identidad nueva. |
| SAMC-022-2026, Gachancipá | `CO1_PCCNTR_9964932_Firmado.pdf`, p. 3, «OFERTA ECONOMICA POR EL TOTAL DEL VALOR DEL CONTRATO»; adjudicación y evaluación financiera | Un renglón global de $376.468.135. La evaluación financiera no desglosa ni acepta el unitario del TV de 40″. Falta cuadro final por ítem. |

La afirmación es **no recuperado con la evidencia local revisada**, no «ese precio no existe en SECOP». Ninguno de esos totales globales fue dividido para fabricar un unitario.

### OCR local pendiente

`COTIZACION ZIPAQUIRA (2).pdf`: 8 páginas sin texto, todas con `ocr_pixel_limit` en el recibo original. Se efectuó una prueba local con el mismo adaptador Tesseract spa a 150 dpi, manteniendo máximo 12 millones de píxeles y 20 páginas. Las 8 páginas siguieron superando el límite: cero páginas reconocidas y cero texto nuevo. No se aumentaron límites ni se repitió la descarga; el original permanece intacto. `local-ocr-receipt.json` conserva política, SHA, motor y error por página.

### MC-002-2026

En `CONTRATO 015 COMPRAVENTA.pdf`, p. 1, la misma referencia **50UA7300PSB** figura en dos renglones: 70″, 1 unidad, $2.553.400; y 55″, 4 unidades, $2.412.750 cada una. Los otros soportes locales no aportan una corrección inequívoca. Se mantienen ambas alternativas y `model_reused_for_incompatible_sizes`; `readiness_status=manual_review`, estado económico `product_conflict`. No se adjudica la referencia a una de las pulgadas por conocimiento de catálogo.

## Matriz de los 19 pares

En todos los casos: precio A/B de compra **no recuperado**, resolución determinística con lo revisado **no alcanzada**, revisión manual **sí**. Las etapas faltantes son un desglose contractual/adjudicado por ítem o la oferta económica final cuya aceptación pueda demostrarse; la tabla anterior especifica los soportes revisados y la falta en cada proceso. Los IDs abreviados distinguen observaciones del mismo proceso, no nuevas compras.

| Par | Proceso A / observación | Proceso B / observación | Producto técnico | Nivel | Precio A / B | Estado | Revisión manual |
|---:|---|---|---|---|---|---|---|
| 1 | RE-00102026 / `fb397fae183a` | SASI-011-2026 / `ced6ea7883fb` | 65″ 4k | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 2 | RE-00102026 / `fb397fae183a` | SAMC-AG-019-2026 / `18ffdd3f83e6` | 65″ 4k | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 3 | RE-00102026 / `5b53adce7c93` | SASI-011-2026 / `ced6ea7883fb` | 65″ 4k | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 4 | RE-00102026 / `5b53adce7c93` | SAMC-AG-019-2026 / `18ffdd3f83e6` | 65″ 4k | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 5 | MC-071-2026 / `6e7462c48fc5` | IEGS-016-2026 / `dd0898e95f26` | 65″ 4k U8200H | exact | No recuperado / No recuperado | missing_both_prices | Sí |
| 6 | INEM-SI-01-2026 / `e9c9c27be14a` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 7 | INEM-SI-01-2026 / `45e611ddd870` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 8 | INEM-SI-01-2026 / `2fa743b1852e` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 9 | INEM-SI-01-2026 / `f478a0f7dbe7` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 10 | INEM-SI-01-2026 / `ee426abf7870` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 11 | INEM-SI-01-2026 / `7b7b43e706ed` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 12 | INEM-SI-01-2026 / `eebc960c4c8b` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 13 | INEM-SI-01-2026 / `cf6bdfcd42c5` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 14 | INEM-SI-01-2026 / `fc5d27b5dc82` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 15 | INEM-SI-01-2026 / `0a82ed75a2a5` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 16 | INEM-SI-01-2026 / `5c3869d45668` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 17 | INEM-SI-01-2026 / `124efd7f99fe` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 18 | INEM-SI-01-2026 / `e7464f13d59e` | SAMC-022-2026 / `8e7dfd3b37a3` | 40″ full_hd | high | No recuperado / No recuperado | missing_both_prices | Sí |
| 19 | SASI-011-2026 / `ced6ea7883fb` | SAMC-AG-019-2026 / `18ffdd3f83e6` | 65″ 4k | high | No recuperado / No recuperado | missing_both_prices | Sí |

La matriz extensa local `blocker_matrix.md` y `pair_blockers.json` contienen, **por cada lado de cada par**, los campos faltantes, el bloqueo, los documentos efectivamente revisados, la etapa necesaria y la resolubilidad local. No se generan diferencias absolutas/porcentuales ni días entre compras con precios/fechas no demostrados.

## Proyección y política

`comparison-readiness-v1` incluye identidad/código, producto, grupo/nivel, cantidad y su evidencia/estado de verificación, unitarios contractual/adjudicado/oferta aceptada, precio preferido/etapa/origen, proveedor con alcance de evidencia, fecha, faltantes, conflictos y referencias documentales. Un proveedor conocido o el nombre «oferta seleccionada» no prueba la aceptación de cada precio. Una cantidad de invitación/cotización no se etiqueta como cantidad contractual verificada.

Solo se reutiliza `purchase_price` cuando el ciclo lo validó. El precio calculado exige total y cantidad del mismo ítem con dos provenance; no se crea a partir del total de lote. Supplier ausente se hace visible, pero no es por sí solo un nuevo bloqueo comercial. Las razones de presupuesto permanecen visibles sin sustituir un precio contractual demostrado.

Seis observaciones tuvieron enlace ambiguo al incorporar fragmentos de recibos previos: se conservó la proyección original y se marcó `ambiguous_local_observation_link`. **No se convirtió esa ambigüedad técnica en un conflicto de precio de la fuente**, ni se eligió una alternativa arbitraria. Los estados finales de los 19 pares siguen siendo `missing_both_prices`.

## UI, artefactos y siguiente paso

En `/senales` se añadió el resultado real: **«19 pares técnicamente comparables evaluados; ninguno alcanzó evidencia económica suficiente en ambos lados.»** Matriz desplegable con 19 filas y 38 enlaces a procesos. `/explorar` conserva el universo y los 48 candidatos originales; no se cambiaron las cifras históricas de la muestra ni se añadieron señales.

Directorio local: `backend/.local/investigation-tv-readiness-20261103/`:

- `comparison_readiness.json`: proyección completa y SHA del ciclo base.
- `pair_blockers.json`, `blocker_matrix.md`: 19 pares con ambos lados y bloqueos.
- `document_review.json`: las 43 versiones económicas revisadas.
- `run_summary.json`: contadores; `local-store-audit.json`: comprobación de los 73 archivos registrados.
- `local-ocr-receipt.json`: prueba local sin texto recuperado.
- `ui-check.json`, `senales-readiness.png`: validación visual local.

El siguiente paso requiere autorización separada para obtener **documentos concretos de estos mismos procesos**, no nuevos procesos: primero los cuadros desglosados del par U8200H (Universidad del Atlántico / General Santander); después los anexos finales de Zipaquirá/Mariquita y la oferta económica final de SHEDA. Con solo las copias disponibles no hay base para cerrar un par. Esa adquisición no se ejecutó en esta iteración.

## Validación

Suite backend afectada: 311 aprobados y uno OCR opcional omitido; después se añadió y aprobó la regresión específica de orden documental. Los 17 tests de readiness están aprobados. Frontend: 153 aprobados. Ruff/format, Mypy, ESLint, TypeScript/build y 13 contratos de importación correctos. Tests nuevos cubren scope congelado, ofertas no aceptadas, conflictos, cantidad, provenance calculada, fechas, proveedor documental y ausencia de mutación del baseline. Smoke local: 19 pares, 38 enlaces, discovery previo conservado y cero errores JS; peticiones externas bloqueadas durante el smoke.

Para reproducir offline desde `backend`:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_investigation_readiness.py `
  --sample-directory .local/investigation-tv-60d-20261103 `
  --evidence-directory .local/investigation-tv-30d-20261103 `
  --evidence-directory .local/investigation-tv-20261103 `
  --output-directory .local/investigation-tv-readiness-20261103
```

`--publish` agrega la auditoría a la proyección local de UI, previa comprobación de que corresponde al mismo informe. No inicia una corrida ni adquiere documentos. Los recibos originales de 60 días permanecen inmutables.
