# Fase 4.4: migración y validación en desarrollo

Validación del 14 de octubre de 2026 sobre `public_procurement`, PostgreSQL local 55432.
Únicamente `0014_transversal_search → 0015_eureka_notifications`, mediante destino
Alembic explícito; sin reset, truncate, recreación, backfill ni cambios a tablas históricas.

## Esquema y restricciones comprobados en PostgreSQL

Se creó el schema `notifications` y exclusivamente estas tablas:

| Tabla | PK | Filas nuevas en desarrollo |
| --- | --- | ---: |
| notification | id | 0 |
| notification_alert | notification_id, alert_id | 0 |

Tres FK verificadas: notification.alert_id → eureka.alert.id;
notification_alert.alert_id → eureka.alert.id; y FK compuesta desde
notification_alert(notification_id, recipient, channel, delivery_scope) hacia
notification(id, recipient, channel, delivery_scope). La última garantiza que la
pertenencia de una alerta al digest corresponda al mismo destinatario/canal/ámbito.

`uq_notification_alert_claim` impone UNIQUE(alert_id, recipient, channel, delivery_scope).
El destinatario del padre tiene CHECK de minúsculas y trim; la FK compuesta impide
que el hijo se aparte de ese valor. Para scope constante `real`, la identidad es
alert_id + recipient_normalized + channel, compartida por individual y digest.
Captura usa scope separado: no reserva una entrega real. `idempotency_key` también
es UNIQUE. Verificadas ambas PK, tres FK y las restricciones CHECK/UNIQUE existentes.

## Auditoría histórica

Comparación antes/después por tabla de conteos y SHA-256 de todas las filas
serializadas como JSONB y ordenadas: **28 tablas, 41.582 filas, idénticas**.
La fila de Alembic cambia de revisión según lo esperado. Las dos tablas nuevas
quedaron vacías. Nueva comparación al finalizar los smoke tests coincide con la
instantánea posterior a la migración. No se introdujo ninguna alerta de prueba en desarrollo.

## Validación funcional

- GET /api/eureka/notifications: 200, total 0, aproximadamente 178 ms con TestClient.
- GET /api/eureka/notifications/{id}: 200 con captura controlada en base *_test.
- UI habitual /eureka/notifications: carga correctamente y muestra ausencia de resultados.
- UI aislada: un mensaje capturado, contenido e historial expandibles y enlace al detalle
  de alerta funcional; sin controles para enviar. Captura visual inspeccionada.
- Dispatcher habitual con enabled=false / mode=disabled: prepared=0, sent=0,
  captured=0, failed=0, items vacíos. No consume/reserva alertas ni escribe registros.
- File/capture exclusivamente en `public_procurement_notifications44_test`, destinatario
  sintético `@example.invalid`: primera ejecución captura 1; repetición captura 0.
  Se agrega en esa base aislada 1 notification y su relación notification_alert.
  No se invocó Resend ni se configuró API key o destinatarios reales.
- Radar: GET /api/eureka/alerts y /api/eureka/radar-runs devuelven 200;
  regresión unitaria de reglas/pipeline/repositorios/API aprobada. No se ejecutó una
  corrida SECOP real para esta migración.
- Search: GET /api/search?q=jugo%20hit devuelve 200 y encuentra el golden case.
- Detalle Eureka de Covarachía: 200, score **65**. Evidencia histórica conservada,
  respaldada por igualdad de hashes; sin cambios de scoring, reglas o catálogo.
- Extracción nativa existente: completed, 1 fragmento, dry-run sin escrituras.
- OCR Tesseract real, configuración local habitual: `spa`, ocr_success, página 1,
  cobertura completa, confianza 94,37 %. Fixture aislado produce **7 structured facts
  y 7 canonical facts**, en unos 3,29 s hasta consolidación. Ningún dato OCR escrito en desarrollo.
- Regresión unitaria focalizada de Radar y dispatcher: **42 pruebas aprobadas**.
  Advertencia preexistente: deprecación de httpx en Starlette TestClient; sin fallos.

`.env` permanece sin cambios y excluido de Git. No se modificaron código funcional,
migraciones, scoring, catálogo, OCR ni destinatarios durante esta operación.

## Evidencia local

Archivos ignorados por Git bajo `backend/.local/notifications44/migration015/`:
before.json, after.json, final.json, migration_report.json (restricciones e índices),
smoke.json, browser.json, notifications.png y capture/.
Scripts de esta operación: `backend/.local/notifications44/migrate015.py`,
`smoke015.py` y `migration015/browser.mjs`.

## Estado operativo

Migración y validación funcional local de Fase 4.4 completadas. Los envíos reales
permanecen deshabilitados. La validación de proveedor real está pendiente: requiere
autorizar API key, remitente, destinatario real y envío controlado de un único correo.
La captura local no acredita entrega de correo externo.
