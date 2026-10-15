# Fase 4.5: operación local de Eureka

Implementación técnica del 14 de octubre de 2026. **0016 aplicada a desarrollo con autorización;
sin ciclo real, tarea Windows registrada o correos reales.** [Auditoría de migración](validacion-4.5-migracion-desarrollo.md).
La programación
automática sigue pendiente de las validaciones y autorizaciones operativas finales.

## Arquitectura

Task Scheduler / CLI → AutomationCycleService → Radar → evaluación de cobertura global
→ dispatcher → métricas y logs. PowerShell solo configura o lanza el CLI. FastAPI
expone consultas y una acción manual explícita; no incorpora scheduler ni ejecuta ciclos al arrancar.
La [ejecución manual desde UI](ejecucion-manual-eureka-ui.md) utiliza el mismo servicio.

Los CLI existentes `run-eureka-radar` y `send-eureka-notifications` se mantienen
independientes. Operations consume puertas públicas `*.services`. Ingestion expone
su fuente Socrata mediante `fetch_secop_processes`; extraction expone un probe OCR
saneado mediante `ocr_runtime_status`. No se duplican adquisición, OCR o decisiones.

## Migración 0016_eureka_operations

Cadena: 0015_eureka_notifications → 0016_eureka_operations.
Crea únicamente schema `operations` y tabla `operations.automation_cycle`:

| Columna | Tipo / restricción |
| --- | --- |
| id | UUID, PK |
| started_at, heartbeat_at | TIMESTAMPTZ NOT NULL |
| finished_at | TIMESTAMPTZ nullable |
| status | VARCHAR(32) NOT NULL, CHECK de los cinco estados aprobados |
| radar_run_id | UUID nullable, UNIQUE, FK a eureka.radar_run(id) |
| payload | JSONB NOT NULL, contrato schema_version=1 |

Índices `ix_cycle_started(started_at)` y `ix_cycle_status_started(status, started_at)`.
El payload agrupa trigger, host, app_version, config_snapshot permitido,
notification_summary, metrics, reasons, decision_reasons, errors, events, duraciones,
processes_seen y failures. Candidates, enriched, alert_created y contadores de
notificaciones están en `payload.metrics`. La duración total está en duration_ms.
Las columnas relacionales permiten consultar estado/fechas y validar la relación;
el resto del resumen operacional tiene contrato versionado JSONB.

`radar_run` no representa el coordinador, las notificaciones ni intentos que pierden
el lock antes de iniciar Radar. Por eso se añade una entidad propia. El UUID Radar
se reserva antes de la etapa; la FK se vincula cuando Radar confirma su persistencia.
Recovery puede reconciliar el UUID reservado mediante la consulta pública de Radar.

Sin backfill, ALTER de tablas históricas o cambios de sus datos. Downgrade elimina
únicamente la tabla y schema operations, perdiendo el historial operacional propio.
Upgrade/downgrade/upgrade se probó exclusivamente en una base *_test.

## Ciclo, lock y recovery

Lock PostgreSQL session-level **741045**, diferente de Radar 741041 y notifications
741044. Se mantiene en una conexión dedicada; se verifica al observar progreso y
antes de avanzar a otra etapa. No se usa un fichero PID como autoridad.

Si está ocupado, el intento se persiste con status=skipped, reason=already_running,
sin iniciar Radar ni dispatcher. Los ciclos manuales independientes conservan sus
propios locks; si interfieren, el coordinador registra el fallo y no despacha a ciegas.

Solo un nuevo propietario del lock reconcilia ciclos running abandonados: failed,
coordinator_interrupted, fecha final y duración. STALE_MINUTES añade diagnóstico de
antigüedad, no es criterio suficiente de muerte. La pérdida del lock impide avanzar.

| Resultado | Comportamiento |
| --- | --- |
| Radar completed | Dispatcher habilitado según configuración |
| Radar partial por fallos individuales, sin error global | completed_with_warnings; dispatcher permitido |
| Radar failed, interrupted o limited | failed, coverage_complete=false, sin dispatcher |
| Notifications disabled | Resultado esperado, sin warning por ese motivo |
| Fallo/retryable de notificación | completed_with_warnings, conservar estado/reintentos existentes |
| Error de logs/retención | Diagnóstico saneado; no declarar éxito limpio |

