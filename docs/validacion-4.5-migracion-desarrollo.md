# Fase 4.5: migración 0016 en desarrollo

14 de octubre de 2026. Aplicada exclusivamente la migración autorizada en
`public_procurement`, PostgreSQL local puerto 55432:

**0015_eureka_notifications → 0016_eureka_operations**.

Sin reset, truncate, recreación, backfill, ALTER de tablas históricas ni ejecución
del ciclo. Alembic recibió como destino explícito 0016, con validación del predecessor.

## Objetos verificados

Schema `operations` y única tabla nueva `operations.automation_cycle`, **0 filas**.

| Restricción | Definición verificada |
| --- | --- |
| pk_automation_cycle | PRIMARY KEY(id) |
| fk_automation_cycle_radar_run_id_radar_run | FOREIGN KEY(radar_run_id) REFERENCES eureka.radar_run(id) |
| uq_automation_cycle_radar_run_id | UNIQUE(radar_run_id) |
| ck_automation_cycle_status | CHECK: running, completed, completed_with_warnings, failed, skipped |

Columnas: id UUID; started_at/heartbeat_at TIMESTAMPTZ NOT NULL;
finished_at TIMESTAMPTZ nullable; status VARCHAR(32) NOT NULL;
radar_run_id UUID nullable; payload JSONB NOT NULL.

Cuatro índices válidos y listos: índices únicos de PK y radar_run_id, más
`ix_cycle_started(started_at)` y `ix_cycle_status_started(status, started_at)`.

## Históricos

Antes/después: **30 tablas históricas, 41.582 filas, mismos conteos y SHA-256 por tabla**.
Hash calculado sobre filas JSONB ordenadas, incluyendo todos sus campos. Se excluye
de esa comparación la fila Alembic, cuya revisión cambia según lo solicitado.
La única tabla agregada está vacía. La auditoría se repitió tras los smoke de lectura.
Covarachía sigue con score **65**, comprobado tanto en SQL como en el detalle API.

## Smoke de lectura

- GET /api/operations/status: 200; db_connected=true, schema_ready=true, sin diagnóstico pendiente.
- GET /api/operations/cycles: 200, lista vacía.
- GET /api/eureka/notifications: 200.
- GET detalle Eureka de Covarachía: 200, score 65.
- /eureka/operations: HTTP 200 y comprobación de navegador real aprobada. Sin aviso
  de migración pendiente; muestra ausencia de ciclos y últimos ciclos no disponibles.
- Scheduler consultado desde Windows: **not_registered**, próxima real null.
- Próxima teórica informada durante el smoke: **2026-10-14 19:00 America/Bogota**,
  mostrada separadamente y con aclaración de que no acredita tarea registrada.
- Notifications enabled=false, mode=disabled; automatización enabled=false.
- Health conserva OCR disponible, Tesseract 5.5.3.20260724, idioma spa.

No se ejecutó `run-eureka-cycle`, dispatcher, Radar o prueba de envío. No se registró
ninguna tarea Windows ni se alteraron configuración local, reglas, scoring o catálogo.
No se detectaron cambios inesperados.

## Evidencia y siguiente paso

Artefactos ignorados en `backend/.local/operations45/migration016/`:
before.json, after.json, final.json, migration_report.json (columnas/restricciones/índices),
smoke.json, browser.json y operations.png. Scripts de auditoría: migrate016.py y smoke016.py
en backend/.local/operations45/; browser.mjs en el directorio de evidencia.

Pendiente autorización separada para el primer ciclo manual real y su repetición
contra desarrollo. El registro y validación de Task Scheduler real siguen posteriores.
La programación automática de Fase 4.5 todavía no está cerrada.
