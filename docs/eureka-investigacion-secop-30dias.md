# Segundo ejercicio investigativo: televisores, 30 días

La UI muestra ahora el [tercer ejercicio real de 60 días](eureka-investigacion-secop-60dias.md).
Este documento conserva los resultados históricos de la muestra de 30 días.

Actualización posterior: la [reconstrucción económica por etapa](eureka-investigacion-ciclo-economico.md)
reutiliza los 12 procesos confirmados y recupera precios contractuales adicionales. Las
cifras de este documento conservan el resultado de la proyección anterior.

Validación: 231 tests backend afectados correctos (un test OCR opcional omitido),
más seis regresiones posteriores de confirmación documental correctas; 147 tests frontend.
Ruff/format, Mypy, ESLint, TypeScript/build y los 13 contratos de importación correctos.
Smoke visual de Explorar, detalle real y Señales en Edge, sin errores JavaScript.

Ventana: **04/10/2026 inclusive–03/11/2026 exclusivo**, America/Bogota (hasta el 02/11).
Fuentes: Socrata SECOP II procesos `p6dx-8zbt`, contratos `jbjy-vk9h`, documentos `dmgg-8hin`; binarios SECOP.

## Alcance y resultado

Discovery amplio: 6.329 procesos únicos; 2.175 con estado Seleccionado. Muestra intencional: **18 procesos**, ocho con referencia explícita a televisores (uno de mantenimiento como control) y diez con objetos amplios. No se revisaron documentalmente todos los 2.175 candidatos ni se afirma cobertura nacional exhaustiva.

Inventario: 334 documentos. Seleccionados/disponibles: 163; 143 descargas nuevas y 20 reutilizaciones. Cero fallos de descarga. **9 extracciones fallidas y 16 documentos con cobertura parcial**; no equivalen a descargas fallidas. OCR real con límite de 20 páginas sin ampliarlo.

Adquisición/extracción: 03/11/2026 13:08:19–13:45:08 Bogotá, 36 min 49 s. Las reglas investigativas posteriores se reprocesaron offline sobre fragmentos existentes; sin nuevas descargas ni OCR.

**12 procesos con presencia de TV confirmada en documentos oficiales**, 29 observaciones normalizadas. Confirmar producto solicitado no confirma compra ni precio adjudicado. Tres filas con precio legible/confiable en su etapa documental; **cero precios unitarios de compra adjudicada verificables para el comparador**. Cero comparaciones monetarias sustentadas y cero señales.

## Procesos seleccionados

| Proceso | Identidad | Entidad | Ubicación | TV documental | Docs seleccionados | Observaciones | Disposición |
|---|---|---|---|---|---:|---|
| CRE009-CEPEM2026 | CO1.REQ.11161094 | SUCRE - CENTRO EDUCATIVO PITA EN MEDIO | Santiago De Tolú / Sucre | No confirmado | 1 | 1 | conflicting_document_scope |
| IEJH-CD-09-2026 | CO1.REQ.11194883 | INSTITUCION EDUCATIVA JUAN HURTADO | Belén De Umbría / Risaralda | No confirmado | 6 | 0 | tv_not_confirmed_in_processed_documents |
| C29-2026 | CO1.REQ.11241666 | INSTITUCION EDUCATIVA PIO XI | La Unión / Antioquia | Sí | 14 | 2 | no_reliable_awarded_unit_price |
| RE-00102026 | CO1.REQ.11242744 | INSTITUCION ETNOEDUCATIVO LA GLORIA | Manaure / La Guajira | Sí | 9 | 4 | no_reliable_awarded_unit_price |
| MC-070-2026 | CO1.REQ.11253117 | Universidad del Atlántico | Puerto Colombia / Atlántico | Sí | 3 | 0 | no_reliable_awarded_unit_price |
| IEGM-012-2026 | CO1.REQ.11261672 | INSTITUCION EDUCATIVA GABRIELA MISTRAL. | Jamundí / Valle del Cauca | Sí | 8 | 0 | no_reliable_awarded_unit_price |
| CRE004-CENE2026 | CO1.REQ.11264117 | CENTRO EDUCATIVO NUEVA ERA | Santiago De Tolú / Sucre | Sí | 2 | 1 | no_reliable_awarded_unit_price |
| 0971-2026 | CO1.REQ.11266026 | COMPRADOR ESE CARMEN EMILIA OSPINA PERFIL | Neiva / Huila | Sí | 9 | 3 | no_reliable_awarded_unit_price |
| MC-VLL-CNPB-0022-2026 | CO1.REQ.11075456 | SENA REGIONAL VALLE Grupo Administrativo CNPB | Buenaventura / Valle del Cauca | Sí | 10 | 2 | no_reliable_awarded_unit_price |
| MIN-170-2026 | CO1.REQ.11156708 | Universidad del Atlántico | Puerto Colombia / Atlántico | No confirmado | 4 | 0 | tv_not_confirmed_in_processed_documents |
| CHQ-SAMC-013-2026 (Manifestación de interés (Menor Cuantía)) (Presentación de oferta) | CO1.REQ.11162361 | MUNICIPIO DE CHIQUINQUIRA+ | Chiquinquirá / Boyacá | Sí | 17 | 1 | no_reliable_awarded_unit_price |
| SPD-MC-048-2026 | CO1.REQ.11168282 | GOBERNACIÓN DEPARTAMENTO DEL PUTUMAYO | Mocoa / Putumayo | Sí | 4 | 1 | no_reliable_awarded_unit_price |
| MC-15-2026 | CO1.REQ.11181537 | INSTITUTO DE DEPORTE CULTURA Y TURISMO DE SUBACHOQUE | Subachoque / Cundinamarca | Sí | 32 | 1 | no_reliable_awarded_unit_price |
| PN MEMAZ MIC 045 2026 | CO1.REQ.11181681 | POLICÍA METROPOLITANA DE MANIZALES | Manizales / Caldas | Sí | 6 | 1 | no_reliable_awarded_unit_price |
| INEM-SI-01-2026 (Presentación de oferta) | CO1.REQ.11210541 | IED INEM JOSE EUSTASIO RIVERA | Leticia / Amazonas | Sí | 21 | 12 | no_reliable_awarded_unit_price |
| PMC 045 - 2026 | CO1.REQ.11244663 | ALCALDIA DE SANTO TOMAS, ATLANTICO | Santo Tomás / Atlántico | No confirmado | 4 | 0 | tv_not_confirmed_in_processed_documents |
| INVITACIÓN No. DHMA-SECD-IMC-037 DE 2026 | CO1.REQ.11251999 | ALCALDIA MUNICIPAL DE EL AGRADO HUILA | Agrado / Huila | No confirmado | 5 | 0 | insufficient_document_coverage |
| 310.021.002.109-2026 | CO1.REQ.11287097 | Secretaría de Educación - Alcaldía de Tuluá | Tuluá / Valle del Cauca | No confirmado | 8 | 0 | insufficient_document_coverage |