Un fallo global tampoco permite enviar pendientes anteriores. Tras un reinicio o
interrupción entre etapas, el siguiente ciclo satisfactorio consulta pendientes y
reintenta retryable según lease/límites existentes. No hay reintento infinito del
ciclo: se invoca una vez y termina. Radar limita intentos de procesos; OCR conserva
sus límites; notifications conserva sus plazos e idempotencia de proveedor.

Si DB/config impide iniciar el ciclo, el CLI genera, si el disco lo permite, un
diagnóstico local `persisted=false`, sin secretos; no inventa un ciclo persistido.

## Métricas y logs

Embudo: SECOP recibidos → fuera de ventana/región → ya vistos → prefilter rechazado
→ candidatos → documentos inventariados/errores → extracción nativa/OCR/reutilizada
→ consolidación/canónicos reutilizados → enriquecidos → alertas/no alertas
→ notificaciones preparadas/aceptadas/capturadas/fallidas.

Se conservan códigos reales como terminal_phase, no_metadata_match, strong_exclusion,
publication_unknown, limit_deferred y attempts_exhausted; no se cambia el negocio
para renombrarlos. decision_reasons permite consultar razones de evaluación, incluida
no_confirmed_affinity. Un registro repetido de origen cuenta como recibido, aunque
Radar lo deduplica antes de evaluarlo.

Los filtros remotos impiden conocer cuántos registros Socrata excluyó antes de
responder: los contadores fuera de región/fecha solo cubren registros recibidos.
documents_processed representa inventario consultado, no garantiza descarga o
extracción completa; errores y cobertura se muestran separadamente. OCR se cuenta
por páginas; documents_available informa binarios disponibles, document_download_failed
cuenta descargas fallidas y document_errors procesos con error documental. Extracción nativa se cuenta
por documento con fragmentos nativos. Resultados
reutilizados no se presentan como páginas OCR ejecutadas otra vez.

Duraciones monotónicas de adquisición, prefilter, documentos, extracción, OCR,
consolidación, Eureka, notifications, Radar y total. OCR es subetapa de extracción;
no se deben sumar todos los valores como etapas independientes. Etapas no ejecutadas
quedan en cero. Una petición fuente fallida conserva el tiempo observado.

Directorio configurable; un `.log` JSON-lines y `.json` resumen por ciclo:
`eureka-cycle-YYYYMMDD-HHMMSS-<UUID>`. Fechas del nombre en UTC; UI en Bogotá.
Checkpoint de eventos y resumen mediante temporal, fsync y reemplazo atómico.
La base es fuente de verdad. Se permiten tipos/códigos e identificadores, no mensajes
arbitrarios de excepciones, claves, URLs con credenciales o cuerpos de proveedor.

Retención de 30 días por defecto: solo ficheros propios reconocidos, en el directorio
resuelto, sin seguir symlinks ni eliminar ficheros de ciclos running. No elimina
registros de DB ni documentos. Fallos de disco quedan diagnosticados en DB si está disponible.

## Configuración

Defaults documentados en backend/.env.example:

```dotenv
EUREKA_AUTOMATION_ENABLED=false
EUREKA_AUTOMATION_ALLOW_REAL_SEND=false
EUREKA_AUTOMATION_INTERVAL_HOURS=12
EUREKA_AUTOMATION_TIMEZONE=America/Bogota
EUREKA_AUTOMATION_RUN_TIMES=07:00,19:00
EUREKA_AUTOMATION_LOG_PATH=.local/logs/eureka
EUREKA_LOG_RETENTION_DAYS=30
EUREKA_AUTOMATION_STALE_MINUTES=180
EUREKA_AUTOMATION_TASK_NAME=ComprasPublicas-EurekaRadar
```

RUN_TIMES prevalece sobre intervalo. Si está vacío, intervalo usa un ancla fija para
que la próxima hora teórica no se desplace con cada consulta; el registro toma esa
misma próxima hora como primer trigger. Horas HH:MM, zona IANA y nombre de tarea
validan antes de ejecutar. El registro Windows inicial admite America/Bogota y
Windows `SA Pacific Standard Time`; no cambia la zona del equipo.

Se configuró únicamente `EUREKA_RADAR_START_DATE=2026-10-13` en backend/.env local,
ignorado por Git. No se agregaron rutas personales al código/versionado. Se conservan
la configuración OCR habitual y notifications enabled=false / mode=disabled.
ALLOW_REAL_SEND queda false: cualquier futura entrega exige autorización explícita
y configuración del proveedor; nada de ello se validó o activó en esta fase.

