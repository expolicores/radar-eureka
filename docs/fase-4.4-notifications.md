# Fase 4.4 · Notificaciones de alertas Eureka

Implementación técnica validada en aislamiento el 14 de octubre de 2026.
**Desarrollo actualizado, con autorización, de 0014_transversal_search a 0015_eureka_notifications.**
Auditoría y smoke operativos: [validación en desarrollo](validacion-4.4-desarrollo.md).
El modo habitual permanece disabled; no se modificó `.env` ni se enviaron correos externos.

## Arquitectura y flujo

`entrypoints → notifications → eureka.services → alertas persistidas`.
`NotificationDispatcher` prepara un outbox, reserva alertas por destinatario y luego llama
al puerto `EmailSender`. Los adapters son `DevEmailSender` y `ResendEmailSender`.
El único acceso de notifications a Eureka es su interfaz pública de lectura
`notification_alerts`; el SQL de alertas sigue siendo propiedad de Eureka.

No se llama a Radar, scoring, catálogo, ingestion, documents, extraction, OCR ni search.
Las plantillas utilizan el snapshot histórico, prioridad, motivos y review de la alerta.
No se consulta la oportunidad actual para reconstruir un correo. Solo se congelan los
datos usados en el mensaje: no se copian fragments/documentos completos al outbox.
12 contratos de importación verifican las fronteras de módulos.

## Migración 0015_eureka_notifications

Crea schema `notifications` y únicamente dos tablas:

| Tabla | Contenido |
|---|---|
| notification | Un mensaje para un destinatario; individual o digest. |
| notification_alert | Alertas incluidas en cada mensaje y sus reservas de entrega. |

`notification`: PK id UUID; alert_id UUID nullable/FK a eureka.alert (individual);
channel VARCHAR(16); recipient VARCHAR(254) normalizado; notification_type VARCHAR(16);
delivery_scope VARCHAR(16); delivery_mode VARCHAR(16); provider VARCHAR(32); status
VARCHAR(16); timestamps TIMESTAMPTZ de creación, actualización, aceptación, captura,
fallo, inicio processing, próximo retry, límite de idempotencia y ventana digest;
delivery_ambiguous BOOLEAN; attempt_count/retry_count INTEGER; provider_message_id
VARCHAR(256); error_code VARCHAR(64); error_message TEXT; payload_snapshot JSONB NOT NULL;
attempt_history JSONB NOT NULL; idempotency_key VARCHAR(64) UNIQUE.

CHECKs para estados, email como canal inicial, scopes capture/real, tipos immediate/digest,
contadores no negativos y recipient en minúsculas/sin espacios externos.
Índices `ix_notification_ready(delivery_scope,status,next_retry_at)` y
`ix_notification_created(created_at,id)`.

`notification_alert`: PK compuesta notification_id/alert_id; FK a eureka.alert; recipient,
channel y delivery_scope. FK compuesta al mensaje garantiza que destinatario, canal y
scope coincidan con los del padre. Índice por alert_id y restricción:

`UNIQUE(alert_id, recipient, channel, delivery_scope)`.

Sin tercera tabla de intentos, backfill ni alteración de tablas históricas. Downgrade
elimina las dos tablas y su schema; elimina el historial propio de notificaciones y sus
reservas, por lo que no es una operación de recuperación de envíos. Se probó
0014 → 0015 → 0014 → 0015 en una base exclusiva de migraciones *_test, nunca desarrollo.

## Idempotencia final

Para **real**, scope es la constante `real`: la unicidad efectiva es exactamente
alert_id + recipient_normalized + channel. Notification type, ventana del digest,
delivery_mode y provider no permiten repetir una alerta real.

Para **capture**, las reservas se guardan separadamente. Una captura nunca consume la
reserva real. El digest de captura también excluye alertas ya asignadas a un mensaje real.

El mensaje tiene clave SHA-256 estable calculada con destinatario, scope, canal, tipo,
IDs de alertas y ventana; la reserva única de alertas protege los cruces entre claves de
individual/digest. Preparación del mensaje y reservas se confirman en una transacción:
una carrera perdida no deja un mensaje huérfano. Solo se trata como duplicado una
violación de unicidad; otros errores de integridad no se ocultan.

