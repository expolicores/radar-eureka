# Diagnóstico de disponibilidad de Socrata

Después de una consulta normal completada con `processes_seen == 0`, Radar hace
una petición adicional de solo lectura al mismo dataset `p6dx-8zbt`:

```sql
SELECT max(fecha_de_publicacion_del) AS latest_available_date
LIMIT 1
```

Parámetros SODA: `$select=max(fecha_de_publicacion_del) AS latest_available_date`
y `$limit=1`, en `https://www.datos.gov.co/resource/p6dx-8zbt.json`.
Sin `$where`, paginación, retries ni recuperación de procesos completos. Timeout: 15 s.

Se eligió `fecha_de_publicacion_del` porque es el campo de la ventana remota de
Radar. El máximo global es un indicio de cobertura por fecha de publicación;
no demuestra la hora de carga del dataset ni cobertura por región. No se sustituye
por última actualización ni por la fecha límite de ofertas.

Con ventana `[2026-10-21, 2026-10-24)` (21–23 de octubre incluidos):

| Última fecha disponible en Bogotá | Estado | Interpretación |
| --- | --- | --- |
| 20/10/2026 | `dataset_lag` | Probable rezago respecto del inicio consultado. |
| 23/10/2026 | `no_rows_in_window` | El vacío no parece explicarse por rezago global. |
| No disponible | `diagnostic_failed` | No fue posible verificar disponibilidad. |

Los timestamps con zona se normalizan a UTC y se comparan por día en Bogotá.
Los timestamps flotantes se interpretan bajo una **suposición explícita de zona
del publicador America/Bogota**, registrada en el diagnóstico; no incluyen zona
por definición. Una fecha sin hora conserva precisión de día, sin inventar hora.
La UI muestra Bogotá y no usa la hora actual como fallback.

El resultado se persiste en
`radar_run.metrics.socrata_availability_diagnostic` y se copia a
`cycle.source_summary.socrata_availability_diagnostic`. Los logs de Operaciones
registran el evento con endpoint, dataset, campo, comparación y error sanitizado.
Con procesos, consulta fallida o dry-run se registra `performed=false`.

Un fallo del diagnóstico **no cambia `completed`**, no añade fallos al pipeline,
no amplía la ventana ni inicia otra corrida. No persiste procesos, no evalúa
scoring y no consulta documentos. No requiere migración: usa los JSON existentes.

Referencia del agregado: [Socrata MAX](https://dev.socrata.com/docs/functions/max.html).
Semántica temporal: [floating timestamp](https://dev.socrata.com/docs/datatypes/floating_timestamp.html).
