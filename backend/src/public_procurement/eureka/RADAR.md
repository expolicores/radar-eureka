# Fase 4.1 · Radar Eureka

El Radar ejecuta una corrida única sobre SECOP II (`p6dx-8zbt`), preselecciona procesos,
reutiliza el pipeline documental y registra alertas comerciales explicables. No incluye IA,
OCR, embeddings, recomendaciones de participación ni envío de mensajes.

## Conceptos

- **Corrida:** ejecución con ventana inclusiva/exclusiva, regiones y configuración congeladas.
- **Proceso nuevo:** identidad SECOP dentro de la ventana/región, sin atención inicial completada
  por Radar. Estar previamente en ingestion por una consulta manual no lo convierte en atendido.
- **Candidato:** proceso que supera filtros baratos de metadata. No implica producto confirmado.
- **Oportunidad:** candidato con detalle documental consolidado y oportunidad persistida.
- **Alerta:** oportunidad con afinidad comercial canónica confirmada, referencias documentales
  y ausencia de exclusión fuerte. No equivale a recomendación de participar.

## Consulta y filtros

Cada corrida consulta nuevamente desde `EUREKA_RADAR_START_DATE` hasta el fin exclusivo.
No hay watermark. Esta estrategia admite cargas tardías e interrupciones y se optimizará
cuando aumente el volumen. Los filtros de fecha y departamento se envían a Socrata; después
se vuelven a validar en memoria. Los procesos excluidos por el proveedor no se contabilizan
como registros leídos o descartados localmente: no se inventa un listado de ellos.

Se conserva la paginación por `:id`, con tamaño/límite configurables. Alcanzar el límite de
páginas o fallar el proveedor marca la corrida como incompleta. `--max-processes` limita
identidades nuevas o reintentables atendidas; los ya vistos no consumen ese cupo. Un registro
leído después de agotar el cupo queda auditado como `limit_deferred`, sin marcarlo atendido.

Región, publicación conocida y fase no terminal son filtros iniciales. Fase no preferida
requiere revisión, sin descarte automático. La fecha de cierre de oferta todavía no está en
la metadata persistida: se registra desconocida; la antigüedad no confirma vigencia.

## Afinidad y decisión

`config/eureka_radar.v1.json` contiene familias, términos, frases, marcas, aliases, UNSPSC,
exclusiones y prioridades, además de reglas y límites. Parte del catálogo anterior y conserva
papelería, tecnología, aseo/cafetería, impresión y mobiliario; añade ferretería y aliases de bebidas.

La normalización determinística separa números/unidades, tildes, puntuación y espacios.
Las variantes/plurales y abreviaciones son explícitos en `token_aliases`; las frases coinciden
por límites de tokens. Las negaciones inmediatas no cuentan como coincidencias afirmativas.
No se aplica stemming indiscriminado ni similitud semántica.

**Candidate match:** objeto/description, términos generales y UNSPSC de metadata, con lógica OR.
Permite decidir qué merece enriquecimiento. No confirma un producto.

**Confirmed commercial match:** nombre de PRODUCT o descripción de PURCHASE_ITEM con estado
canónico `confirmed`, coincidencia con catálogo y `structured_fact_ids` en las referencias.
Los hechos conflictivos o sin referencias no confirman afinidad. UNSPSC documental se guarda
como razón adicional y tampoco sustituye un producto/ítem confirmado.

El score Eureka se conserva. `alert_score_threshold` es una referencia **sin gate obligatorio**:
un match documental fuerte puede alertar con score 0, 20 o 59. La prioridad inicial procede de
Eureka; la prioridad de las familias ordena coincidencias del catálogo, sin recalcular ese score.

Presupuesto superior a `EUREKA_PREFERRED_BUDGET_MAX` permite alerta, requiere revisión y baja
una banda de prioridad de la alerta. No cambia el score/prioridad de la oportunidad. Presupuesto
desconocido/conflictivo requiere revisión. RUP, experiencia y número de entregas desconocidos
no bloquean. Plazos largos, garantías y barreras explícitas producen revisión; las exclusiones
fuertes configuradas bloquean. Las reglas son heurísticas, no interpretación jurídica.

## Pipeline y recuperación

Eureka coordina exclusivamente servicios públicos:

`ingestion → discovery → documents → extraction → structured → consolidation → detail → alert`

La adquisición SECOP ocurre una sola vez. `ProcessIngestionService.persist` acepta registros
ya consultados; no repite Socrata. Las oportunidades existentes conservan score y regla; el
estado canónico disponible se reutiliza. Documentos, extracción y consolidación siguen compartidos.

Las etapas son transacciones independientes, sin transacciones SQL abiertas durante descargas.
Un fallo de proceso se registra y no interrumpe los siguientes. Adquisición/extracción incompleta
deja el proceso fallido, sin emitir una alerta a partir de un pipeline incompleto.