La ventana incluye el día local actual mediante el día siguiente como límite
calendario **exclusivo**. Por ejemplo, el 14 de octubre: [13 octubre,15 octubre).
No incluye el día 15. La fecha de inicio futura se rechaza. No se implementa un
watermark: se sigue reconsultando desde el inicio y usando estados/idempotencia.

## CLI y scripts

Desde backend, con el entorno del proyecto:

```text
python -m public_procurement.entrypoints.cli run-eureka-cycle --dry-run --json
python -m public_procurement.entrypoints.cli run-eureka-cycle --json
```

El primer comando es **PREFLIGHT / CONFIGURATION DRY-RUN**: valida config, DB, estado
del esquema, OCR, ventana y etapas. NO consulta SECOP, NO predice procesos/candidatos,
NO crea alertas, ciclos, capturas, logs ni tareas. schema_ready=false informa que
falta la migración. El segundo requiere 0016 y ejecuta una sola vez; no se ejecutó
contra desarrollo en esta implementación.

Exit code 1 para failed; completed_with_warnings y skipped terminan con 0 y resumen
explícito. Ejecución manual disponible aunque AUTOMATION_ENABLED=false; trigger
scheduled se omite si está deshabilitada.

Scripts versionados:

- run_eureka_cycle.ps1: resuelve backend/venv relativos; lanza CLI y conserva exit code.
- register_eureka_task.ps1: valida Python/rutas/preflight/migración/zona; registra con
  ShouldProcess/-WhatIf y muestra NextRunTime. Requiere habilitación explícita para registrar.
- unregister_eureka_task.ps1: solo elimina la tarea configurada, con ShouldProcess/-WhatIf.
- eureka_task_config.py: puente de configuración permitida para PowerShell, sin secretos.

La acción usa PowerShell sin perfil, no interactivo y ExecutionPolicy Bypass **solo
para ese proceso**; no cambia la política global de Windows. Usuario actual con
LogonType Interactive, RunLevel Limited, sin almacenar contraseña. El working directory
y las rutas quedan correctamente delimitados, incluidos espacios.

StartWhenAvailable=true, MultipleInstances=IgnoreNew, WakeToRun=false; no se corta una
corrida a una hora arbitraria. Permite batería y no interrumpe al cambiar a batería.
Mientras el PC está apagado no se ejecuta nada. Tras volver a estar disponible el
equipo/usuario, Windows puede recuperar la ejecución perdida; no promete reproducir
cada horario omitido. No arranca Docker/PostgreSQL automáticamente. El lock evita
solapamiento también con lanzamientos manuales, independientemente del scheduler.

**Scripts preparados, no tarea instalada.** -WhatIf valida dependencias: puede
rechazar el preflight si aún falta 0016; no se debe interpretar como registro realizado.

## Health/API/UI

GET /api/operations/status, /api/operations/cycles?limit=5 y /api/operations/cycles/{UUID}.
Estas rutas GET son de lectura. Sin 0016: status informa migration_0016_pending; consultas de ciclos
responden 503 controlado. ID inexistente 404; UUID inválido conforme a validación existente.
Se añadió POST /api/operations/cycles/manual, con confirmación en UI y respuesta 202.

Status muestra DB, OCR/version/idioma, último ciclo y satisfactorio, última alerta,
modo de notifications, automatización y dos conceptos separados:

- next_theoretical: calculado de configuración, incluso si no existe tarea.
- scheduler: consulta Windows acotada a nombre configurado, timeout y caché de 30 s;
  active, disabled, not_registered o unknown. next_run solo viene de Windows.

No se invoca registro desde HTTP ni se exponen comandos, claves o rutas de Tesseract.
La UI `/eureka/operations`, accesible desde Operación, muestra esos estados, embudo
ordenado, errores y tiempos; último ciclo expandido e historial breve desplegable.
Enlaza al detalle Radar existente en JSON, alertas y notifications. No tiene controles
para activar automatización ni enviar correo.

## Validación y límites

Se probaron ciclo vacío/exitoso, fallos globales/individuales, OCR/reutilización,
notifications disabled, captura/fallo, lock ocupado auditado, recovery reciente sin
gate temporal, interrupción antes del dispatcher y después de captura, idempotencia,
logs/retención, preflight sin SECOP, health, zona, scripts y UI. Las pruebas PostgreSQL
requieren `OPERATIONS_ACCEPTANCE_DATABASE_URL` y la validación *_test; no usan DATABASE_URL
como fallback. El test de política Windows no acredita recuperación real de un PC apagado.