## Productos normalizados y provenance

Observaciones, no unidades compradas. El JSON conserva cantidades, totales, impuestos, fecha, proveedor cuando existe, advertencias, alternativas y ubicación exacta de evidencia. Los duplicados binarios no son evidencia independiente.

| Proceso | Pulgadas | Marca/modelo | Resolución/panel/Smart | Cantidad | Unitario COP | Etapa | Precio fiable en esa etapa | Documento/página |
|---|---:|---|---|---:|---:|---|---|---|
| CRE009-CEPEM2026 | 50 | — / — | 4k / — / Smart=True | — | — | contract | False | CONTRATO CRE009-CEPEM2026 SUMINISTRO MEDIOS PEDAGOGICOS.pdf p.1 |
| C29-2026 | 50 | — / — | 4k / — / Smart=True | — | — | offer | False | 10 cotizacion y docuemntos lida rodriguez.pdf p.1 |
| C29-2026 | 50 | SAMSUNG / — | 4k / — / Smart=True | — | — | offer | False | 12 cotizacion y docuemntos natalia botero.pdf p.1 |
| RE-00102026 | 65 | — / — | 4k / LED / Smart=True | 1 | 3970000 | offer | False |  p.? |
| RE-00102026 | 65 | — / — | 4k / LED / Smart=True | 1 | 3970000 | offer | False |  p.? |
| RE-00102026 | 65 | — / — | 4k / LED / Smart=True | 1 | 3970000 | budget | False |  p.? |
| RE-00102026 | 65 | — / — | — / LED / Smart=True | — | — | offer | False | 1 Propuesta Economica (1).pdf p.2 |
| CRE004-CENE2026 | 55 | — / — | — / — / Smart=True | 2 | 2610000 | specifications | True |  p.? |
| 0971-2026 | 32 | — / — | — / LED / Smart=True | — | — | specifications | False | ESTUDIO PREVIO.pdf p.3 |
| 0971-2026 | 32 | — / — | — / LED / Smart=None | — | — | specifications | False | ESTUDIO PREVIO.pdf p.5 |
| 0971-2026 | 32 | — / — | hd / LED / Smart=True | — | — | offer | False | COTIZACION.pdf p.1 |
| MC-VLL-CNPB-0022-2026 | 65 | — / — | 4k / — / Smart=True | 3 | 2761773.62 | budget | False |  p.? |
| MC-VLL-CNPB-0022-2026 | 65 | — / — | 4k / — / Smart=True | 3 | 2448492.00 | budget | False |  p.? |
| CHQ-SAMC-013-2026 (Manifestación de interés (Menor Cuantía)) (Presentación de oferta) | 58 | — / — | 4k / LED / Smart=True | — | — | other | False | ANEXOS CHQ-SAMC-013-2026.pdf p.1 |
| SPD-MC-048-2026 | 75 | SAMSUNG / — | 4k / MINI LED / Smart=True | 2 | — | contract | False | CLAUSULADO  ADICIONAL 1810- 2026 SPD-MC-048-2026 PLANEACION.pdf p.1 |
| MC-15-2026 | 55 | — / — | 4k / — / Smart=None | — | — | specifications | False | 5. ESTUDIOS PREVIOS  SOFTWARE ajustado.pdf p.6 |
| PN MEMAZ MIC 045 2026 | 75 | — / — | — / — / Smart=None | — | — | specifications | False | 1. ESTUDIO PREVIO.pdf p.1 |
| INEM-SI-01-2026 (Presentación de oferta) | 55 | — / — | full_hd / LED / Smart=True | 4 | 3500000 | offer | True |  p.? |
| INEM-SI-01-2026 (Presentación de oferta) | 65 | — / — | full_hd / LED / Smart=True | 1 | 5050000 | offer | True |  p.? |
| INEM-SI-01-2026 (Presentación de oferta) | 40 | — / — | full_hd / LED / Smart=True | — | — | offer | False | COTIZACION AMAZON FROZEN - INEM MOBILIARIO COMPUTO.pdf p.5 |
| INEM-SI-01-2026 (Presentación de oferta) | 40 | — / — | — / — / Smart=None | — | — | offer | False | COTIZACION AMAZON FROZEN - INEM MOBILIARIO COMPUTO.pdf p.14 |
| INEM-SI-01-2026 (Presentación de oferta) | 50 | — / — | full_hd / LED / Smart=True | — | — | offer | False | COTIZACION AMAZON FROZEN - INEM MOBILIARIO COMPUTO.pdf p.102 |
| INEM-SI-01-2026 (Presentación de oferta) | 40 | — / — | full_hd / — / Smart=True | — | — | specifications | False | ESTUDIO PREVIO INEM.pdf p.16 |
| INEM-SI-01-2026 (Presentación de oferta) | 50 | — / — | full_hd / — / Smart=True | — | — | specifications | False | ESTUDIO DEL SECTOR Y COSTOS.pdf p.30 |
| INEM-SI-01-2026 (Presentación de oferta) | 65 | — / — | — / — / Smart=True | — | — | specifications | False | ESTUDIO DEL SECTOR Y COSTOS.pdf p.30 |
| INEM-SI-01-2026 (Presentación de oferta) | 65 | — / — | 4k / — / Smart=True | — | — | specifications | False | ESTUDIO DEL SECTOR Y COSTOS.pdf p.31 |
| INEM-SI-01-2026 (Presentación de oferta) | 65 | — / — | full_hd / — / Smart=True | — | — | other | False | PLIEGO DE CONDICIONES DEFINITIVOS.pdf p.57 |
| INEM-SI-01-2026 (Presentación de oferta) | 50 | — / — | — / LED / Smart=True | — | — | other | False | PLIEGO DE CONDICIONES DEFINITIVOS.pdf p.61 |
| INEM-SI-01-2026 (Presentación de oferta) | 40 | — / — | full_hd / LED / Smart=None | — | — | other | False | PLIEGO DE CONDICIONES DEFINITIVOS.pdf p.112 |