`radar_process_state` distingue `processing`, `failed` y `completed`. Los fallidos/interrumpidos
pueden reintentarse hasta `max_attempts`; los completados, incluidos descartados, no se reenriquecen.
Cambiar reglas no vuelve automáticamente a evaluar procesos conocidos. Los descartados por
ventana/región desconocida o diferente no quedan completados de forma irreversible.

Un advisory lock PostgreSQL evita dos corridas escritoras simultáneas. Si el proceso muere,
PostgreSQL libera el bloqueo; la siguiente corrida marca las corridas previas activas como
interrumpidas. Un intento interno de extracción que siga marcado `running` requiere revisar
la recuperación operativa existente: Radar no fuerza su desbloqueo ni invade el módulo.

## Persistencia y trazabilidad

Migración `0012_eureka_radar`, cuatro tablas propias en `eureka`:

- `radar_run`: ventana, regiones, configuración/hash, timestamps, contadores y errores.
- `radar_process_state`: identidad `(dataset_id, secop_id)`, intentos y última etapa/estado.
- `radar_run_process`: resultado y motivos por proceso/corrida, incluidos omisiones y errores.
- `alert`: snapshot histórico, motivos JSONB y referencias originales documentales/canónicas.

Las razones distinguen `metadata`, `canonical_fact`, `document` y `radar_state`; el método
indica términos, aliases/normalización o UNSPSC. Se conservan IDs y localizadores documentales.
La identidad de alerta es `(opportunity_id, alert_type, rule_version)`, protegida por UNIQUE.
No se borra ni actualiza el snapshot de una alerta anterior en cada corrida.

La configuración efectiva se congela en cada corrida. Al publicar cambios funcionales del
catálogo/reglas debe incrementarse `version`; no editar retroactivamente snapshots históricos.

## Configuración local

```dotenv
EUREKA_RADAR_START_DATE=2026-10-13
EUREKA_RADAR_REGIONS=Boyacá,Casanare
EUREKA_RADAR_INTERVAL_HOURS=12
EUREKA_PREFERRED_BUDGET_MAX=30000000
EUREKA_RADAR_CONFIG_PATH=config/eureka_radar.v1.json
```

El inicio es obligatorio salvo `--from-date`. Las rutas relativas de configuración se resuelven
desde backend. No se modificó `.env` ni se activaron tareas del sistema automáticamente.

## CLI y dry-run

Desde backend, después de aplicar la migración al ambiente autorizado:

```powershell
.\.venv\Scripts\python.exe -m public_procurement.entrypoints.cli run-eureka-radar --from-date 2026-10-13 --department Boyacá --department Casanare --max-processes 20 --json
.\.venv\Scripts\python.exe -m public_procurement.entrypoints.cli run-eureka-radar --from-date 2026-10-13 --dry-run --json
.\.venv\Scripts\python.exe -m public_procurement.entrypoints.cli run-eureka-radar --process CO1.REQ.11172521 --from-date 2026-10-07 --before-date 2026-10-14 --json
```

`--before-date` es exclusivo; su defecto es mañana en Colombia. `--process` usa un proceso
persistido para evaluación dirigida, conservando los mismos filtros y estado Radar.
`--department` reemplaza regiones para esa ejecución. `--json` emite un documento JSON único;
los logs se envían a stderr. Fallos de corrida/proceso devuelven exit code 1.

Dry-run consulta metadata y lee el estado disponible, sin crear corrida/estado/alertas ni
descargar o extraer documentos. Si existe consolidación puede explicar la decisión; si no,
reporta `pending_enrichment`, sin inventar qué productos habría en los archivos. Si el proceso
ya está atendido, también se omite en dry-run. `alerts_created` siempre es 0 en dry-run;
`would_create_alert` distingue una predicción con evidencia disponible.

## Scheduler externo

`scripts/run_eureka_radar.ps1` ejecuta una sola corrida. `-ShowSchedule` muestra el intervalo
configurado. Programador de tareas de Windows debe invocar ese script con repetición según
`EUREKA_RADAR_INTERVAL_HOURS`; en Linux/cron se invoca la misma CLI de Python.

La variable documenta el intervalo que debe configurar el scheduler externo; cambiarla no
reprograma una tarea instalada. No hay loop ni scheduler embebido en FastAPI, ni infraestructura
cloud. Se preserva el código de salida para que el scheduler pueda identificar fallos.

## API y UI

- `GET /api/eureka/alerts` y `GET /api/eureka/alerts/{alert_id}`.
- `GET /api/eureka/radar-runs` y `GET /api/eureka/radar-runs/{run_id}`.
- Listas paginadas: `page`, `page_size` (máximo 100).
- `/eureka/alerts`: fecha, prioridad, región, presupuesto, productos, motivos, revisión y enlace
  al detalle original. La vista muestra snapshots, sin reenriquecer al consultarlos.
