# Fechas propias y orden de las tablas de Eureka/CDP

## Resultado dentro de una corrida

`eureka.radar_run_process` no tenía created_at/inserted_at propio: solo id,
run_id, dataset_id, secop_id y result JSON. Los timestamps de la corrida, estado
global del proceso y alertas representan otros eventos y no se reutilizan.

Se añade **`result.recorded_at`**, con timestamp UTC capturado al insertar por
primera vez ese resultado en esa corrida. Es inmutable en actualizaciones de
progreso, documentos y decisión. El servicio CDP conserva el mismo valor en su
resultado en memoria. Una corrida nueva registra su propio momento; no hereda
el registro de una corrida anterior.

No requiere migración: es un campo nuevo en el contrato JSON existente. No hay
backfill. Una fila histórica sin el campo conserva la ausencia, incluso si se
actualiza después. La UI muestra «No registrada (histórico)».

Orden PostgreSQL generado por SQLAlchemy:

```sql
ORDER BY CAST(eureka.radar_run_process.result ->> 'recorded_at' AS VARCHAR)
         DESC NULLS LAST
```

Los valores nuevos se escriben siempre como ISO 8601 UTC, de modo que el orden
textual coincide con el temporal. La UI también ordena una copia por ese mismo
campo para respetar el orden mientras recibe resultados de una corrida en curso.
Los valores ausentes o inválidos se colocan al final en la UI. No hay otro criterio.

## Primera entrada a Merecen Revisión

Se reutiliza **`review_first_seen_at`** existente, sin tocar `reviewed_at` ni
crear otra columna. Su persistencia insert-only mantiene el evento de primera
entrada aunque aparezcan otras corridas, fuentes o evaluaciones humanas.

La proyección actual filtra y ordena en memoria antes de paginar. El criterio
exacto equivale a:

```sql
ORDER BY review_first_seen_at DESC NULLS LAST
```

No se ejecuta un ORDER BY SQL nuevo para esta vista. La clave Python es:

```python
key=lambda r: (
    (first_seen := moment(r.get("review_first_seen_at"))) is None,
    -first_seen.timestamp() if first_seen else 0,
)
```

Se retira el relleno automático durante lecturas de históricos: leer una fila
sin fecha no significa que esa fuera su entrada original a revisión. Los registros
sin fecha siguen NULL/no registrados. Los backfills ya existentes se conservan
con su origen y advertencia histórica; no se alteran datos operativos.

Ambas columnas se muestran en America/Bogota con segundos, cada una usando
exclusivamente su propio evento. Nunca se usa publicación, deadline, fecha del
proveedor, reviewed_at, fecha de alerta ni inicio/fin de corrida como fallback.

## Ejemplo sintético de orden

| Posición | Detalle de corrida: recorded_at Bogotá | Revisión: review_first_seen_at Bogotá |
| --- | --- | --- |
| 1 | A · 22/10/2026 20:19:40 | B · 22/10/2026 20:19:40 |
| 2 | B · 22/10/2026 20:19:20 | A · 22/10/2026 20:19:20 |
| 3 | C · No registrada (histórico) | C · No registrada (histórico) |

Los nombres A/B/C y las fechas son ejemplos de pruebas; no son timestamps
reconstruidos de registros reales. No se modifica scoring, filtros, dedupe,
vigencia, alertas, criterios de revisión ni el pipeline de procesamiento.
