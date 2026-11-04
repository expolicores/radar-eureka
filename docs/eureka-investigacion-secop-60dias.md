# Tercer ejercicio investigativo real: televisores, 60 días

Continuación: [cierre económico dirigido de los 19 pares técnicos](eureka-investigacion-cierre-pares.md).
No amplía el discovery ni altera los resultados históricos de este ejercicio.

Ejecutado el **3 de noviembre de 2026**, America/Bogota. Resultado: **ningún par monetario válido y ninguna señal**. La ampliación aporta evidencia documental, pero no un nuevo precio de compra utilizable respecto de la reconstrucción anterior.

## Ventana y adquisición

Ventana de publicaciones: **04/09/2026 inclusive–03/11/2026 exclusivo** (hasta el 02/11). Se exige además fecha de compra verificada dentro de la misma ventana para comparar: no se sustituye con publicación. Adquisición/extracción: **19:26:04–20:21:26 Bogotá**, 55 min 22 s. El discovery, los inventarios y la proyección offline son actividades adicionales a esa duración.

Fuentes únicas: Socrata SECOP II procesos `p6dx-8zbt`, contratos `jbjy-vk9h`, inventarios `dmgg-8hin` y binarios oficiales SECOP. No CDP, Web Search, mercado privado, TVEC, agentes, LLM ni LECTOR. OCR real Tesseract con el límite existente de 20 páginas, sin ampliarlo.

Discovery nacional amplio por objetos tecnológicos, audiovisuales, electrónicos, dotación/equipamiento y UNSPSC, incluyendo 521615/521600/432119. Ranking determinístico con prioridad 55/65 pulgadas, sin excluir otros tamaños. Muestra intencional, no representativa ni exhaustiva. Se seleccionaron los 16 candidatos con TV explícito en metadata y 32 de objetos amplios, máximo dos por entidad. La confirmación sigue siendo documental.

| Métrica | Resultado |
|---|---:|
| Procesos únicos encontrados | 13.080 |
| Candidatos maduros en metadata | 6.147 |
| Seleccionados / intentados | 48 |
| Revisados con extracción | 47 |
| Procesos con TV documentados | 28 |
| Procesos con registros TV reconstruidos | 26 |
| Documentos en inventarios | 1.031 |
| Documentos seleccionados / disponibles | 280 |
| Descargas nuevas / reutilizaciones | 221 / 59 |
| Descargas fallidas | 0 |
| Resultados de extracción reutilizados | 58 |
| Extracciones completed / partial_text | 245 / 26 |
| Extracciones failed / requires_ocr | 8 / 1 |
| Documentos sin texto / cobertura incompleta | 9 / 28 |
| Documentos con páginas que requirieron OCR | 69 |
| Páginas OCR computadas / reutilizadas | 560 / 157 |
| Facts / canonicals de la muestra | 3.033 / 517 |
| Observaciones TV normalizadas del extractor | 47 |
| Registros TV del ciclo, incluidos parciales | 88 |
| Procesos con algún valor económico TV recuperado | 8 |
| Registros con precio unitario contractual recuperado | 4 |
| Registros con precio unitario adjudicado recuperado | 0 |
| Precios unitarios de compra verificables | 2 |
| Pares monetarios válidos / señales | **0 / 0** |

Los 88 registros del ciclo no son 88 televisores comprados: incluyen filas parciales y observaciones no vinculables de manera segura entre documentos. Las 47 observaciones son otra proyección, procedente del extractor de facts. No sumar ambos contadores. Los precios recuperados tampoco equivalen automáticamente a precios aptos para comparar.

Los estados de extracción y la cobertura se superponen: 28 con cobertura incompleta no significan 28 fallos adicionales. El inventario vacío de **CVNMIED-PRESO-057-2026 / CO1.REQ.11060074, Colegio Venecia**, produjo un error aislado por ausencia de fragmentos; no se sustituyó por otra fuente ni se detuvo el resto.

## Reconstrucción económica y provenance

Se preservan cantidad/unidad, presupuesto, oferta, oferta evaluada, adjudicación y contrato por separado, junto con oferente/proveedor cuando se demuestra el enlace. No se promueve una evaluación a adjudicación ni una cotización a precio de compra. Un nombre de archivo «oferta seleccionada» no demuestra por sí solo aceptación.

