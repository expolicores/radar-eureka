# Eureka Assistant — cinco tools de lectura

Sin frontend, Web Search ni nuevas reglas comerciales. Las tools leen servicios
existentes con transacciones PostgreSQL READ ONLY; no adquieren documentos, ejecutan
OCR, scoring, corridas ni escrituras. Se mantiene el modelo y las instrucciones
remotas al registrar la nueva versión del mismo agente.

## Schemas de las cuatro tools nuevas

Todas usan `type=function`, `strict=true`, `additionalProperties=false`.

```json
[
  {"type":"function","name":"get_run_alerts","parameters":{"type":"object","properties":{"run_id":{"type":"string"}},"required":["run_id"],"additionalProperties":false},"strict":true},
  {"type":"function","name":"get_run_review_candidates","parameters":{"type":"object","properties":{"run_id":{"type":"string"}},"required":["run_id"],"additionalProperties":false},"strict":true},
  {"type":"function","name":"get_process_detail","parameters":{"type":"object","properties":{"identity":{"type":"string"}},"required":["identity"],"additionalProperties":false},"strict":true},
  {"type":"function","name":"get_process_evidence","parameters":{"type":"object","properties":{"identity":{"type":"string"}},"required":["identity"],"additionalProperties":false},"strict":true}
]
```

El schema completo con descriptions, incluyendo get_latest_cdp_run, se imprime con
`python scripts/eureka_foundry_spike.py --show-tool-schema` y está respaldado en
`backend/.local/audits/foundry-five-tools/tool-schemas.json`.

El runtime valida UUID de corrida e identidad canónica exacta; rechaza campos
adicionales y funciones ajenas. No interpreta código de proceso como identidad ni
infiere equivalencias NTC–REQ.

## Semántica de salidas

- `get_run_alerts`: hasta 10 alertas **creadas** en esa corrida, con total/truncated.
  Una alerta anterior omitida por dedupe no se presenta como nueva de esa corrida.
- `get_run_review_candidates`: intersección de la corrida y la bandeja visible
  actual, excluyendo alertas, preservando sus reglas y ventana de siete días.
  Filtra antes de paginar; primero entradas con review_entry=new en esa corrida.
  Los contadores históricos del funnel pueden diferir de esta lista actual.
- `get_process_detail`: proyección consolidada por identidad y referencias oficiales
  explícitas, exista o no membresía de revisión. Incluye hasta diez corridas/alertas;
  no trae evidencia documental completa ni ratings privados/notas libres.
- `get_process_evidence`: hasta 20 facts, 20 canonicals, 10 documentos de extracción
  y 10 del inventario persistido. Incluye total/truncated y provenance. Fragmentos
  de evidencia de máximo 250 caracteres y dos referencias por fact. No carga texto
  documental completo ni entrega logs/snapshots/headers.
- Los campos ausentes siguen como null; no se inventan plazos, scores o montos.
  Estado de canonicals y alertas son persistidos, no recalculados. La validez temporal
  viene de la proyección existente y no representa una consulta nueva a SECOP.
- Un proceso sin extracción puede tener inventario, pero no evidencia textual;
  se diferencia de una identidad inexistente (`found=false`).
- Un fact solo se marca suspicious si existe ese atributo en su evidencia; el
  resumen de revisión del proceso se muestra aparte como suspicious_facts_reported.
  No se recalculan suspicious facts.
- Diagnósticos de cobertura completa tienen prioridad sobre contar solo páginas OCR
  en un PDF híbrido: pocas páginas OCR no equivalen a documento parcialmente leído.

## JSON de ejemplo

Caso de última corrida verificado localmente antes de inferencia:

```json
{"found":true,"run_id":"9e578b72-0e2d-4582-bbd6-4491d9764437","scope":"created_in_run","items":[],"total":0,"limit":10,"truncated":false}
```

Fragmento de un candidato (la salida real incluye el resto de campos):

```json
{
  "identity":"secop:CO1.NTC.11146017",
  "process_code":"MC-131-2026",
  "entity":"MUNICIPIO DE CUBARA BOYACA",
  "municipality":"Cubará",
  "department":"Boyacá",
  "amount":"34999000",
  "deadline":"2026-11-03T16:00:00-05:00",
  "validity":"open",
  "score":null,
  "commercial_decision":"Sin evaluar",
  "has_alert":false
}
```

Ejemplos completos de las cuatro tools: `backend/.local/audits/foundry-five-tools/examples.json`.
Ejemplo documental acotado: `documentary-example.json` en esa carpeta.

## Conversación y límites

Se conserva primera lectura get_latest_cdp_run para obtener run_id; las siguientes
tools las decide el modelo. Sin ejecución paralela. Máximo 12 calls y 13 turnos;
cache por nombre/argumentos y validación de call_id, con la misma conversación y
versión del agente en cada respuesta. Los outputs se devuelven como function_call_output.
El guard pide distinguir metadata, evidencia documental e inferencia, y exige
processes_total=encontrados/registrados, processed=procesados por pipeline.

## Validación