Evidencia ignorada bajo backend/.local/operations45/: auditorías de desarrollo,
migration.json, acceptance.txt, browser.json y capturas development.png/isolated.png.
Se inspeccionó UI real en navegador con esquema pendiente y con ciclos aislados.

Advertencia conocida: deprecación de httpx en Starlette TestClient; no es fallo funcional.
No hay prueba de Task Scheduler ejecutando una tarea real ni envío Resend real.

Resultados ejecutados:

- Backend: 623 unitarias aprobadas, 1 omitida (aceptación OCR real opt-in).
- PostgreSQL aislado: 2 pruebas aprobadas, incluyendo lock real ocupado, persistencia,
  repetición vacía y recovery. Migración roundtrip aislada aprobada.
- Frontend: 74 pruebas aprobadas; las 2 de operations se repitieron tras ordenar el embudo.
- Ruff, mypy (154 archivos), import-linter, frontend lint y build aprobados.
- PowerShell: parse de los scripts, launcher -DryRun real y settings construidos en
  memoria: StartWhenAvailable=True, IgnoreNew, WakeToRun=False. Sin registro.
- Browser: UI de desarrollo con migración pendiente y UI con ciclos aislados aprobadas.
- Durante la implementación, desarrollo conservó 0015; **30 tablas y 41.582 filas con conteos/hashes idénticos**,
  incluyendo las dos tablas vacías de notifications. Covarachía mantiene score 65.
- GET real de operations/status, notifications, radar-runs, search y detalle Eureka: 200.
  Scheduler consultado: not_registered; próxima real null; OCR spa disponible.

Archivos de implementación:

- `backend/alembic/versions/0016_eureka_operations.py`.
- `backend/src/public_procurement/operations/`: services.py, repositories.py, ports.py,
  api.py, domain/cycle.py, adapters/file_logs.py, adapters/windows_scheduler.py y sus __init__.py.
- `backend/src/public_procurement/eureka/`: services.py, radar_services.py y
  adapters/radar_pipeline.py (UUID opcional y observación, sin reglas nuevas).
- `backend/src/public_procurement/ingestion/services.py` y extraction/services.py
  (las dos puertas públicas adicionales).
- `backend/src/public_procurement/shared/config.py`, entrypoints/cli/__main__.py,
  entrypoints/api/app.py, backend/pyproject.toml y backend/.env.example.
- Los cuatro scripts enumerados arriba; backend/.env únicamente local e ignorado.
- `backend/tests/unit/operations/`, unit/entrypoints/test_cycle_cli.py,
  unit/test_env_example.py y acceptance/test_operations_postgres.py.
- `frontend/src/features/operations/OperationsPage.tsx` y OperationsPage.test.tsx,
  frontend/src/App.tsx, app/AppShell.tsx y api/openapi.json/schema.ts regenerados.
- README.md y este documento. Los archivos .local son solo evidencia ignorada.

Para incidentes: comprobar DB/puerto 55432 y revisión Alembic; después .env, preflight,
configuración OCR y logs del UUID. scheduler=unknown indica que no se pudo verificar,
no que esté ausente. Si Windows lanza el script pero DB no está disponible, revisar
diagnóstico local persisted=false. No borrar reservas de notifications para forzar retries.

## Pendientes autorizados por separado

1. Completado con autorización posterior: 0015 → 0016 en desarrollo, auditoría histórica y smoke de lectura aprobados.
2. El usuario ejecutará el primer ciclo manual real desde el botón de Operations.
3. Repetir y verificar idempotencia, recovery, métricas y logs persistidos.
4. Autorizar/habilitar y registrar la tarea Windows real.
5. Comprobar estado activo, próxima ejecución, lanzamiento desde Task Scheduler,
   logs, automation_cycle y cero duplicados.

Solo después queda resuelto el pendiente de programación automática. Resend real
sigue separado: API key, remitente, destinatario autorizado y un único envío controlado.

## Migración futura a cloud

Se sustituyen scheduler/launcher y, si procede, adapters de logs/host. Se conservan
AutomationCycleService, locks/idempotencia, persistencia, métricas, Radar y dispatcher.
No se añadió infraestructura cloud, IA ni coordinación distribuida.