Los PDFs de contrato pueden contener cotizaciones o estudios anexos. Se clasifica también por encabezados de página; por ejemplo, las páginas de `2026015` con `ASUNTO: COTIZACION` permanecen como oferta, aunque el archivo se llame contrato. No se divide un valor global de lotes heterogéneos entre televisores.

Los dos precios utilizables siguen siendo los recuperados anteriormente:

| Entidad / proceso | Producto documentado | Cantidad | Unitario COP | Total del ítem COP | Firma publicada | Evidencia |
|---|---|---:|---:|---:|---|---|
| SENA Regional Valle, CNPB / MC-VLL-CNPB-0022-2026 / CO1.REQ.11075456 | TV 65″, 4K UHD HDR Smart, Google TV, control por voz y soporte de pared | 3 UN | 2.670.920 | 8.012.760 | 29/10/2026 10:40:00.615 | `CO1_PCCNTR_10114833_Firmado.pdf`, p. 3, native_pdf_text |
| Policía Metropolitana de Manizales / PN MEMAZ MIC 045 2026 / CO1.REQ.11181681 | TV 75″ profesional tipo business | 3 UN | 5.850.000 | 17.550.000 | 30/10/2026 16:29:43.740 | `CO1_PCCNTR_10133299_Firmado.pdf`, p. 3, native_pdf_text |

Firma: `jbjy-vk9h.fecha_de_firma`, enlazada por `proceso_de_compra = id_del_portafolio` BDOS y contrato exacto. Se conserva el valor temporal publicado por Socrata, sin inventar una conversión horaria para su timestamp sin zona. No es prueba de entrega o pago efectivo.

Cada precio conserva documento, página, fragmento, versión, SHA-256, texto de evidencia, etapa, confianza y origen explicit/calculated. Si se calcula un unitario, ambos insumos deben corresponder al mismo ítem homogéneo y conservar sus evidencias. El precio explícito de Manizales también tiene comprobación aritmética 17.550.000 / 3.

**SENA y Manizales no forman un par**: difieren en pulgadas y clase de producto; las especificaciones de Manizales están incompletas. No se publica una diferencia porcentual entre ellos. El conflicto de presupuesto de SENA sigue visible y requiere revisión, pero no sustituye ni invalida por sí solo el precio contractual explícito posterior.

## Comparabilidad y cuello de botella

| Pares técnicos entre registros de entidades diferentes | Cantidad | Pares monetarios válidos |
|---|---:|---:|
| exact | 1 | 0 |
| high | 18 | 0 |
| partial | 295 | 0 |
| not_comparable | 2.927 | 0 |

Son pares de registros, no grupos transitivos ni cantidades de compras. Varios pueden corresponder a los mismos procesos con observaciones distintas. El comparador exige dos precios sustentados, cantidad/unidad, fecha de compra y ausencia de conflictos críticos; `partial` nunca genera señal. En esta ejecución no se recuperó precio adjudicado ni oferta ganadora demostrada que completara un par.

Casos que explican el resultado y orientan el siguiente paso:

1. **MC-002-2026, I.E. Técnica Pedro Pabón Parga**: hay dos unitarios contractuales legibles (2.553.400 y 2.412.750 COP), pero la misma referencia `50UA7300PSB` se vincula a filas de 70″ y 55″. Se conservan ambos valores y el conflicto crítico `model_reused_for_incompatible_sizes`; ninguno pasa como compra comparable. Hace falta verificar el ítem realmente contratado/corregido, no escoger una de las pulgadas.
2. **MC-071-2026, Universidad del Atlántico, e IEGS-016-2026, I.E. General Santander**: referencia explícita coincidente en la evidencia, pero sin precio de compra atribuible recuperado. Este es el par técnico exacto; su bloqueo es económico/documental, no un umbral porcentual.
3. **RE-00102026 (La Gloria), SASI-011-2026 (Zipaquirá), SAMC-AG-019-2026 (Mariquita)**: compatibilidad técnica alta en observaciones de 65″, pero falta reconstruir un precio de compra verificable con cantidad/unidad y fecha. Priorizar su cuadro de ítems adjudicado/contratado y la cobertura de los documentos ya descargados antes de ampliar otro discovery.
4. **INEM-SI-01-2026**: se recuperan múltiples unitarios de ofertas y conflictos de cantidad/resolución; no hay demostración suficiente de aceptación e identidad homogénea para convertirlos en compras.
5. **Colegio Venecia**: inventario sin documentos; no hay base para confirmar TV o precio documental.