Tests mockean Foundry: cinco schemas, cada tool, vacíos, identidad desconocida,
límites, provenance, campos null, chaining, fallos sin escrituras y pinned version.
También se prueba que revisión filtre la corrida antes de paginar y priorice nuevos
sin incorporar alertas ni candidatos de otras corridas.

La prueba real autorizada se realizará una sola vez tras verificar versión/tools/tests:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_foundry_spike.py --agent-version <VERSION_VERIFICADA> "Revisa la última corrida CDP y dime si viste algo interesante para mí."
```

La creación de versión se verifica separadamente para evitar crear otra al ejecutar.
Las versiones previas se conservan. El registro de creación y el transcript se
guardan en `.local/audits/foundry-five-tools/` sin secretos ni endpoint del proyecto.

## Resultado de esta iteración

- Versión creada y verificada: **5**, derivada de **4**, mismo modelo
  `gpt-4.1-mini-eureka`, instrucciones conservadas con SHA-256
  `eb411aae1c8700cefed2f3c7e8acaf5ee23d9d24895d1e0319c574c8c69908ef`.
  Tools almacenadas: exactamente las cinco indicadas; ninguna Web Search. Las
  versiones 1–4 siguen disponibles. V4 ya tenía Web Search; se quitó solo de v5.
- 327 tests afectados pasan; Ruff, mypy y 13 contratos de arquitectura pasan.
  Suite general: 1185 pasan, 4 fallos previos por fixtures CDP con fechas fijas,
  1 omitido. No se alteraron reglas de vigencia ni fixtures para ocultar esos fallos.
- Se ejecutó **una sola pregunta real** sobre v5. El modelo solicitó únicamente
  `get_latest_cdp_run({})`. Recibió 144 encontrados, 17 recientes, 7 abiertos,
  3 procesados, 6 candidatos de revisión (3 nuevos/3 existentes), cero alertas.
- **Aceptación parcial:** la conexión/tool loop funcionan, pero el modelo no usó
  las cuatro tools nuevas y no priorizó casos concretos. Preguntó al usuario si
  quería consultar detalles, pese a la petición de revisión. Los tests mockeados
  de chaining pasan y las cuatro tools se validaron con lectura DB local; esto
  no equivale a validar su selección autónoma por el modelo en Azure.
- No se retocaron las instrucciones remotas ni se hizo una segunda prueba para
  forzar un resultado. Siguiente decisión: precisar la política de iniciativa
  conversacional manteniendo el principio de selección de casos por el agente.
- Evidencia: `created-version.json`, `tool-schemas.json`, `examples.json`,
  `documentary-example.json`, `spike-output.txt` y `result.json` en la carpeta local.
- La revisión automática inicialmente bloqueó la ejecución por dudas sobre el
  envío ampliado. Se verificaron la autorización explícita del adjunto y los
  campos de salida; la revisión de la misma acción fue aprobada antes de ejecutar.
  El intento bloqueado no inició ninguna conversación/prueba.

## Política de investigación — versión 6

Se aplicó la instrucción posterior del usuario a una nueva versión **6** del mismo
agente, conservando el contenido anterior de las instrucciones y añadiendo una
sección delimitada de investigación. Modelo y cinco tools sin cambios; versiones
anteriores conservadas. Hash de instrucciones verificado:
`46fcc136ce2148e59a8a141277c06b50acc8400e0bf1c736e9a5135f0b849bab`.

La política compartida está en `agents/eureka_assistant/policy.py`. Para solicitudes
de revisión/priorización/oportunidades, obliga a continuar leyendo alertas nuevas
y candidatos existentes antes de concluir, sin pedir confirmación. El agente decide
qué casos merecen detalle/evidencia; no hay consulta documental obligatoria para todos.
Para peticiones solo de resumen/métricas no se añaden lecturas innecesarias.

El runtime verifica que se hayan realizado las lecturas necesarias de **la misma
corrida**. Si el modelo devuelve una conclusión prematura, envía hasta dos
recordatorios developer en esa conversación. Si sigue omitiendo las lecturas,
falla explícitamente: no devuelve ese resumen como una investigación completada.
Se mantienen los topes de turnos, tiempo y calls; no se ejecutan tools ocultas ni
se sustituye la selección de casos del modelo por reglas comerciales nuevas.

Validación: **51 tests del agente pasan**, lint/formato/mypy y los 13 contratos de
arquitectura pasan. Tests incluyen resumen prematuro, chaining, cero alertas nuevas,
candidatos vacíos, petición de solo métricas y negativa repetida del modelo.

No se ejecutó otra prueba de inferencia en este cambio. Solo GET/creación/verificación
de la versión de instrucciones en Foundry. No se crearon conversaciones ni respuestas,
ni se consultaron/escribieron datos de procesos. Evidencia sanitizada:
`backend/.local/audits/foundry-investigation-policy/updated-version.json`.

Comando para una futura prueba autorizada:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_foundry_spike.py --agent-version 6 "Revisa la última corrida CDP y dime si viste algo interesante para mí."
```
