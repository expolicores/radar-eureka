# Licitaciones.info como agregador y revisión humana de incidencias

Esta iteración elimina el requisito de origen SECOP II de la admisión CDP. No
cambia scoring, categorías, umbrales comerciales, exclusiones metadata-only,
dedupe de alertas, geografía, ventana de siete días, seis búsquedas, paginación,
pausas, retries, OCR ni scheduler. No requiere migración ni ejecuta una corrida.

## Gates retirados y capacidad documental

Los gates estaban en `licitaciones_search_plan.py` (`eligible` dependía de los
identificadores SECOP II), `licitaciones_cdp/services.py` (`not_secop_ii` y exigencia
de CO1.NTC) y `eureka/review_services.py` (filtraba fuentes y exigía identidad SECOP).
El filtro del CLI experimental también excluía fuentes antes del pipeline.

La corrida admite procesos dentro del alcance, recientes, abiertos, con objeto,
entidad, departamento, publicación e identidad estable. El proveedor conserva
todos los resultados consolidados y los motivos de diferimiento. `unknown` en
vigencia se conserva y no inicia documentos automáticamente; no se convierte en
un fallo de origen. La vigencia sigue dependiendo del deadline, no del estado.

La provenance `provider_source` clasifica secop2, secop1, fao, cruz_roja,
universidad, otro_portal y unknown. Se conservan los identificadores y referencia
raw del proveedor. `document_capable` es capacidad técnica, no elegibilidad.

La estrategia documental validada sigue siendo el inventario del portal para
SECOP II. SECOP I y otros orígenes sin estrategia verificada usan inventario vacío
y **el mismo pipeline compartido**, que devuelve `documents_unavailable` y evalúa
metadata-only. No se crean nuevos conectores documentales ni se prueban endpoints.
La interfaz permite una capacidad explícita `licitaciones_inventory` verificada;
los tests la simulan para una fuente externa. Esa capacidad no se infiere de un
enlace PDF ni se activa automáticamente para FAO u otras fuentes.

La publicación, fuente y perfil se comprueban sin otro login automatizado. El
preflight operativo usa la misma request y el mismo 80%, medido sobre metadata
útil del agregador, sin exigir una muestra SECOP. Conserva detección de 401,
JSON inválido, universo genérico y filas insuficientes. El validador SECOP previo
permanece disponible para diagnóstico interno; el comando del adapter utiliza
la comprobación de agregador.

## Identidad exacta

- SECOP II conserva la identidad NTC/REQ existente y el noticeUID exacto; nunca
  se transforma NTC en REQ.
- SECOP I usa `secop1:<numConstancia>` cuando aparece en su URL oficial.
- Si no existe identidad de origen comprobable, se usa el ID estable de contrato
  en el namespace `licitaciones_info:<perfil>:<id>`. No se deduplica por título,
  monto ni parecido entre referencias.
- Sin identificador estable no se inventa una identidad: se conserva el resultado
  incompleto/diferido. Dos fuentes sin identidad exacta común no se fusionan.

El mecanismo de alerta y sus restricciones únicas no cambia. El mismo namespace
se utiliza en la proyección de revisión. No se reescriben alertas históricas.

## Tres bloques de observabilidad

`metrics.event_groups` y la UI separan:

| Bloque | Ejemplos | Efecto |
| --- | --- | --- |
| Descartes del funnel | fuera de alcance, stale, closed, vigencia desconocida diferida, límite, fila incompleta, exclusión metadata, no elegibilidad comercial | Decisión esperada; no es un error |
| Advertencias | conflicto estado/deadline, suspicious_fact, OCR truncado, cobertura parcial, documentos ausentes, metadata-only, origen desconocido | No implica descarte automático |
| Errores | descarga fallida, extracción fallida, red terminal, respuesta inválida, fallo de proceso/fuente | Fallo técnico; se mantiene aislamiento por proceso |

