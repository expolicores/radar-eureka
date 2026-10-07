# Asunciones parciales — ÉPICA-002: De Documentos a Datos Comparables

Supuestos resueltos durante la generación de las HU de esta épica (convertidos en reglas de negocio configurables o eliminados por reformulación). IDs temporales; el consolidador los renumera.

| Asunción | Categoría | HUs Relacionadas (IDs temporales) | Impacto | Estado |
|---|---|---|---|---|
| Se listan los documentos de contratos candidatos "incluido", "requiere revisión" o sin clasificar (no los "excluido"), porque la clasificación por ítem puede necesitar los documentos | Negocio | HU-014 | Medio | Resuelta |
| Para cada proceso se consultan todos los datasets anuales de Archivos Descarga (dmgg-8hin, nbae-kzan, 3skv-9na7, kgcd-kt7i, f8va-cf4m), en una lista configurable | Datos | HU-014 | Medio | Resuelta |
| Las descargas solo se aceptan desde una lista configurable de dominios oficiales (inicial community.secop.gov.co), sin seguir redirecciones a otros dominios | Seguridad | HU-014, HU-016 | Alto | Resuelta |
| Una consulta o descarga fallida nunca se interpreta como "sin documentos"; reintentos con espera exponencial (3) y tiempo de espera inicial de 120 s por descarga | Integraciones | HU-014, HU-016 | Medio | Resuelta |
| El listado documental se reejecuta sobre todos los procesos objetivo (volumen MVP ≈ 355) con páginas de 1.000 registros; los documentos nuevos no disparan reextracción | Técnico | HU-014, HU-022 | Bajo | Resuelta |
| Orden y palabras clave iniciales de categorías documentales relevantes y excluidas (basadas en D4), configurables; la exclusión prevalece sobre la relevancia | Negocio | HU-015 | Alto | Resuelta |
| "Priorizar por contenido" se resuelve recalculando la priorización cuando un documento resulta vacío, en blanco, duplicado, ilegible o con descarga fallida | Negocio | HU-015, HU-017 | Medio | Resuelta |
| Los comprimidos no consumen cupo; sus archivos internos compiten por los cupos; máximo inicial de 10 contenedores por proceso | Técnico | HU-015, HU-018 | Medio | Resuelta |
| Rango válido del límite de documentos por proceso: 1 a 50 (inicial 8); cambios de configuración no repriorizan procesos ya extraídos | Negocio | HU-015 | Bajo | Resuelta |
| El lote del televisor se toma del objeto o la descripción del contrato; si no se puede determinar, no se descarta por lote y se marca "lote no determinado" para revisión | Negocio | HU-015, HU-022, HU-026 | Medio | Resuelta |
| Límites iniciales de descarga: 200 MB por archivo, 1 s entre solicitudes al mismo dominio, 2 en paralelo, suspensión tras 5 bloqueos consecutivos; User-Agent propio con contacto | Técnico | HU-016 | Medio | Resuelta |
| Archivo vacío: menos de 1.024 bytes o sin contenido estructural | Datos | HU-017 | Bajo | Resuelta |
| Formulario en blanco detectado de forma determinística: documento económico con ≥ 200 caracteres utilizables y 0 valores monetarios (≥ 10.000 o con símbolo de moneda); los escaneados no se marcan | Datos | HU-017 | Medio | Resuelta |
| Deduplicación por hash SHA-256 dentro de cada proceso; el Administrador puede revertir una marca automática con comentario | Datos | HU-017 | Bajo | Resuelta |
| Identificador del archivo interno de un comprimido: `{id_documento}::{ruta interna}`; solo ZIP y RAR; límites iniciales de profundidad 3, 500 archivos, 1 GB y relación 100:1; protegidos nunca se abren | Seguridad | HU-018 | Medio | Resuelta |
| DOCX/DOC se convierten a representación paginada (conservada) para citar "página N"; en hojas de cálculo se usa el valor calculado; límites iniciales de 300 páginas y 100.000 celdas | Técnico | HU-019, HU-021 | Medio | Resuelta |
| Detección de lectura visual: < 50 caracteres utilizables o imagen incrustada ≥ 10 % del área; imágenes a 110 dpi (valor de D4); máximo inicial 60 páginas visuales por proceso | Técnico | HU-020 | Medio | Resuelta |
| La copia de evidencia se conserva para todo documento del que se extrajo algún dato (no solo los usados en señales), sin eliminación automática en el MVP, con verificación de hash al servirla y acceso solo con sesión | Seguridad | HU-021 | Alto | Resuelta |
| Se registra la etapa del precio (adjudicado, contratado, presupuesto o cotización); un ítem con solo precio de presupuesto queda con información insuficiente | Negocio | HU-022, HU-025 | Alto | Resuelta |
| Precedencia entre documentos ante valores distintos: contrato > aceptación > oferta del adjudicatario > evaluación > cotización/presupuesto; el conflicto envía el ítem a revisión | Negocio | HU-022, HU-026 | Medio | Resuelta |
| Una extracción por proceso con el paquete priorizado; tiempo de espera 300 s, 3 reintentos y 3 ejecuciones antes de requerir intervención; el valor de datos abiertos no se entrega al extractor | Técnico | HU-022 | Medio | Resuelta |
| Escala de confianza 0,00–1,00; niveles cualitativos alta/media/baja se mapean a 0,90/0,60/0,30; la confianza no es probabilidad de acierto | Técnico | HU-022, HU-026 | Medio | Resuelta |
| Una reextracción no sobrescribe campos validados por el Administrador; las diferencias quedan como "propuesta de reextracción" | Negocio | HU-022, HU-028 | Medio | Resuelta |
| La base tributaria se determina por valor (unitario y total) solo con declaración explícita; exentos se registran sin IVA con indicador; la coincidencia aritmética con 19 % no determina la base | Negocio | HU-023 | Alto | Resuelta |
| Precio derivado: condiciones 2–5 reportadas por la extracción con soporte, 1 y 6 verificadas de forma determinística; base indeterminada por ausencia de declaración no es incompatibilidad | Negocio | HU-024 | Alto | Resuelta |
| Confianza del precio derivado = mínimo de la confianza de sus insumos × factor configurable (inicial 0,80); redondeo a 2 decimales mitad hacia arriba | Negocio | HU-024 | Medio | Resuelta |
| Catálogo cerrado de motivos de información insuficiente con causa "fuente" o "procesamiento"; la base indeterminada no hace insuficiente al ítem | Datos | HU-025, HU-026 | Alto | Resuelta |
| Mientras el umbral de aceptación no tenga valor, ningún ítem se acepta automáticamente; al fijarlo es obligatoria la fuente de calibración; se permiten umbrales específicos por dato crítico | Negocio | HU-026 | Alto | Resuelta |
| Solo los ítems aceptados (automática o manualmente) quedan disponibles para comparación; los insuficientes por causas de fuente no van a revisión | Negocio | HU-026, HU-028 | Alto | Resuelta |
| Tolerancia aritmética inicial: el mayor entre 0,5 % y COP 100; entre bases distintas solo se comprueba con tasa de IVA documentada; la suma de ítems solo si la tabla es solo de televisores | Negocio | HU-027 | Medio | Resuelta |
| El Revisor puede cerrar una inconsistencia que proviene del documento, dejándola visible como "inconsistencia del documento" | Negocio | HU-027, HU-028 | Bajo | Resuelta |
| La revisión humana no crea ítems nuevos; rangos de corrección (cantidad 1–999.999, valores hasta 10.000 millones, tamaño hasta 150 pulgadas); motivos cerrados de rechazo; control de versión ante cambios concurrentes | Negocio | HU-028 | Medio | Resuelta |
| La desactivación de la IA detiene también el OCR/lectura multimodal con IA; las extracciones en curso terminan; los pendientes se procesan por antigüedad al reactivar | Técnico | HU-029 | Medio | Resuelta |
| El costo y el tiempo de una solicitud de IA se reparten entre sus documentos por tamaño de entrada; factores de estimación de D4; costos en USD por tarifa vigente; sin tarifa el costo es "no estimado", nunca 0 | Técnico | HU-030 | Bajo | Resuelta |
| HU-030 (costo y tiempo) se prioriza Alta y no Crítica porque es medición y no bloquea el flujo principal | Negocio | HU-030 | Bajo | Resuelta |
