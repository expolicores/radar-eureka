# Vigencia conservadora por fecha de recepción

Regla `valid_offer_deadline_required`: `fecha_de_recepcion_de` debe ser una fecha
ISO o un timestamp ISO parseable. No se compara con el día actual. Se rechazan
campo ausente, null, vacío, whitespace, `-` y valores no parseables, incluyendo
timestamps malformados con un prefijo de fecha aparentemente válido.

El adapter de ingestion conserva el valor original como `offer_deadline_raw`.
`SecopProcess.offer_deadline` usa `parse_offer_deadline`; el prefilter de Radar
usa el resultado sin volver a consultar Socrata ni inferir fechas alternativas.

Los descartes conservan en el resultado de Radar y los eventos/logs de Operations:

```json
{
  "reason": "missing_or_invalid_offer_deadline",
  "field": "fecha_de_recepcion_de",
  "raw_value": null,
  "rule": "valid_offer_deadline_required"
}
```

El descarte no es un fallo técnico. No consume el límite de trabajo ni marca el
proceso como atendido; una corrida posterior puede continuar si la fuente incorpora
una fecha válida. Los procesos ya completados conservan su idempotencia; no se
resetean estados ni se reprocesan históricos automáticamente.

Se retira `terminal_phase` como condición dura del prefilter: estado y fase no
excluyen por sí mismos. Los términos versionados se conservan sin modificación.
La fase no preferida puede seguir produciendo una nota de revisión. No había una
regla de descarte por paréntesis; referencia, título y descripción conservan su texto.
Las reglas comerciales, scoring y generación de alertas permanecen iguales; cumplir
esta condición de fecha no garantiza ser candidato ni generar una alerta.

## Auditoría puntual de Socrata, 15/10/2026

Lectura de metadata únicamente, sin ejecutar Radar, enriquecimiento ni persistencia.
Los dos últimos casos fueron seleccionados entre IDs previamente observados por Radar.

| Proceso | Referencia | Valor recibido | Pasa regla de fecha | Prefilter con Boyacá/Casanare y ventana 05–16/10 |
|---|---|---|---|---|
| CO1.REQ.11172206 | FGN-RCS-IPSE-0042-2026 (Presentación de oferta) | `2026-10-16T00:00:00.000` | Sí | `outside_region`: pertenece a Tolima |
| CO1.REQ.11193302 | IETSG-2026-10 | Campo ausente → `null` | No | `missing_or_invalid_offer_deadline` |
| CO1.REQ.11172521 | 012-2026 | `2026-10-13T00:00:00.000` | Sí | `candidate` |
| CO1.REQ.11195041 | SAMC-001-2026 (Manifestación de interés (Menor Cuantía)) (Presentación de oferta) | `2026-10-13T00:00:00.000` | Sí | `no_metadata_match` |
| CO1.REQ.11192819 | 006-2026 | Campo ausente → `null` | No | `missing_or_invalid_offer_deadline` |

La ventana mantiene el límite superior exclusivo. No se agregaron regiones para
forzar el caso Fiscalía, ni términos para hacer pasar el otro caso con fecha válida.

## Migración y activación

`0017_offer_deadline`, desde `0016_eureka_operations`, añade únicamente
`ingestion.secop_process.offer_deadline_raw JSONB NULL`. Sin nuevos índices, FK,
tablas, defaults ni backfill. Los registros históricos quedan en NULL; no se les
inventa una fecha. Las nuevas adquisiciones pueden guardar el valor real de Socrata.
El downgrade elimina solo esta columna y los valores que se hayan adquirido en ella.

La migración se crea y verifica mediante SQL offline; no se aplica a desarrollo.
Antes de activar esta versión del backend se requiere autorizar/aplicar 0017 y
recargarlo. El backend previamente iniciado no se recarga con el esquema 0016.