Los errores explícitos conservan severidad de error incluso si su código no está
en el catálogo. Un reintento transitorio es advertencia; no se amplía la política.
Los eventos contienen hora propia, run id, proceso/identidad y, cuando existen,
etapa y fuente. El histórico sin timestamp sigue mostrándose sin hora registrada.
La separación es una proyección: no borra los arrays históricos de incidencias.

## Advertencia hacia Merecen Revisión

Para CDP se exige:

1. Objeto no vacío (mínimo cinco caracteres), entidad y ubicación en Boyacá/Casanare.
2. Publicación parseable.
3. Al menos una señal: monto informado, búsqueda coincidente, score disponible,
   facts documentales o etapa de extracción parcial/structured/consolidación/reutilización.
4. La bandeja predeterminada mantiene exclusión de closed, stale, fuera de alcance
   y filas sin identidad/información mínima.

El deadline desconocido no elimina definitivamente el proceso de revisión; sí
impide documentos automáticos. `review_candidates` de la corrida cuenta solo
recent/open con evidencia suficiente. Un warning sin estos datos no basta para
entrar. Los procesos útiles pueden permanecer aunque fallen documentos o no haya
afinidad confirmada. Las banderas documentales actuales y persistidas siguen
combinándose sin recalcular facts ni bloquear una alerta comercial válida.

La proyección entrega `review_explanations`, con mensajes como «Requiere revisión
por hechos documentales sospechosos» o «Sin documentos disponibles; evaluación
basada en metadata». La UI muestra origen y explicaciones legibles.

## Contadores

Los principales son `processes_total`, `recent_processes`, `open_processes`,
`closed_processes`, `unknown_validity_processes`, `document_capable`, `metadata_only`,
`processed`, `commercially_eligible`, `alert_candidates`, `alerts_created` y
`review_candidates`. Los estados open/closed/unknown corresponden a los recientes;
`document_capable` cuenta recientes abiertos con estrategia técnica disponible.
`processed` incluye intentos que terminan en alerta, no alerta o fallo; `metadata_only`
cuenta decisiones con documentos no disponibles. Un diferido por límite no se
cuenta como procesado. El máximo de tres procesos y dos documentos se conserva.

`by_source` ofrece composición por origen con totales, recientes, abiertos,
procesados, alertas y candidatos a revisión. Las métricas SECOP II anteriores se
mantienen como composición, sin controlar la admisión.

## Validación offline con evidencia existente

Reporte local: `backend/.local/aggregator-review-validation/offline_validation.json`.
Reutiliza el discovery R3 del **22/10/2026 09:16:56 Bogotá**; no afirma vigencia
actual fuera de ese instante. Sin requests ni escrituras en DB.

Nueve procesos SECOP I eran recent/open en ese snapshot y resultan revisables por
metadata: PM-MC-003-2026, MC-MJ-056-2026, MP-MC-0028-2026, PER-MINC-002-2026,
PC-MGS-MCW-006-2026, PMP-MC-002-2026, PC-MGS-MCW-005-2026, MP-MC-0026-2026 y
PMSC-MC-02-2026. Se verifica su identidad por constancia oficial; no se descarga.
Esto prueba admisión y revisión útil, no que todos producirán alerta ni que los
nueve pasarán el límite de procesamiento en una corrida.

Los resultados persistidos de CMI-2026078, CM-MC-02-2026 y SMC MP 032 2026 conservan
sus suspicious facts y son revisables en ese instante. MRAM-MC-066-2026 conserva
OCR truncado/cobertura parcial pero está cerrado y continúa excluido por vigencia.
Algunos warnings ya eran revisables antes; no se atribuye su aparición al cambio.

Las pruebas automatizadas cubren fuentes SECOP I/II y externas, estrategia
documental verificada frente a metadata-only, identidad, gates restantes,
advertencias útiles frente a basura, separación de eventos, timestamps y UI.