## Comparabilidad y precios

Conteos de pares de observaciones entre entidades (no grupos transitivos, ni número de compras independientes): `{"partially_comparable": 30, "not_comparable": 299}`.

Ejemplos parciales: SENA Valle y La Gloria describen 65 pulgadas 4K Smart; Pío XI e INEM Leticia describen 50 pulgadas; faltan equivalencia técnica completa y precios de compra confirmados. Las pantallas interactivas de Subachoque no se equiparan automáticamente a televisores de consumo.

Precios legibles: Nueva Era, 55 pulgadas, cantidad 2, $2.610.000 (especificaciones; contrato sin firma publicada); INEM Leticia, 55 pulgadas, cantidad 4, $3.500.000 y 65 pulgadas, cantidad 1, $5.050.000 (oferta sin aceptación verificada). No son tres compras adjudicadas comparables.

Otras cifras se conservan con reservas: La Gloria $3.970.000/65 pulgadas, encabezados ambiguos; SENA $2.448.492 y promedio $2.761.773, estudio de mercado. En Pío XI las cotizaciones sí contienen cifras, pero sus tablas y marcas contradictorias no producen un precio de adjudicación verificable en esta extracción. No se presume que toda cifra visible esté normalizada correctamente.

Pita: encabezado sobre TV pero cuerpo sobre talleres pedagógicos, conflicto de alcance; no compra confirmada. Juan Hurtado: mantenimiento, no adquisición. ESE Carmen: 14 TV + cableado/instalación por monto global; no se divide ese monto por 14. Los ejemplos de experiencia del proveedor se excluyen del alcance actual.

