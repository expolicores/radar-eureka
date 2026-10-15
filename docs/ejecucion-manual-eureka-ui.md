# Ejecución manual de Eureka desde Operations

Abrir `/eureka/operations` y pulsar **Ejecutar corrida manual**. Se muestra confirmación
con Cancelar / Ejecutar. Solo Ejecutar emite el POST. Se usan configuración habitual,
fecha inicial temporal **2026-10-05** para la prueba ciega del funnel; no se admiten
filtros comerciales desde el botón. El alcance base sigue siendo Boyacá/Casanare.
Para la validación local se añadió temporalmente Bogotá como
[validation_region](validacion-regiones-eureka.md), usando `Distrito Capital de Bogotá`.
Notifications permanece enabled=false / mode=disabled. No se registró tarea Windows.

Desde el 15 de octubre de 2026, GET /api/operations/status incluye execution_config,
leída del mismo Settings que utiliza el lanzador manual: start_date, before_date,
before_exclusive, timezone y regions. Operations muestra esa ventana y regiones antes
del botón, sin ejecutar consultas SECOP. before_date es mañana en la zona configurada,
exclusivo, igual que la corrida existente. El 15 de octubre la ventana es
`2026-10-05 <= fecha < 2026-10-16`. La fecha anterior 2026-10-13 corresponde a la prueba
previa documentada; no se reescriben sus resultados ni se introducen casos esperados.

## API y background

`POST /api/operations/cycles/manual`, JSON `{}`. Campos adicionales se rechazan
con 400, conforme al contrato de validación existente.

Devuelve 202 con cycle_id, status=running y started_at después de adquirir el advisory
lock y persistir automation_cycle. No espera la consulta SECOP o el enriquecimiento.
Un hilo Python local ejecuta exactamente `AutomationCycleService.run(trigger="manual_ui")`,
compartido con CLI/scheduler. La conexión del lock pertenece al hilo; no se transfiere
una sesión del request.

La espera de acuse inicial se limita a 8 s. Si vence antes de confirmar persistencia,
el callback cancela antes de Radar y se responde 503. Los errores de inicio incluyen
stage/code/detail saneados, sin cuerpos de excepciones del driver o proveedor.

Si el lock está ocupado: intento skipped/already_running auditado, HTTP 409,
cycle_id del intento y active_cycle_id cuando está disponible. La UI informa
“Ya hay una corrida en ejecución” y sigue el ciclo activo. La protección efectiva
es el advisory lock 741045, también frente a CLI y otras instancias API.

El hilo es local y no durable: terminar/reiniciar el backend puede dejar running
persistido. El lock se libera; el siguiente ciclo autorizado usa el recovery existente.
Para producción/cloud se debe sustituir este lanzador por ejecución durable,
conservando servicio, persistencia e idempotencia. No se agregó cola ni scheduler.

## Polling y diagnóstico

GET /api/operations/cycles/{UUID} cada **4 segundos** mientras running. Se detiene
al terminar o si se detecta coordinador interrumpido. DB es la fuente de verdad.
Status informa active_cycle solo con lock real en esa base. El detalle añade
coordinator_active como proyección de lectura, sin modificar estado persistido.
Una página recargada puede reencontrar la corrida activa.

El servicio persiste progreso de recibidos, candidatos, enriquecidos y alertas,
además de etapas documentales/OCR. Contadores de cierre aparecen al terminar su etapa.
No se cambiaron reglas, scoring, catálogo o capacidades documentales.

source_summary distingue cero registros confirmado tras consulta completa, registros
recibidos pero sin alertas, y consulta pendiente/incompleta/fallida. Un cero observado
durante un fallo no se presenta como respuesta vacía confirmada. Los filtros remotos
de Socrata impiden medir exclusiones anteriores a la respuesta; la UI lo aclara.

La vista muestra estado, etapa, cycle_id, inicio, duración, recibidos, candidatos,
enriquecidos, alertas y errores. Errores/advertencias muestran etapa, código y tipo
saneados; también se puede abrir el desglose y el detalle Radar. Si hay alertas,
Ver alertas enlaza a /eureka/alerts. Notifications disabled no constituye warning.

Son los mismos `.log` y `.json` del servicio, con su retención. La vista muestra
nombres lógicos y timestamps; no sirve archivos ni rutas personales. Cada confirmación
admitida crea un nuevo ciclo; permanecen las garantías de procesos/alertas, OCR
reutilizable y reservas de notifications. CLI y scripts existentes siguen disponibles.

## Verificación

- 629 unitarias backend aprobadas, 1 omitida OCR real opt-in; 83 frontend aprobadas.
- 3 PostgreSQL aisladas: 202 persistido antes de finalizar, polling, lock/409,
  repetición vacía y recovery, con fuente controlada sin consultar SECOP real.
- Confirmación/cancelación, polling de 4 s, estados terminales, botón deshabilitado,
  error visible, respuesta vacía vs descartes, cero/una alerta y enlace, nueva ejecución.
- Pruebas de idempotencia/restart de Radar y captura existentes siguen aprobadas.
- Ruff, mypy, 13 contratos de arquitectura, frontend lint y build aprobados.

Backend y frontend habituales quedan levantados. Se inspeccionó la página de
desarrollo en lectura, **sin pulsar el botón**. No se ejecutó el CLI del ciclo,
no se aplicaron migraciones y no se enviaron correos reales. La primera corrida
SECOP real queda reservada al usuario.

Archivos principales: operations/background.py, api.py, services.py, repositories.py;
entrypoints/api/app.py; eureka/radar_services.py (observación); OperationsPage.tsx y
pruebas correspondientes; contrato OpenAPI/TypeScript regenerado. Sin dependencias nuevas.
