# Alertas provisionales cuando el inventario documental está vacío

`ExistingRadarPipeline.enrich` conserva el intento de `documents.sync`. Si responde
un inventario vacío, devuelve la oportunidad ya persistida con
`enrichment_status=documents_unavailable`, `document_status=unavailable` y
`evidence_level=metadata_only`. No ejecuta descarga, extracción ni consolidación.
Un error de transporte o de descarga conserva el tratamiento de fallo reintentable.

Radar permite evaluar ese resultado sin contarlo como enriquecimiento documental.
Solo un candidato aceptado por los filtros actuales puede producir esta alerta.
No se alteran el catálogo, score, región, ventana ni la condición de fecha de recepción.
La alerta tiene `confirmed=false`, revisión obligatoria y razones de metadata.
No se representa UNSPSC o metadata como producto confirmado documentalmente.

El resultado de proceso y snapshot de alerta conservan las marcas documentales.
Operations lo muestra como advertencia, sin incrementar los fallos técnicos; el ciclo
puede terminar `completed_with_warnings`. El aviso de UI es:

> No se pudo validar documentalmente, pero por metadatos parece viable. Revisar manualmente.

## Persistencia e idempotencia

Se reutilizan los JSONB y columnas de estado actuales, sin migración ni backfill.
El estado Radar es `pending_documents`; no se marca `completed`. La ausencia normal
de inventario restablece el contador de intentos técnicos para permitir futuras consultas.
Las siguientes corridas siguen llamando `documents.sync` para esos procesos.

La restricción existente de alerta por oportunidad/tipo/versión evita duplicados.
Cuando una evaluación posterior confirma afinidad documental, la misma alerta se
actualiza con sus razones y snapshot documental. Conserva ID, fecha y corrida originales,
además de `initial_metadata_alert` (snapshot y razones iniciales), `evidence_run_id` y
`evidence_updated_at` para auditar la ampliación. Repetir el estado provisional no
sobrescribe su snapshot; una alerta confirmada tampoco se degrada ni se sobrescribe.
La oportunidad mantiene su identidad y su scoring existente.

Los estados fallidos históricos no se resetean mediante backfill. Solo cuando el último
resultado contiene exactamente el antiguo ValueError por inventario vacío, la lectura
de estado lo considera pendiente documental sin agotar intentos técnicos. El contador
se reinicia únicamente si una próxima corrida llega a reclamar ese proceso. Otros
errores agotados conservan su límite. Los pendientes se evaluarán en la próxima
corrida manual; no se ejecuta una corrida ni se generan alertas artificiales como parte
de la implementación.

## Validación dirigida

Pruebas aisladas cubren inventario vacío, error real de consulta, alerta provisional,
reintentos repetidos, aparición posterior de documentos y actualización SQL en SQLite
efímero sin duplicados. Las pruebas HTTP/UI cubren flags, aviso y ausencia de textos de
confirmación documental para alertas provisionales.

La consulta puntual del 16/10/2026 para `CO1.REQ.11195961` devuelve Casanare,
publicación `2026-10-13` y recepción `2026-10-16T00:00:00.000`. La función de candidatos
lo acepta por papelería, impresoras y suministro de elementos. Solo se leyó metadata;
no se ejecutó su pipeline contra desarrollo ni se insertó una alerta real de prueba.
# Exclusión configurable por objeto, solo en el fallback provisional Socrata

Política: `backend/config/eureka_metadata_alert_exclusions.v1.json`, con `version: 1`,
`enabled` booleano y `terms` (inicialmente solo transporte, acueducto, arrendamiento,
agua potable). Puede editarse manualmente; se carga al comenzar cada corrida, sin
modificar código para cambiar términos. La ruta puede configurarse con
`EUREKA_METADATA_ALERT_EXCLUSIONS_PATH`.

`eureka.metadata_alert_policy` valida el JSON con Pydantic siguiendo el patrón de
configuración de Eureka. `RadarService.run` aplica la política después de
`evaluate_alert` y antes de persistir una nueva alerta, exclusivamente cuando la
decisión Socrata ya tiene `create=true`, `confirmed=false`, `evidence_level=metadata_only`
y `document_status=unavailable`. El evaluador compartido no cambia; CDP no consume
esta política. Tampoco interviene en discovery, scoring, canonicals o extracción.

Objeto evaluado: `SecopProcess.description` (descripción principal de Socrata), o
`title` si aquella está vacía. No se concatena entidad, municipio, facts, documentos
ni otros campos. Se normalizan mayúsculas, tildes y espacios; comparación substring
sin stemming ni fuzzy matching. Si hay varias coincidencias, se elige primero el
término normalizado más largo y se desempata por orden del JSON.

La coincidencia cambia únicamente `AlertDecision.create` a false y agrega evidencia:
`reason=metadata_object_exclusion`, `metadata_exclusion_term`, objeto y versión de
política en el snapshot/razones y resultado de proceso. El score, prioridad y demás
evaluación se conservan. El proceso queda `no_alert` y `documents_pending`, conserva
persistencia y reintento documental. Si luego obtiene confirmación documental, esta
política no interviene y se usa el dedupe existente sin cambios.

La corrida guarda `metrics.metadata_alerts_excluded_by_object` y
`metrics.metadata_alert_exclusions` (identidad SECOP exacta, objeto, matched_term,
reason). El ciclo operativo copia el contador al embudo y lo presenta como
«Alertas provisionales excluidas por objeto». Los GET `/api/eureka/radar-runs` y
`/api/eureka/radar-runs/{run_id}` exponen `metrics`; no hay nuevas rutas ni migración.
El contenido/configuración aplicados quedan en `config_snapshot.metadata_alert_exclusions`.

Con `enabled=false` el filtro no excluye. Un JSON ausente/inválido se rechaza
explícitamente: solo los candidatos provisionales quedan sin alerta, con
`reason=metadata_exclusion_policy_invalid` y contador `metadata_exclusion_policy_errors`.
No se inventa una política de respaldo ni se permite silenciosamente la alerta.
Las decisiones documentales siguen funcionando y el error queda visible por proceso,
en configuración de corrida y en el embudo. No se cambia el estado global para bloquear
las alertas documentales válidas de otros procesos.

Merecen Revisión conserva sus criterios, filtros y orden. Un proceso que cumple sus
reglas puede seguir apareciendo con «Alerta provisional excluida por objeto: término».
La vista solo muestra el motivo ya persistido; no vuelve a evaluar ni aplica esta
política a sus procesos históricos. Ninguna alerta anterior se borra o modifica.

Validación offline sobre decisiones Socrata persistidas (sin nueva corrida):

| Proceso | Coincidencia | Resultado simulado |
| --- | --- | --- |
| INVITACION PÚBLICA No RE ITEF 030-2026 | transporte | No crear alerta provisional |
| SMIC-051-2026 | acueducto | No crear alerta provisional |
| MC-MIN-044-2026 | agua potable | No crear alerta provisional |
| SI-CPMSSRVIT-002-2026 | arrendamiento | No crear alerta provisional |
| CM-006-2026 | Ninguna | Conservar decisión anterior |

La evidencia local está en
`backend/.local/metadata-alert-exclusion-validation/offline_validation.json`.
Es una simulación de la política sobre resultados anteriores: no constituye una
corrida ni reescribe ese historial. Pruebas cubren normalización, alcance, invalid/disabled,
conservación de score/resultados, contador, revisión humana y confirmación documental posterior.