La ausencia de un precio recuperado no prueba que el documento o el precio no exista: puede faltar cobertura, enlace entre etapas o soporte para ese diseño de tabla en las reglas determinísticas. El siguiente paso recomendado es una revisión dirigida de estas evidencias concretas, no otra ampliación indiscriminada ni rebajar requisitos de comparación. No se ejecutó esa adquisición adicional.

## Política y UI

Política independiente `research-60d-v1`; ciclo `economic-cycle-v2`. Solo exact/high pueden emitir `PUBLIC_PRICE_DIFFERENCE`, sin umbral porcentual rígido. Porcentaje respecto al precio menor. Fechas de compra verificadas y diferencia de días ≤60; sin inflación, TRM ni benchmark histórico. La cercanía temporal no garantiza condiciones iguales; impuestos, accesorios, instalación, garantía y entrega deben quedar explícitos como limitaciones cuando no se verifican. No se etiqueta fraude, corrupción ni sobreprecio.

`/explorar` y `/senales` consumen el informe real finalizado, publicado atómicamente. Las señales admiten abrir ambos lados y su provenance; en esta ejecución muestran cero señales. No se reemplazan faltantes con demo. Los ejercicios de 7/30 días permanecen en sus archivos originales.

Smoke local en Edge headless: ventana correcta, 48 candidatos, 28 TV documentados, precio/fecha de SENA con conflicto visible y cero señales; sin errores JavaScript. Ese navegador solo visitó la UI local, no se conectó a CDP ni a portales externos.

## Validación y persistencia

- 295 tests backend afectados aprobados, uno OCR opcional omitido; 10 tests frontend investigativos aprobados. La suite frontend completa previa de esta iteración aprobó 152 tests.
- Ruff/format, Mypy y controles frontend de lint/TypeScript/build correctos. Pruebas incluyen diferencia moderada sin umbral, exclusión partial, fecha de publicación no sustituida por compra, clase profesional distinta, conflictos, cotización embebida y provenance de especificaciones complementarias.
- No migración. Se usaron los almacenes existentes de procesos/documentos/extracción/facts/canonicals; el informe analítico es JSON local, no un nuevo esquema productivo.
- Los contadores de compras demo (1.280), ítems (1.376), comparaciones previas (1.267), oportunidades (218) y casos (2/2) permanecieron iguales.
- El baseline temprano registraba 52 `eureka.radar_run`; la comprobación final ve 54. Sus dos corridas adicionales figuran a las 16:39 y 17:11 Bogotá, **antes del inicio documental a las 19:26**. No se ejecutaron servicios Radar/scoring/alertas desde este ejercicio. Se conserva esa diferencia observada en `database-audit.json`; no se presenta falsamente como baseline idéntico.

## Artefactos locales

Directorio: `backend/.local/investigation-tv-60d-20261103/` (ignorado por Git).

- `discovery.json`, `selection.json`: universo, ventana y selección.
- `inventories.json`, `selected-documents.json`, `inventory-reuse.json`: inventarios, selección y reutilización.
- `sample-result.json`: recibo final de adquisición/extracción.
- `research-report.json`: proyección previa al ciclo.
- `research-cycle-report.json`: resultado final consumido por UI.
- `economic-cycle.json`, `.csv`, `.md`: columnas por producto, evidencia y conflictos.
- `run-summary.json`, `results.md`: resumen y tabla de los 48 procesos.
- `acquisition-audit.json`, `database-audit.json`: recibos y verificación DB de solo lectura.
- `ui-check.json`, `explorar-60dias.png`, `sena-evidencia.png`, `senales-60dias.png`: validación local.

Permanecen en backlog mercado privado, histórico longitudinal, TVEC, LECTOR/extracción agéntica, inflación/TRM y nuevas familias de señales.