Las comparaciones por pares admiten dos compras de entidades distintas; no exigen cinco. Ningún par real superó los requisitos de precio/etapa/cantidad/equivalencia. Umbrales investigativos existentes 30% mismo modelo / 50% equivalente; no se tocaron reglas Radar.

## Extracciones fallidas

| Proceso | Documento | Código |
|---|---|---|
| MC-070-2026 | OFERTA ECONOMICA  MC-070-2026.pdf | page_limit |
| MC-15-2026 | EVALUACION TECNICA FINAL PROCESO MC-15-2026.xlsx | corrupt_file |
| MC-15-2026 | EVALUACION JURIDICA FINAL PROCESO MC-15-2026.xlsx | corrupt_file |
| MC-15-2026 | EVALUACION JURIDICA FINAL PROCESO MC-15-2026.xlsx | corrupt_file |
| MC-15-2026 | EVALUACION JURIDICA FINAL PROCESO MC-15-2026.xlsx | corrupt_file |
| MC-15-2026 | EVALUACION JURIDICA FINAL PROCESO MC-15-2026.xlsx | corrupt_file |
| MC-15-2026 | EVALUACION TECNICA FINAL PROCESO MC-15-2026.xlsx | corrupt_file |
| MC-15-2026 | EVALUACION TECNICA FINAL PROCESO MC-15-2026.xlsx | corrupt_file |
| MC-15-2026 | EVALUACION TECNICA FINAL PROCESO MC-15-2026.xlsx | corrupt_file |

Los ocho XLSX de evaluación de Subachoque fallaron con `corrupt_file`; no se afirma que su contenido sea inexistente. La oferta de Universidad del Atlántico falló con `page_limit`. Cobertura parcial/ausencia de TV en fragmentos no demuestra ausencia en el proceso completo.

## Persistencia y UI

Informe local real publicado en Explorar compras (`/explorar`) y Señales (`/senales`), separado de demo. Permite revisar los 18 procesos, inventario, productos y evidencia, incluidos casos insuficientes. Endpoint de lectura `/api/v1/investigation/research`; no inicia adquisiciones.

Sin migración. Se reutilizaron documentos/extracción nativa/OCR/facts/canonicals; reglas investigativas versionadas `structured-tv-research-v3` y `canonical-tv-research-v3`. No se ejecutó Radar, scoring comercial, CDP, alertas, mercado privado, TVEC ni benchmark histórico.

Conteos protegidos antes/después: `{"before": {"ingestion.purchase": 1280, "ingestion.purchase_item": 1376, "comparison.item_comparison": 1267, "eureka.opportunity": 218, "eureka.radar_run": 52, "investigation.case": 2, "investigation.case_item": 2}, "after": {"ingestion.purchase": 1280, "ingestion.purchase_item": 1376, "comparison.item_comparison": 1267, "eureka.opportunity": 218, "eureka.radar_run": 52, "investigation.case": 2, "investigation.case_item": 2}, "unchanged": true, "acquisition_attempts": 143, "acquisition_statuses": {"available": 143}, "comparability_counts": {"partially_comparable": 30, "not_comparable": 299}, "summary": {"processes_found": 6329, "mature_metadata_candidates": 2175, "document_candidates": 18, "processes_with_documented_tv": 12, "tv_observations": 29, "reliable_unit_prices": 3, "reliable_purchase_unit_prices": 0, "documents_selected": 163, "documents_downloaded": 163, "documents_failed": 0, "extraction_failed": 9, "partial_coverage_documents": 16, "disposition_counts": {"conflicting_document_scope": 1, "tv_not_confirmed_in_processed_documents": 3, "no_reliable_awarded_unit_price": 12, "insufficient_document_coverage": 2}, "comparisons_possible": 0, "signals_generated": 0, "processes_without_tv_confirmation": ["CO1.REQ.11161094", "CO1.REQ.11194883", "CO1.REQ.11156708", "CO1.REQ.11244663", "CO1.REQ.11251999", "CO1.REQ.11287097"]}}`.

Artefactos completos locales: `backend/.local/investigation-tv-30d-20261103/`: discovery, selección, inventarios, contratos, recibo original, fragmentos, informe, CSV de productos y auditoría de adquisición. No se incluyen documentos ni texto sensible en Git.

Limitaciones: muestra intencional, Socrata puede rezagarse; paginación sin snapshot; publicación del proceso no equivale a fecha de compra; estados Seleccionado no garantizan firma; 16 coberturas parciales; formatos de tablas heterogéneos. No se declara inexistencia de sobreprecios ni representatividad estadística nacional.