Una alerta reservada por pending/processing/retryable/failed sigue perteneciendo al
mensaje original. Se reintenta ese mensaje, sin asignarla a otro digest. Asunto, texto,
HTML, links, destinatario, remitente y datos comerciales permanecen congelados.

## Estados, intentos y recuperación

Estados: pending, processing, captured, sent, retryable, failed, skipped.
**sent significa aceptación por proveedor, no entrega, apertura ni lectura.**
captured tiene captured_at y no sent_at; no representa un correo externo.

Cada intento se registra antes del I/O. attempt_history conserva timestamp, provider,
número, resultado, duración disponible, HTTP status/error code, error sanitizado y recibo
cuando existe. Completar un intento actualiza esa entrada; iniciar otro añade una nueva,
sin borrar resultados anteriores. Los fallos previos permanecen tras un éxito.

El dispatcher usa un advisory lock PostgreSQL distinto del de Radar. Dos dispatchers
simultáneos producen un único emisor; el segundo informa busy y sale con código 2.
La unicidad de la base protege incluso una reserva concurrente sin ese lock.

Processing guarda processing_started_at. En cada invocación, los registros seleccionados
que superan el lease se recuperan: capture puede repetir la operación idempotente de
archivo; real solo puede reintentar si conserva protección del proveedor y cupo de intentos.
Un resultado ambiguo sin protección pasa a failed/delivery_unknown_review. No permanece
processing indefinidamente cuando se vuelve a invocar el dispatcher después del lease.
En un intento interrumpido la duración real es desconocida: se registra null, junto al
tiempo transcurrido observado hasta la recuperación.