- La API de una corrida ofrece qué registros leyó, cuáles omitió y la etapa de cada fallo.

## Golden case y validación

CO1.REQ.11172521 se publicó el 2026-10-07: **no corresponde a la ventana desde 2026-10-13**.
Se acepta explícitamente con inicio 2026-10-07 y estado Radar vacío, sin modificar fechas ni score.
Debe producir alerta Alta, score 65, Jugo Hit 200 ml y Chocorramo tradicional 65 g, presupuesto
2.080.000 COP, ejecución 5 días, pago 30 días y póliza no requerida. Vigencia y habilitantes
desconocidos quedan visibles como revisión. Repetir la corrida no genera otra alerta.

Se validó en una base PostgreSQL independiente terminada en `_test`, con copia de solo lectura
del caso existente. Desarrollo permaneció en `0011_fact_consolidation`. Las corridas reales a
Socrata desde el 13 hasta el 14 de octubre devolvieron cero registros en las regiones configuradas:
ese resultado no se presenta como prueba de un enriquecimiento nuevo completo en vivo.

## Límites y Fase 4.2

- Falta muestra real reciente para calibrar score, afinidad, exclusiones y volumen operativo.
- La fecha de cierre de oferta está pendiente de incorporación con fuente oficial validada.
- Las familias nuevas dependen de los hechos que produzca la extracción determinística actual;
  el catálogo no amplía automáticamente los tipos/productos que puede extraer.
- La reanudación de un intento interno de extracción bloqueado requiere recuperación operativa.
- Se rescannea toda la ventana; optimización de consultas, cobertura y retención quedan pendientes.
- Corridas y alertas no tienen todavía administración multiusuario ni política de retención.
- **Seguimiento longitudinal de cambios de procesos ya conocidos** queda pendiente. Será
  especialmente importante para Observatorio/investigación: documentos nuevos, fases,
  presupuestos, reaperturas y adjudicaciones.
- OCR, RAG, agentes, Foundry y envío por correo/WhatsApp permanecen fuera de esta fase.

## Archivos de esta entrega

Nuevos, relativos a la raíz del proyecto:

```text
backend/config/eureka_radar.v1.json
backend/alembic/versions/0012_eureka_radar.py
backend/scripts/run_eureka_radar.ps1
backend/src/public_procurement/eureka/radar_config.py
backend/src/public_procurement/eureka/radar_services.py
backend/src/public_procurement/eureka/radar_repositories.py
backend/src/public_procurement/eureka/domain/affinity.py
backend/src/public_procurement/eureka/domain/radar.py
backend/src/public_procurement/eureka/adapters/radar_pipeline.py
backend/src/public_procurement/eureka/RADAR.md
backend/tests/unit/eureka/test_affinity.py
backend/tests/unit/eureka/test_radar.py
backend/tests/unit/eureka/test_radar_api.py
backend/tests/unit/eureka/test_radar_pipeline.py
backend/tests/unit/eureka/test_radar_repositories.py
backend/tests/unit/entrypoints/test_radar_cli.py
frontend/src/features/eureka/EurekaAlertsPage.tsx
frontend/src/features/eureka/EurekaAlertsPage.test.tsx
```

Modificados en esta fase, conservando los cambios previos de la beta:

```text
README.md
backend/.env.example
backend/pyproject.toml
backend/alembic/env.py
backend/src/public_procurement/shared/config.py
backend/src/public_procurement/ingestion/domain/process.py
backend/src/public_procurement/ingestion/adapters/socrata_processes.py
backend/src/public_procurement/ingestion/services.py
backend/src/public_procurement/eureka/services.py
backend/src/public_procurement/eureka/ports.py
backend/src/public_procurement/eureka/api.py
backend/src/public_procurement/entrypoints/cli/__main__.py
backend/src/public_procurement/entrypoints/api/app.py
backend/tests/unit/shared/test_config.py
backend/tests/unit/test_env_example.py
backend/tests/unit/ingestion/test_socrata_processes.py
backend/tests/integration/test_migrations.py
frontend/src/App.tsx
frontend/src/features/eureka/EurekaPage.tsx
frontend/src/features/eureka/useEureka.ts
frontend/src/api/openapi.json
frontend/src/api/schema.ts
```

Artefactos locales de aceptación, excluidos de Git: `backend/.local/radar41/` contiene
informes CLI, resumen de idempotencia/dry-run y capturas; los auxiliares de validación están
en `backend/.local/ui-validation/`. No son infraestructura del producto ni tareas instaladas.

Resultado: 498 pruebas unitarias backend, 59 pruebas de integración (58 de la beta y una
nueva de esquema Radar) y 60 pruebas frontend aprobadas. Import-linter conserva sus diez
contratos; Ruff, mypy, TypeScript, ESLint y build pasan. Las integraciones destructivas se
ejecutaron exclusivamente en una base nueva `public_procurement_radar41_integration_test`.