Resend conserva sus claves durante 24 horas. Se reutilizan el mismo key y cuerpo; no se
renueva el plazo de una entrega ambigua. La comprobación utiliza el reloj actual de cada
intento y un margen configurable, mínimo superior al timeout, para evitar iniciar un retry
al borde de expirar la protección. No se promete exactly-once delivery.
[Documentación oficial de idempotencia](https://resend.com/docs/dashboard/emails/idempotency-keys).

Timeout, 429 y 5xx son retryable; errores permanentes quedan failed. Retry-After en
segundos se respeta. La espera crece hasta una hora salvo Retry-After mayor. MAX_RETRIES
cuenta reintentos adicionales: 3 permite hasta 4 intentos. No hay loops internos hasta éxito;
cada registro se intenta como máximo una vez por invocación. --retry respeta next_retry_at.
Los failed permanentes/ambiguos necesitan revisión operativa y no se liberan automáticamente
ni tienen botón de reenvío. Cambiar provider de un mensaje preparado requiere revisión.

## Modo local y adapter Resend

Disabled no envía, prepara ni consume alertas. File genera un JSON con asunto, texto, HTML,
links y snapshot en EUREKA_NOTIFICATION_CAPTURE_PATH. Constructor y dry-run no crean
directorios. Captura usa temporal, fsync y movimiento atómico; repetir el mismo key/contenido
devuelve el recibo existente, y contenido diferente con esa clave falla sin sobrescribirlo.

Resend usa HTTPS fijo, redirects deshabilitados, timeout e Idempotency-Key. No requiere SDK
cloud adicional. HTTP es inyectable para pruebas. Errores guardan mensajes controlados;
no se persisten cuerpos de error del proveedor ni API keys. El envío real requiere modo
resend, enabled y `--allow-real-send` explícito. No se utilizó ese camino con HTTP real.

## Configuración

`.env.example` documenta:

```dotenv
EUREKA_NOTIFICATION_ENABLED=false
EUREKA_NOTIFICATION_MODE=disabled
EUREKA_NOTIFICATION_RECIPIENTS=
EUREKA_NOTIFICATION_BASE_URL=http://127.0.0.1:5173
EUREKA_NOTIFICATION_CAPTURE_PATH=.local/notifications
EUREKA_NOTIFICATION_MAX_RETRIES=3
EUREKA_NOTIFICATION_RETRY_SECONDS=60
EUREKA_NOTIFICATION_TIMEOUT_SECONDS=15
EUREKA_NOTIFICATION_PROCESSING_LEASE_SECONDS=300
EUREKA_NOTIFICATION_IDEMPOTENCY_MARGIN_SECONDS=60
EUREKA_NOTIFICATION_MAX_MESSAGES=100
EUREKA_NOTIFICATION_DIGEST_MAX_ALERTS=100
RESEND_API_KEY=
RESEND_FROM_EMAIL=
```

Destinatarios por comas o --recipient repetible. Normalización: trim/minúsculas, sin
heurísticas de alias de proveedor. Validación inicial de direcciones ASCII; no comprueba
existencia de la bandeja. Remitente admite dirección con nombre de presentación y rechaza
controles. API key usa SecretStr. Base URL permite HTTP/HTTPS sin credenciales/query/fragment;
links solo incorporan UUID de oportunidad. HTML escapa valores y encabezados rechazan controles.
Los logs usan huella SHA-256 del destinatario, IDs, provider, intento, estado, duración y
error code, sin correo completo, API keys ni cuerpo. CLI/API muestran el destinatario autorizado.

## CLI, digest y dry-run

Desde backend, con la base destino correctamente configurada y migrada:

```powershell
uv run python -m public_procurement.entrypoints.cli send-eureka-notifications --pending --dry-run --json
uv run python -m public_procurement.entrypoints.cli send-eureka-notifications --alert-id <uuid> --mode file --recipient reviewer@example.invalid --json
uv run python -m public_procurement.entrypoints.cli send-eureka-notifications --digest daily --date 2026-10-14 --mode file --recipient reviewer@example.invalid --json
uv run python -m public_procurement.entrypoints.cli send-eureka-notifications --digest since-last --mode file --recipient reviewer@example.invalid --json
uv run python -m public_procurement.entrypoints.cli send-eureka-notifications --pending --retry --mode file --recipient reviewer@example.invalid --json
```

--mode es un override por invocación y no modifica .env. La dirección del ejemplo es
ficticia. No ejecutar esos ejemplos como una inserción de alertas de prueba en desarrollo.
Seleccionar únicamente uno de --pending, --alert-id o --digest; sin selector equivale a pending.

Daily toma el día indicado, o el día anterior completo en America/Bogota. Window utiliza
--from-date/--before-date locales y ordenadas. Todas las ventanas son `[desde,hasta)`.
Since-last selecciona alertas no asignadas, sin watermark que pueda perder cargas tardías.
Digest ordena por prioridad, fecha descendente y número de coincidencias confirmadas ya
guardadas como desempate; no recalcula afinidad. Digest vacío no crea mensajes ni reservas
y no envía mensajes ajenos a su selección. Cada destinatario tiene su propio mensaje.

Dry-run muestra contenido, destinatario, alertas y links, reutiliza el snapshot de los retries,
proyecta recuperaciones de processing sin escribirlas, y marca would_send/blocked_reason.
Respeta el límite de mensajes y advierte configuración ausente o protección expirada.
No envía, crea capturas, filas ni asignaciones. --json/dry-run dejan stdout como JSON parseable;
logs del comando nuevo salen por stderr. Códigos: 0 éxito/disabled/vacío; 1 fallo/retryable;
2 busy o parámetros inválidos. No cambia el logging de los comandos anteriores.

## API y UI

`GET /api/eureka/notifications`: page/page_size, status, channel, recipient, alert_id,
delivery_scope, created_from y created_before. Fechas con zona, fin exclusivo; page_size 1–100.
Listado no devuelve cuerpos ni historial completo, y expone contadores globales por estado.
`GET /api/eureka/notifications/{id}` devuelve el snapshot y attempt_history.
Consultas PostgreSQL READ ONLY. Sin endpoints POST de envío. Si falta 0015, devuelve 503
controlado y mantiene las APIs anteriores operativas.

`/eureka/notifications`: filtros, paginación, estado, fecha Colombia, destinatario, canal,
scope/provider, intentos, error/aceptación/captura, contenido e intentos bajo demanda.
El HTML guardado no se ejecuta en UI: se presenta texto. Sin editor ni botón de envío.
El enlace de alerta abre `/eureka/alerts/{alertId}` usando la página existente y la API
histórica ya disponible; no cambia decisiones de Radar. Desde alertas se accede a notificaciones.

## Pruebas y evidencia

- **593 tests unitarios backend** pasan; una aceptación OCR real opt-in se omite porque
  notifications no ejecuta OCR. Incluye nuevos tests A–S, CLI, config y seguridad.
- **9 tests PostgreSQL** opt-in pasan en `public_procurement_notifications44_test`:
  ambos cruces individual/digest; capture→real; proveedor simulado aceptó y perdió respuesta;
  retry con mismo cuerpo/key y una aceptación; dos dispatchers; carrera sin lock;
  recuperación processing con protección y revisión cuando expiró; API/dry-run.
- **72 tests frontend** pasan; cinco nuevos de notificaciones y enlace histórico.
- Ruff, Mypy, 12 contratos de arquitectura, ESLint, formato y build verificados.
- Migración roundtrip en `public_procurement_notifications44_migration_test` confirma dos
  tablas y dos JSONB; ninguna tercera tabla.
- Validación persistida por CLI real de proyecto en la base aislada: dry-run, captura,
  segunda corrida sin duplicar, aceptación Resend HTTP simulada después de captura,
  individual seguido de digest sin reenvío, y retry tras aceptación con respuesta perdida.
- Edge headless sobre API/frontend aislados: dos estados diferenciados, mensaje congelado,
  intentos, enlace histórico y ausencia de controles de envío.

Golden Covarachía: Alta, score 65, Covarachía/Boyacá, Refrigerios, 2.080.000 COP, Jugo Hit
200 ml, Chocorramo 65 g, plazo 5 días, pago 30 días, póliza No requerida, revisión de vigencia
y enlace al detalle. La alerta fixture solo existe en aislamiento. Desarrollo sigue con
**cero alertas**, score 65, **28 tablas y 41.582 filas históricas con hashes SHA-256 idénticos**.
`.env` sigue intacto, ignorado por Git y sin habilitación de notificaciones.

Para PostgreSQL opt-in, NOTIFICATIONS_ACCEPTANCE_DATABASE_URL debe apuntar a una base *_test
distinta de desarrollo, con fixture aislada y 0015. Usa el guard existente de pruebas;
no utiliza fixtures destructivas de tests/integration:
`python -m pytest tests/acceptance/test_notifications_postgres.py -q`.

Artefactos locales no versionados en `backend/.local/notifications44/`: migration.json,
acceptance.json, development_before/after.json, golden_email.json/txt, capturas JSON,
browser.json y notifications.png. Las filas scope real de aceptación usan HTTP simulado:
**cero correos externos enviados**, no una prueba de entrega real de Resend.

## Archivos de esta fase

Nuevos: `notifications/{__init__,api,ports,repositories,services}.py`,
`notifications/domain/{__init__,message}.py`,
`notifications/adapters/{__init__,alerts,file,resend}.py`, `eureka/notification_queries.py`,
`alembic/versions/0015_eureka_notifications.py`, tests unitarios notifications,
`tests/unit/entrypoints/test_notifications_cli.py`,
`tests/acceptance/test_notifications_postgres.py`,
`frontend/src/features/eureka/EurekaNotificationsPage.tsx` y su test, este documento.

Modificados: `shared/config.py`, `.env.example`, `eureka/services.py` (solo lector público),
entrypoints API/CLI, alembic/env.py, pyproject.toml (contratos), tests de configuración,
frontend App.tsx, EurekaAlertsPage.tsx, useEureka.ts, contrato OpenAPI/tipos y README.
No se modificaron dependencias, .env, scoring, generación Radar, catálogo, OCR ni search.

## Pendientes y límites

Aplicar 0015 en desarrollo requiere autorización posterior. La validación externa de Resend
requiere credenciales, remitente verificado y autorización explícita de envío; no bloquea
la implementación técnica validada con captura/HTTP simulado. No se verifica entrega,
bounces, apertura o lectura. Failed ambiguos/permanentes requieren revisión; no hay un
comando que fuerce su reenvío y omita las protecciones.

El límite inicial es 100 mensajes por ejecución y 100 alertas por digest, configurables.
La selección de alertas usa páginas SQL y reúne la ventana elegida en memoria; no se ha
medido una carga masiva de notificaciones. No hay automatización de retries: el dispatcher
debe volver a invocarse. Sus códigos de salida permiten integrarlo después con un scheduler
externo. Windows/cloud scheduler, otros canales y notificaciones con IA siguen fuera de fase.
